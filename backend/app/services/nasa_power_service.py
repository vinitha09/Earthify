import asyncio
import hashlib
import json
from datetime import date, timedelta
from app.config import CACHE_DIR, POWER_PARAMETERS, POWER_UNITS, POWER_URL
from app.processing.climate_processing import parse_power_response
from app.services.http_service import get_json

_IN_FLIGHT_FETCHES: dict[str, asyncio.Task[dict]] = {}

async def retrieve_climate(lat: float, lon: float) -> dict:
    end = date.today() - timedelta(days=5)
    start = end - timedelta(days=364)
    key = hashlib.sha256(f"{lat:.4f}:{lon:.4f}:{start}:{end}".encode()).hexdigest()
    cache = CACHE_DIR / f"power-{key}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    existing = _IN_FLIGHT_FETCHES.get(key)
    if existing is not None:
        return await existing

    async def fetch_climate() -> dict:
        try:
            params = {"parameters": POWER_PARAMETERS, "community": "AG", "longitude": lon,
                      "latitude": lat, "start": start.strftime("%Y%m%d"),
                      "end": end.strftime("%Y%m%d"), "format": "JSON", "time-standard": "UTC"}
            raw = await get_json(POWER_URL, params)
            climate = parse_power_response(raw, start, end, POWER_UNITS)
            cache.write_text(json.dumps(climate), encoding="utf-8")
            return climate
        finally:
            _IN_FLIGHT_FETCHES.pop(key, None)

    task = asyncio.create_task(fetch_climate())
    _IN_FLIGHT_FETCHES[key] = task
    return await task
