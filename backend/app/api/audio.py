import asyncio
import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import AUDIO_DIR
from app.processing.climate_processing import aggregate_monthly_climate
from app.schemas.requests import SonifyRequest
from app.services.location_service import reverse_geocode
from app.services.nasa_power_service import retrieve_climate
from app.services.nasa_gibs_service import retrieve_imagery
from app.sonification.audio_synthesis import create_soundscape

router = APIRouter()

@router.post("/sonify")
async def sonify(request: SonifyRequest):
    place = await reverse_geocode(request.lat, request.lon)
    try:
        climate, imagery = await asyncio.gather(
            retrieve_climate(request.lat, request.lon),
            retrieve_imagery(request.lat, request.lon),
            return_exceptions=True,
        )
        if isinstance(climate, Exception):
            raise climate
        if isinstance(imagery, Exception):
            imagery = {"source": "NASA GIBS", "observations": [],
                       "unavailable_dates": [{"error": str(imagery)}]}
        wav, explanation = await asyncio.to_thread(
            create_soundscape, climate, imagery, request.duration, place, request.factors
        )
        monthly_climate = aggregate_monthly_climate(climate)
        audio_id = uuid.uuid4().hex
        (AUDIO_DIR / f"{audio_id}.wav").write_bytes(wav)
        result = {"audio_id": audio_id, "audio_url": f"/api/audio/{audio_id}",
                  "coordinates": {"lat": request.lat, "lon": request.lon}, "location": place,
                  "climate": climate, "imagery": imagery,
                  "monthly_climate": monthly_climate,
                  "explanation": explanation}
        (AUDIO_DIR / f"{audio_id}.json").write_text(json.dumps(result), encoding="utf-8")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Soundscape generation failed: {exc}") from exc
def _metadata_path(audio_id: str):
    if len(audio_id) != 32 or any(c not in "0123456789abcdef" for c in audio_id):
        raise HTTPException(404, "Audio not found")
    return AUDIO_DIR / f"{audio_id}"

@router.get("/audio/{audio_id}")
def audio(audio_id: str):
    path = _metadata_path(audio_id).with_suffix(".wav")
    if not path.exists():
        raise HTTPException(404, "Audio not found")
    return FileResponse(path, media_type="audio/wav")

@router.get("/explanation/{audio_id}")
def explanation(audio_id: str):
    path = _metadata_path(audio_id).with_suffix(".json")
    if not path.exists():
        raise HTTPException(404, "Explanation not found")
    return json.loads(path.read_text(encoding="utf-8"))
