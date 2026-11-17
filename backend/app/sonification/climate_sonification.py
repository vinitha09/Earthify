import numpy as np

PARAMETERS = ("T2M", "PRECTOTCORR", "WS2M", "RH2M", "ALLSKY_SFC_SW_DWN")


def _to_sound_scale(name: str, values: np.ndarray) -> np.ndarray:
    """Map NASA's physical units to shared global sound ranges.

    Fixed ranges retain differences between climates; per-location percentile
    scaling made every place span almost the same 0..1 range.
    """
    if name == "T2M":
        return np.clip((values + 30.0) / 70.0, 0.0, 1.0)  # -30 to 40 °C
    if name == "PRECTOTCORR":
        return np.clip(np.log1p(np.maximum(values, 0.0)) / np.log1p(50.0), 0.0, 1.0)
    if name == "WS2M":
        return np.clip(values / 20.0, 0.0, 1.0)  # 0 to 20 m/s
    if name == "RH2M":
        return np.clip(values / 100.0, 0.0, 1.0)  # 0 to 100 percent
    return np.clip(values / 30.0, 0.0, 1.0)  # solar energy, 0 to 30 kWh/m²/day

def normalize_climate(climate: dict, sample_count: int) -> dict:
    rows = climate["rows"]
    if not rows:
        raise ValueError("No NASA POWER observations available")
    count = min(24, len(rows))
    source_indexes = np.linspace(0, len(rows) - 1, count).astype(int)
    normalized = {}
    for name in PARAMETERS:
        values = np.array([rows[i].get(name, np.nan) for i in source_indexes], dtype=float)
        valid = np.isfinite(values)
        if valid.any():
            values = _to_sound_scale(name, np.where(valid, values, np.nanmedian(values)))
        else:
            values = np.full(count, 0.5)
        normalized[name] = np.interp(np.linspace(0, count - 1, sample_count),
                                     np.arange(count), values)
    return normalized
