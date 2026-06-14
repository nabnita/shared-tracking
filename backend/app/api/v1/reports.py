from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_reports():
    """List import reports. Implemented in Phase 7."""
    return {"message": "Reports endpoint — coming in Phase 7"}
