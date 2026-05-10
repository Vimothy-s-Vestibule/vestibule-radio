# Vestibule Community Radio

A 24/7 radio station for the Vestibule community. Post a YouTube or Spotify link in the music thread and it ends up on the station.

The stream is running. Sylvan is getting it set up on the server -- link coming soon.

## Get your music on the radio

Post a YouTube or Spotify link in the music thread. That's it. The system downloads it and adds it to the rotation. The web player will show who posted each song.

## Run it locally

```bash
git clone https://github.com/jack123xyz/vestibule-radio.git
cd vestibule-radio
cp .env.example .env        # edit passwords
                             # drop some mp3s in music/
docker compose up --build
```

Web player at `http://localhost:8080`. Direct stream at `http://localhost:8000/stream`. Status page at `http://localhost:8000`.

The web container proxies `/stream` and `/status-json.xsl` to Icecast so the browser can use same-origin URLs.

## What's built

- Liquidsoap shuffles and crossfades tracks from the music directory
- Icecast serves the stream over HTTP
- Docker Compose runs the whole thing

## What we're building next

- **Discord bot** that automatically grabs links from the music thread and downloads them ([issues](https://github.com/jack123xyz/vestibule-radio/issues?q=label%3Abot))
- **Web player** so people can listen in a browser without VLC ([issues](https://github.com/jack123xyz/vestibule-radio/issues?q=label%3Afrontend))
- **Smart queue** that avoids repeats and lets listeners upvote/downvote songs

## Help out

Check the [issues](https://github.com/jack123xyz/vestibule-radio/issues). Pick something, open a PR. If you don't code, post music, record audio clips for between songs, or share design ideas in the Discord.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup details.
