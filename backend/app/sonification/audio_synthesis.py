import hashlib
import io

import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter, sosfilt

from app.config import SAMPLE_RATE
from app.sonification.audio_mixer import mix_tracks
from app.sonification.climate_sonification import normalize_climate

ALL_FACTORS = {"temperature", "rainfall", "wind", "humidity"}


def create_soundscape(climate: dict, imagery: dict | None, duration: int,
                      region: dict | None = None,
                      factors: list[str] | None = None) -> tuple[bytes, dict]:
    size = duration * SAMPLE_RATE
    weather = normalize_climate(climate, size)
    time = np.arange(size) / SAMPLE_RATE
    place_name = (region or {}).get("name", "")
    place_kind = (region or {}).get("kind", "")
    requested_factors = set(factors or []) & ALL_FACTORS
    active_factors = requested_factors or ALL_FACTORS

    seed = hashlib.sha256(
        f"{climate['rows']}:{duration}:{place_name}:{place_kind}".encode()
    ).digest()
    rng = np.random.default_rng(int.from_bytes(seed[:8], "big"))
    humidity_source = rng.normal(0, 1, size)
    wind_source = rng.normal(0, 1, size)
    tracks = []

    image_observations = (imagery or {}).get("observations", [])
    image_observations = [item for item in image_observations if item.get("features")]
    if len(image_observations) > 1:
        image_observations.sort(key=lambda item: item["date"])
        dates = [item["date"] for item in image_observations]
        start_day = np.datetime64(dates[0])
        day_span = max(1, int((np.datetime64(dates[-1]) - start_day).astype(int)))
        observation_positions = np.array([
            int((np.datetime64(day) - start_day).astype(int)) / day_span for day in dates
        ])
        image_time = np.linspace(0, 1, size)
        features = [item["features"] for item in image_observations]
        brightness = np.interp(image_time, observation_positions,
                               [feature.get("brightness", 0.5) for feature in features])
        variation = np.interp(image_time, observation_positions,
                              [feature.get("colour_variation", 0.25) for feature in features])
        rgb = np.stack([
            np.interp(image_time, observation_positions,
                      [feature.get("rgb_mean", [0.5, 0.5, 0.5])[channel]
                       for feature in features])
            for channel in range(3)
        ])
        image_hz = 180 + brightness * 220
        image_phase = 2 * np.pi * np.cumsum(image_hz) / SAMPLE_RATE
        image_tone = (np.sin(image_phase)
                      + (0.08 + 0.18 * rgb[0]) * np.sin(2 * image_phase)
                      + (0.05 + 0.16 * rgb[1]) * np.sin(3 * image_phase)
                      + (0.04 + 0.14 * rgb[2]) * np.sin(4 * image_phase))
        tracks.append(image_tone * (0.025 + variation * 0.07))

    if "temperature" in active_factors:
        temperature_hz = 110 * np.power(2.0, weather["T2M"] * 2.5)
        phase = 2 * np.pi * np.cumsum(temperature_hz) / SAMPLE_RATE
        temperature_tone = np.sin(phase) + 0.18 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)
        temperature_rhythm = 0.76 + 0.24 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * time))
        temperature_gain = 0.12 + weather["T2M"] * 0.9
        tracks.append(temperature_tone * temperature_rhythm * temperature_gain)

    if "rainfall" in active_factors:
        rain_rate = 0.15 + weather["PRECTOTCORR"] * 20
        rain_cycles = np.cumsum(rain_rate) / SAMPLE_RATE
        rain_events = (np.floor(rain_cycles) > np.floor(np.r_[0, rain_cycles[:-1]])).astype(float)
        droplet_decay = np.exp(-1 / (0.035 * SAMPLE_RATE))
        droplet_envelope = lfilter([1.0], [1.0, -droplet_decay], rain_events)
        droplet_pitch = 950 + weather["PRECTOTCORR"] * 550
        droplets = droplet_envelope * np.sin(2 * np.pi * droplet_pitch * time)
        rain_gain = 0.10 + weather["PRECTOTCORR"] * 0.75
        tracks.append(droplets * rain_gain)

    if "wind" in active_factors:
        wind_rate = 0.12 + weather["WS2M"] * 0.32
        wind_gusts = 0.22 + 0.78 * (0.5 + 0.5 * np.sin(2 * np.pi * wind_rate * time))
        wind_noise = sosfilt(butter(2, 0.22, btype="lowpass", output="sos"), wind_source)
        wind_gain = 0.02 + weather["WS2M"] * 0.25
        tracks.append(wind_noise * wind_gain * wind_gusts)

    if "humidity" in active_factors:
        humidity_rate = 0.55 + weather["RH2M"] * 0.9
        humidity_rhythm = 0.55 + 0.45 * (0.5 + 0.5 * np.sin(2 * np.pi * humidity_rate * time))
        humidity_texture = sosfilt(butter(2, 0.08, btype="lowpass", output="sos"), humidity_source)
        humidity_gain = 0.04 + weather["RH2M"] * 0.22
        tracks.append(humidity_texture * humidity_gain * humidity_rhythm)

    mixed = mix_tracks(tracks or [np.zeros(size)], SAMPLE_RATE)
    wav = io.BytesIO()
    sf.write(wav, np.column_stack((mixed, mixed)).astype(np.float32), SAMPLE_RATE,
             format="WAV", subtype="PCM_16")
    explanation = {
        "duration_seconds": duration,
        "sample_rate": SAMPLE_RATE,
        "selected_factors": sorted(requested_factors),
        "active_factors": sorted(active_factors),
        "factor_sounds": sorted(active_factors),
        "audio_source": "Distinct generated factor sounds from the selected climate conditions.",
        "selection_mode": "mixed" if not requested_factors else "selected factors only",
        "mapping": {
            "T2M": "absolute temperature controls pitch and slow pulse",
            "PRECTOTCORR": "rainfall controls droplet rate and intensity",
            "WS2M": "wind speed controls gust rhythm and noise intensity",
            "RH2M": "humidity controls a separate soft texture rhythm",
            "NASA GIBS RGB and brightness": "satellite image colours shape harmonics and brightness shapes pitch",
            "NASA GIBS colour variation": "image colour variation controls the image tone level",
        },
        "imagery_observations_used": len(image_observations),
        "climate_scaling": "Fixed shared physical ranges preserve climate differences between locations.",
        "region": region or {},
        "missing_climate_values": climate["missing_count"],
        "representation": "Synthetic sonification, not an environmental field recording.",
    }
    return wav.getvalue(), explanation