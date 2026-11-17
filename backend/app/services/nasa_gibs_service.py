import io
import math
from datetime import date, timedelta
from PIL import Image
from app.config import GIBS_LAYER, GIBS_TILE_MATRIX_SET, GIBS_TILE_ROOT, GIBS_ZOOM
from app.processing.image_comparison import compare_observations
from app.processing.image_features import extract_image_features
from app.services.image_download_service import download_cached_image

def _tile_for_point(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    count = 2 ** zoom
    x = min(count - 1, max(0, int((lon + 180) / 360 * count)))
    lat_rad = math.radians(max(-85.0511, min(85.0511, lat)))
    y = int((1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * count)
    return x, y

async def retrieve_imagery(lat: float, lon: float) -> dict:
    zoom, matrix = GIBS_ZOOM, GIBS_TILE_MATRIX_SET
    x, y = _tile_for_point(lat, lon, zoom)
    latest = date.today() - timedelta(days=20)
    observations, unavailable = [], []
    for age in (330, 240, 150, 60, 0):
        observation_date = latest - timedelta(days=age)
        url = (f"{GIBS_TILE_ROOT}/{GIBS_LAYER}/default/{observation_date}/"
               f"{matrix}/{zoom}/{y}/{x}.jpg")
        try:
            content = await download_cached_image(url)
            image = Image.open(io.BytesIO(content))
            observations.append({"date": observation_date.isoformat(),
                                 "source": f"NASA GIBS {GIBS_LAYER}", "url": url,
                                 "features": extract_image_features(image)})
        except Exception as exc:
            unavailable.append({"date": observation_date.isoformat(), "error": str(exc)})
    return {"source": f"NASA GIBS {GIBS_LAYER}", "layer": GIBS_LAYER,
            "projection": "EPSG:3857", "tile_matrix_set": matrix, "zoom": zoom,
            "observations": observations,
            "features": [item["features"] for item in observations],
            "changes": compare_observations(observations), "unavailable_dates": unavailable}
