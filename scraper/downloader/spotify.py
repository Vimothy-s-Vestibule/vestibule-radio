from pathlib import Path
import os
import logging
from downloader.dl_types import Downloader, TrackMetadata
from spotdl.types.options import SpotDLOptionalOptions
from spotdl import Spotdl


opts = SpotDLOptionalOptions(
    {
        "bitrate": "192",
        "format": "mp3",
        # "force_update_metadata": True,
        "output": "./music",
        "headless": True,
        "threads": 4,  # TODO: Read from env
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

    def download(self, link: str) -> TrackMetadata:
        results = self.dl.search([link])
        if len(results) == 0:
            raise Exception("No results have been found for " + link)

        meta, output = self.dl.download(results[0])

        if not output:
            raise Exception("No output file returned")

        return TrackMetadata(
            id=meta.song_id,
            title=meta.name,
            album=meta.album_name,
            artist=meta.artist,
            duration_seconds=meta.duration,
            genre=" ".join(meta.genres if any(meta.genres) else "").strip(),
            fp=Path(os.path.abspath(output)),
        )


if __name__ == "__main__":
    dl = SpotifyDownloader()
    dl.download(
        "https://open.spotify.com/album/5bUtogkovAGfPbgPZ3O1RJ?si=RyBr7wVsS6KKRCxNuiCvPw"
    )
