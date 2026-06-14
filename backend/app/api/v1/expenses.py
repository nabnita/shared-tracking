from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_expenses():
    """List expenses. Implemented in Phase 8."""
    return {"message": "Expenses endpoint — coming in Phase 8"}
