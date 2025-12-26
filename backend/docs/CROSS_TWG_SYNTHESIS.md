# Cross-TWG Synthesis

The **Cross-TWG Synthesis** feature enables the Supervisor agent to automatically or manually generate strategic summaries, identify synergies, and check alignment across multiple Technical Working Groups (TWGs).

## Overview

The Supervisor agent can generate 5 types of strategic syntheses:

1. **Pillar Overview** - Comprehensive summary of a single pillar (Energy, Agriculture, Minerals, Digital)
2. **Cross-Pillar Synthesis** - Synergies and dependencies between 2+ pillars
3. **Strategic Priorities** - Top priorities across all TWGs
4. **Policy Coherence Check** - Alignment and conflicts in policy recommendations
5. **Summit Readiness Assessment** - Comprehensive readiness evaluation

## Architecture

###Files

- **[synthesis_templates.py](../app/agents/synthesis_templates.py)** - Prompt templates for each synthesis type
- **[supervisor.py](../app/agents/supervisor.py)** - Synthesis generation methods
- **[chat_agent.py](../scripts/chat_agent.py)** - CLI commands for synthesis
- **[test_synthesis.py](../test_synthesis.py)** - Test suite

### How It Works

1. **Supervisor collects input** from relevant TWG agents
2. **Template is selected** based on synthesis type
3. **Prompt is formatted** with TWG inputs
4. **Supervisor's LLM generates** structured synthesis
5. **Result is returned** as formatted report

## Usage

### Via CLI (Interactive)

```bash
cd backend
python3 scripts/chat_agent.py --agent supervisor
```

#### Available Commands

```
synthesis:pillar PILLAR              # Generate pillar overview
synthesis:cross PILLAR1 PILLAR2      # Generate cross-pillar synthesis
synthesis:priorities                 # Generate strategic priorities
synthesis:coherence                  # Check policy coherence
synthesis:readiness                  # Assess summit readiness
```

#### Examples

**Single Pillar Overview:**
```
You: synthesis:pillar energy

🔄 Generating Energy pillar overview...

## Energy & Infrastructure Pillar Overview

### Key Priorities
- Regional power pool expansion (WAPP)
...
```

**Cross-Pillar Synthesis:**
```
You: synthesis:cross energy agriculture

🔄 Generating cross-pillar synthesis for energy & agriculture...

## Cross-Pillar Synthesis: Energy & Agriculture

### Synergies & Complementarities
- Energy access enables agricultural mechanization...
```

**Strategic Priorities:**
```
You: synthesis:priorities

🔄 Generating strategic priorities synthesis...
⏳ This may take 30-60 seconds (querying all TWGs)...

## Strategic Priorities for ECOWAS Summit 2026

### Top Strategic Priorities
1. Regional Power Integration...
2. Agricultural Value Chain Development...
```

### Via Python API

```python
from app.agents.supervisor import create_supervisor

# Create supervisor with all TWGs registered
supervisor = create_supervisor(auto_register=True)

# Generate pillar overview
energy_overview = supervisor.generate_pillar_overview("energy")
print(energy_overview)

# Generate cross-pillar synthesis
energy_agri_synthesis = supervisor.generate_cross_pillar_synthesis(
    ["energy", "agriculture"]
)
print(energy_agri_synthesis)

# Generate strategic priorities
priorities = supervisor.generate_strategic_priorities()
print(priorities)

# Policy coherence check
coherence = supervisor.generate_policy_coherence_check()
print(coherence)

# Summit readiness assessment
readiness = supervisor.generate_summit_readiness_assessment()
print(readiness)
```

## Synthesis Types Detailed

### 1. Pillar Overview

**Purpose**: Strategic summary of a single pillar

**Inputs**: Comprehensive status from the pillar TWG

**Output Sections**:
- Key Priorities
- Flagship Initiatives
- Expected Outcomes
- Critical Success Factors
- Risks & Dependencies

**Use Cases**:
- Briefing materials for stakeholders
- Progress reporting
- Investment pitch preparation

**Example**:
```python
overview = supervisor.generate_pillar_overview("energy")
```

---

### 2. Cross-Pillar Synthesis

**Purpose**: Identify synergies and dependencies between pillars

**Inputs**: Status and priorities from 2+ pillar TWGs

**Output Sections**:
- Synergies & Complementarities
- Shared Infrastructure & Resources
- Policy Coordination Needs
- Multi-Pillar Investment Opportunities
- Potential Trade-offs
- Recommendations

**Use Cases**:
- Coordination planning
- Multi-pillar project identification
- Dependency mapping

**Example**:
```python
synthesis = supervisor.generate_cross_pillar_synthesis(
    ["energy", "minerals", "digital"]
)
```

---

### 3. Strategic Priorities

**Purpose**: Top-level priorities across all TWGs

**Inputs**: Status from all 6 TWGs

**Output Sections**:
- Top Strategic Priorities (5-7 items)
- Quick Wins (0-12 months)
- Moonshots (3-5 years)
- Cross-Cutting Themes
- Critical Path Items
- Resource Mobilization Focus

**Use Cases**:
- Summit agenda setting
- Leadership briefings
- Resource allocation decisions

**Example**:
```python
priorities = supervisor.generate_strategic_priorities()
```

---

### 4. Policy Coherence Check

**Purpose**: Ensure policy recommendations are aligned

**Inputs**: Policy recommendations from all TWGs

**Output Sections**:
- Areas of Strong Alignment
- Potential Conflicts (with resolutions)
- Coordination Gaps
- Joint Policy Framework Opportunities
- Sequencing Recommendations
- Action Items for TWG Coordinators

**Use Cases**:
- Pre-summit policy review
- Declaration drafting
- Conflict resolution

**Example**:
```python
coherence = supervisor.generate_policy_coherence_check()
```

---

### 5. Summit Readiness Assessment

**Purpose**: Comprehensive readiness evaluation

**Inputs**: Readiness status from all TWGs + Protocol

**Output Sections**:
- Overall Readiness Score
- Readiness by Dimension (Content, Pipeline, Logistics, etc.)
- Critical Path to Summit
- Red Flags
- Mitigation Actions
- Go/No-Go Recommendation

**Use Cases**:
- Progress tracking
- Risk management
- Decision-making on summit timing

**Example**:
```python
readiness = supervisor.generate_summit_readiness_assessment()
```

## Automated Triggers (Future Enhancement)

Synthesis can be triggered automatically based on:

| Trigger | Frequency | Synthesis Type |
|---------|-----------|---------------|
| Daily Summary | Daily | Strategic Priorities |
| Weekly Check | Weekly | Policy Coherence |
| Monthly Report | Monthly | Summit Readiness |
| Milestone | Event-driven | Pillar Overview, Investment Pipeline |
| On Request | Manual | All types |

**Note**: Automated triggers are designed but not yet implemented. Currently all synthesis is manual/on-demand.

## Performance Considerations

- **Time**: Each synthesis takes 30-60 seconds (multiple LLM calls)
- **LLM Calls**:
  - Pillar Overview: 1 TWG query + 1 synthesis = 2 calls
  - Cross-Pillar: N TWG queries + 1 synthesis = N+1 calls
  - Strategic Priorities: 6 TWG queries + 1 synthesis = 7 calls
  - Policy Coherence: 6 TWG queries + 1 synthesis = 7 calls
  - Summit Readiness: 6 TWG queries + 1 synthesis = 7 calls

- **Optimization**: TWG responses are cached during collection phase

## Best Practices

1. **Timing**: Run synthesis when TWGs have recent updates
2. **Specificity**: Use cross-pillar synthesis for specific combinations
3. **Regular Cadence**: Weekly policy coherence + monthly readiness recommended
4. **Save Outputs**: Store synthesis reports for historical tracking
5. **Act on Findings**: Use synthesis to drive TWG coordination meetings

## Troubleshooting

### Synthesis Takes Too Long

- Check Ollama is running and responsive
- Verify all TWG agents are registered
- Try with fewer TWGs (e.g., 2-pillar cross synthesis)

### Incomplete or Generic Output

- Ensure TWGs have been active (have conversation history)
- Try querying TWGs individually first to populate context
- Check that system prompts are detailed

### Connection Errors

- Verify Redis is running if using memory
- Check Ollama service status
- Review logs for specific error messages

## Testing

Run the test suite:

```bash
cd backend
python3 test_synthesis.py
```

This provides interactive testing of all synthesis types.

## Future Enhancements

Planned improvements:

1. **Automated Scheduling**: Cron-like triggers for regular synthesis
2. **Synthesis History**: Store and retrieve past syntheses
3. **Comparison Mode**: Compare current vs. previous synthesis
4. **Export Formats**: PDF, DOCX, PowerPoint generation
5. **Interactive Refinement**: Follow-up questions to deepen synthesis
6. **Multi-Language**: Generate synthesis in French, Portuguese
7. **Custom Templates**: User-defined synthesis templates

---

**Last Updated**: 2025-12-26
**Version**: 1.0.0
