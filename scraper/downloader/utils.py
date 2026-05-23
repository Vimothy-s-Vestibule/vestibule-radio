import os
import re
from urllib.parse import urlparse
from .dl_types import MusicPlatform

def parse_title(title: str) -> dict:
    """Extract artist, title, and genre from a YouTube-style title string.

    Handles patterns like:
      "Artist - Song Title (Genre)"
      "Artist – Song Title | Genre"
      "Artist – Song Title [Genre]"
      "Song Title - Artist (Genre)"
    """
    out = {"artist": None, "title": title, "genre": None}

    # Strip common video qualifiers first
    cleaned = re.sub(
        r'\s*[\(\[({].*(?:official|audio|video|lyric|lyrics|visualizer|'
        r'music\s*video|hq|hd|4k|1080p|720p|360).*[\)\]})]\s*',
        '', title, flags=re.IGNORECASE
    )

    # Try "Artist - Title (Genre)" or "Artist – Title | Genre"
    m = re.match(
        r'^\s*(.+?)\s*[-–—|]\s*(.+?)\s*(?:[\(\[({](.+?)[\)\]})]|'
        r'[|]\s*(.+?))\s*$', cleaned
    )
    if m:
        out["artist"] = m.group(1).strip()
        out["title"] = m.group(2).strip()
        genre = m.group(3) or m.group(4)
        if genre:
            genre = genre.strip()
            genre = re.sub(r'\s*\(.*\)\s*', '', genre).strip()
            if genre and not re.search(
                r'(official|video|lyric|audio)', genre, re.IGNORECASE
            ):
                out["genre"] = genre
        return out

    m = re.match(r'^\s*(.+?)\s*[-–—|]\s*(.+?)\s*$', cleaned)
    if m:
        out["artist"] = m.group(1).strip()
        out["title"] = m.group(2).strip()

    return out


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Remove characters that are problematic in file paths. Accepts a full path."""
    head, tail = os.path.split(name)
    clean = re.sub(r'[<>:"/\\|?*,\']', replacement, tail).strip()
    return os.path.join(head, clean) if head else clean


def extract_id(url: str) -> str:
    """Extract the platform-specific resource ID from a URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")

    if "youtube.com" in domain or "youtu.be" in domain:
        if parsed.path == "/watch" or "music.youtube.com" in domain:
            return parsed.query.split("&")[0].split("=")[1]  # v=ID
        return parsed.path.strip("/").split("/")[0]  # youtu.be/ID

    if "spotify.com" in domain:
        parts = parsed.path.strip("/").split("/")
        return parts[1]  # /track/ID, /album/ID, /playlist/ID

    raise ValueError(f"Cannot extract id from {url}")


def identify_music_platform(url) -> MusicPlatform:
    """
    Determines if a URL belongs to YouTube (including YT Music) or Spotify.
    """
 
    parsed_url = urlparse(url)
    # Extract the domain and convert to lowercase for uniform checking
    domain = parsed_url.netloc.lower()
    
    # Strip 'www.' if it exists so the domain checks work consistently
    if domain.startswith("www."):
        domain = domain[4:]
        
    if domain in ["youtube.com", "youtu.be", "://youtube.com", "music.youtube.com"]:
        return MusicPlatform.YouTube
    elif domain == "spotify.com" or "spotify.com" in domain:
        return MusicPlatform.Spotify
    else:
        raise Exception("Non-supported platform")
        

