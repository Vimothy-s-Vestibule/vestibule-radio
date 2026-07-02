import asyncio
import logging
from typing import Annotated, Coroutine, Dict, List, Literal, Union

from fastapi import WebSocket
from pydantic import BaseModel, Field
import uuid

from models import CurrentlyPlaying


class ClientChatMessage(BaseModel):
    type: Literal["message"] = "message"
    message: str


class ClientVoteMessage(BaseModel):
    type: Literal["vote"] = "vote"
    trackID: str


ClientPayload = Annotated[
    Union[ClientChatMessage, ClientVoteMessage],
    Field(discriminator="type"),
]


class WSIncomingMessage(BaseModel):
    payload: ClientPayload


class CurrentlyPlayingMessage(BaseModel):
    type: Literal["playingNow"] = "playingNow"
    trackID: str
    trackUrl: str
    timeSeconds: int


class ConnectionsManager:
    connections: Dict[str, WebSocket]

    def __init__(self):
        self.connections = {}

    async def _get_id(self) -> str:
        while True:
            id = str(uuid.uuid4())
            if id in self.connections:
                continue
            return id

    async def add_client(self, client: WebSocket) -> str:
        id = await self._get_id()
        self.connections[id] = client
        return id

    async def remove_client(self, id: str):
        if id not in self.connections:
            logging.error(f"Attempted to delete non-existing ID {id}")
            return
        self.connections.pop(id)

    async def send_message(self, payload: ClientChatMessage):
        proms: List[Coroutine] = []
        for _, ws in self.connections.items():
            proms.append(ws.send_json(payload.model_dump()))
        if proms:
            await asyncio.gather(*proms)

    async def send_now_playing(self, now_playing: CurrentlyPlaying):
        message = CurrentlyPlayingMessage(
            type="playingNow",
            trackID=now_playing.track.video_id,
            trackUrl=now_playing.track.url,
            timeSeconds=now_playing.timeElapsedSec,
        )
        await self._broadcast(message.model_dump())

    async def _broadcast(self, message: dict):
        if not self.connections:
            return
        await asyncio.gather(
            *(ws.send_json(message) for ws in self.connections.values())
        )
