package controller

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"

	kubesentinelv1beta1 "github.com/kubesentinel/autohealer-operator/api/v1beta1"
	appsv1 "k8s.io/api/apps/v1"
	autoscalingv2 "k8s.io/api/autoscaling/v2"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

// HealingRuleReconciler reconciles a HealingRule object
type HealingRuleReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// callbackURL is the Python backend URL for notifying execution results
var callbackURL = getEnv("BACKEND_CALLBACK_URL", "http://kubesentinel-backend:8000")

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// Reconcile is the main kubernetes reconciliation loop
func (r *HealingRuleReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	// Fetch the HealingRule instance
	var rule kubesentinelv1beta1.HealingRule
	if err := r.Get(ctx, req.NamespacedName, &rule); err != nil {
		if errors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		logger.Error(err, "Failed to get HealingRule")
		return ctrl.Result{}, err
	}

	// 1. Skip if already finished
	if rule.Status.Phase == "Completed" || rule.Status.Phase == "Failed" {
		return ctrl.Result{}, nil
	}

	// 2. Mark as executing
	if rule.Status.Phase == "" || rule.Status.Phase == "Pending" {
		rule.Status.Phase = "Executing"
		if err := r.Status().Update(ctx, &rule); err != nil {
			logger.Error(err, "Failed to update HealingRule status to Executing")
			return ctrl.Result{}, err
		}
		logger.Info("Starting execution of HealingRule", "Action", rule.Spec.Action, "Target", rule.Spec.TargetResource)
	}

	// 3. Execute the action
	var execErr error
	targetName := sanitizeTargetName(rule.Spec.TargetResource)

	switch rule.Spec.Action {
	case "rolling_restart":
		execErr = r.performRollingRestart(ctx, rule.Spec.TargetNamespace, targetName)
	case "scale_up":
		execErr = r.performScaleUp(ctx, rule.Spec.TargetNamespace, targetName)
	case "scale_down":
		execErr = r.performScaleDown(ctx, rule.Spec.TargetNamespace, targetName)
	case "rollback":
		execErr = r.performRollback(ctx, rule.Spec.TargetNamespace, targetName)
	case "delete_pod":
		execErr = r.performDeletePod(ctx, rule.Spec.TargetNamespace, targetName)
	case "adjust_hpa":
		execErr = r.performAdjustHPA(ctx, rule.Spec.TargetNamespace, targetName)
	case "cordon_node":
		execErr = r.performCordonNode(ctx, targetName)
	case "evict_pods":
		execErr = r.performEvictPods(ctx, rule.Spec.TargetNamespace, targetName)
	default:
		execErr = fmt.Errorf("unknown action type: %s", rule.Spec.Action)
	}

	// 4. Update final status
	now := metav1.Now()
	rule.Status.ExecutionTime = &now

	if execErr != nil {
		logger.Error(execErr, "Healing execution failed", "Action", rule.Spec.Action)
		rule.Status.Phase = "Failed"
		rule.Status.Message = execErr.Error()
	} else {
		logger.Info("Healing execution succeeded", "Action", rule.Spec.Action)
		rule.Status.Phase = "Completed"
		rule.Status.Message = "Action executed successfully by KubeSentinel Operator"
	}

	if err := r.Status().Update(ctx, &rule); err != nil {
		logger.Error(err, "Failed to update final HealingRule status")
		return ctrl.Result{}, err
	}

	// 5. Callback to Python backend (best-effort, non-blocking)
	go r.notifyBackend(rule.Name, rule.Spec.Action, rule.Status.Phase, rule.Status.Message)

	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *HealingRuleReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&kubesentinelv1beta1.HealingRule{}).
		Complete(r)
}

// --- Action Implementations ---

func sanitizeTargetName(raw string) string {
	parts := strings.Split(raw, "/")
	if len(parts) > 1 {
		return parts[1]
	}
	return raw
}

func (r *HealingRuleReconciler) performRollingRestart(ctx context.Context, namespace, targetResource string) error {
	var dep appsv1.Deployment
	if err := r.Get(ctx, types.NamespacedName{Name: targetResource, Namespace: namespace}, &dep); err != nil {
		return fmt.Errorf("failed to get deployment %s/%s: %v", namespace, targetResource, err)
	}

	if dep.Spec.Template.Annotations == nil {
		dep.Spec.Template.Annotations = make(map[string]string)
	}
	dep.Spec.Template.Annotations["kubesentinel.io/restartedAt"] = time.Now().Format(time.RFC3339)

	if err := r.Update(ctx, &dep); err != nil {
		return fmt.Errorf("failed to update deployment annotations: %v", err)
	}
	return nil
}

func (r *HealingRuleReconciler) performScaleUp(ctx context.Context, namespace, targetResource string) error {
	var dep appsv1.Deployment
	if err := r.Get(ctx, types.NamespacedName{Name: targetResource, Namespace: namespace}, &dep); err != nil {
		return fmt.Errorf("failed to get deployment %s/%s: %v", namespace, targetResource, err)
	}

	if dep.Spec.Replicas != nil {
		newReplicas := *dep.Spec.Replicas + 1
		dep.Spec.Replicas = &newReplicas
		if err := r.Update(ctx, &dep); err != nil {
			return fmt.Errorf("failed to scale up deployment: %v", err)
		}
	} else {
		return fmt.Errorf("deployment %s does not have replicas set", targetResource)
	}
	return nil
}

func (r *HealingRuleReconciler) performScaleDown(ctx context.Context, namespace, targetResource string) error {
	var dep appsv1.Deployment
	if err := r.Get(ctx, types.NamespacedName{Name: targetResource, Namespace: namespace}, &dep); err != nil {
		return fmt.Errorf("failed to get deployment %s/%s: %v", namespace, targetResource, err)
	}

	if dep.Spec.Replicas != nil && *dep.Spec.Replicas > 1 {
		newReplicas := *dep.Spec.Replicas - 1
		dep.Spec.Replicas = &newReplicas
		if err := r.Update(ctx, &dep); err != nil {
			return fmt.Errorf("failed to scale down deployment: %v", err)
		}
	} else {
		return fmt.Errorf("deployment %s replicas already at minimum or not set", targetResource)
	}
	return nil
}

func (r *HealingRuleReconciler) performRollback(ctx context.Context, namespace, targetResource string) error {
	// Rollback strategy: find the previous ReplicaSet and update the Deployment spec to match
	var dep appsv1.Deployment
	if err := r.Get(ctx, types.NamespacedName{Name: targetResource, Namespace: namespace}, &dep); err != nil {
		return fmt.Errorf("failed to get deployment %s/%s: %v", namespace, targetResource, err)
	}

	// List ReplicaSets owned by this Deployment
	var rsList appsv1.ReplicaSetList
	if err := r.List(ctx, &rsList, client.InNamespace(namespace)); err != nil {
		return fmt.Errorf("failed to list replicasets in %s: %v", namespace, err)
	}

	// Filter ReplicaSets that belong to this Deployment
	var ownedRS []appsv1.ReplicaSet
	for _, rs := range rsList.Items {
		for _, ref := range rs.OwnerReferences {
			if ref.UID == dep.UID {
				ownedRS = append(ownedRS, rs)
				break
			}
		}
	}

	if len(ownedRS) < 2 {
		return fmt.Errorf("no previous revision found for deployment %s (only %d ReplicaSets)", targetResource, len(ownedRS))
	}

	// Sort by revision annotation (descending)
	sort.Slice(ownedRS, func(i, j int) bool {
		revI := ownedRS[i].Annotations["deployment.kubernetes.io/revision"]
		revJ := ownedRS[j].Annotations["deployment.kubernetes.io/revision"]
		return revI > revJ
	})

	// The second one is the previous revision
	previousRS := ownedRS[1]

	// Apply the previous RS's pod template to the deployment
	dep.Spec.Template.Spec = previousRS.Spec.Template.Spec
	if dep.Spec.Template.Annotations == nil {
		dep.Spec.Template.Annotations = make(map[string]string)
	}
	dep.Spec.Template.Annotations["kubesentinel.io/rolledBackAt"] = time.Now().Format(time.RFC3339)

	if err := r.Update(ctx, &dep); err != nil {
		return fmt.Errorf("failed to rollback deployment: %v", err)
	}
	return nil
}

func (r *HealingRuleReconciler) performDeletePod(ctx context.Context, namespace, podName string) error {
	var pod corev1.Pod
	if err := r.Get(ctx, types.NamespacedName{Name: podName, Namespace: namespace}, &pod); err != nil {
		return fmt.Errorf("failed to get pod %s/%s: %v", namespace, podName, err)
	}

	if err := r.Delete(ctx, &pod); err != nil {
		return fmt.Errorf("failed to delete pod %s/%s: %v", namespace, podName, err)
	}
	return nil
}

func (r *HealingRuleReconciler) performAdjustHPA(ctx context.Context, namespace, targetResource string) error {
	var hpa autoscalingv2.HorizontalPodAutoscaler
	if err := r.Get(ctx, types.NamespacedName{Name: targetResource, Namespace: namespace}, &hpa); err != nil {
		return fmt.Errorf("failed to get HPA %s/%s: %v", namespace, targetResource, err)
	}

	// Default: increase maxReplicas by 2, minReplicas by 1
	if hpa.Spec.MaxReplicas > 0 {
		hpa.Spec.MaxReplicas = hpa.Spec.MaxReplicas + 2
	}
	if hpa.Spec.MinReplicas != nil {
		newMin := *hpa.Spec.MinReplicas + 1
		hpa.Spec.MinReplicas = &newMin
	}

	if err := r.Update(ctx, &hpa); err != nil {
		return fmt.Errorf("failed to adjust HPA: %v", err)
	}
	return nil
}

func (r *HealingRuleReconciler) performCordonNode(ctx context.Context, targetNode string) error {
	var node corev1.Node
	if err := r.Get(ctx, types.NamespacedName{Name: targetNode}, &node); err != nil {
		return fmt.Errorf("failed to get node %s: %v", targetNode, err)
	}

	node.Spec.Unschedulable = true
	if err := r.Update(ctx, &node); err != nil {
		return fmt.Errorf("failed to cordon node: %v", err)
	}
	return nil
}

func (r *HealingRuleReconciler) performEvictPods(ctx context.Context, namespace, targetNode string) error {
	// List all pods on the given node
	var podList corev1.PodList
	if err := r.List(ctx, &podList, client.MatchingFields{"spec.nodeName": targetNode}); err != nil {
		return fmt.Errorf("failed to list pods on node %s: %v", targetNode, err)
	}

	var lastErr error
	evicted := 0
	for i := range podList.Items {
		pod := &podList.Items[i]
		// Skip DaemonSet pods and system pods
		if pod.Namespace == "kube-system" {
			continue
		}
		if err := r.Delete(ctx, pod, client.GracePeriodSeconds(30)); err != nil {
			lastErr = err
		} else {
			evicted++
		}
	}

	if lastErr != nil {
		return fmt.Errorf("evicted %d pods but encountered errors, last: %v", evicted, lastErr)
	}
	return nil
}

// --- Callback to Python backend ---

func (r *HealingRuleReconciler) notifyBackend(ruleName, action, phase, message string) {
	payload := map[string]string{
		"rule_name": ruleName,
		"action":    action,
		"phase":     phase,
		"message":   message,
	}
	body, _ := json.Marshal(payload)

	url := fmt.Sprintf("%s/api/v1/operator/callback", callbackURL)
	resp, err := http.Post(url, "application/json", bytes.NewReader(body))
	if err != nil {
		// Best-effort, log and move on
		return
	}
	defer resp.Body.Close()
}
