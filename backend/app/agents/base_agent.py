"""
Base Agent Class

Provides common functionality for all TWG agents including:
- LLM initialization
- System prompt loading
- Chat interface
- Conversation history management
- Logging
"""

from typing import List, Dict, Optional
from loguru import logger

from app.services.llm_service import get_llm_service
from app.agents.prompts import get_prompt


class BaseAgent:
    """Base class for all TWG agents"""

    def __init__(
        self,
        agent_id: str,
        keep_history: bool = False,
        max_history: int = 10
    ):
        """
        Initialize a base agent.

        Args:
            agent_id: Unique identifier for the agent (e.g., 'supervisor', 'energy')
            keep_history: Whether to maintain conversation history
            max_history: Maximum number of messages to keep in history
        """
        self.agent_id = agent_id
        self.keep_history = keep_history
        self.max_history = max_history

        # Load system prompt for this agent
        try:
            self.system_prompt = get_prompt(agent_id)
            logger.info(f"Initialized {agent_id} agent with system prompt")
        except ValueError as e:
            logger.error(f"Failed to load prompt for {agent_id}: {e}")
            raise

        # Get LLM service
        self.llm = get_llm_service()

        # Conversation history
        self.history: List[Dict[str, str]] = []

        logger.info(f"Agent '{agent_id}' initialized successfully")

    def chat(self, message: str, temperature: Optional[float] = None) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User message/question
            temperature: Optional temperature override (0-1)

        Returns:
            str: Agent response
        """
        try:
            logger.info(f"[{self.agent_id}] Received message: {message[:100]}...")

            if self.keep_history and self.history:
                # Use conversation history
                self.history.append({"role": "user", "content": message})

                # Trim history if too long
                if len(self.history) > self.max_history * 2:  # *2 for user+assistant pairs
                    self.history = self.history[-(self.max_history * 2):]

                response = self.llm.chat_with_history(
                    messages=self.history,
                    system_prompt=self.system_prompt,
                    temperature=temperature
                )

                # Add response to history
                self.history.append({"role": "assistant", "content": response})

            else:
                # No history - simple chat
                response = self.llm.chat(
                    prompt=message,
                    system_prompt=self.system_prompt,
                    temperature=temperature
                )

            logger.info(f"[{self.agent_id}] Generated response: {response[:100]}...")
            return response

        except Exception as e:
            error_msg = f"Error in {self.agent_id} agent: {str(e)}"
            logger.error(error_msg)
            return f"I apologize, but I encountered an error: {str(e)}"

    def reset_history(self):
        """Clear the conversation history"""
        self.history = []
        logger.info(f"[{self.agent_id}] Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.

        Returns:
            List of message dictionaries
        """
        return self.history.copy()

    def get_agent_info(self) -> Dict[str, any]:
        """
        Get information about this agent.

        Returns:
            Dictionary with agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "system_prompt": self.system_prompt[:200] + "...",  # Truncated
            "keep_history": self.keep_history,
            "max_history": self.max_history,
            "history_length": len(self.history)
        }

    def __repr__(self) -> str:
        return f"<Agent: {self.agent_id}>"
