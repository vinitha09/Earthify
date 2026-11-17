from fastapi import APIRouter, HTTPException, Query
from app.services.nasa_power_service import retrieve_climate

router = APIRouter()

@router.get("/climate")
async def climate(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)):
    try:
        return await retrieve_climate(lat, lon)
    except Exception as exc:
        raise HTTPException(502, f"NASA POWER unavailable: {exc}") from exc
