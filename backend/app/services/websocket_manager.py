import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept websocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if user_id:
            self.user_connections[user_id] = websocket
            
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Remove websocket connection"""
        self.active_connections.discard(websocket)
        
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
            
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending personal message: {e}")
                self.disconnect(websocket, user_id)
                
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        disconnected = set()
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.add(connection)
                
        # Remove disconnected connections
        for connection in disconnected:
            self.active_connections.discard(connection)
            # Also remove from user connections
            for user_id, ws in list(self.user_connections.items()):
                if ws == connection:
                    del self.user_connections[user_id]
                    break
