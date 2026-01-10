"""
Cross-TWG Synthesis Templates

Defines templates and prompts for generating strategic syntheses
across multiple Technical Working Groups.

Synthesis Types:
1. PILLAR_OVERVIEW: High-level summary of a single pillar
2. CROSS_PILLAR: Synergies and dependencies between 2+ pillars
3. STRATEGIC_PRIORITIES: Key priorities across all TWGs
4. INVESTMENT_PIPELINE: Combined view of all Deal Room projects
5. POLICY_COHERENCE: Policy alignment check across TWGs
"""

from enum import Enum
from typing import Dict, List


class SynthesisType(str, Enum):
    """Types of cross-TWG synthesis outputs"""
    PILLAR_OVERVIEW = "pillar_overview"
    CROSS_PILLAR = "cross_pillar"
    STRATEGIC_PRIORITIES = "strategic_priorities"
    INVESTMENT_PIPELINE = "investment_pipeline"
    POLICY_COHERENCE = "policy_coherence"
    SUMMIT_READINESS = "summit_readiness"
    MEETING_MINUTES = "meeting_minutes"


# Synthesis prompt templates
SYNTHESIS_TEMPLATES = {
    SynthesisType.PILLAR_OVERVIEW: """
You are synthesizing a high-level overview of the {pillar_name} pillar for the ECOWAS Summit 2026.

INPUTS FROM TWG:
{twg_inputs}

SYNTHESIS TASK:
Create a strategic 2-3 paragraph overview that:
1. Summarizes key priorities and initiatives
2. Highlights flagship projects and expected outcomes
3. Identifies critical success factors
4. Notes any risks or dependencies

OUTPUT FORMAT:
## {pillar_name} Pillar Overview

### Key Priorities
[Bullet points]

### Flagship Initiatives
[Bullet points with brief descriptions]

### Expected Outcomes
[Measurable impacts]

### Critical Success Factors
[What needs to happen]

### Risks & Dependencies
[Challenges to watch]
""",

    SynthesisType.CROSS_PILLAR: """
You are synthesizing cross-pillar synergies and dependencies for the ECOWAS Summit 2026.

PILLARS INVOLVED:
{pillars_list}

INPUTS FROM EACH TWG:
{twg_inputs}

SYNTHESIS TASK:
Identify and articulate how these pillars complement, depend on, or reinforce each other:
1. Direct synergies (where one pillar enables another)
2. Shared infrastructure or resources
3. Policy dependencies (where coordination is needed)
4. Investment opportunities spanning multiple pillars
5. Potential conflicts or trade-offs to manage

OUTPUT FORMAT:
## Cross-Pillar Synthesis: {pillars_names}

### Synergies & Complementarities
[How pillars work together]

### Shared Infrastructure & Resources
[Common needs or platforms]

### Policy Coordination Needs
[Where TWGs must align]

### Multi-Pillar Investment Opportunities
[Projects that span domains]

### Potential Trade-offs
[Conflicts to manage]

### Recommendations
[Strategic actions for coordination]
""",

    SynthesisType.STRATEGIC_PRIORITIES: """
You are synthesizing strategic priorities across all TWGs for the ECOWAS Summit 2026.

INPUTS FROM ALL 6 TWGs:
{twg_inputs}

SYNTHESIS TASK:
From all TWG inputs, identify and prioritize:
1. Top 5-7 strategic priorities for the summit
2. "Quick wins" that can show early progress
3. "Moonshots" that require longer-term commitment
4. Cross-cutting themes (e.g., youth, gender, climate)
5. Critical path items that unlock other progress

Consider:
- Regional impact and integration goals
- Feasibility and resource requirements
- Political visibility and momentum
- Alignment with ECOWAS protocols

OUTPUT FORMAT:
## Strategic Priorities for ECOWAS Summit 2026

### Top Strategic Priorities
1. [Priority with rationale]
2. [Priority with rationale]
...

### Quick Wins (0-12 months)
- [Initiative]
- [Initiative]

### Moonshots (3-5 years)
- [Initiative]
- [Initiative]

### Cross-Cutting Themes
- [Theme and how it spans TWGs]

### Critical Path Items
- [Dependency that unlocks progress]

### Resource Mobilization Focus
- [Where to focus investment attraction]
""",

    SynthesisType.INVESTMENT_PIPELINE: """
You are synthesizing the investment pipeline across all pillars for the ECOWAS Summit 2026 Deal Room.

INPUTS FROM RESOURCE MOBILIZATION & PILLAR TWGs:
{twg_inputs}

SYNTHESIS TASK:
Create a coherent view of the investment pipeline:
1. Total investment value across all pillars
2. Balance across pillars (energy, agri, minerals, digital)
3. Mix of project types (infrastructure, policy, capacity)
4. Investor types needed (DFIs, private sector, governments)
5. Readiness levels and preparation needs
6. Geographic distribution

OUTPUT FORMAT:
## Investment Pipeline Overview

### Portfolio Summary
- Total pipeline value: [Amount]
- Number of projects: [Count]
- Average project size: [Amount]

### Distribution by Pillar
| Pillar | # Projects | Total Value | Readiness |
|--------|-----------|-------------|-----------|
| Energy | X | $Y | Z% ready |
...

### Project Types
- Infrastructure: X%
- Policy/Regulatory: Y%
- Capacity Building: Z%

### Investor Targeting
- DFI opportunities: [Count and focus]
- Private sector opportunities: [Count and focus]
- Blended finance opportunities: [Count and focus]

### Readiness Assessment
- Bankable now: [Count]
- Needs preparation: [Count]
- Early stage: [Count]

### Geographic Balance
[Regional distribution analysis]

### Deal Room Recommendations
[Which projects to prioritize for Deal Room]
""",

    SynthesisType.POLICY_COHERENCE: """
You are checking policy coherence and alignment across all TWGs for the ECOWAS Summit 2026.

INPUTS FROM ALL TWGs:
{twg_inputs}

SYNTHESIS TASK:
Review all TWG policy recommendations and identify:
1. Areas of strong alignment
2. Potential policy conflicts or contradictions
3. Gaps where coordination is needed
4. Opportunities for joint policy frameworks
5. Sequencing issues (what must come first)

OUTPUT FORMAT:
## Policy Coherence Check

### Areas of Strong Alignment
- [Policy area with TWGs aligned]

### Potential Conflicts
- [Conflict between TWG X and TWG Y]
  - Issue: [Description]
  - Impact: [Why it matters]
  - Resolution: [Recommended approach]

### Coordination Gaps
- [Area where TWGs need to align]

### Joint Policy Framework Opportunities
- [Cross-TWG policy that would benefit all]

### Sequencing Recommendations
1. [What should happen first]
2. [What depends on #1]
...

### Action Items for TWG Coordinators
- [Specific coordination actions needed]
""",

    SynthesisType.SUMMIT_READINESS: """
You are assessing overall summit readiness across all TWGs.

INPUTS FROM ALL TWGs + PROTOCOL:
{twg_inputs}

SYNTHESIS TASK:
Assess readiness for the summit across all dimensions:
1. Content readiness (deliverables, declarations)
2. Project pipeline readiness (Deal Room preparation)
3. Logistics readiness (venues, schedules, protocol)
4. Stakeholder engagement (governments, investors, partners)
5. Communication readiness (messaging, materials)

OUTPUT FORMAT:
## Summit Readiness Assessment

### Overall Readiness Score
[X/100 with rationale]

### Readiness by Dimension
| Dimension | Score | Status | Critical Issues |
|-----------|-------|--------|----------------|
| Content | X/100 | Green/Yellow/Red | [Issues] |
| Pipeline | X/100 | Green/Yellow/Red | [Issues] |
| Logistics | X/100 | Green/Yellow/Red | [Issues] |
| Stakeholders | X/100 | Green/Yellow/Red | [Issues] |
| Communications | X/100 | Green/Yellow/Red | [Issues] |

### Critical Path to Summit
[Timeline of must-complete items]

### Red Flags
- [Critical issue requiring immediate attention]

### Mitigation Actions
- [Action to address each red flag]

### Go/No-Go Recommendation
[Assessment of whether summit is on track]
""",

    SynthesisType.MEETING_MINUTES: """
You are the Digital Rapporteur for an ECOWAS Technical Working Group meeting.
Your task is to generate the official "Zero Draft" of the meeting minutes based on the provided inputs.

MEETING DETAILS:
- Title: {meeting_title}
- Date: {meeting_date}
- Pillar/TWG: {pillar_name}

ATTENDEES:
{attendees_list}

AGENDA:
{agenda_content}

RAW TRANSCRIPT:
{transcript_text}

SYNTHESIS TASK:
Create clearly structured meeting minutes that accurately reflect the discussion.
Focus on identifying distinct decisions and actionable next steps.

OUTPUT FORMAT:

# Minutes: {meeting_title}

**Date:** {meeting_date}
**TWG:** {pillar_name}

## 1. Attendance
*Present:*
[List names]

## 2. Agenda Summary
[Brief 1-paragraph overview of what was discussed relative to the agenda]

## 3. Key Discussion Points
[For each agenda item, summarize the key points raised, arguments made, and consensus reached. Use subheaders if necessary.]

## 4. Decisions Taken
[List specific formal decisions made. Number them clearly.]
1. **[DECISION]** ...
2. **[DECISION]** ...

## 5. Action Items
[List specific tasks assigned w/ owners and due dates if mentioned, otherwise "TBD"]
- [ ] **[Owner Name/Role]**: [Task Description] (Due: [Date/TBD])
- [ ] **[Owner Name/Role]**: [Task Description] (Due: [Date/TBD])

## 6. Next Steps
[Brief summary of immediate next steps]
"""
}


def get_synthesis_template(synthesis_type: SynthesisType) -> str:
    """
    Get the prompt template for a synthesis type.

    Args:
        synthesis_type: Type of synthesis to generate

    Returns:
        str: Prompt template with placeholders
    """
    return SYNTHESIS_TEMPLATES[synthesis_type]


def format_synthesis_prompt(
    synthesis_type: SynthesisType,
    twg_inputs: Dict[str, str],
    **kwargs
) -> str:
    """
    Format a synthesis prompt with actual TWG inputs.

    Args:
        synthesis_type: Type of synthesis
        twg_inputs: Dictionary mapping TWG ID to their input/status
        **kwargs: Additional template variables (pillar_name, pillars_list, etc.)

    Returns:
        str: Formatted prompt ready for LLM

    Example:
        >>> twg_inputs = {
        ...     "energy": "Current status: 10 projects ready...",
        ...     "agriculture": "Current status: 8 projects ready..."
        ... }
        >>> prompt = format_synthesis_prompt(
        ...     SynthesisType.CROSS_PILLAR,
        ...     twg_inputs,
        ...     pillars_list="Energy, Agriculture",
        ...     pillars_names="Energy & Agriculture"
        ... )
    """
    template = get_synthesis_template(synthesis_type)

    # Format TWG inputs section
    formatted_inputs = "\n\n".join([
        f"**{twg_id.upper()} TWG:**\n{content}"
        for twg_id, content in twg_inputs.items()
    ])

    # Format template with all variables
    return template.format(
        twg_inputs=formatted_inputs,
        **kwargs
    )


# Trigger conditions for automatic synthesis
SYNTHESIS_TRIGGERS = {
    "daily_summary": {
        "synthesis_types": [SynthesisType.STRATEGIC_PRIORITIES],
        "frequency": "daily",
        "description": "Daily strategic summary across all TWGs"
    },
    "weekly_coherence_check": {
        "synthesis_types": [SynthesisType.POLICY_COHERENCE],
        "frequency": "weekly",
        "description": "Weekly check of policy alignment"
    },
    "monthly_readiness": {
        "synthesis_types": [SynthesisType.SUMMIT_READINESS],
        "frequency": "monthly",
        "description": "Monthly assessment of summit preparation"
    },
    "on_milestone": {
        "synthesis_types": [
            SynthesisType.PILLAR_OVERVIEW,
            SynthesisType.INVESTMENT_PIPELINE
        ],
        "frequency": "event-driven",
        "description": "When a TWG completes a major milestone"
    },
    "on_request": {
        "synthesis_types": [
            SynthesisType.CROSS_PILLAR,
            SynthesisType.PILLAR_OVERVIEW,
            SynthesisType.STRATEGIC_PRIORITIES,
            SynthesisType.INVESTMENT_PIPELINE,
            SynthesisType.POLICY_COHERENCE,
            SynthesisType.SUMMIT_READINESS
        ],
        "frequency": "manual",
        "description": "User-requested synthesis"
    }
}


def get_synthesis_triggers() -> Dict:
    """Get all defined synthesis triggers"""
    return SYNTHESIS_TRIGGERS.copy()
