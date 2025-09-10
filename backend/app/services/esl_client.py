import asyncio
import socket
import logging
from typing import Dict, Callable, Optional
from app.utils.ssh_tunnel import SSHTunnel
from app.config import settings

logger = logging.getLogger(__name__)


class ESLClient:
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.ssh_tunnel: Optional[SSHTunnel] = None
        self.local_port: Optional[int] = None
        self.event_handlers: Dict[str, Callable] = {}
        self.connected = False
        
    async def connect(self):
        """Connect to FreeSWITCH ESL through SSH tunnel"""
        try:
            logger.info("🚇 Step 1: Creating SSH tunnel...")
            # Create SSH tunnel
            self.ssh_tunnel = SSHTunnel(
                ssh_host=settings.freeswitch_host,
                ssh_username=settings.ssh_username,
                ssh_key_path=settings.ssh_private_key_path,
                remote_host='localhost',
                remote_port=settings.freeswitch_esl_port
            )
            
            logger.info("🚇 Step 2: Starting SSH tunnel...")
            self.local_port = await self.ssh_tunnel.start()
            logger.info(f"✅ SSH tunnel started on local port {self.local_port}")
            
            # Wait a moment for SSH tunnel to be ready
            await asyncio.sleep(2)
            
            # Connect to ESL through tunnel using asyncio streams
            logger.info(f"🔌 Step 3: Connecting to ESL through tunnel on localhost:{self.local_port}")
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection('localhost', self.local_port),
                timeout=10.0
            )
            logger.info("✅ Connected to ESL through tunnel")
            
            # Read initial ESL welcome message
            logger.info("📨 Step 4: Reading ESL welcome message...")
            welcome = await self._read_response()
            logger.info(f"ESL Welcome: {welcome.strip()}")
            
            # Authenticate
            logger.info("🔑 Step 5: Authenticating...")
            auth_response = await self._send_command(f"auth {settings.freeswitch_esl_password}")
            logger.info(f"Auth response: {auth_response.strip()}")
            
            # Subscribe to events
            logger.info("📡 Step 6: Subscribing to events...")
            events_response = await self._send_command("events json ALL")
            logger.info(f"Events response: {events_response.strip()}")
            
            self.connected = True
            logger.info("🎉 ESL connection fully established")
            
            # Start event listener
            asyncio.create_task(self._event_listener())
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to ESL: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            await self.disconnect()
            
    async def disconnect(self):
        """Disconnect from ESL and close SSH tunnel"""
        self.connected = False
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None
            
        if self.ssh_tunnel:
            await self.ssh_tunnel.stop()
            self.ssh_tunnel = None
            
    async def _send_command(self, command: str) -> str:
        """Send command to FreeSWITCH"""
        if not self.writer:
            raise Exception("Not connected to ESL")
            
        self.writer.write(f"{command}\n\n".encode())
        await self.writer.drain()
        return await self._read_response()
        
    async def _read_response(self) -> str:
        """Read response from FreeSWITCH"""
        if not self.reader:
            raise Exception("Not connected to ESL")
            
        response = ""
        try:
            # Read with timeout to prevent hanging
            while True:
                line = await asyncio.wait_for(self.reader.readline(), timeout=5.0)
                if not line:
                    #logger.info("📭 No more data from ESL")
                    break
                    
                line_str = line.decode().rstrip('\r\n')
                response += line_str + '\n'
                
                # ESL responses end with an empty line
                if line_str == "":
                    break
                    
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout reading ESL response")
            if response:
                logger.info(f"📨 Partial response received: {response}")
        except Exception as e:
            logger.error(f"❌ Error reading ESL response: {e}")
                
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