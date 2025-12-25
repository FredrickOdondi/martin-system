# AI Agents - Setup and Usage Guide

## Overview

This system includes 7 AI agents for the ECOWAS Summit 2026 TWG Support System:

1. **Supervisor Agent** - Central coordinator with intelligent delegation to all TWGs
2. **Energy Agent** - Energy & Infrastructure TWG
3. **Agriculture Agent** - Agriculture & Food Systems TWG
4. **Minerals Agent** - Critical Minerals & Industrialization TWG
5. **Digital Agent** - Digital Economy & Transformation TWG
6. **Protocol Agent** - Protocol & Logistics TWG
7. **Resource Mobilization Agent** - Investment pipeline TWG

### Supervisor Agent - Enhanced Orchestration

The Supervisor Agent is the central coordinator with advanced capabilities:

- **Automatic Agent Registration**: Automatically connects to all 6 TWG agents on initialization
- **Intelligent Query Routing**: Analyzes queries and delegates to the most relevant agent(s)
- **Multi-Agent Consultation**: Can consult multiple TWG agents for cross-cutting issues
- **Response Synthesis**: Combines insights from multiple agents into coherent recommendations
- **Domain Expertise Mapping**: Uses keyword analysis to match queries to appropriate TWGs

## Prerequisites

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai](https://ollama.ai)

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

### 2. Pull the Model

```bash
ollama pull qwen2.5:0.5b
```

### 3. Start Ollama Server

```bash
ollama serve
```

Keep this running in a separate terminal.

### 4. Install Python Dependencies

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Testing Agents via CLI

### Basic Usage

```bash
# From the backend directory
python scripts/chat_agent.py --agent <agent_name>
```

### Examples

**Chat with Supervisor:**
```bash
python scripts/chat_agent.py --agent supervisor
```

**Chat with Energy Agent:**
```bash
python scripts/chat_agent.py --agent energy
```

**Chat with Agriculture Agent:**
```bash
python scripts/chat_agent.py --agent agriculture
```

**All available agents:**
- `supervisor`
- `energy`
- `agriculture`
- `minerals`
- `digital`
- `protocol`
- `resource_mobilization`

### CLI Options

```bash
# Disable conversation history
python scripts/chat_agent.py --agent energy --no-history

# Enable debug logging
python scripts/chat_agent.py --agent supervisor --debug

# Show help
python scripts/chat_agent.py --help
```

### CLI Commands

While chatting with an agent:

- **Type a message** - Send to the agent
- **quit** or **exit** - Exit the chat
- **reset** - Clear conversation history
- **info** - Show agent information
- **help** - Show help message

## Example Conversations

### Supervisor Agent - Intelligent Delegation

The Supervisor Agent automatically delegates to the appropriate TWG agents:

**Single Agent Delegation:**
```
You: What are the renewable energy opportunities in West Africa?
Supervisor: [Consulted ENERGY TWG]

West Africa has massive renewable energy potential:
1. Solar - Abundant sunshine across the Sahel region
2. Wind - Strong coastal winds in Senegal, Mauritania
3. Hydropower - Major rivers (Niger, Senegal, Volta)
4. The WAPP (West African Power Pool) framework enables regional integration...
```

**Multi-Agent Synthesis:**
```
You: How can we attract investment for solar-powered irrigation systems?
Supervisor: [Consulted ENERGY, AGRICULTURE, and RESOURCE_MOBILIZATION TWGs]

This cross-cutting opportunity requires coordinated action:

ENERGY Perspective: Solar mini-grids can provide reliable off-grid power for
agricultural operations with declining costs making them increasingly viable...

AGRICULTURE Perspective: Irrigation is critical for year-round farming and
climate resilience. Solar-powered systems reduce operational costs...

INVESTMENT Perspective: These projects score high on AfCEN criteria - strong
regional impact, clear revenue models from crop sales, and innovation in
agri-energy nexus...

SYNTHESIS: Priority actions include...
```

**General Knowledge:**
```
You: What are the main objectives of the ECOWAS Summit 2026?
Supervisor: The ECOWAS Summit 2026 aims to accelerate regional economic integration
through four integrated pillars:
1. Energy Transition - Regional power integration and renewable energy
2. Mineral Industrialization - Value chain development for critical minerals
3. Agriculture & Food Security - Regional food systems and agribusiness
4. Digital Economy - Infrastructure and services for digital transformation
...
```

### Energy Agent

```
You: What are the key challenges for regional power integration in West Africa?
Energy: West Africa faces several challenges for regional power integration:
1. Infrastructure gaps - Limited cross-border transmission capacity
2. Financing constraints - High upfront costs for energy projects
3. Regulatory harmonization - Different power sector frameworks across countries
4. Technical capacity - Need for skilled personnel and modern grid management
...
```

### Resource Mobilization Agent

```
You: How do you score projects for the Deal Room?
Resource Mobilization: Projects for the Deal Room are scored using AfCEN criteria:
1. Strategic Alignment (30%) - Fits with summit priorities
2. Readiness (25%) - Has feasibility studies and legal frameworks
3. Regional Impact (20%) - Benefits multiple member states
4. Financial Viability (15%) - Clear business case and revenue model
5. Innovation (10%) - Novel or transformative approach
...
```

## File Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── prompts.py                    # System prompts for all agents
│   │   ├── base_agent.py                 # Base agent class
│   │   ├── supervisor.py                 # Supervisor agent
│   │   ├── energy_agent.py               # Energy TWG agent
│   │   ├── agriculture_agent.py          # Agriculture TWG agent
│   │   ├── minerals_agent.py             # Minerals TWG agent
│   │   ├── digital_agent.py              # Digital Economy agent
│   │   ├── protocol_agent.py             # Protocol & Logistics agent
│   │   └── resource_mobilization_agent.py # Resource Mobilization agent
│   └── services/
│       └── llm_service.py                # Ollama LLM integration
└── scripts/
    └── chat_agent.py                     # CLI interface
```

## Programmatic Usage

### Using Individual Agents

```python
from app.agents.energy_agent import create_energy_agent

# Create an agent
agent = create_energy_agent(keep_history=True)

# Chat with the agent
response = agent.chat("What are the main renewable energy opportunities in West Africa?")
print(response)

# Get agent info
info = agent.get_agent_info()
print(info)

# Reset conversation history
agent.reset_history()
```

### Using the Supervisor Agent

```python
from app.agents.supervisor import create_supervisor

# Create supervisor with auto-registration of all TWG agents
supervisor = create_supervisor(keep_history=True, auto_register=True)

# Check supervisor status
status = supervisor.get_supervisor_status()
print(f"Registered agents: {status['registered_agents']}")
# Output: ['energy', 'agriculture', 'minerals', 'digital', 'protocol', 'resource_mobilization']

# Use smart_chat for automatic delegation
response = supervisor.smart_chat("How can solar energy support agriculture?")
print(response)
# The supervisor automatically identifies this involves both Energy and Agriculture TWGs,
# consults both, and synthesizes their responses

# Manual delegation to specific agent
energy_response = supervisor.delegate_to_agent("energy", "What is WAPP?")
print(energy_response)

# Consult multiple agents manually
query = "Investment opportunities in renewable energy"
responses = supervisor.consult_multiple_agents(query, ["energy", "resource_mobilization"])
for agent_id, response in responses.items():
    print(f"\n{agent_id.upper()}:\n{response}")

# Identify which agents are relevant for a query
relevant = supervisor.identify_relevant_agents("digital infrastructure for mining")
print(relevant)  # Output: ['digital', 'minerals']
```

### Advanced: Custom Supervisor Setup

```python
from app.agents.supervisor import SupervisorAgent
from app.agents.energy_agent import create_energy_agent
from app.agents.agriculture_agent import create_agriculture_agent

# Create supervisor without auto-registration
supervisor = SupervisorAgent(keep_history=True)

# Manually register specific agents only
supervisor.register_agent("energy", create_energy_agent())
supervisor.register_agent("agriculture", create_agriculture_agent())

# Now supervisor only has access to these two agents
print(supervisor.get_registered_agents())  # Output: ['energy', 'agriculture']
```

## System Prompts

All agent system prompts are defined in `app/agents/prompts.py`. Each prompt includes:

- **Role** - Agent's position and purpose
- **Expertise** - Domain knowledge areas
- **Responsibilities** - Key tasks
- **Context** - ECOWAS Summit 2026 background
- **Output Style** - How the agent should respond

You can view or modify prompts by editing this file.

## Troubleshooting

### "Cannot connect to Ollama"

**Solution:**
1. Make sure Ollama is running: `ollama serve`
2. Check if the model is pulled: `ollama list`
3. Pull the model if needed: `ollama pull qwen2.5:0.5b`

### "Unknown agent_id"

**Solution:**
Check the list of available agents:
```bash
python scripts/chat_agent.py --help
```

### Slow Responses

The `qwen2.5:0.5b` model is optimized for speed. If responses are still slow:
- Check your system resources
- Reduce the prompt length
- Use `--no-history` flag to disable conversation history

### Import Errors

**Solution:**
Make sure you're in the backend directory and virtual environment is activated:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

1. **Add Tools** - Integrate email, calendar, and document tools
2. **LangGraph Integration** - Build agent orchestration graph
3. **API Endpoints** - Expose agents via FastAPI
4. **Frontend Integration** - Connect to React chat interface

## Support

For issues or questions:
- Check the logs (enable with `--debug` flag)
- Review the system prompts in `app/agents/prompts.py`
- Ensure Ollama is running and accessible

---

**Status**: ✅ All 7 agents implemented and ready for testing
**Model**: qwen2.5:0.5b (local Ollama)
**Created**: December 2025
