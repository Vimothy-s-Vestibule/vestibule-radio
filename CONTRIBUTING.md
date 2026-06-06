# Contributing

There are two ways to help: post music, or write code.

## Post music

Drop a YouTube or Spotify link in the music thread. That's the easiest way to contribute, and it's what keeps the station running.

## Write code

### Quick start

You need: Python 3.13, git. Docker is only needed for the parts that ship as containers, and there's no streaming stack or VM to set up anymore.

```bash
git clone https://github.com/Vimothy-s-Vestibule/vestibule-radio
cd vestibule-radio
cp .env.example .env
```

The Discord bot runs today:

```bash
pip install -r scraper/requirements.txt
python scraper/bot.py
```

If you're only working on the frontend, you don't need Discord credentials in `.env`. Leave `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` blank. Playback in the web app is YouTube embeds, so you can develop it with nothing but a browser.

### Pick something to work on

Browse the [issues](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues). `good first issue` is a good place to start.

The work is organized in rough phases, so you can see where a task fits:

1. **Ingestion pivot** - resolve links to video IDs and store metadata ([#26](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/26), [#27](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/27), [#28](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/28), [#21](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/21))
2. **Minimal playback** - API server and a YouTube IFrame player ([#29](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/29), [#30](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/30), [#37](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/37))
3. **Sync and chat** - shared playback, voting, chat, login ([#31](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/31), [#33](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/33), [#34](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/34), [#35](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/35))
4. **Polish and mobile** - PWA, smart queue, desync handling ([#36](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/36), [#38](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/38), [#32](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/32))

Comment on the issue saying you're taking it so two people don't end up doing the same thing. If you get stuck, ask in the project Discord forum. No question is too small.

### Submitting changes

1. **Work on a feature branch, not `main`.** Branch off `main` and open your PR from that branch. A couple of early PRs came straight off `main` and caused friction, so this one matters.
2. Keep PRs small and focused, one thing per PR
3. Write a clear PR description: what changed, why, how to test it
4. Link the issue it closes (`Closes #30`)

PRs are reviewed by a maintainer before they're merged, so expect some back and forth.

### Project layout

| Path | What it is |
|------|------------|
| `web/` | Static frontend (HTML/CSS/JS, no build step), YouTube IFrame player |
| `scraper/` | Discord bot, link parser, and Spotify to YouTube resolver |
| `data/` | JSON state files (tracks, votes, recent plays) |
| `docs/` | Architecture and design notes |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit together.

### Working on one piece in isolation

You don't always need everything running:

- **Frontend only:** `cd web && python3 -m http.server 8001`. The player embeds run against YouTube directly.
- **Resolver, parser, or other Python scripts:** runnable standalone with fixture data, no Docker needed.
- **Discord bot:** needs a bot token in `.env`, but you can point it at a private test server instead of the real Vestibule one.

## Code of conduct

Be kind. This is a community project built for fun. Any music submitted that isn't 'girly pop' will be brutally roasted by Finn.
