from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.web_socket_manager import manager


router = APIRouter(
    tags=["websocket"]
)


@router.websocket("/ws/tracks")
async def websocket_tracks(
    websocket: WebSocket
):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)