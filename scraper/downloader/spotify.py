from typing import Set
from pathlib import Path
import os
import logging
from downloader.dl_types import Downloader, TrackMetadata, DuplicateTrackException
from downloader.utils import sanitize_filename
from spotdl.types.options import SpotDLOptionalOptions
from spotdl import Spotdl


opts = SpotDLOptionalOptions(
    {
        "bitrate": "192",
        "format": "mp3",

        "output": "./music",
        "headless": True,
        "threads": 4,  # NOTE: Maybe read from env?
        "overwrite": "skip",
        "simple_tui": False,
        "no_cache": False,
        "cache_path": "./music/.spotify.cache",
        "use_cache_file": True,
    }
)


class SpotifyDownloader(Downloader):
    dl: Spotdl
        
    def __init__(self):
        self.dl = Spotdl(client_id="", client_secret="", downloader_settings=opts)
        logging.info("Spotdl initialized")
        pass

    def download(self, link: str, track_ids: Set[str]) -> TrackMetadata:
        results = self.dl.search([link])
        if len(results) == 0:
            raise Exception("No results have been found for " + link)

        song_to_download = results[0]

        if song_to_download.song_id in track_ids:
            raise DuplicateTrackException

        meta, output = self.dl.download(results[0])

        if not output:
            raise Exception("No output file returned")

        fp_orig = Path(os.path.abspath(output))
        fp_clean = Path(sanitize_filename(str(fp_orig)))
        if fp_orig != fp_clean:
            fp_orig.rename(fp_clean)

        return TrackMetadata(
            id=meta.song_id,
            title=meta.name,
            album=meta.album_name,
            artist=meta.artist,
            duration_seconds=meta.duration,
            genre=" ".join(meta.genres if any(meta.genres) else "").strip(),
            fp=fp_clean,
        )


