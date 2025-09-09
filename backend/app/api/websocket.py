import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_manager import WebSocketManager
from app.services.call_manager import CallManager
from app.services.esl_client import ESLClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (should be properly managed in production)
websocket_manager = WebSocketManager()
esl_client = ESLClient()
call_manager = CallManager(websocket_manager)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_websocket_message(message, websocket)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


async def handle_websocket_message(message: dict, websocket: WebSocket):
    """Handle incoming WebSocket messages"""
    message_type = message.get('type')
    data = message.get('data', {})
    
    try:
        if message_type == 'transfer_call':
            if esl_client.connected:
                result = await esl_client.transfer_call(
                    data.get('uuid'),
                    data.get('destination')
                )
                await websocket.send_text(json.dumps({
                    'type': 'transfer_result',
                    'data': {'success': True, 'result': result}
                }))
            else:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'data': {'message': 'ESL connection not available'}
                }))
                
        elif message_type == 'park_call':
            if esl_client.connected:
                result = await esl_client.park_call(
                    data.get('uuid'),
                    data.get('orbit')
                )
                await websocket.send_text(json.dumps({
                    'type': 'park_result',
                    'data': {'success': True, 'result': result}
                }))
            else:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'data': {'message': 'ESL connection not available'}
                }))
                
        elif message_type == 'hangup_call':
            if esl_client.connected:
                result = await esl_client.hangup_call(data.get('uuid'))
                await websocket.send_text(json.dumps({
                    'type': 'hangup_result',
                    'data': {'success': True, 'result': result}
                }))
            else:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'data': {'message': 'ESL connection not available'}
                }))
                
        elif message_type == 'get_active_calls':
            active_calls = await call_manager.get_active_calls()
            await websocket.send_text(json.dumps({
                'type': 'active_calls',
                'data': active_calls
            }))
            
        else:
            await websocket.send_text(json.dumps({
                'type': 'error',
                'data': {'message': f'Unknown message type: {message_type}'}
            }))
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await websocket.send_text(json.dumps({
            'type': 'error',
            'data': {'message': str(e)}
        }))


# Function to get the global instances (for dependency injection)
def get_websocket_manager() -> WebSocketManager:
    return websocket_manager


def get_call_manager() -> CallManager:
    return call_manager


def get_esl_client() -> ESLClient:
    return esl_client
