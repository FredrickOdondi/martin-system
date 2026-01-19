
from typing import List, Optional
from uuid import UUID
from app.agents.langgraph_base_agent import LangGraphBaseAgent
from loguru import logger

class LangGraphResourceMobilizationAgent(LangGraphBaseAgent):
    """LangGraph-based Resource Mobilization TWG Agent ('Investment Martin')"""

    def __init__(self, keep_history: bool = True, session_id: str = None):
        super().__init__(
            agent_id="resource_mobilization",
            keep_history=keep_history,
            max_history=15,
            session_id=session_id
        )
        # Register specialized tools
        self._add_investment_tools()

    def _add_investment_tools(self):
        """Add tools for Deal Pipeline and Investor Matching."""
        
        # Import new specialized tools
        from app.tools.deal_pipeline_tools import (
            get_project_details,
            list_flagship_projects,
            trigger_investor_matching,
            generate_investment_memo,
            analyze_project_documents
        )

        async def get_deal_pipeline_summary_tool() -> str:
            """
            Get a comprehensive summary of the Deal Pipeline.
            Returns status counts, total investment value, and list of key projects with their AfCEN scores.
            Use this to generate the 'Deal Pipeline Status' report.
            """
            from app.core.database import get_db_session_context
            from app.models.models import Project
            from sqlalchemy import select

            try:
                async with get_db_session_context() as db:
                    stmt = select(Project)
                    result = await db.execute(stmt)
                    projects = result.scalars().all()
                    
                    if not projects:
                        return "Deal Pipeline is currently empty. No projects identified."

                    total_value = sum(float(p.investment_size or 0) for p in projects)
                    by_status = {}
                    by_score = {"Ready (8-10)": [], "Near-Ready (6-7)": [], "Early (0-5)": []}
                    
                    for p in projects:
                        # Status count
                        s = p.status.value
                        by_status[s] = by_status.get(s, 0) + 1
                        
                        # Score grouping
                        score = float(p.afcen_score or 0)
                        info = f"- {p.name} (${p.investment_size:,.0f} {p.currency}) [Score: {score}]"
                        
                        if score >= 80: # Scaled 0-100
                            by_score["Ready (8-10)"].append(info)
                        elif score >= 60:
                            by_score["Near-Ready (6-7)"].append(info)
                        else:
                            by_score["Early (0-5)"].append(info)

                    # Build Report
                    report = f"💰 **DEAL PIPELINE SUMMARY**\n\n"
                    report += f"**Total Projects:** {len(projects)}\n"
                    report += f"**Total Investment Value:** ${total_value:,.2f}\n\n"
                    
                    report += "**By Readiness (AfCEN Score):**\n"
                    for category, items in by_score.items():
                        report += f"**{category}**: {len(items)}\n"
                        for item in items[:5]: # Top 5 only
                            report += f"  {item}\n"
                        if len(items) > 5:
                            report += f"  ...and {len(items)-5} more\n"
                        report += "\n"
                        
                    report += "**By Stage:**\n"
                    for status, count in by_status.items():
                        report += f"- {status}: {count}\n"
                        
                    return report

            except Exception as e:
                logger.error(f"Error in pipeline summary tool: {e}")
                return f"Error retrieving pipeline data: {str(e)}"

        async def get_project_matches_tool(project_name: str) -> str:
            """
            Get detailed list of matched investors for a project.
            Args:
                project_name: Name of the project (fuzzy match)
            """
            from app.core.database import get_db_session_context
            from app.services.investor_matching_service import get_investor_matching_service
            from app.models.models import Project
            from sqlalchemy import select
            
            async with get_db_session_context() as db:
                stmt = select(Project).where(Project.name.ilike(f"%{project_name}%"))
                res = await db.execute(stmt)
                project = res.scalars().first()
                if not project:
                    return f"Error: Project '{project_name}' not found."
                
                service = get_investor_matching_service(db)
                matches = await service.get_matches_for_project(project.id)
                
                if not matches:
                    return f"No investors matched yet for {project.name}. Try running `trigger_investor_matching` first."
                
                out = f"🤝 **Investor Matches for {project.name}**\n\n"
                for m in matches[:10]: # Limit 10
                    inv = m['investor']
                    score = m['score']
                    status = m['status']
                    out += f"- **{inv.name}** (Score: {score})\n"
                    out += f"  Type: {inv.investor_type} | Status: {status}\n"
                    
                return out

        # Register inline tools
        self.add_tool(get_deal_pipeline_summary_tool)
        self.add_tool(get_project_matches_tool)
        
        # Register new specialized tools
        self.add_tool(get_project_details)
        self.add_tool(list_flagship_projects)
        self.add_tool(trigger_investor_matching)
        self.add_tool(generate_investment_memo)
        self.add_tool(analyze_project_documents)  # NEW: AI document analysis

def create_langgraph_resource_mobilization_agent(keep_history: bool = True, session_id: str = None) -> LangGraphResourceMobilizationAgent:
    return LangGraphResourceMobilizationAgent(keep_history=keep_history, session_id=session_id)
