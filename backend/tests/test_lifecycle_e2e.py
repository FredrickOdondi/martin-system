import pytest
import uuid
import pytest_asyncio
from httpx import AsyncClient
from app.models.models import ProjectStatus, UserRole
from app.services.lifecycle_service import LifecycleService

# Mock or use actual client setup
# We assume standard pytest-asyncio and httpx setup available in the project

@pytest.mark.asyncio
async def test_full_lifecycle_flow(client: AsyncClient, admin_token_headers):
    async_client = client # Alias for clarity if needed, or just use client
    # 1. Create a Project in DRAFT (via Ingestion)
    # Need to create a TWG first as it is required
    twg_payload = {"name": "Test TWG", "pillar": "energy_infrastructure"}
    twg_res = await async_client.post("/api/v1/twgs/", json=twg_payload, headers=admin_token_headers)
    assert twg_res.status_code == 201
    twg_id = twg_res.json()["id"]

    ingest_payload = {
        "twg_id": twg_id,
        "name": "Lifecycle Test Project",
        "description": "Testing the 11-stage flow",
        "investment_size": 5000000,
        "readiness_score": 7.5,
        "strategic_alignment_score": 8.0,
        "pillar": "Energy Infrastructure", # Project pillar might be string? Or Enum?
        "lead_country": "Kenya"
    }

    res = await async_client.post("/api/v1/pipeline/ingest", json=ingest_payload, headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    project_id = data["id"]
    assert data["status"] == ProjectStatus.DRAFT.value
    
    # Verify allowed transitions for DRAFT
    assert ProjectStatus.PIPELINE.value in data["allowed_transitions"]

    # 2. Advance to PIPELINE
    advance_payload = {"new_stage": ProjectStatus.PIPELINE.value, "notes": "Submitting for review"}
    res = await async_client.post(f"/api/v1/pipeline/{project_id}/advance", json=advance_payload, headers=admin_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == ProjectStatus.PIPELINE.value

    # 3. Advance to UNDER_REVIEW (Auto or Manual)
    # Check allowed transitions
    allowed = res.json()["allowed_transitions"]
    assert ProjectStatus.UNDER_REVIEW.value in allowed

    advance_payload = {"new_stage": ProjectStatus.UNDER_REVIEW.value, "notes": "Starting deep dive"}
    res = await async_client.post(f"/api/v1/pipeline/{project_id}/advance", json=advance_payload, headers=admin_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == ProjectStatus.UNDER_REVIEW.value

    # 4. Advance to SUMMIT_READY (Success Path)
    # Could also go to NEEDS_REVISION or DECLINED
    advance_payload = {"new_stage": ProjectStatus.SUMMIT_READY.value, "notes": "Excellent project"}
    res = await async_client.post(f"/api/v1/pipeline/{project_id}/advance", json=advance_payload, headers=admin_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == ProjectStatus.SUMMIT_READY.value

    # 5. Advance to DEAL_ROOM_FEATURED
    advance_payload = {"new_stage": ProjectStatus.DEAL_ROOM_FEATURED.value, "notes": "Listing in deal room"}
    res = await async_client.post(f"/api/v1/pipeline/{project_id}/advance", json=advance_payload, headers=admin_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == ProjectStatus.DEAL_ROOM_FEATURED.value

    # 6. Advance to IN_NEGOTIATION
    advance_payload = {"new_stage": ProjectStatus.IN_NEGOTIATION.value, "notes": "Investors interested"}
    res = await async_client.post(f"/api/v1/pipeline/{project_id}/advance", json=advance_payload, headers=admin_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == ProjectStatus.IN_NEGOTIATION.value

    # 7. Advance to COMMITTED
    advance_payload = {"new_stage": ProjectStatus.COMMITTED.value, "notes": "Deal signed"}
    res = await async_client.post(f"/api/v1/pipeline/{project_id}/advance", json=advance_payload, headers=admin_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == ProjectStatus.COMMITTED.value
    
    # 8. Advance to IMPLEMENTED
    advance_payload = {"new_stage": ProjectStatus.IMPLEMENTED.value, "notes": "Construction complete"}
    res = await async_client.post(f"/api/v1/pipeline/{project_id}/advance", json=advance_payload, headers=admin_token_headers)
    assert res.status_code == 200
    assert res.json()["status"] == ProjectStatus.IMPLEMENTED.value

    # Done
