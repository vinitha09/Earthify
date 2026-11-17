import numpy as np

def interpolate_image_features(features: list[dict], sample_count: int) -> dict:
    if not features:
        return {"rgb": np.tile(np.array([[0.3], [0.3], [0.4]]), (1, sample_count)),
                "brightness": np.full(sample_count, 0.4), "texture": np.full(sample_count, 0.2),
                "green": np.full(sample_count, 0.2), "pale": np.full(sample_count, 0.2)}
    indexes = np.linspace(0, sample_count - 1, len(features))
    samples = np.arange(sample_count)
    return {
        "rgb": np.array([np.interp(samples, indexes, [f["rgb_mean"][c] for f in features])
                         for c in range(3)]),
        "brightness": np.interp(samples, indexes, [f["brightness"] for f in features]),
        "texture": np.interp(samples, indexes, [f["texture"] for f in features]),
        "green": np.interp(samples, indexes, [f["green_fraction"] for f in features]),
        "pale": np.interp(samples, indexes, [f["bright_low_saturation_fraction"] for f in features]),
    }
