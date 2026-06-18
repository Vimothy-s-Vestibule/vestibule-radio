import logging
from typing import Set
from downloader.dl_types import Extractor, TrackMetadata

logger = logging.getLogger(__name__)


class SpotifyExtractor(Extractor):
    """
    Returns empty metadata until Spotify -> Youtube resolver is reimplemented.
    See Issue #27 Build the Spotify -> Youtube Resolver.
    """

    def __init__(self):
        logger.warning("SpotifyExtractor is a placeholder and does not resolve real metadata yet")

    def extract(self, link: str, track_ids: Set[str]) -> TrackMetadata:
        return TrackMetadata(
            video_id="",
            mbid="",
            title="",
            artist="",
            album="",
            genres=[],
            duration_seconds=0,
        )
