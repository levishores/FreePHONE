from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_async_session
from app.models.user import Extension, User
from app.schemas.extension import ExtensionCreate, ExtensionRead, ExtensionUpdate
from app.api.auth import current_active_user

router = APIRouter()


@router.get("/", response_model=List[ExtensionRead])
async def get_extensions(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Get all extensions"""
    stmt = select(Extension).where(Extension.is_active == True)
    result = await session.execute(stmt)
    extensions = result.scalars().all()
    return extensions


@router.get("/{extension_id}", response_model=ExtensionRead)
async def get_extension(
    extension_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Get extension by ID"""
    stmt = select(Extension).where(Extension.id == extension_id)
    result = await session.execute(stmt)
    extension = result.scalar_one_or_none()
    
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extension not found"
        )
    
    return extension


@router.post("/", response_model=ExtensionRead)
async def create_extension(
    extension_data: ExtensionCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Create new extension"""
    # Check if extension number already exists
    stmt = select(Extension).where(Extension.extension_number == extension_data.extension_number)
    result = await session.execute(stmt)
    existing_extension = result.scalar_one_or_none()
    
    if existing_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension number already exists"
        )
    
    extension = Extension(**extension_data.dict())
    session.add(extension)
    await session.commit()
    await session.refresh(extension)
    
    return extension


@router.put("/{extension_id}", response_model=ExtensionRead)
async def update_extension(
    extension_id: str,
    extension_data: ExtensionUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Update extension"""
    stmt = select(Extension).where(Extension.id == extension_id)
    result = await session.execute(stmt)
    extension = result.scalar_one_or_none()
    
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extension not found"
        )
    
    # Update fields
    update_data = extension_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(extension, field, value)
    
    await session.commit()
    await session.refresh(extension)
    
    return extension


@router.delete("/{extension_id}")
async def delete_extension(
    extension_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """Delete extension (soft delete)"""
    stmt = select(Extension).where(Extension.id == extension_id)
    result = await session.execute(stmt)
    extension = result.scalar_one_or_none()
    
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extension not found"
        )
    
    extension.is_active = False
    await session.commit()
    
    return {"message": "Extension deleted successfully"}