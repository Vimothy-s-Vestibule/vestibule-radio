from pydantic import BaseModel
import json
import threading
from pathlib import Path
import os
from datetime import datetime
from downloader.spotify import SpotifyDownloader
from downloader.youtube import YoutubeDownloader
from downloader.dl_types import Downloader, TrackData, TracksFileDataType, MusicPlatform
from downloader.utils import identify_music_platform
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List


tracks_json_fp = Path(os.path.abspath("./tracks.json"))


class DownloadTask(BaseModel):
    link: str
    msg_author: str
    msg_date: str


class SongDownloader:
    pool: ThreadPoolExecutor
    downloaders: Dict[MusicPlatform, Downloader]

    def __init__(self):
        self.pool = ThreadPoolExecutor()
        self.downloaders = {}
        self._save_lock = threading.Lock()
        self._downloaders_lock = threading.Lock()
        pass

    def get_downloader(self, type: MusicPlatform) -> Downloader:
        """
        Lazy loads the downloader depending on the type, this literally exists just because spotdl takes forever to startup
        """
        with self._downloaders_lock:
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
        with self._save_lock:
            tracks_json_fp.touch()

            if tracks_json_fp.stat().st_size == 0:
                with open(tracks_json_fp, "w") as f:
                    json.dump(
                        TracksFileDataType(tracks=[data]).model_dump(mode="json"), f
                    )
                return

            with open(tracks_json_fp, "r+") as f:
                f_data = TracksFileDataType(**json.load(f))
                f_data.tracks.append(data)
                json.dump(f_data.model_dump(mode="json"), f)

    def batch_download(self, items: List[DownloadTask]):
        # NOTE: Both yt-dl and spotdl provide batch downloading features, it might be worth it to use them instead of this one
        futures = [self.pool.submit(self.download, task) for task in items]
        for f in futures:
            f.result()

    def download(self, task: DownloadTask):
        """
        Main function intended to be used by the consumer(s), it is responsible for getting the right type of downloader
        depending in the link, writting to disk the just downloaded data and return it
        """
        platform = identify_music_platform(task.link)

        dl = self.get_downloader(platform)

        data = dl.download(task.link)

        final_data = TrackData(
            **data.model_dump(),
            posted_by=task.msg_author,
            posted_at=task.msg_date,
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
    task = DownloadTask(link=sys.argv[1], msg_author=sys.argv[2], msg_date=sys.argv[3])
    sd.download(task)
