import asyncio
import datetime
import logging
from collections.abc import Awaitable, Callable

from models import CurrentlyPlaying, Track
from store import get_random_track

# Fallback track length when duration is missing from metadata.
DEFAULT_TRACK_DURATION = 180


class Player:
    current_track: Track
    started_at: datetime.datetime
    _task: asyncio.Task | None = None
    _on_advance: list[Callable[[CurrentlyPlaying], Awaitable[None]]]

    def __init__(self):
        self.current_track = get_random_track()
        self.started_at = datetime.datetime.now()
        self._on_advance = []

    def on_advance(self, callback: Callable[[CurrentlyPlaying], Awaitable[None]]) -> None:
        """Register a callback invoked each time the track changes."""
        self._on_advance.append(callback)

    def get_current_track(self) -> CurrentlyPlaying:
        elapsed = int((datetime.datetime.now() - self.started_at).total_seconds())
        return CurrentlyPlaying(track=self.current_track, timeElapsedSec=elapsed)

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
        self.current_track = get_random_track()
        self.started_at = datetime.datetime.now()
        now_playing = self.get_current_track()
        if self._on_advance:
            await asyncio.gather(
                *(callback(now_playing) for callback in self._on_advance),
                return_exceptions=True,
            )
