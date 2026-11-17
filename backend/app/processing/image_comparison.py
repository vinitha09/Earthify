import numpy as np

def _vector(features: dict) -> np.ndarray:
    return np.array(features["rgb_mean"] + [features[k] for k in (
        "brightness", "colour_variation", "texture", "green_fraction",
        "bright_low_saturation_fraction")], dtype=float)

def compare_observations(observations: list[dict]) -> list[float]:
    features = [item["features"] for item in observations]
    return [round(float(np.mean(np.abs(_vector(features[i]) - _vector(features[i - 1])))), 4)
            for i in range(1, len(features))]
