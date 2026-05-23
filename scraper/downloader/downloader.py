import json
from pathlib import Path
import os
from datetime import datetime
from downloader.spotify import SpotifyDownloader
from downloader.youtube import YoutubeDownloader
from downloader.dl_types import Downloader, TrackData, TracksFileDataType
from downloader.utils import identify_music_platform
from downloader.dl_types import MusicPlatform
from concurrent.futures import ThreadPoolExecutor
from typing import Dict



tracks_json_fp = Path(os.path.abspath("./tracks.json"))

class SongDownloader:
    pool: ThreadPoolExecutor
    downloaders: Dict[MusicPlatform, Downloader]

    def __init__(self):
        self.pool = ThreadPoolExecutor()
        self.downloaders = {}
        pass

    def get_downloader(self, type: MusicPlatform) -> Downloader:
        """
        Lazy loads the downloader depending on the type, this literally exists just because spotdl takes forever to startup
        """
        if type in self.downloaders:
            return self.downloaders[type]

        dl: Downloader
        match type:
            case MusicPlatform.YouTube:
                dl = YoutubeDownloader()
            case MusicPlatform.Spotify:
                dl = SpotifyDownloader()

        self.downloaders[type] = dl
        return dl

    def _save_data(self, data: TrackData):
        # Ensure it exists
        tracks_json_fp.touch()
        
        f_data: TracksFileDataType
        if tracks_json_fp.stat().st_size == 0:
            with open(tracks_json_fp, "w") as f:
                json.dump(TracksFileDataType(tracks=[data]).model_dump(mode="json"), f)
            return
            
        with open(tracks_json_fp, "r+") as f:
            f_data = TracksFileDataType(**json.load(f))
            f_data.tracks.append(data)
            json.dump(f_data.model_dump(mode="json"), f)

    def download(self, link: str, poster_username: str, message_date: str):
        """
        Main function intended to be used by the consumer(s), it is responsible for getting the right type of downloader
        depending in the link, writting to disk the just downloaded data and return it
        """
        platform = identify_music_platform(link)

        dl = self.get_downloader(platform)

        data = dl.download(link)

        final_data = TrackData(
            **data.model_dump(),
            posted_by=poster_username,
            posted_at=message_date,
            downloaded_at=datetime.now().isoformat(),
            source=platform.name,
        )

        self._save_data(final_data)
        return


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <link> <poster_username> <message_date>")
        sys.exit(1)
    sd = SongDownloader()
    sd.download(sys.argv[1], sys.argv[2], sys.argv[3])

        
