import asyncio
import io
from datetime import date

import numpy as np
import pytest
import soundfile as sf
from PIL import Image
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.main import app
from app.processing.climate_processing import aggregate_monthly_climate, parse_power_response
from app.processing.image_comparison import compare_observations
from app.processing.image_features import extract_image_features
from app.schemas.requests import ExploreRequest, SonifyRequest
from app.sonification.audio_mixer import mix_tracks
from app.sonification.audio_synthesis import create_soundscape
from app.sonification.climate_sonification import normalize_climate
from app.sonification.image_sonification import interpolate_image_features
from app.services import nasa_gibs_service, nasa_power_service

client = TestClient(app)

def climate_fixture():
    rows = [{"T2M": 10 + i, "PRECTOTCORR": i % 4, "WS2M": 2 + i * .1,
             "RH2M": 50 + i, "ALLSKY_SFC_SW_DWN": 12 - i * .1}
            for i in range(30)]
    return {"rows": rows, "missing_count": 0}

def image_fixture(colour=(25, 140, 60)):
    return extract_image_features(Image.new("RGB", (64, 64), colour))

def imagery_fixture():
    return {"features": [image_fixture(), image_fixture((90, 90, 120))],
            "observations": [], "changes": []}

def test_power_parser_preserves_dates_units_and_missing_values():
    raw = {"properties": {"parameter": {
        "T2M": {"20260101": 21.0, "20260102": -999},
        "WS2M": {"20260101": 3.0, "20260102": 4.0},
    }}}
    parsed = parse_power_response(raw, date(2026, 1, 1), date(2026, 1, 2),
                                  {"T2M": "deg C", "WS2M": "m/s"})
    assert parsed["rows"][0]["T2M"] == 21
    assert parsed["rows"][1]["T2M"] is None
    assert parsed["units"]["WS2M"] == "m/s"
    assert parsed["missing_count"] == 1

def test_monthly_climate_aggregates_daily_rows_and_skips_missing_values():
    climate = {"rows": [
        {"date": "20260101", "T2M": 10, "PRECTOTCORR": 2, "WS2M": 4, "RH2M": 60},
        {"date": "20260102", "T2M": 12, "PRECTOTCORR": None, "WS2M": 6, "RH2M": 80},
        {"date": "20260201", "T2M": 8, "PRECTOTCORR": 1, "WS2M": 3, "RH2M": None},
    ]}
    assert aggregate_monthly_climate(climate) == [
        {"month": "2026-01", "T2M": 11, "PRECTOTCORR": 2, "WS2M": 5, "RH2M": 70},
        {"month": "2026-02", "T2M": 8, "PRECTOTCORR": 1, "WS2M": 3},
    ]

def test_concurrent_climate_requests_share_the_same_fetch(monkeypatch, tmp_path):
    calls = 0
    parameters = {
        name: {"20260101": 1.0}
        for name in nasa_power_service.POWER_PARAMETERS.split(",")
    }

    async def fake_get_json(url, params):
        nonlocal calls
        calls += 1
        await asyncio.sleep(.01)
        return {"properties": {"parameter": parameters}}

    monkeypatch.setattr(nasa_power_service, "get_json", fake_get_json)
    monkeypatch.setattr(nasa_power_service, "CACHE_DIR", tmp_path)

    async def retrieve_twice():
        return await asyncio.gather(
            nasa_power_service.retrieve_climate(12.3456, 23.4567),
            nasa_power_service.retrieve_climate(12.3456, 23.4567),
        )

    first, second = asyncio.run(retrieve_twice())
    assert calls == 1
    assert first == second

def test_coordinate_validation_rejects_out_of_range_values():
    with pytest.raises(ValidationError):
        ExploreRequest(lat=91, lon=0)
    with pytest.raises(ValidationError):
        SonifyRequest(lat=0, lon=0, duration=31)

def test_image_features_and_temporal_comparison():
    first, second = image_fixture(), image_fixture((200, 180, 160))
    assert len(first["rgb_mean"]) == 3 and first["texture"] >= 0
    changes = compare_observations([{"features": first}, {"features": second}])
    assert len(changes) == 1 and changes[0] > 0

def test_climate_normalization_and_image_interpolation():
    climate = normalize_climate(climate_fixture(), 128)
    assert set(climate) == {"T2M", "PRECTOTCORR", "WS2M", "RH2M", "ALLSKY_SFC_SW_DWN"}
    assert all(v.shape == (128,) and np.nanmin(v) >= 0 and np.nanmax(v) <= 1
               for v in climate.values())
    visual = interpolate_image_features([image_fixture(), image_fixture((240, 240, 240))], 128)
    assert visual["rgb"].shape == (3, 128)
    assert visual["brightness"][-1] > visual["brightness"][0]

def test_audio_mix_uses_distinct_factor_sounds_and_is_climate_sensitive():
    mixed = mix_tracks([np.ones(100), np.ones(100) * .1], 100)
    assert len(mixed) == 100 and mixed[0] == 0 and mixed[-1] == 0
    climate, imagery = climate_fixture(), imagery_fixture()
    audio1, explanation = create_soundscape(climate, imagery, 8)
    audio2, _ = create_soundscape(climate, imagery, 8)
    assert audio1 == audio2
    data, rate = sf.read(io.BytesIO(audio1))
    assert rate == 22050 and data.shape == (8 * rate, 2)
    assert set(explanation["factor_sounds"]) == {
        "temperature", "rainfall", "wind", "humidity",
    }
    assert explanation["audio_source"].startswith("Distinct generated factor sounds")

    factor_audio = [
        create_soundscape(climate, None, 8, factors=[factor])[0]
        for factor in ("temperature", "rainfall", "wind", "humidity")
    ]
    assert len(set(factor_audio)) == 4

    alternate_imagery = {"observations": [{
        "date": "2026-01-01",
        "features": {"brightness": 1, "colour_variation": 1, "rgb_mean": [1, 0, 0]},
    }]}
    audio_without_image_layer, _ = create_soundscape(climate, alternate_imagery, 8)
    assert audio1 == audio_without_image_layer

    climate["rows"][10]["T2M"] += 30
    audio_changed, _ = create_soundscape(climate, imagery, 8)
    assert audio1 != audio_changed and explanation["duration_seconds"] == 8

@pytest.mark.parametrize(("factor", "field", "low", "high"), [
    ("temperature", "T2M", -30, 40),
    ("rainfall", "PRECTOTCORR", 0, 50),
    ("wind", "WS2M", 0, 20),
    ("humidity", "RH2M", 0, 100),
])
def test_factor_audio_intensity_increases_with_climate(factor, field, low, high):
    low_climate = climate_fixture()
    high_climate = climate_fixture()
    for row in low_climate["rows"]:
        row[field] = low
    for row in high_climate["rows"]:
        row[field] = high

    low_wav, _ = create_soundscape(low_climate, None, 8, factors=[factor])
    high_wav, _ = create_soundscape(high_climate, None, 8, factors=[factor])
    low_audio, _ = sf.read(io.BytesIO(low_wav))
    high_audio, _ = sf.read(io.BytesIO(high_wav))

    low_level = np.sqrt(np.mean(low_audio ** 2))
    high_level = np.sqrt(np.mean(high_audio ** 2))
    assert high_level > low_level * 1.8

def test_gibs_service_uses_valid_matrix_and_extracts_multiple_dates(monkeypatch):
    buffer = io.BytesIO()
    Image.new("RGB", (256, 256), (80, 120, 60)).save(buffer, format="JPEG")
    async def fake_download(url):
        assert "GoogleMapsCompatible_Level9/6/" in url
        return buffer.getvalue()
    monkeypatch.setattr(nasa_gibs_service, "download_cached_image", fake_download)
    result = asyncio.run(nasa_gibs_service.retrieve_imagery(0, 0))
    assert len(result["observations"]) == 5
    assert result["tile_matrix_set"] == "GoogleMapsCompatible_Level9"

def test_api_health_and_coordinate_errors():
    assert client.get("/api/health").json() == {"status": "ok"}
    response = client.post("/api/explore", json={"lat": 100, "lon": 0})
    assert response.status_code == 422
