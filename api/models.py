"""Track models served by the API. Reuses the downloader's TrackMetadata shape."""

from pydantic import BaseModel


class TrackMetadata(BaseModel):
    # video_id is the bare youtube id and the store key; it's what the frontend
    # feeds to the player. mbid is the musicbrainz id from the enhancer.
    video_id: str
    title: str = ""
    artist: str = ""
    album: str = ""
    genres: list[str] = []
    mbid: str = ""
    duration_seconds: float = 0.0


class Track(TrackMetadata):
    # the posting context the parser records on top of the metadata.
    # url is the original posted link (spotify or youtube); video_id is the
    # resolved youtube id that actually plays.
    url: str = ""
    source: str = ""
    posted_by: str = ""
    posted_at: str = ""


class CurrentlyPlaying(BaseModel):
    track: Track
    timeElapsedSec: int
