const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch { /* Keep the HTTP status when the response is not JSON. */ }
    throw new Error(detail);
  }
  return response.json();
}

export const explorePoint = (lat, lon) => request("/api/explore", {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ lat, lon }),
});

export const createSoundscape = (lat, lon, factors = []) => request("/api/sonify", {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ lat, lon, duration: 30, factors }),
});

export const retrieveMonthlyClimate = (lat, lon) =>
  request(`/api/climate?lat=${lat}&lon=${lon}`);

export const searchLocations = (query) =>
  request(`/api/search?q=${encodeURIComponent(query)}`);

export const audioUrl = (path) => `${API}${path}`;
