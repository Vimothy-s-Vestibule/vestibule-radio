# Contributing

There are three ways to help: post music, record clips, write code.

## Post music

Drop a YouTube or Spotify link in the music thread. That's the easiest way to contribute.

## Record audio clips

Station IDs, DJ intros, the story behind a song you posted, weird ambient noises -- anything that could play between songs. Drop them in the Discord.

## Write code

### Quick start

You need: Docker, Docker Compose, git.

```bash
git clone https://github.com/Vimothy-s-Vestibule/vestibule-radio
cd vestibule-radio
cp .env.example .env
docker compose up
```

Open http://localhost:8001 — you should see the player. Drop an MP3 into `music/` and Liquidsoap will pick it up quickly.

If you're only working on the frontend, you don't need Discord credentials in `.env` — just leave `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` blank.

### Pick something to work on

Browse the [issues](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues). `good first issue` is a good place to start.

Comment on the issue saying you're taking it so two people don't end up doing the same thing. If you get stuck, ask in the project Discord forum — no question is too small.

### Submitting changes

1. Branch off `main`
2. Keep PRs small and focused - one thing per PR
3. Write a clear PR description: what changed, why, how to test it
4. Link the issue it closes (`Closes #14`)

### Project layout

| Path | What it is |
|------|------------|
| `web/` | Static frontend (HTML/CSS/JS, no build step) |
| `scraper/` | Discord bot + audio downloader |
| `streaming/` | Liquidsoap config |
| `data/` | JSON state files (tracks, votes, recent plays) |
| `music/` | Downloaded MP3s — gitignored |
| `docs/` | Architecture and design notes |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit together.

### Working on one piece in isolation

You don't always need the full stack running:

- **Frontend only:** `cd web && python3 -m http.server 8001` Stream won't play but UI works.
- **Smart queue / downloader / other Python scripts:** runnable standalone with fixture data, no Docker needed.
- **Discord bot:** needs a bot token in `.env`, but you can point it at a private test server instead of the real Vestibule one.

## Code of conduct

Be kind. This is a community project built for fun. Any music submitted that isn't 'girly pop' will be brutally roasted by Finn.
