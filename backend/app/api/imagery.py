from fastapi import APIRouter, HTTPException, Query
from app.services.nasa_gibs_service import retrieve_imagery

router = APIRouter()

@router.get("/imagery")
async def imagery(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)):
    try:
        return await retrieve_imagery(lat, lon)
    except Exception as exc:
        raise HTTPException(502, f"NASA GIBS unavailable: {exc}") from exc
