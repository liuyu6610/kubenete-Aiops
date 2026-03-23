from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from typing import List
from core.errors import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class ConnectionManager:
    """Singleton WebSocket Connection Manager"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_connections = []
        return cls._instance

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("Client disconnected.")

    async def broadcast_alert(self, alert_data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json({"type": "NEW_ALERT", "payload": alert_data})
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

manager = ConnectionManager()

@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    from services.agent.glm5_agent import GLM5Agent
    import asyncio
    await manager.connect(websocket)
    
    # Initialize a clean GLM-5 context for this UI session
    agent = GLM5Agent()
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "CHAT_REQUEST":
                    prompt = msg.get("payload")
                    loop = asyncio.get_event_loop()
                    # Execute synchronous LLM chat logic in executor to free event loop
                    reply = await loop.run_in_executor(None, agent.chat, prompt)
                    
                    await websocket.send_json({
                        "type": "CHAT_RESPONSE",
                        "payload": reply
                    })
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON websocket message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
