import asyncio

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        async def send(connection):
            try:
                await asyncio.wait_for(connection.send_json(data), timeout=2)
            except (WebSocketDisconnect, OSError, RuntimeError, TimeoutError):
                self.disconnect(connection)

        await asyncio.gather(*(send(connection) for connection in list(self.active_connections)))


manager = ConnectionManager()
