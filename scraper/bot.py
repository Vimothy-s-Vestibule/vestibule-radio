"""Authenticate with Discord, fetch messages from a channel, and print them."""

import os
import sys

import discord
from dotenv import load_dotenv
from link_parser import parse_message


def main() -> None:
    load_dotenv()

    token = os.getenv("DISCORD_BOT_TOKEN")
    channel_id = os.getenv("DISCORD_CHANNEL_ID")

    if not token:
        print("ERROR: DISCORD_BOT_TOKEN not set in .env", file=sys.stderr)
        sys.exit(1)
    if not channel_id:
        print("ERROR: DISCORD_CHANNEL_ID not set in .env", file=sys.stderr)
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        print(f"Logged in as {client.user} (ID: {client.user.id})")
        try:
            channel = client.get_channel(int(channel_id))
            if channel is None:
                channel = await client.fetch_channel(int(channel_id))
        except (ValueError, discord.NotFound, discord.Forbidden) as exc:
            print(f"ERROR: could not resolve channel: {exc}", file=sys.stderr)
            await client.close()
            return

        print(f"Fetching messages from {channel.name} (ID: {channel.id})...")
        links = []
        try:
            async for message in channel.history(limit=100):
                print(f"[{message.author}] {message.content}")
                parsed_links = parse_message(
                    message_content=message.content,
                    posted_by=message.author,
                    posted_at=message.created_at,
                )
                for link in parsed_links:
                    links.append(link)
            print(links)
        except discord.Forbidden:
            print(
                "ERROR: missing permission to read message history",
                file=sys.stderr,
            )
        finally:
            await client.close()

    client.run(token)


if __name__ == "__main__":
    main()
