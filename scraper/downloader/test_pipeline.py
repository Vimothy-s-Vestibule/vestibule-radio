"""
Run from scraper/: uv run python -m downloader.test_pipeline
Simulates Discord messages arriving
"""
import sys
import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from link_parser import parse_message, SEEN_LINKS_PATH
from downloader.extractor import SongExtractor, ExtractTask, tracks_json_fp

TEST_MESSAGES = [
    "never gets old https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "check this one https://www.youtube.com/watch?v=hTWKbfoikeg cool track",
    "https://youtu.be/3JZ_D3ELwOQ",
    "two in one go https://www.youtube.com/watch?v=YR5ApYxkU-U and https://www.youtube.com/watch?v=kXYiU_JCYtU",
    "totally unrelated message with no links",
    "check this out https://open.spotify.com/track/0tgVpDi06FyKpA1z0VMD4v?si=60b1ecce91c4489e"
]


@dataclass
class FakeMessage:
    content: str
    author: str = "test_user"
    created_at: datetime = field(default_factory=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc))


def links_to_tasks(links: list[dict]) -> list[ExtractTask]:
    return [
        ExtractTask(link=l["url"], msg_author=l["posted_by"], msg_date=l["posted_at"])
        for l in links
    ]


if __name__ == "__main__":
    tracks_json_fp.write_text("")
    if SEEN_LINKS_PATH.exists():
        SEEN_LINKS_PATH.write_text("[]")

    se = SongExtractor()
    all_tasks: list[ExtractTask] = []

    for raw in TEST_MESSAGES:
        msg = FakeMessage(content=raw)
        links = parse_message(
            message_content=msg.content,
            posted_by=msg.author,
            posted_at=msg.created_at,
        )
        tasks = links_to_tasks(links)
        if tasks:
            print(f"  '{raw[:60]}' -> {len(tasks)} link(s)")
        else:
            print(f"  '{raw[:60]}' -> skipped (no links / already seen)")
        all_tasks.extend(tasks)

    if not all_tasks:
        print("\nNo tasks to run.")
        sys.exit(0)

    print(f"\nRunning {len(all_tasks)} task(s) through extractor + enhancer...\n")
    se.batch_extract(all_tasks)

    if not tracks_json_fp.exists() or tracks_json_fp.stat().st_size == 0:
        print("tracks.json is empty.")
        sys.exit(1)

    saved = json.loads(tracks_json_fp.read_text())
    tracks = saved.get("tracks", {})

    print(f"Saved {len(tracks)} track(s):\n" + "=" * 60)
    for vid_id, t in tracks.items():
        print(f"\nvideo_id : {vid_id}")
        print(f"title    : {t.get('title')}")
        print(f"artist   : {t.get('artist')}")
        print(f"album    : {t.get('album') or '—'}")
        print(f"genres   : {t.get('genres') or '—'}")
        print(f"mbid     : {t.get('mbid') or '—'}")
        print(f"duration : {t.get('duration_seconds')}s")
        print(f"url      : {t.get('url')}")
    print("=" * 60)
