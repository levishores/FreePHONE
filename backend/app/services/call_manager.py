import json
import logging
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.call import Call, Conference, ParkOrbit
from app.models.user import Extension
from app.services.websocket_manager import WebSocketManager
from app.database import async_session_maker

logger = logging.getLogger(__name__)


class CallManager:
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.active_calls: Dict[str, Dict] = {}
        
    async def handle_call_event(self, event_data: str):
        """Handle call events from FreeSWITCH"""
        try:
            event = json.loads(event_data)
            event_name = event.get('Event-Name', '')
            
            if event_name == 'CHANNEL_CREATE':
                await self._handle_channel_create(event)
            elif event_name == 'CHANNEL_ANSWER':
                await self._handle_channel_answer(event)
            elif event_name == 'CHANNEL_HANGUP':
                await self._handle_channel_hangup(event)
            elif event_name == 'CHANNEL_PARK':
                await self._handle_channel_park(event)
            elif event_name == 'CONFERENCE_MEMBER_ADD':
                await self._handle_conference_join(event)
            elif event_name == 'CONFERENCE_MEMBER_DEL':
                await self._handle_conference_leave(event)
                
        except Exception as e:
            logger.error(f"Error handling call event: {e}")
            
    async def _handle_channel_create(self, event: Dict):
        """Handle new call creation"""
        call_uuid = event.get('Unique-ID')
        caller_id_number = event.get('Caller-Caller-ID-Number')
        caller_id_name = event.get('Caller-Caller-ID-Name')
        destination_number = event.get('Caller-Destination-Number')
        direction = event.get('Call-Direction', 'unknown')
        
        async with async_session_maker() as session:
            # Find extension
            extension = None
            if direction == 'inbound':
                stmt = select(Extension).where(Extension.extension_number == destination_number)
                result = await session.execute(stmt)
                extension = result.scalar_one_or_none()
            elif direction == 'outbound':
                stmt = select(Extension).where(Extension.extension_number == caller_id_number)
                result = await session.execute(stmt)
                extension = result.scalar_one_or_none()
                
            # Create call record
            call = Call(
                uuid=call_uuid,
                direction=direction,
                caller_id_number=caller_id_number,
                caller_id_name=caller_id_name,
                destination_number=destination_number,
                extension_id=extension.id if extension else None,
                state='RINGING'
            )
            
            session.add(call)
            await session.commit()
            
            # Update active calls
            self.active_calls[call_uuid] = {
                'uuid': call_uuid,
                'direction': direction,
                'caller_id_number': caller_id_number,
                'caller_id_name': caller_id_name,
                'destination_number': destination_number,
                'extension_number': extension.extension_number if extension else None,
                'state': 'RINGING',
                'created_at': call.created_at.isoformat()
            }
            
            # Broadcast to clients
            await self.websocket_manager.broadcast({
                'type': 'call_created',
                'data': self.active_calls[call_uuid]
            })
            
    async def _handle_channel_answer(self, event: Dict):
        """Handle call answer"""
        call_uuid = event.get('Unique-ID')
        
        if call_uuid in self.active_calls:
            self.active_calls[call_uuid]['state'] = 'ACTIVE'
            
            async with async_session_maker() as session:
                stmt = select(Call).where(Call.uuid == call_uuid)
                result = await session.execute(stmt)
                call = result.scalar_one_or_none()
                
                if call:
                    call.state = 'ACTIVE'
                    call.answered_at = event.get('Event-Date-Timestamp')
                    await session.commit()
                    
            await self.websocket_manager.broadcast({
                'type': 'call_answered',
                'data': self.active_calls[call_uuid]
            })
            
    async def _handle_channel_hangup(self, event: Dict):
        """Handle call hangup"""
        call_uuid = event.get('Unique-ID')
        
        if call_uuid in self.active_calls:
            del self.active_calls[call_uuid]
            
            async with async_session_maker() as session:
                stmt = select(Call).where(Call.uuid == call_uuid)
                result = await session.execute(stmt)
                call = result.scalar_one_or_none()
                
                if call:
                    call.state = 'ENDED'
                    call.ended_at = event.get('Event-Date-Timestamp')
                    await session.commit()
                    
            await self.websocket_manager.broadcast({
                'type': 'call_ended',
                'data': {'uuid': call_uuid}
            })
            
    async def _handle_channel_park(self, event: Dict):
        """Handle call parking"""
        call_uuid = event.get('Unique-ID')
        park_orbit = event.get('variable_park_orbit')
        
        if call_uuid in self.active_calls:
            self.active_calls[call_uuid]['state'] = 'PARKED'
            self.active_calls[call_uuid]['park_orbit'] = park_orbit
            
            async with async_session_maker() as session:
                stmt = select(Call).where(Call.uuid == call_uuid)
                result = await session.execute(stmt)
                call = result.scalar_one_or_none()
                
                if call:
                    call.state = 'PARKED'
                    call.park_orbit = park_orbit
                    await session.commit()
                    
                # Update park orbit status
                stmt = select(ParkOrbit).where(ParkOrbit.orbit_number == park_orbit)
                result = await session.execute(stmt)
                orbit = result.scalar_one_or_none()
                
                if orbit:
                    orbit.is_occupied = True
                    orbit.occupied_by_call_uuid = call_uuid
                    await session.commit()
                    
            await self.websocket_manager.broadcast({
                'type': 'call_parked',
                'data': self.active_calls[call_uuid]
            })
            
    async def _handle_conference_join(self, event: Dict):
        """Handle conference member join"""
        conference_name = event.get('Conference-Name')
        member_id = event.get('Member-ID')
        caller_id_number = event.get('Caller-Caller-ID-Number')
        
        await self.websocket_manager.broadcast({
            'type': 'conference_member_add',
            'data': {
                'conference_name': conference_name,
                'member_id': member_id,
                'caller_id_number': caller_id_number
            }
        })
        
    async def _handle_conference_leave(self, event: Dict):
        """Handle conference member leave"""
        conference_name = event.get('Conference-Name')
        member_id = event.get('Member-ID')
        
        await self.websocket_manager.broadcast({
            'type': 'conference_member_del',
            'data': {
                'conference_name': conference_name,
                'member_id': member_id
            }
        })
            
    async def get_active_calls(self) -> List[Dict]:
        """Get all active calls"""
        return list(self.active_calls.values())
        
    async def transfer_call(self, call_uuid: str, destination: str) -> bool:
        """Transfer a call (to be called by API)"""
        # This would interact with ESL client
        # Implementation depends on ESL client integration
        pass
