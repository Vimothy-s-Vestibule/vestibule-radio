"""Vestibule Radio API, serves the track queue to the frontend.

REST only for now. The sync server, chat, and voting (separate issues) will be
WebSocket layers added onto this same app, so keep the app object reusable and
don't bake in REST-only assumptions.
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import Track
from .store import get_track, load_tracks

# comma-separated origins, e.g. "http://localhost:8001,http://localhost:3000"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:8001").split(",")
    if origin.strip()
]

app = FastAPI(title="Vestibule Radio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/queue", response_model=list[Track])
@app.get("/tracks", response_model=list[Track])
def queue() -> list[Track]:
    return load_tracks()


@app.get("/tracks/{video_id}", response_model=Track)
def track(video_id: str) -> Track:
    found = get_track(video_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No track with video_id {video_id}")

    return found


@app.get("/now-playing", response_model=Track | None)
def now_playing() -> Track | None:
    # placeholder until the sync server exists. for now just the head of the
    # queue so the frontend has something real to render
    tracks = load_tracks()
    return tracks[0] if tracks else None
