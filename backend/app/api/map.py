from fastapi import APIRouter, HTTPException, Query
from app.schemas.requests import ExploreRequest
from app.services.location_service import reverse_geocode, search_locations

router = APIRouter()

@router.post("/explore")
async def explore(request: ExploreRequest):
    place = await reverse_geocode(request.lat, request.lon)
    return {"coordinates": {"lat": request.lat, "lon": request.lon}, "location": place,
            "message": f"You selected {place['name']}. Retrieving observations."}

@router.get("/search")
async def search(q: str = Query(min_length=2, max_length=120)):
    try:
        return await search_locations(q)
    except Exception as exc:
        raise HTTPException(502, f"Location search unavailable: {exc}") from exc
