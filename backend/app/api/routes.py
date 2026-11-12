
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.db.database import engine

from app.schemas.dashboard import (
    DashboardSummary,
    AnomalyResponse,
    FunnelStage,
    EvaluationResponse,
)

from app.services.dashboard_service import (
    get_dashboard_summary,
    get_anomalies,
    get_funnel,
)

from app.analytics.anomaly_detection import (
    detect_anomalies,
    evaluate_detection,
)

router = APIRouter(
    prefix="/api",
    tags=["Journey Intelligence"]
)


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummary
)
def dashboard_summary():

    with engine.connect() as conn:
        return get_dashboard_summary(conn)


@router.get(
    "/anomalies",
    response_model=list[AnomalyResponse]
)
def list_anomalies(
    issue_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
):

    with engine.connect() as conn:
        return get_anomalies(conn, issue_type, limit)


@router.get("/anomalies/detect", include_in_schema=False)
def detection_placeholder():
    raise HTTPException(
        status_code=405,
        detail="Use POST /api/anomalies/detect"
    )


@router.post("/anomalies/detect")
def run_detection():

    try:
        return detect_anomalies()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Anomaly detection failed."
        ) from exc


@router.get(
    "/sessions/{session_id}/events"
)
def get_session_events(session_id: str):

    query = text("""
        SELECT
            event_id,
            session_id,
            customer_id,
            page_id,
            event_type,
            channel,
            event_timestamp,
            ingestion_timestamp,
            deduplication_key,
            source_event_id,
            is_late
        FROM journey_events
        WHERE session_id = :session_id
        ORDER BY ingestion_timestamp ASC, event_id ASC
    """)

    with engine.connect() as conn:

        result = conn.execute(
            query,
            {"session_id": session_id}
        )

        events = [
            dict(row)
            for row in result.mappings().all()
        ]

        if not events:
            session_exists = conn.execute(
                text("""
                    SELECT 1
                    FROM sessions
                    WHERE session_id = :session_id
                    LIMIT 1
                """),
                {"session_id": session_id}
            ).first()

            if not session_exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} was not found."
                )

    return {
        "session_id": session_id,
        "total_events": len(events),
        "events": events
    }


@router.get(
    "/analytics/funnel",
    response_model=list[FunnelStage]
)
def analytics_funnel():

    with engine.connect() as conn:
        return get_funnel(conn)


@router.get(
    "/analytics/evaluation",
    response_model=EvaluationResponse
)
def analytics_evaluation():

    try:
        return evaluate_detection()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Detection evaluation failed."
        ) from exc


@router.get("/health")
def health():

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected"
    }
