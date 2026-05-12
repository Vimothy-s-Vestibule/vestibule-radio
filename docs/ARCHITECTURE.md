# Architecture

How Vestibule Community Radio works.

## Flow

Solid arrows are built. Dashed arrows are planned.

```
                                  ┌──────────────────────────────────────┐
                                  │                                      │
   [planned]                      ▼                                      │
Discord Thread ┄┄> Bot ┄┄> Downloader ┄┄> music/ + tracks.json           │
                                                  │                       │
                                                  ▼                       │
                                              Liquidsoap ──> Icecast      │
                                                                │         │
                                                                ▼         │
                                                            Traefik ──> Listeners
                                                                ▲
                                                                │
                                                            Frontend (web/)
```

Today, the music in `music/` is added manually. Once the bot + downloader land, that step becomes automatic.

## Components

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend (`web/`) | live | Static HTML/CSS/JS, no build step |
| Reverse proxy (Traefik + Authentik) | live in prod, dev WIP | Routes `/`, `/stream`, `/status-json.xsl` to the right backend. Every route is gated by Authentik - the station is members-only. |
| Stream server (Icecast) | live | Serves the audio stream + metadata JSON |
| Playout (Liquidsoap) | live | Shuffles `music/`, crossfades, normalizes, pushes to Icecast |
| Discord bot | planned | Issues [#1](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/1), [#2](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/2) |
| Downloader | planned | Issue [#3](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/3) |
| Smart queue | planned | Issue [#14](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/14) |
| Voting / now-playing wiring | planned | Issue [#13](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/13) |
| Taste map | planned | Issue [#12](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/12) |

## Data files

| File | Purpose |
|------|---------|
| `data/tracks.json` | Every downloaded track: title, artist, who posted it, file path, etc. |
| `data/seen_links.json` | URLs already processed, for deduplication |
| `data/feedback.json` | Thumbs up/down tallies per track |
| `data/recent_plays.json` | Last N track IDs, used by the smart queue to avoid repeats |

Schema for `tracks.json` is defined in issue [#4](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/4).

## Deployment

**Local:** `docker compose up` runs Icecast + Liquidsoap. The frontend can be served with `python3 -m http.server` from `web/` or via the dev Traefik setup once that lands.

**Prod:** the stack runs on Sylvan's cluster at `radio.vestibule.gripe`, joined to the external Docker network `proxy`. Traefik (already on the cluster) handles TLS via `websecure` and routes by Host/PathPrefix labels. The `authentik-auth@file` middleware is attached to every router - frontend, stream, metadata, and admin all require a Vestibule login. The radio is members-only by design.

## Related projects

[`server-library`](https://github.com/Vimothy-s-Vestibule/server-library) is a separate Vestibule project that catalogues members' books / music / movies into a SQLite-backed static site. There's been discussion of feeding radio plays into it (so a member's "music shelf" reflects what they've shared on the station), but no integration is built yet.

