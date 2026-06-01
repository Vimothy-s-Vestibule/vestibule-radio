"""Watch a Discord music thread and download posted tracks to disk.

Modes (via ``--listen`` / ``--backfill`` flag or ``MODE`` env var; flag wins):
  listen   - default; process messages as they arrive.
  backfill - read history once, process, exit.
"""

import argparse
import asyncio
import logging
import os
import signal
import sys

import discord
from dotenv import load_dotenv

from link_parser import parse_message
from downloader.downloader import SongDownloader, DownloadTask


logger = logging.getLogger("vestibule.scraper")

HISTORY_LIMIT = 100


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("discord").setLevel(logging.WARNING)


def resolve_mode(args: argparse.Namespace) -> str:
    if args.backfill:
        return "backfill"
    if args.listen:
        return "listen"

    mode = os.getenv("MODE", "listen").lower()
    if mode not in ("backfill", "listen"):
        logger.warning("Unknown MODE=%r, defaulting to 'listen'", mode)
        return "listen"
    return mode


def links_to_tasks(links: list[dict]) -> list[DownloadTask]:
    return [
        DownloadTask(
            link=link["url"],
            msg_author=link["posted_by"],
            msg_date=link["posted_at"],
        )
        for link in links
    ]


async def download_task(downloader: SongDownloader, task: DownloadTask) -> None:
    future = downloader.pool.submit(downloader.download, task)
    try:
        await asyncio.wrap_future(future)
        logger.info("Downloaded %s", task.link)
    except Exception:
        logger.exception("Failed to download %s", task.link)


async def process_message(downloader: SongDownloader, message: discord.Message) -> None:
    try:
        links = parse_message(
            message_content=message.content,
            posted_by=message.author,
            posted_at=message.created_at,
        )
    except Exception:
        logger.exception("Failed to parse message %s", message.id)
        return

    if not links:
        return

    tasks = links_to_tasks(links)
    logger.info("Found %d new link(s) in message %s", len(tasks), message.id)
    for task in tasks:
        await download_task(downloader, task)


async def resolve_channel(client: discord.Client, channel_id: int):
    channel = client.get_channel(channel_id)
    if channel is not None:
        return channel
    try:
        return await client.fetch_channel(channel_id)
    except (discord.NotFound, discord.Forbidden) as exc:
        logger.error("Could not resolve channel %s: %s", channel_id, exc)
        return None


async def run_backfill(
    client: discord.Client, downloader: SongDownloader, channel_id: int
) -> None:
    channel = await resolve_channel(client, channel_id)
    if channel is None:
        return

    logger.info("Backfilling from %s (ID: %s)", channel.name, channel.id)
    try:
        async for message in channel.history(limit=HISTORY_LIMIT):
            await process_message(downloader, message)
    except discord.Forbidden:
        logger.error("Missing permission to read message history")
    logger.info("Backfill complete")


async def runner(
    client: discord.Client, token: str, downloader: SongDownloader
) -> None:
    loop = asyncio.get_running_loop()
    closing = False

    def request_shutdown() -> None:
        nonlocal closing
        if closing:
            return
        closing = True
        logger.info("Shutdown signal received, closing bot")
        loop.create_task(client.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_shutdown)
        except NotImplementedError:
            pass

    try:
        async with client:
            await client.start(token)
    finally:
        await asyncio.to_thread(downloader.pool.shutdown, wait=True)
        logger.info("Shutdown complete")


def main() -> None:
    configure_logging()
    load_dotenv()

    parser = argparse.ArgumentParser(description="Vestibule Radio scraper bot")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--backfill", action="store_true", help="Read history once and exit.")
    modes.add_argument("--listen", action="store_true", help="Run continuously (default).")
    mode = resolve_mode(parser.parse_args())

    token = os.getenv("DISCORD_BOT_TOKEN")
    raw_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    if not token:
        logger.error("DISCORD_BOT_TOKEN not set in environment/.env")
        sys.exit(1)
    if not raw_channel_id:
        logger.error("DISCORD_CHANNEL_ID not set in environment/.env")
        sys.exit(1)
    try:
        channel_id = int(raw_channel_id)
    except ValueError:
        logger.error("DISCORD_CHANNEL_ID must be an integer, got %r", raw_channel_id)
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    downloader = SongDownloader()

    @client.event
    async def on_ready() -> None:
        logger.info("Logged in as %s (ID: %s)", client.user, client.user.id)
        if mode == "backfill":
            await run_backfill(client, downloader, channel_id)
            await client.close()
        else:
            logger.info("Listening for new messages in channel %s", channel_id)

    @client.event
    async def on_message(message: discord.Message) -> None:
        if mode != "listen" or message.author == client.user:
            return
        if message.channel.id != channel_id:
            return
        await process_message(downloader, message)

    try:
        asyncio.run(runner(client, token, downloader))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
