import asyncio
import paramiko
import socket
import threading
from typing import Optional


class SSHTunnel:
    def __init__(self, ssh_host: str, ssh_username: str, ssh_key_path: str, 
                 remote_host: str, remote_port: int):
        self.ssh_host = ssh_host
        self.ssh_username = ssh_username
        self.ssh_key_path = ssh_key_path
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_port: Optional[int] = None
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.tunnel_thread: Optional[threading.Thread] = None
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        
    async def start(self) -> int:
        """Start SSH tunnel and return local port"""
        # Find available local port
        self.local_port = self._find_free_port()
        
        # Create SSH client
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to SSH server
        private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
        self.ssh_client.connect(
            hostname=self.ssh_host,
            username=self.ssh_username,
            pkey=private_key
        )
        
        # Start tunnel in separate thread
        self.running = True
        self.tunnel_thread = threading.Thread(target=self._tunnel_worker)
        self.tunnel_thread.daemon = True
        self.tunnel_thread.start()
        
        return self.local_port
        
    async def stop(self):
        """Stop SSH tunnel"""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
            
        if self.ssh_client:
            self.ssh_client.close()
            
        if self.tunnel_thread:
            self.tunnel_thread.join(timeout=5)
            
    def _find_free_port(self) -> int:
        """Find a free local port"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def _tunnel_worker(self):
        """Worker thread for SSH tunnel"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.local_port))
        self.server_socket.listen(5)
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True
                ).start()
            except Exception:
                break
                
    def _handle_client(self, client_socket: socket.socket):
        """Handle client connection through tunnel"""
        try:
            # Create channel through SSH
            transport = self.ssh_client.get_transport()
            remote_socket = transport.open_channel(
                'direct-tcpip',
                (self.remote_host, self.remote_port),
                ('localhost', self.local_port)
            )
            
            # Forward data between client and remote
            def forward(source, destination):
                while True:
                    try:
                        data = source.recv(1024)
                        if not data:
                            break
                        destination.send(data)
                    except Exception:
                        break
                        
            # Start forwarding in both directions
            threading.Thread(target=forward, args=(client_socket, remote_socket), daemon=True).start()
            threading.Thread(target=forward, args=(remote_socket, client_socket), daemon=True).start()
            
        except Exception as e:
            print(f"Error in tunnel client handler: {e}")
        finally:
            client_socket.close()