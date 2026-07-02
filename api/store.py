"""Thin read layer over the track store.

Everything that touches persistence goes through here, so swapping the JSON
file for SQLite later is a change in this file only. The store is currently
data/tracks.json, written by the parser/resolver step.
"""
import random

import json
import os
from pathlib import Path

from models import Track

TRACKS_PATH = Path(os.getenv("TRACKS_PATH", "data/tracks.json"))


def load_tracks() -> list[Track]:
    if not TRACKS_PATH.exists():
        return []

    try:
        with open(TRACKS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    # tracks.json may be a {video_id: track} map or a bare list, accept both
    if isinstance(data, dict):
        raw_tracks = data.get("tracks", data).values()
    elif isinstance(data, list):
        raw_tracks = data
    else:
        return []

    tracks = []
    for raw in raw_tracks:
        # skip malformed rows rather than 500 the whole queue
        track = _parse_track(raw)
        if track is not None:
            tracks.append(track)

    return tracks

def get_random_track() -> Track:
    tracks = load_tracks()
    if not tracks:
        return Track(
            video_id="none",
            title="No tracks available",
            duration_seconds=10,
        )
    return random.choice(tracks)
    

def get_track(video_id: str) -> Track | None:
    for track in load_tracks():
        if track.video_id == video_id:
            return track

    return None


def _parse_track(raw) -> Track | None:
    if not isinstance(raw, dict):
        return None

    try:
        return Track(**raw)
    except (TypeError, ValueError):
        return None
