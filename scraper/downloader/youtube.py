from typing import Any, Set
from downloader.dl_types import Extractor, TrackMetadata, DuplicateTrackException
from yt_dlp import YoutubeDL
from downloader.utils import parse_title

yt_dl_params: dict[str, Any] = {
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
}


class YoutubeExtractor(Extractor):
    dl: YoutubeDL

    def __init__(self):
        self.dl = YoutubeDL(params=yt_dl_params)  # type: ignore[arg-type]

    def extract(self, link: str, track_ids : Set[str]) -> TrackMetadata:
        info = self.dl.extract_info(link, download=False)
        id = info.get("id")

        if not id:
            raise Exception("Track doesn't contain ID")

        if id in track_ids:
            raise DuplicateTrackException

        title = info.get("title") or ""
        parsed_title = parse_title(title)
        artist = (
            info.get("artist")
            or info.get("creator")
            or info.get("uploader")
            or parsed_title.get("artist")
            or ""
        )

        d = info.get("duration")
        duration = int(-1 if d is None else d)

        if d == -1:
            raise Exception("Track doesn't have a duration")

        out = TrackMetadata(
            video_id=id,
            title=parsed_title.get("title") or title,
            artist=artist,
            album=info.get("album") or info.get("alt_title") or "",
            genres=[g for g in [info.get("genre") or parsed_title.get("genre")] if g],
            mbid = "",
            duration_seconds=duration
        )

        return out
