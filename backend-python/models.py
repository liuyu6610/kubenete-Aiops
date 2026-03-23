from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AlertPayload(BaseModel):
    status: str
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None

class AlertmanagerWebhook(BaseModel):
    status: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    alerts: Optional[list[AlertPayload]] = None
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None

class HealingTarget(BaseModel):
    resource_type: str = Field(description="e.g., 'deployment', 'statefulset', 'node'")
    name: str = Field(description="Name of the target resource to heal")
    namespace: str = Field(default="default", description="Namespace of the resource")

class HealingDecision(BaseModel):
    analysis: str = Field(description="Detailed explanation of the root cause and reasoning")
    root_cause: str = Field(default="", description="Concise root cause determination")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    action: str = Field(description="The automated action to perform: 'rolling_restart', 'scale_up', 'rollback', etc.")
    target: HealingTarget = Field(description="The specific resource to apply the action to")
    fallback: Optional[str] = Field(default="none", description="Action to take if the primary action fails")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for the action")
    risk_level: str = Field(default="medium", description="Risk level: 'low', 'medium', 'high'")
    human_approval_required: bool = Field(default=False, description="Whether human approval is needed before execution")
    notify: bool = Field(default=True, description="Whether to send a notification for this event")
    summary_for_notification: str = Field(default="", description="Short summary for push notification (Feishu/DingTalk)")

class StatsResponse(BaseModel):
    total_alerts_today: int = 0
    auto_healed_count: int = 0
    success_rate: float = 0.0
    pending_approval: int = 0
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list)
