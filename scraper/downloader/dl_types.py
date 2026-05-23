from typing import List
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
    tracks: List[TrackData]

class Downloader(ABC):
    @abstractmethod
    def download(self, link: str) -> TrackMetadata:
        pass
    
