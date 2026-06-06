# Architecture

How Vestibule Community Radio works.

The station plays songs through YouTube's embedded player. Listeners watch the same queue in sync, and YouTube serves the actual audio and video. We don't host or stream any audio ourselves, which keeps licensing and delivery with YouTube.

## Flow

```
Discord Thread --> Bot --> Parser --> Resolver (Spotify to YouTube if needed)
                                          |
                                          v
                              MusicBrainz enrichment
                                          |
                                          v
                            Track store (video IDs + metadata)
                                          |
                                          v
                    API server  <-->  WebSocket sync server
                                          |
                                          v
        Web client: YouTube IFrame player + chat + queue + voting
                                          |
                                          v
                    YouTube serves the audio/video
```

A posted link becomes a YouTube video ID plus metadata. The server decides what's playing and how far into it, and every client lines its embed up to that.

## Components

| Component | Status | Notes |
|-----------|--------|-------|
| Discord bot | built | Watches the music thread, listen + backfill modes, graceful shutdown |
| Link parser | built | Extracts and normalizes YouTube and Spotify URLs, dedupes |
| Spotify to YouTube resolver | planned | Matches a Spotify link to a YouTube video ID, ISRC first, falling back to "Artist - Song" plus duration. [#27](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/27) |
| MusicBrainz enrichment | planned | Fills in genre and cleans metadata for the UI. [#21](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/21) |
| Track store | planned | Video IDs + metadata. JSON to start, SQLite when it hurts. Schema in [#28](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/28) |
| API server | planned | Serves the queue and track list to the frontend. [#29](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/29) |
| WebSocket sync server | planned | Server-authoritative now-playing state and progress, plus chat and voting transport. [#31](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/31) |
| Web player | planned | YouTube IFrame Player API, plays the queue in sync. [#30](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/30) |
| Per-channel chat | planned | Over the same WebSocket layer. [#33](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/33) |
| Live voting | planned | Listeners vote on the next track. [#34](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/34) |
| Discord OAuth | planned | Identities match the community. [#35](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/35) |
| PWA | planned | Installable on mobile via manifest + service worker. [#36](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/36) |

The old self-hosted audio stack (downloader, Liquidsoap, Icecast) is being removed as part of the pivot, tracked in [#25](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/25). Some of that code is still in the tree until that lands.

## How sync works

The sync server holds the current track and a progress counter that runs from 0 to the track's duration. When a client connects it gets the current video ID and progress, loads the embed, and uses the IFrame API `seekTo` to jump to the right spot. From there it follows the server's lead through the queue.

The player has to stay visible to satisfy YouTube's terms. Small or secondary is fine, hidden is not.

## Known constraints

- **Mobile background playback.** YouTube embeds stop when the phone is locked or the app is backgrounded, since uninterrupted background play is a Premium feature. Picture-in-Picture helps on Android. We ship YouTube only and revisit this if it turns into a real pain point. We do not work around it by downloading audio, since that brings back the liability the pivot removed.
- **Ad-induced desync.** When a client's embed plays a YouTube ad, that client falls behind the server's timestamp. We detect the stall and `seekTo` the correct position once playback resumes. Temporary per-client desync during ads is accepted. Tracked in [#32](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/32).

## Data files

| File | Purpose |
|------|---------|
| `data/tracks.json` | Every track: YouTube video ID, title, artist, genre, who posted it, when. No file paths |
| `data/seen_links.json` | URLs already processed, for deduplication |
| `data/feedback.json` | Thumbs up/down tallies per track |
| `data/recent_plays.json` | Last N track IDs, used by the smart queue to avoid repeats |

The track schema is being updated for the embed model in [#28](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/28).

## Tech stack

- **Backend and bot:** Python (discord.py for the bot, FastAPI for the API and WebSocket layer)
- **Frontend:** Web app using the YouTube IFrame Player API, packaged as a PWA for mobile
- **Realtime:** WebSocket, chosen over SSE so chat and voting can share one transport
- **Storage:** JSON, moving to SQLite when it hurts
- **Auth:** Discord OAuth
- **Deployment:** Docker Compose. The stack is the bot, the API and sync server, and a static frontend. There are no streaming containers.

## Related projects

The radio and the planned **Vestibule TV** converge under this architecture. Both are "play curated YouTube content from the community with shared chat." Radio is a music-focused UI with a small player, TV is a video-focused UI. Same backend and pipeline, different frontend mode. The radio web app is the immediate deliverable.

[`server-library`](https://github.com/Vimothy-s-Vestibule/server-library) is a separate Vestibule project that catalogues members' books, music, and movies into a SQLite-backed static site. There's been discussion of feeding radio plays into it, but no integration is built yet.
