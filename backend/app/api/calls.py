from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_async_session
from app.models.call import Call
from app.models.user import User
from app.schemas.call import CallRead, CallTransferRequest, CallParkRequest, CallHangupRequest
from app.api.auth import current_active_user
from app.services.esl_client import ESLClient

router = APIRouter()

# Global ESL client instance (should be properly managed in production)
esl_client = ESLClient()


@router.get("/active", response_model=List[CallRead])
async def get_active_calls(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Get all active calls"""
    stmt = select(Call).where(Call.state.in_(['RINGING', 'ACTIVE', 'HELD', 'PARKED']))
    result = await session.execute(stmt)
    calls = result.scalars().all()
    return calls


@router.get("/", response_model=List[CallRead])
async def get_all_calls(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Get all calls (including ended)"""
    stmt = select(Call)
    result = await session.execute(stmt)
    calls = result.scalars().all()
    return calls


@router.post("/transfer")
async def transfer_call(
    transfer_request: CallTransferRequest,
    user: User = Depends(current_active_user)
):
    """Transfer a call"""
    try:
        if not esl_client.connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ESL connection not available"
            )
        
        result = await esl_client.transfer_call(
            transfer_request.uuid,
            transfer_request.destination
        )
        
        return {"message": "Call transfer initiated", "result": result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transfer call: {str(e)}"
        )


@router.post("/park")
async def park_call(
    park_request: CallParkRequest,
    user: User = Depends(current_active_user)
):
    """Park a call"""
    try:
        if not esl_client.connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ESL connection not available"
            )
        
        result = await esl_client.park_call(
            park_request.uuid,
            park_request.orbit
        )
        
        return {"message": "Call park initiated", "result": result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to park call: {str(e)}"
        )


@router.post("/hangup")
async def hangup_call(
    hangup_request: CallHangupRequest,
    user: User = Depends(current_active_user)
):
    """Hangup a call"""
    try:
        if not esl_client.connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ESL connection not available"
            )
        
        result = await esl_client.hangup_call(hangup_request.uuid)
        
        return {"message": "Call hangup initiated", "result": result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to hangup call: {str(e)}"
        )