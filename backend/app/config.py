from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./cti_dev.db"
    
    # JWT
    secret_key: str = "your-super-secret-jwt-key-here"
    
    # FreeSWITCH
    freeswitch_host: str = "192.168.1.100"
    freeswitch_esl_port: int = 8021
    freeswitch_esl_password: str = "ClueCon"
    ssh_username: str = "freeswitch"
    ssh_private_key_path: str = "/path/to/ssh/key"
    
    # Application
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"


settings = Settings()