from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import audio, climate, imagery, map

app = FastAPI(title="Earth Jukebox", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://earthify.pages.dev", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(map.router, prefix="/api")
app.include_router(imagery.router, prefix="/api")
app.include_router(climate.router, prefix="/api")
app.include_router(audio.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
