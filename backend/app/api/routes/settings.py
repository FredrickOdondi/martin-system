from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.core.database import get_db
from app.models.models import SystemSettings, TwgSettings, User, UserRole, TWG
from app.api.deps import get_current_active_user, require_admin, has_twg_access
from app.schemas.schemas import (
    SystemSettingsRead, SystemSettingsUpdate,
    TwgSettingsRead, TwgSettingsUpdate
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# --- System Settings (Admin Only) ---

@router.get("/system", response_model=SystemSettingsRead)
async def get_system_settings(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get global system configuration. Admin only.
    """
    # Fetch singleton
    result = await db.execute(select(SystemSettings))
    settings = result.scalars().first()
    
    if not settings:
        # Lazy initialization of default settings
        settings = SystemSettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        
    return SystemSettingsRead.from_orm_custom(settings)

@router.patch("/system", response_model=SystemSettingsRead)
async def update_system_settings(
    settings_in: SystemSettingsUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update global system configuration. Admin only.
    """
    result = await db.execute(select(SystemSettings))
    db_settings = result.scalars().first()
    
    if not db_settings:
        db_settings = SystemSettings()
        db.add(db_settings)
    
    update_data = settings_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_settings, field, value)
        
    db_settings.updated_by_id = current_user.id
    
    await db.commit()
    await db.refresh(db_settings)
    
    return SystemSettingsRead.from_orm_custom(db_settings)

# --- TWG Settings (Facilitator/Admin) ---

@router.get("/twg/{twg_id}", response_model=TwgSettingsRead)
async def get_twg_settings(
    twg_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get settings for a specific TWG.
    Access: Admin or Member of the TWG.
    """
    # 1. Verify TWG exists
    twg = await db.get(TWG, twg_id)
    if not twg:
        raise HTTPException(status_code=404, detail="TWG not found")
        
    # 2. Check Access (Read allowed for members)
    if not has_twg_access(current_user, twg_id) and current_user.role not in [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD]:
         raise HTTPException(status_code=403, detail="Access denied to this TWG")
         
    # 3. Fetch Settings
    result = await db.execute(select(TwgSettings).where(TwgSettings.twg_id == twg_id))
    settings = result.scalars().first()
    
    if not settings:
        # Default lazy init
        settings = TwgSettings(twg_id=twg_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        
    return settings

@router.patch("/twg/{twg_id}", response_model=TwgSettingsRead)
async def update_twg_settings(
    twg_id: uuid.UUID,
    settings_in: TwgSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update TWG settings.
    Access: Admin, Secretariat Lead, or Facilitator of THIS Twg.
    """
    # 1. Check Role & Access
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SECRETARIAT_LEAD]
    
    # Logic from `require_facilitator` implies strictly role check, but we need context check too
    # Simple check:
    if not is_admin:
        # Must be facilitator AND have access
        if current_user.role != UserRole.TWG_FACILITATOR:
             raise HTTPException(status_code=403, detail="Only Facilitators can modify TWG settings")
        if not has_twg_access(current_user, twg_id):
             raise HTTPException(status_code=403, detail="Access denied to this TWG")

    # 2. Fetch
    result = await db.execute(select(TwgSettings).where(TwgSettings.twg_id == twg_id))
    db_settings = result.scalars().first()
    
    if not db_settings:
        db_settings = TwgSettings(twg_id=twg_id)
        db.add(db_settings)
        
    # 3. Update
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_settings, field, value)
        
    db_settings.updated_by_id = current_user.id
    
    await db.commit()
    await db.refresh(db_settings)
    
    return db_settings
