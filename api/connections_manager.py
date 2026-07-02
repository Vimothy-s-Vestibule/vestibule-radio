import asyncio

import logging
from typing import Dict,Literal,  List, Coroutine, Annotated 
from fastapi import WebSocket
import uuid
from pydantic import BaseModel, Field

class ClientChatMessage(BaseModel):
    type: Literal["message"]
    data: str

class ClientVoteMessage(BaseModel):
    type: Literal["vote"]
    data: str # The ID of the track

ClientPayload = Annotated[ClientChatMessage, ClientVoteMessage]

class WSIncomingMessage(BaseModel):
    payload: ClientPayload = Field(..., discriminator="type")


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

    async def send_message(self, payload: ClientChatMessage):
        proms: List[Coroutine] = []

        for _, ws in self.connections.items():
            proms.append(ws.send_json(payload))

        await asyncio.gather(*proms)
            

    async def add_client(self, client: WebSocket) -> str:
        id = await self._get_id()

        self.connections[id] = client

        return id

    async def remove_client(self, id: str):
        if id not in self.connections:
            logging.error(f"Attempted to delete non-existing ID {id}")
            return

        self.connections.pop(id)
        

        


    
