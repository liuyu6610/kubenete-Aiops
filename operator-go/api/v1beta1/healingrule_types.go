package v1beta1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

// GroupVersion is group version used to register these objects
var GroupVersion = schema.GroupVersion{Group: "kubesentinel.io", Version: "v1beta1"}

// SchemeBuilder is used to add go types to the GroupVersionKind scheme
var SchemeBuilder = runtime.NewSchemeBuilder(addKnownTypes)

// AddToScheme adds the types in this group-version to the given scheme.
var AddToScheme = SchemeBuilder.AddToScheme

func addKnownTypes(scheme *runtime.Scheme) error {
	scheme.AddKnownTypes(GroupVersion,
		&HealingRule{},
		&HealingRuleList{},
	)
	metav1.AddToGroupVersion(scheme, GroupVersion)
	return nil
}

// HealingRuleSpec defines the desired state of HealingRule
type HealingRuleSpec struct {
	// Action specifies the healing action e.g., "rolling_restart", "scale_up", "cordon_node"
	Action string `json:"action"`

	// TargetResource is the name of the resource to heal, e.g., "order-service"
	TargetResource string `json:"targetResource"`

	// TargetNamespace is the namespace of the resource
	TargetNamespace string `json:"targetNamespace"`

	// TriggerAlert is the name of the alert that caused this healing rule
	TriggerAlert string `json:"triggerAlert,omitempty"`

	// AIConfidence represents the confidence score from the LLM
	AIConfidence float64 `json:"aiConfidence,omitempty"`
}

// HealingRuleStatus defines the observed state of HealingRule
type HealingRuleStatus struct {
	// Phase represents the state of execution: Pending, Executing, Completed, Failed
	Phase string `json:"phase,omitempty"`

	// ExecutionTime marks when the action was taken
	ExecutionTime *metav1.Time `json:"executionTime,omitempty"`

	// Message holds human-readable execution details or error logs
	Message string `json:"message,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Action",type="string",JSONPath=".spec.action",description="The healing action to perform"
// +kubebuilder:printcolumn:name="Target",type="string",JSONPath=".spec.targetResource",description="Target resource"
// +kubebuilder:printcolumn:name="Phase",type="string",JSONPath=".status.phase",description="Execution status phase"

// HealingRule is the Schema for the healingrules API
type HealingRule struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   HealingRuleSpec   `json:"spec,omitempty"`
	Status HealingRuleStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// HealingRuleList contains a list of HealingRule
type HealingRuleList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []HealingRule `json:"items"`
}

// ----- Manual DeepCopy Implementations (to bypass needing controller-gen dependency for simple thesis demo) -----

func (in *HealingRule) DeepCopyInto(out *HealingRule) {
	*out = *in
	out.TypeMeta = in.TypeMeta
	in.ObjectMeta.DeepCopyInto(&out.ObjectMeta)
	out.Spec = in.Spec
	in.Status.DeepCopyInto(&out.Status)
}

func (in *HealingRule) DeepCopy() *HealingRule {
	if in == nil {
		return nil
	}
	out := new(HealingRule)
	in.DeepCopyInto(out)
	return out
}

func (in *HealingRule) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

func (in *HealingRuleList) DeepCopyInto(out *HealingRuleList) {
	*out = *in
	out.TypeMeta = in.TypeMeta
	in.ListMeta.DeepCopyInto(&out.ListMeta)
	if in.Items != nil {
		in, out := &in.Items, &out.Items
		*out = make([]HealingRule, len(*in))
		for i := range *in {
			(*in)[i].DeepCopyInto(&(*out)[i])
		}
	}
}

func (in *HealingRuleList) DeepCopy() *HealingRuleList {
	if in == nil {
		return nil
	}
	out := new(HealingRuleList)
	in.DeepCopyInto(out)
	return out
}

func (in *HealingRuleList) DeepCopyObject() runtime.Object {
	if c := in.DeepCopy(); c != nil {
		return c
	}
	return nil
}

func (in *HealingRuleStatus) DeepCopyInto(out *HealingRuleStatus) {
	*out = *in
	if in.ExecutionTime != nil {
		in, out := &in.ExecutionTime, &out.ExecutionTime
		*out = (*in).DeepCopy()
	}
}
