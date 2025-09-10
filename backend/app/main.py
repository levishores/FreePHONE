import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables
from app.api.auth import auth_backend, fastapi_users
from app.api import extensions, calls, websocket
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.esl_client import ESLClient
from app.services.call_manager import CallManager
from app.api.websocket import get_websocket_manager, get_call_manager, get_esl_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting FreeSWITCH CTI application...")
    
    # Create database tables
    await create_db_and_tables()
    
    # Initialize ESL connection and event handlers
    esl_client = get_esl_client()
    call_manager = get_call_manager()
    
    # Register event handlers
    esl_client.register_event_handler('CHANNEL_CREATE', call_manager.handle_call_event)
    esl_client.register_event_handler('CHANNEL_ANSWER', call_manager.handle_call_event)
    esl_client.register_event_handler('CHANNEL_HANGUP', call_manager.handle_call_event)
    esl_client.register_event_handler('CHANNEL_PARK', call_manager.handle_call_event)
    esl_client.register_event_handler('CONFERENCE_MEMBER_ADD', call_manager.handle_call_event)
    esl_client.register_event_handler('CONFERENCE_MEMBER_DEL', call_manager.handle_call_event)
    
    # Connect to FreeSWITCH ESL (in background task)
    asyncio.create_task(connect_esl_with_retry(esl_client))
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if esl_client:
        await esl_client.disconnect()
    logger.info("Application shutdown complete")


async def connect_esl_with_retry(esl_client: ESLClient, max_retries: int = 5):
    """Connect to ESL with retry logic"""
    for attempt in range(max_retries):
        try:
            await esl_client.connect()
            logger.info("ESL connection established successfully")
            return
        except Exception as e:
            logger.error(f"ESL connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)  # Wait 5 seconds before retry
    
    logger.error("Failed to establish ESL connection after all retries")


# Create FastAPI app
app = FastAPI(
    title="FreeSWITCH CTI API",
    description="Call Technology Integration API for FreeSWITCH",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)

# Include API routes
app.include_router(
    extensions.router,
    prefix="/api/extensions",
    tags=["extensions"]
)

app.include_router(
    calls.router,
    prefix="/api/calls",
    tags=["calls"]
)

# Include WebSocket route
app.include_router(
    websocket.router,
    tags=["websocket"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FreeSWITCH CTI API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    esl_client = get_esl_client()
    return {
        "status": "healthy",
        "esl_connected": esl_client.connected if esl_client else False
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )