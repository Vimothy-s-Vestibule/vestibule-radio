"""Vestibule Radio API, serves the track queue to the frontend.

REST only for now. The sync server, chat, and voting (separate issues) will be
WebSocket layers added onto this same app, so keep the app object reusable and
don't bake in REST-only assumptions.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from connections_manager import ConnectionsManager, WSIncomingMessage
from models import CurrentlyPlaying, Track
from player import Player
from store import get_track, load_tracks

# comma-separated origins, e.g. "http://localhost:8001,http://localhost:3000"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:8001").split(",")
    if origin.strip()
]

manager = ConnectionsManager()
player = Player()


@asynccontextmanager
async def lifespan(app: FastAPI):
    player.on_advance(manager.send_now_playing)
    await player.start()
    yield
    await player.stop()


app = FastAPI(title="Vestibule Radio API", lifespan=lifespan)

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


@app.get("/now-playing", response_model=CurrentlyPlaying)
def now_playing() -> CurrentlyPlaying:
    return player.get_current_track()


@app.websocket("/ws")
async def now_playing_ws(ws: WebSocket):
    await ws.accept()
    id = await manager.add_client(ws)

    # On connect, send the currently playing song.
    await manager.send_now_playing(player.get_current_track())

    try:
        while True:
            try:
                raw = await ws.receive_json()
                result = WSIncomingMessage.model_validate(raw)

                if result.payload.type == "message":
                    await manager.send_message(result.payload)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logging.error(f"Failed to receive incoming client message: {e}")
                continue
    finally:
        await manager.remove_client(id)
