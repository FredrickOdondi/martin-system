# AI Agents - Setup and Usage Guide

## Overview

This system includes 7 AI agents for the ECOWAS Summit 2026 TWG Support System:

1. **Supervisor Agent** - Central coordinator
2. **Energy Agent** - Energy & Infrastructure TWG
3. **Agriculture Agent** - Agriculture & Food Systems TWG
4. **Minerals Agent** - Critical Minerals & Industrialization TWG
5. **Digital Agent** - Digital Economy & Transformation TWG
6. **Protocol Agent** - Protocol & Logistics TWG
7. **Resource Mobilization Agent** - Investment pipeline TWG

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

### Supervisor Agent

```
You: What are the main priorities for the ECOWAS Summit 2026?
Supervisor: The ECOWAS Summit 2026 focuses on four integrated pillars:
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

You can also use the agents in your own Python code:

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
