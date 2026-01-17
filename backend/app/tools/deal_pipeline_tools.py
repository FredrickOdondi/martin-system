"""
Deal Pipeline Tools for AI Agents

This module provides tools for the Resource Mobilization Agent to interact with
the deal pipeline, including fetching project details, running matching, and
generating investment memos.
"""

from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
from sqlalchemy import select

# Import dependencies
from app.core.database import get_db_session_context
from app.services.project_pipeline_service import ProjectPipelineService
from app.services.investor_matching_service import InvestorMatchingService, get_investor_matching_service
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Note: These tools are async because they need DB access

async def get_project_details(project_id: str) -> str:
    """
    Fetch detailed information about a specific project, including scores and status.
    
    Args:
        project_id: The UUID of the project to retrieve.
        
    Returns:
        JSON string containing project details, scores, and status.
    """
    try:
        async with get_db_session_context() as db:
            service = ProjectPipelineService(db)
            
            # Use service method if available, or manual fetch for details not in service
            # ProjectPipelineService doesn't have a simple 'get_full_details' yet, so we use logic here.
            
            from app.models.models import Project, ProjectScoreDetail, ScoringCriteria
            
            # 1. Fetch Project
            stmt = select(Project).where(Project.id == project_id)
            result = await db.execute(stmt)
            project = result.scalars().first()
            
            if not project:
                return f"Error: Project with ID {project_id} not found."
            
            # 2. Fetch Scores
            score_stmt = select(ProjectScoreDetail, ScoringCriteria).join(ScoringCriteria)\
                .where(ProjectScoreDetail.project_id == project_id)
            score_res = await db.execute(score_stmt)
            scores = score_res.all() # list of (ProjectScoreDetail, ScoringCriteria)
            
            # 3. Format Response
            project_dict = {
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status.value if hasattr(project.status, 'value') else project.status,
                "investment_size": float(project.investment_size or 0),
                "currency": project.currency,
                "readiness_score": float(project.readiness_score or 0),
                "afcen_score": float(project.afcen_score or 0),
                "pillar": project.pillar.value if hasattr(project.pillar, 'value') else project.pillar,
                "is_flagship": project.is_flagship,
                "lead_country": project.lead_country
            }
            
            score_details = []
            for detail, criteria in scores:
                score_details.append({
                    "criterion": criteria.criterion_name,
                    "score": float(detail.score or 0),
                    "notes": detail.notes
                })
                
            return json.dumps({
                "project": project_dict,
                "scores": score_details
            }, indent=2)
            
    except Exception as e:
        logger.error(f"Error fetching project details: {e}")
        return f"Error fetching project details: {str(e)}"

async def list_flagship_projects() -> str:
    """
    List all projects marked as 'Flagship' in the Deal Room.
    
    Returns:
        JSON string of flagship projects.
    """
    try:
        async with get_db_session_context() as db:
            from app.models.models import Project
            
            stmt = select(Project).where(Project.is_flagship == True)
            result = await db.execute(stmt)
            projects = result.scalars().all()
            
            formatted = []
            for p in projects:
                formatted.append({
                    "id": str(p.id),
                    "name": p.name,
                    "investment_size": float(p.investment_size or 0),
                    "status": p.status.value if hasattr(p.status, 'value') else p.status,
                    "afcen_score": float(p.afcen_score or 0)
                })
                
            if not formatted:
                return "No flagship projects found in the Deal Room."
                
            return json.dumps(formatted, indent=2)
            
    except Exception as e:
        logger.error(f"Error listing flagship projects: {e}")
        return f"Error listing flagship projects: {str(e)}"

async def trigger_investor_matching(project_id: str) -> str:
    """
    Trigger the investor matching engine for a specific project.
    
    Args:
        project_id: The UUID of the project.
        
    Returns:
        Summary of matches found.
    """
    try:
        async with get_db_session_context() as db:
            service = get_investor_matching_service(db)
            result = await service.match_investors(project_id)
            
            return json.dumps(result, indent=2)
            
    except Exception as e:
        logger.error(f"Error triggering matching: {e}")
        return f"Error triggering matching: {str(e)}"

async def generate_investment_memo(project_id: str) -> str:
    """
    Generate a draft investment memo for a project.
    
    Args:
        project_id: The UUID of the project.
        
    Returns:
        The generated memo text.
    """
    try:
        # 1. Fetch Data (Re-using the logic from get_project_details but internally)
        details_json = await get_project_details(project_id)
        
        if "Error" in details_json:
            return details_json
            
        # 2. LLM Service
        # LLMService might not need DB session depending on implementation.
        # Assuming we can instantiate it directly as it likely uses API keys from env.
        llm = LLMService() 
        
        prompt = f"""
        You are an Investment Analyst for the ECOWAS Summit.
        Please draft a professional Investment Memo for the following project based on the data provided:
        
        {details_json}
        
        Structure the memo with the following sections:
        1. Executive Summary
        2. Strategic Rationale
        3. Financial Overview
        4. Risks & Mitigations
        5. Recommendation
        
        Format as Markdown.
        """
        
        # We need an async generation method if available, otherwise strict synchronous might block loop
        # Check if LLMService has async method. If not, run in executor or if it is fast enough.
        # Most LLM calls are I/O bound.
        memo = await llm.generate_text_async(prompt, max_tokens=2000)
        return memo
        
    except Exception as e:
        logger.error(f"Error generating memo: {e}")
        return f"Error generating memo: {str(e)}"

# Tool definitions
DEAL_PIPELINE_TOOLS = [
    {
        "name": "get_project_details",
        "description": "Fetch details, scores, and status for a specific project.",
        "parameters": {
            "project_id": "The UUID of the project"
        },
        "function": get_project_details
    },
    {
        "name": "list_flagship_projects",
        "description": "List all high-priority 'Flagship' projects in the Deal Room.",
        "parameters": {},
        "function": list_flagship_projects
    },
    {
        "name": "trigger_investor_matching",
        "description": "Run the investor matching engine for a project to find new potential investors.",
        "parameters": {
            "project_id": "The UUID of the project"
        },
        "function": trigger_investor_matching
    },
    {
        "name": "generate_investment_memo",
        "description": "Draft a professional investment memo for a project.",
        "parameters": {
            "project_id": "The UUID of the project"
        },
        "function": generate_investment_memo
    }
]
