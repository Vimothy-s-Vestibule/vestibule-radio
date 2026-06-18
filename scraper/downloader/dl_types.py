from typing import Dict, Set
from enum import Enum
import pathlib
from abc import ABC, abstractmethod
from pydantic import BaseModel

class MusicPlatform(Enum):
    YouTube = 1
    Spotify = 2


class TrackMetadata(BaseModel):
    """
        The type of object that extractors return
    """
    video_id: str #resolved youtube video id
    mbid: str
    title: str
    artist: str
    album: str
    genres: list [str]
    duration_seconds: int

class TrackData(TrackMetadata):
    """
        Adds on top of the music data some fields that will end up being written to disk
    """
    url: str #url as posted in the discord
    posted_by: str
    posted_at: str
    source: str

class TracksFileDataType(BaseModel):
    tracks: Dict[str, TrackData]

class Extractor(ABC):
    @abstractmethod
    def extract(self, link: str, track_ids: Set[str]) -> TrackMetadata:
        """
            Resolves the track's metadata, accepts a track ids set to avoid duplicates
        """
        pass

class DuplicateTrackException(Exception):
    pass
    
