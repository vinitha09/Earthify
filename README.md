# Earth Jukebox

## Project description

EARTHIFY (Earth Jukebox) is an interactive climate exploration app that lets users select a place on a 3D globe and explore its recent climate. It charts monthly temperature, rainfall, wind, and humidity trends, then turns those factors into distinct sounds whose intensity follows the climate data. Spoken place names and a pauseable audio story make the graph easier to explore through listening as well as sight.

## Technologies used

- **Frontend:** React, JavaScript, Vite, CSS, and WebGL for the interactive globe.
- **Backend:** Python, FastAPI, and Pydantic for the API and request validation.
- **Data and media processing:** NASA POWER climate data, NASA imagery, OpenStreetMap Nominatim geocoding, HTTPX, NumPy, SciPy, SoundFile, Pillow, and OpenCV.
- **Testing:** Pytest for backend tests and Vite’s production build for frontend validation.

## Run

Requires Python 3.11+ and Node.js 20+.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. No NASA credentials are required. Optional `.env` setting: `VITE_API_URL=http://localhost:8000`. API docs: http://localhost:8000/docs.

Run backend unit tests from `backend` with `python -m pytest`.

## Project layout

- `frontend/src/components/` contains the map, voice assistant, player, location details, and loading status components. `frontend/src/services/api.js` owns backend requests.
- `backend/app/api/` defines the HTTP routes. `services/` handles geocoding, NASA requests, and cached imagery downloads. `processing/` parses POWER data and extracts/compares image features. `sonification/` normalizes climate inputs, generates distinct factor sounds, and mixes them. `schemas/` validates requests, while `config.py` centralizes paths and data settings.

## Data and sound

- The default interactive map is CARTO Voyager, a colorful labelled world basemap with OpenStreetMap/CARTO attribution. Use the map layer switcher to select NASA MODIS satellite imagery.
- NASA GIBS MODIS Terra Corrected Reflectance True Color: dated JPEG tiles using EPSG:3857 and `GoogleMapsCompatible_Level9`; the sonification endpoint samples zoom 6 tiles at five roughly quarterly dates. Unavailable dates are reported and skipped. The interactive globe itself uses NASA Blue Marble imagery.
- NASA POWER Daily Point API: T2M, PRECTOTCORR, WS2M, RH2M, ALLSKY_SFC_SW_DWN for a dynamic trailing 365-day period ending five days before today, a conservative availability buffer. Source units, date range, and missing-value count are returned. The graph's monthly aggregation is fetched in parallel with location lookup and audio generation so it can render before imagery and soundscape work finish. A point/grid estimate does not represent an entire ecosystem or country.
- Climate sound layers are generated per factor, so temperature, rainfall, wind, and humidity have distinct timbres; each layer gets louder as its normalized factor intensity rises. No audio files are required. The frontend uses the supplied `Background.jpg`, served locally from `frontend/public`.
- The `EARTHIFY` title and “Atmosphere into music” tagline form a brand lockup centered vertically on the right while the graph is loading, then hide when graph data appears. The globe view uses NASA Blue Marble imagery with directional sunlight, brighter oceans, and a subtle blue atmospheric rim against the star-field background. It reveals factor icons after a globe point is selected; clicking a factor announces its name, and the right side shows the selected place, an aqua location tagline, a playback-synced graph with white trend text and factor-colored markers, and play/pause plus audio-story controls. The audio story pauses the climate sound and slowly speaks the graph trends followed by the location tagline; the Audio story button toggles narration pause/resume, while climate playback remains paused until Play is pressed. The globe rotates slowly before a selection, can be rotated by dragging, and zooms to clicked places.
- OpenStreetMap Nominatim reverse geocoding, with coordinates fallback when unavailable.

Temperature uses a warm harmonic tone whose pitch and level rise with temperature; rainfall uses droplets whose rate and level rise with rainfall; wind uses airy filtered noise with stronger gusts at higher wind speeds; humidity uses a soft pulsing pad whose level rises with humidity. The factor layers are mixed together by default, or selecting factors plays only those layers. The player shows a monthly graph for the selected climate factor, or all factors on a shared normalized scale when none are selected; its playhead follows audio playback. Missing climate data are retained as nulls, counted, and filled by interpolation/neutral fallback for the intensity mapping.

## Implementation notes

FastAPI calls POWER and GIBS in parallel, analyzes imagery with Pillow/OpenCV/NumPy, creates and mixes the factor sounds with NumPy/SciPy/SoundFile, and writes the WAV before returning success. POWER and downloaded tiles are cached in `backend/.cache`; audio and full metadata are stored in `backend/generated_audio`. The maximum audio duration is validated at 30 seconds. Speech announces only the selected location name; soundscape playback begins after the name finishes. The native audio controls provide play, pause, resume, volume, and progress; Stop resets playback. Keyboard users can enter a global place name (Nominatim search selects its top result) or use the Amazon, Sahara, Tokyo and Pacific shortcuts.

The full flow was exercised locally: NASA POWER returned 365 daily records, NASA GIBS returned five dated image tiles, generation produced a 30-second WAV, and the audio endpoint returned it successfully. `npm run build` succeeds; all eleven backend unit tests pass.

## Limitations

Imagery is rendered visualization data, not a quantitative science product. The backend samples one small tile at zoom 6 and generates synchronously inside a request; generation may take time under slow external services. Free-form location search uses Nominatim and selects its first result. Caches and generated files have no cleanup policy yet.

## References

- [NASA GIBS access basics](https://nasa-gibs.github.io/gibs-api-docs/access-basics/)
- [NASA GIBS map library usage](https://nasa-gibs.github.io/gibs-api-docs/map-library-usage/)
- [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

