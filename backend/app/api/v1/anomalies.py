from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_anomalies():
    """List anomalies. Implemented in Phase 8."""
    return {"message": "Anomalies endpoint — coming in Phase 8"}
