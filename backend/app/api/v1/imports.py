from fastapi import APIRouter

router = APIRouter()


@router.post("", status_code=202)
async def upload_csv():
    """Upload a CSV file for import. Implemented in Phase 4."""
    return {"message": "CSV import endpoint — coming in Phase 4"}
