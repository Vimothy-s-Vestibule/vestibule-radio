# Vestibule Community Radio

A 24/7 listening room for the Vestibule community. Post a YouTube or Spotify link in the music thread and it gets added to the station. Everyone tuned in hears the same song at the same time, right in the browser.

The radio plays songs through YouTube's embedded player, so the audio comes straight from YouTube. We don't host or stream any audio ourselves.

## Get your music on the radio

Post a YouTube or Spotify link in the music thread. That's it. The bot picks it up, finds the matching YouTube video, and adds it to the rotation. Spotify links get matched to a YouTube version automatically, since that's what the player can embed. The web player shows who posted each song.

## How it works

- The Discord bot watches the music thread and pulls out every YouTube and Spotify link.
- Spotify links are resolved to a matching YouTube video, because only YouTube can be embedded.
- Each track is stored as a YouTube video ID plus metadata (title, artist, genre, who posted it). No audio files.
- The web app plays the queue through the YouTube IFrame player, kept in sync across listeners by the server.

## Run it locally

The web app and the bot run locally. Playback is just YouTube embeds in your browser, so there's no streaming server or media to host, and no VM required.

```bash
git clone https://github.com/Vimothy-s-Vestibule/vestibule-radio
cd vestibule-radio
cp .env.example .env        # edit values
```

The project is mid-pivot, so the pieces are still coming together. The Discord bot and link parser run today. The API, sync server, and web player are in active development, tracked in the [issues](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues).

## Discord bot

The bot reads song links from a Discord channel. To set it up:

1. Create a bot at https://discord.com/developers/applications
2. Under **Bot** settings, enable **Message Content Intent**
3. Invite the bot to your server with `Send Messages` and `Read Message History` permissions
4. Copy the bot token into `DISCORD_BOT_TOKEN` in your `.env`
5. Right-click the target channel/thread and copy its ID into `DISCORD_CHANNEL_ID`

Run the bot:

```bash
pip install -r scraper/requirements.txt
python scraper/bot.py
```

It runs in two modes: `--listen` (default) processes new posts as they arrive, and `--backfill` reads the channel history once and then exits.

## What's built

- **Discord bot** connects to the music thread, with listen and backfill modes and graceful shutdown
- **Link parser** extracts and normalizes YouTube and Spotify links from messages, and dedupes them

## What we're building next

- **Spotify to YouTube resolver** so Spotify links can be embedded ([#27](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/27))
- **Web player** using the YouTube IFrame API ([#30](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/30))
- **WebSocket sync server** so everyone hears the same song at the same time ([#31](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/31))
- **Chat and live voting** for the next track ([#33](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/33), [#34](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues/34))

## Help out

Check the [issues](https://github.com/Vimothy-s-Vestibule/vestibule-radio/issues). Pick something, open a PR. If you don't code, post music or share design ideas in the Discord.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup details.
