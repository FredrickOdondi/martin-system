"""
Deal Pipeline API Routes - Insights Endpoint Addition

Add this endpoint after line 298 in pipeline.py (after the score-details endpoint)
"""

@router.get("/{project_id}/insights")
async def get_project_insights(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered insights and recommendations for a project.
    Uses LLM to analyze project status, scores, and generate actionable next steps.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    insights = await insights_service.generate_project_insights(project, db)
    
    return {
        "project_id": str(project_id),
        "insight": insights["insight"],
        "recommendation": insights["recommendation"],
        "generated_at": datetime.now(UTC).isoformat()
    }
