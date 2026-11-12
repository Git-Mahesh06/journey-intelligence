
from pydantic import BaseModel
from typing import Optional


class DashboardSummary(BaseModel):
    total_sessions: int
    total_events: int
    total_conversions: int
    conversion_rate: float
    total_anomalies: int
    open_anomalies: int
    total_revenue: float


class AnomalyResponse(BaseModel):
    anomaly_id: str
    session_id: Optional[str] = None
    event_id: Optional[str] = None
    issue_type: str
    severity: str
    detection_reason: str
    detection_rule: str
    resolution_status: str



class FunnelStage(BaseModel):
    stage: str
    stage_order: int
    sessions: int
    conversion_percentage: float
    conversion_from_previous: float
    dropoff_sessions: int
    dropoff_percentage: float



class EvaluationResponse(BaseModel):
    expected: int
    detected: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
