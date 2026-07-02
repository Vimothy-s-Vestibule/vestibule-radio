import asyncio
import datetime
import logging
import random
from collections.abc import Awaitable, Callable

from models import CurrentlyPlaying, Track
from store import get_random_track, get_track

# Fallback track length when duration is missing from metadata.
DEFAULT_TRACK_DURATION = 180


class Player:
    current_track: Track
    started_at: datetime.datetime
    votes: dict[str, int]
    _task: asyncio.Task | None = None
    _on_advance: list[Callable[[CurrentlyPlaying], Awaitable[None]]]
    _on_votes_change: list[Callable[[dict[str, int]], Awaitable[None]]]

    def __init__(self):
        self.current_track = get_random_track()
        self.started_at = datetime.datetime.now()
        self.votes = {}
        self._on_advance = []
        self._on_votes_change = []

    def on_advance(self, callback: Callable[[CurrentlyPlaying], Awaitable[None]]) -> None:
        """Register a callback invoked each time the track changes."""
        self._on_advance.append(callback)

    def on_votes_change(self, callback: Callable[[dict[str, int]], Awaitable[None]]) -> None:
        """Register a callback invoked whenever votes change."""
        self._on_votes_change.append(callback)

    def get_current_track(self) -> CurrentlyPlaying:
        elapsed = int((datetime.datetime.now() - self.started_at).total_seconds())
        return CurrentlyPlaying(track=self.current_track, timeElapsedSec=elapsed)

    def get_votes(self) -> dict[str, int]:
        return dict(self.votes)

    async def vote(self, track_id: str) -> None:
        """Cast a vote for a track and notify listeners of the new vote totals."""
        if get_track(track_id) is None:
            logging.warning(f"Vote received for unknown track: {track_id}")
            return

        self.votes[track_id] = self.votes.get(track_id, 0) + 1
        await self._notify_votes_change()

    async def start(self) -> None:
        """Start the background loop that advances tracks when they finish."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._advance_loop())

    async def stop(self) -> None:
        """Stop the background advance loop."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _advance_loop(self) -> None:
        while True:
            try:
                await self._wait_for_track_end()
                await self._advance()
            except asyncio.CancelledError:
                break
            except Exception:
                logging.exception("Error in player advance loop")
                await asyncio.sleep(1)

    async def _wait_for_track_end(self) -> None:
        duration = self.current_track.duration_seconds or DEFAULT_TRACK_DURATION
        elapsed = self.get_current_track().timeElapsedSec
        remaining = max(0.0, duration - elapsed)
        await asyncio.sleep(remaining)

    async def _advance(self) -> None:
        self.current_track = self._pick_next_track()
        self.started_at = datetime.datetime.now()
        self.votes.clear()
        now_playing = self.get_current_track()

        await asyncio.gather(
            *(callback(now_playing) for callback in self._on_advance),
            return_exceptions=True,
        )
        await self._notify_votes_change()

    def _pick_next_track(self) -> Track:
        """Pick the most-voted track, or a random one if there are no votes."""
        if not self.votes:
            return get_random_track()

        max_votes = max(self.votes.values())
        winners = [track_id for track_id, count in self.votes.items() if count == max_votes]
        winner_id = random.choice(winners)
        winner = get_track(winner_id)
        if winner is None:
            return get_random_track()
        return winner

    async def _notify_votes_change(self) -> None:
        if not self._on_votes_change:
            return
        votes_copy = dict(self.votes)
        await asyncio.gather(
            *(callback(votes_copy) for callback in self._on_votes_change),
            return_exceptions=True,
        )
