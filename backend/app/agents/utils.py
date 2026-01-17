"""
Agent Utilities

Provides synchronous database access and helper functions for agents.
Critical for bridging the Gap between Sync Agents and Async Database for RAG context.
"""

from typing import Optional, Dict
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from loguru import logger
import uuid

from app.core.config import settings
from app.models.models import TWG, TWGPillar

# Create a synchronous engine for agent initialization/context resolution
# We must strip '+asyncpg' (Postgres) or '+aiosqlite' (SQLite) to use default sync drivers
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
sync_engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)

# Mapping from Agent ID to TWG Pillar Enum
AGENT_TO_PILLAR_MAP = {
    "energy": TWGPillar.energy_infrastructure,
    "agriculture": TWGPillar.agriculture_food_systems,
    "minerals": TWGPillar.critical_minerals_industrialization,
    "digital": TWGPillar.digital_economy_transformation,
    "protocol": TWGPillar.protocol_logistics,
    "resource_mobilization": TWGPillar.resource_mobilization
}

def get_twg_id_by_agent_id(agent_id: str) -> Optional[str]:
    """
    Synchronously resolve an Agent ID (e.g., 'energy') to its TWG UUID.
    Used for RAG namespace resolution.
    
    Args:
        agent_id: The agent identifier
        
    Returns:
        UUID string of the TWG or None if not found
    """
    pillar = AGENT_TO_PILLAR_MAP.get(agent_id)
    if not pillar:
        return None
        
    try:
        with SyncSession() as session:
            stmt = select(TWG).where(TWG.pillar == pillar).order_by(TWG.id)
            result = session.execute(stmt)
            twg = result.scalars().first()  # Use first() to handle duplicates gracefully
            
            if twg:
                logger.info(f"Resolved agent '{agent_id}' to TWG ID: {twg.id}")
                return str(twg.id)
            return None
    except Exception as e:
        logger.error(f"Error resolving TWG ID for agent {agent_id}: {e}")
        return None


def get_agent_id_by_twg_id(twg_id: str) -> Optional[str]:
    """
    Synchronously resolve a TWG UUID to its Agent ID (e.g., 'energy').
    Used for Strict RBAC routing.

    Args:
        twg_id: The TWG UUID string

    Returns:
        Agent ID string or None if not found
    """
    try:
        with SyncSession() as session:
            stmt = select(TWG).where(TWG.id == uuid.UUID(twg_id))
            twg = session.execute(stmt).scalar_one_or_none()

            if twg:
                # Reverse lookup from pillar
                for agent_id, pillar in AGENT_TO_PILLAR_MAP.items():
                    if pillar == twg.pillar:
                        return agent_id
            return None
    except Exception as e:
        logger.error(f"Error resolving Agent ID for TWG {twg_id}: {e}")
        return None
