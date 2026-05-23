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
        The type of object that downloaders return
    """
    id: str
    title: str
    artist: str
    album: str
    genre: str
    duration_seconds: float

    fp: pathlib.Path # Location of the downloaded file

class TrackData(TrackMetadata):
    """
        Adds on top of the music data some fields that will end up being written to disk
    """
    posted_by: str
    posted_at: str
    downloaded_at: str
    source: str

class TracksFileDataType(BaseModel):
    tracks: Dict[str, TrackData]

class Downloader(ABC):
    @abstractmethod
    def download(self, link: str, track_ids: Set[str]) -> TrackMetadata:
        """
            Downloads the track and its metadata, accepts a track ids set to avoid duplicates
        """
        pass

class DuplicateTrackException(Exception):
    pass
    
