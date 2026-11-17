import numpy as np

def mix_tracks(tracks: list[np.ndarray], sample_rate: int) -> np.ndarray:
    signal = np.sum(np.stack(tracks), axis=0)
    fade = min(int(0.5 * sample_rate), len(signal) // 2)
    if fade:
        signal[:fade] *= np.linspace(0, 1, fade)
        signal[-fade:] *= np.linspace(1, 0, fade)
    return np.tanh(signal * 1.5)
