import asyncio
import socket
import logging
from typing import Dict, Callable, Optional
from app.utils.ssh_tunnel import SSHTunnel
from app.config import settings

logger = logging.getLogger(__name__)


class ESLClient:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.ssh_tunnel: Optional[SSHTunnel] = None
        self.local_port: Optional[int] = None
        self.event_handlers: Dict[str, Callable] = {}
        self.connected = False
        
    async def connect(self):
        """Connect to FreeSWITCH ESL through SSH tunnel"""
        try:
            # Create SSH tunnel
            self.ssh_tunnel = SSHTunnel(
                ssh_host=settings.freeswitch_host,
                ssh_username=settings.ssh_username,
                ssh_key_path=settings.ssh_private_key_path,
                remote_host='localhost',
                remote_port=settings.freeswitch_esl_port
            )
            
            self.local_port = await self.ssh_tunnel.start()
            
            # Connect to ESL through tunnel
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', self.local_port))
            
            # Authenticate
            await self._send_command(f"auth {settings.freeswitch_esl_password}")
            
            # Subscribe to events
            await self._send_command("events json ALL")
            
            self.connected = True
            logger.info("ESL connection established")
            
            # Start event listener
            asyncio.create_task(self._event_listener())
            
        except Exception as e:
            logger.error(f"Failed to connect to ESL: {e}")
            await self.disconnect()
            
    async def disconnect(self):
        """Disconnect from ESL and close SSH tunnel"""
        self.connected = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
            
        if self.ssh_tunnel:
            await self.ssh_tunnel.stop()
            self.ssh_tunnel = None
            
    async def _send_command(self, command: str) -> str:
        """Send command to FreeSWITCH"""
        if not self.socket:
            raise Exception("Not connected to ESL")
            
        self.socket.send(f"{command}\n\n".encode())
        return await self._read_response()
        
    async def _read_response(self) -> str:
        """Read response from FreeSWITCH"""
        response = ""
        while True:
            data = self.socket.recv(1024).decode()
            response += data
            if "\n\n" in response:
                break
        return response
        
    async def _event_listener(self):
        """Listen for events from FreeSWITCH"""
        while self.connected:
            try:
                event_data = await self._read_response()
                if event_data:
                    await self._process_event(event_data)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
                break
                
    async def _process_event(self, event_data: str):
        """Process incoming events"""
        # Parse event data and trigger handlers
        for event_type, handler in self.event_handlers.items():
            if event_type in event_data:
                await handler(event_data)
                
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_type] = handler
        
    async def originate_call(self, extension: str, destination: str) -> str:
        """Originate a call"""
        command = f"api originate user/{extension} {destination}"
        return await self._send_command(command)
        
    async def transfer_call(self, uuid: str, destination: str) -> str:
        """Transfer a call"""
        command = f"api uuid_transfer {uuid} {destination}"
        return await self._send_command(command)
        
    async def park_call(self, uuid: str, orbit: str) -> str:
        """Park a call"""
        command = f"api uuid_transfer {uuid} park+{orbit}"
        return await self._send_command(command)
        
    async def hangup_call(self, uuid: str) -> str:
        """Hangup a call"""
        command = f"api uuid_kill {uuid}"
        return await self._send_command(command)