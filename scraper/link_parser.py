import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


SEEN_LINKS_PATH = Path("../data/seen_links.json")


YOUTUBE_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
}

SPOTIFY_DOMAINS = {
    "open.spotify.com",
}


URL_REGEX = re.compile(
    r"https?://[^\s<>\]\)]+",
    re.IGNORECASE,
)

MARKDOWN_URL_REGEX = re.compile(
    r"\[[^\]]+\]\((https?://[^\s\)]+)\)",
    re.IGNORECASE,
)


def parse_message(message_content, posted_by, posted_at):
    extracted_urls = extract_urls(message_content)

    if not extracted_urls:
        return []

    seen_links = load_seen_links()

    seen_urls = {entry["url"] for entry in seen_links}

    new_links = []

    for raw_url in extracted_urls:
        normalized_url = normalize_url(raw_url)

        if normalized_url is None:
            continue

        if normalized_url in seen_urls:
            continue

        source = detect_source(normalized_url)

        if source is None:
            continue

        link_object = {
            "url": normalized_url,
            "posted_by": str(posted_by),
            "posted_at": posted_at.isoformat(),
            "source": source,
        }

        new_links.append(link_object)

        seen_links.append(link_object)
        seen_urls.add(normalized_url)

    save_seen_links(seen_links)

    return new_links


def extract_urls(text):
    urls = []

    markdown_urls = MARKDOWN_URL_REGEX.findall(text)
    urls.extend(markdown_urls)

    plain_urls = URL_REGEX.findall(text)
    urls.extend(plain_urls)

    cleaned_urls = []

    for url in urls:
        cleaned = cleanup_url(url)

        if cleaned:
            cleaned_urls.append(cleaned)

    return deduplicate_preserve_order(cleaned_urls)


def cleanup_url(url):
    url = url.strip()

    url = url.strip("<>[]()")

    url = url.rstrip(".,!?;:")

    return url


def normalize_url(url):
    parsed = urlparse(url)

    domain = parsed.netloc.lower()

    if domain in YOUTUBE_DOMAINS:
        return normalize_youtube_url(parsed)

    if domain in SPOTIFY_DOMAINS:
        return normalize_spotify_url(parsed)

    return None


def normalize_youtube_url(parsed):
    domain = parsed.netloc.lower()

    # short links
    if domain == "youtu.be":
        video_id = parsed.path.strip("/")

        if not video_id:
            return None

        return urlunparse(
            (
                "https",
                "youtu.be",
                f"/{video_id}",
                "",
                "",
                "",
            )
        )

    query = parse_qs(parsed.query)

    video_id = query.get("v")

    if not video_id:
        return None

    clean_query = urlencode({"v": video_id[0]})

    return urlunparse(
        (
            "https",
            "www.youtube.com",
            "/watch",
            "",
            clean_query,
            "",
        )
    )


def normalize_spotify_url(parsed):
    clean_path = parsed.path.rstrip("/")

    return urlunparse(
        (
            "https",
            "open.spotify.com",
            clean_path,
            "",
            "",
            "",
        )
    )


def detect_source(url):
    domain = urlparse(url).netloc.lower()

    if domain in YOUTUBE_DOMAINS:
        return "youtube"

    if domain in SPOTIFY_DOMAINS:
        return "spotify"

    return None


def load_seen_links():
    SEEN_LINKS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not SEEN_LINKS_PATH.exists():
        return []

    try:
        with open(
            SEEN_LINKS_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        return data

    except (json.JSONDecodeError, OSError):
        return []


def save_seen_links(seen_links):
    SEEN_LINKS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        SEEN_LINKS_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            seen_links,
            file,
            indent=2,
        )


def deduplicate_preserve_order(items):
    seen = set()
    result = []

    for item in items:
        if item in seen:
            continue

        seen.add(item)
        result.append(item)

    return result
