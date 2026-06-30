from pydantic import BaseModel
import json
import threading
from pathlib import Path
import os
from downloader.spotify import SpotifyExtractor
from downloader.youtube import YoutubeExtractor
from downloader.dl_types import Extractor, TrackData, TracksFileDataType, MusicPlatform
from downloader.enhancer import Enhancer
from downloader.utils import identify_music_platform
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Set


# Write to the same store the API reads. TRACKS_PATH keeps the two aligned in
# Docker (the api container reads /app/data/tracks.json); the default resolves to
# data/tracks.json at the repo root so it works no matter where the bot is run from.
_default_tracks_path = Path(__file__).resolve().parents[2] / "data" / "tracks.json"
tracks_json_fp = Path(os.getenv("TRACKS_PATH", _default_tracks_path))
tracks_json_fp.parent.mkdir(parents=True, exist_ok=True)


class ExtractTask(BaseModel):
    link: str
    msg_author: str
    msg_date: str


class SongExtractor:
    pool: ThreadPoolExecutor
    extractors: Dict[MusicPlatform, Extractor]
    track_ids: Set[str]

    def __init__(self):
        self.pool = ThreadPoolExecutor()
        self.extractors = {}
        self._save_lock = threading.Lock()
        self._extractors_lock = threading.Lock()
        self.track_ids = self._get_set_tracks_id()
        self.enhancer = Enhancer()

    @staticmethod
    def _get_set_tracks_id() -> Set[str]:
        tracks_json_fp.touch()

        if tracks_json_fp.stat().st_size == 0:
            return set()

        with open(tracks_json_fp, "r") as f:
            raw = json.load(f)
            f_data = TracksFileDataType(**raw)
            return set(f_data.tracks)


    def get_extractor(self, type: MusicPlatform) -> Extractor:
        """
        Lazy loads the extractor depending on the type, this literally exists just because spotdl takes forever to startup
        """
        with self._extractors_lock:
            if type in self.extractors:
                return self.extractors[type]

            ex: Extractor
            match type:
                case MusicPlatform.YouTube:
                    ex = YoutubeExtractor()
                case MusicPlatform.Spotify:
                    ex = SpotifyExtractor()

            self.extractors[type] = ex
            return ex

    def _save_data(self, data: TrackData):
        with self._save_lock:
            tracks_json_fp.touch()

            if tracks_json_fp.stat().st_size == 0:
                with open(tracks_json_fp, "w") as f:
                    json.dump(
                        TracksFileDataType(tracks={data.video_id: data}).model_dump(mode="json"), f
                    )
                    self.track_ids.add(data.video_id)
                return

            with open(tracks_json_fp, "r+") as f:
                f_data = TracksFileDataType(**json.load(f))
                f_data.tracks[data.video_id] = data
                f.seek(0)
                json.dump(f_data.model_dump(mode="json"), f)
                f.truncate()
                self.track_ids.add(data.video_id)

    def batch_extract(self, items: List[ExtractTask]):
        # NOTE: yt-dl provides batch extraction features, it might be worth it to use it instead of this one
        futures = [self.pool.submit(self.extract, task) for task in items]
        for f in futures:
            f.result()

    def extract(self, task: ExtractTask):
        """
        Main function intended to be used by the consumer(s), it is responsible for getting the right type of extractor
        depending on the link, persisting the resolved metadata and returning it
        """
        platform = identify_music_platform(task.link)

        ex = self.get_extractor(platform)

        data = ex.extract(task.link, self.track_ids)

        data = self.enhancer.get_enhanced_data(data)

        final_data = TrackData(
            **data.model_dump(),
            url=task.link,
            posted_by=task.msg_author,
            posted_at=task.msg_date,
            source=platform.name,
        )

        self._save_data(final_data)
        return


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <poster_username> <message_date> <link1> [link2 ...]")
        sys.exit(1)

    tasks = [ExtractTask(link=link, msg_author=sys.argv[1], msg_date=sys.argv[2])
             for link in sys.argv[3:]]

    se = SongExtractor()
    se.batch_extract(tasks)
