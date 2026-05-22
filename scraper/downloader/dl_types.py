import pathlib
from abc import ABC, abstractmethod
import dataclasses

@dataclasses.dataclass
class MusicData:
    title: str
    artist: str
    album: str
    genre: str
    duration_seconds: float

    fp: pathlib.Path # Location of the downloaded file


class Downloader(ABC):
    @abstractmethod
    def download(self, link: str) -> MusicData:
        pass
    
