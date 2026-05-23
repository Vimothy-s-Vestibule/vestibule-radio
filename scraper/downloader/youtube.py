from pathlib import Path
import os
from downloader.dl_types import Downloader, TrackMetadata
from yt_dlp import YoutubeDL
from downloader.utils import parse_title, sanitize_filename

dl_folder = os.path.abspath("./music")
yt_dl_params = {
    "noplaylist": True,
    "format": "bestaudio/best",
    "addmetadata": True,
    "outtmpl": os.path.join(dl_folder, "%(title)s.%(ext)s"),
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        },
        {
            "key": "FFmpegMetadata",
            "add_metadata": True,
        },
    ],
}


class YoutubeDownloader(Downloader):
    dl: YoutubeDL

    def __init__(self):
        self.dl = YoutubeDL(params=yt_dl_params)
        pass

    def download(self, link: str) -> TrackMetadata:
        info = self.dl.extract_info(link, download=True)

        filepath = info.get("filepath")
        if "requested_downloads" in info and len(info["requested_downloads"]) > 0:
            filepath = info["requested_downloads"][0]["filepath"]

        title = info.get("title") or ""
        parsed_title = parse_title(title)
        artist = (
            info.get("artist")
            or info.get("creator")
            or info.get("uploader")
            or parsed_title.get("artist")
            or ""
        )

        fp_orig = Path(filepath)
        fp_clean = Path(sanitize_filename(filepath))
        if fp_orig != fp_clean:
            fp_orig.rename(fp_clean)

        out = TrackMetadata(
            id=info,
            title=title,
            artist=artist,
            album=info.get("album") or info.get("alt_title") or "",
            genre=info.get("genre") or parsed_title.get("genre") or "",
            duration_seconds=info.get("duration"),
            fp=fp_clean,
        )

        return out
