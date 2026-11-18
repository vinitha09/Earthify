
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Vercel has a read-only application directory.
# Use /tmp for temporary runtime files.
if os.getenv("VERCEL"):
    STORAGE_DIR = Path("/tmp/earthify")
else:
    STORAGE_DIR = BACKEND_DIR

AUDIO_DIR = STORAGE_DIR / "generated_audio"
CACHE_DIR = STORAGE_DIR / ".cache"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

GIBS_TILE_ROOT = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"
GIBS_LAYER = "MODIS_Terra_CorrectedReflectance_TrueColor"
GIBS_TILE_MATRIX_SET = "GoogleMapsCompatible_Level9"
GIBS_ZOOM = 6

POWER_PARAMETERS = "T2M,PRECTOTCORR,WS2M,RH2M,ALLSKY_SFC_SW_DWN"

POWER_UNITS = {
    "T2M": "deg C",
    "PRECTOTCORR": "mm/day",
    "WS2M": "m/s",
    "RH2M": "percent",
    "ALLSKY_SFC_SW_DWN": "kWh/m^2/day",
}

SAMPLE_RATE = 22050
