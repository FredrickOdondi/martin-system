"""
GitHub Models LLM Service

This service provides an interface to GitHub Models API using OpenAI-compatible client.
Supports models like GPT-4o, GPT-4o-mini, and other Azure OpenAI models.
"""

import os
from typing import List, Dict, Optional, Any
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GitHubModelsLLMService:
    """Service for interacting with GitHub Models API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = 600
    ):
        """
        Initialize the GitHub Models LLM service.

        Args:
            api_key: GitHub token (falls back to GITHUB_TOKEN env var)
            model: Model name to use (e.g., gpt-4o-mini, gpt-4o)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("GITHUB_TOKEN")
        if not self.api_key:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Initialize OpenAI client pointing to GitHub Models endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://models.inference.ai.azure.com",
            timeout=timeout
        )

        logger.info(f"Initialized GitHub Models LLM Service: {self.model} (timeout: {timeout}s)")

    def check_connection(self) -> bool:
        """
        Check if GitHub Models API is accessible.

        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            # Try a simple API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"GitHub Models connection check failed: {e}")
            return False

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None
    ) -> Any:
        """
        Send a chat message to Groq and get a response.

        Args:
            prompt: User message/prompt
            system_prompt: Optional system prompt to set context
            temperature: Override default temperature
            max_tokens: Override default max tokens
            tools: Optional list of tool definitions

        Returns:
            str or object: LLM response text or full message object if tools used
        """
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add user message
        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            logger.debug(f"Sending request to GitHub Models: {prompt[:100]}...")
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)

            # If tools were passed, return the full message object to handle tool_calls
            if tools:
                return response.choices[0].message
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"GitHub Models API error: {e}")
            raise Exception(f"LLM API error: {str(e)}")

    def chat_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict]] = None
    ) -> Any:
        """
        Chat with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Override default temperature
            tools: Optional list of tool definitions

        Returns:
            str or object: LLM response or message object
        """
        groq_messages = []

        # Add system prompt if provided
        if system_prompt:
            groq_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add conversation history
        for msg in messages:
            # Safe copy of message to avoid mutating original
            msg_dict = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            # Include tool_calls if present in history
            if "tool_calls" in msg:
                msg_dict["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                msg_dict["tool_call_id"] = msg["tool_call_id"]
                
            groq_messages.append(msg_dict)

        try:
            kwargs = {
                "model": self.model,
                "messages": groq_messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": self.max_tokens
            }

            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)

            if tools:
                return response.choices[0].message

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Chat with history failed: {e}")
            raise Exception(f"LLM API error: {str(e)}")


# Singleton instance
_llm_service = None


def get_llm_service() -> GitHubModelsLLMService:
    """
    Get or create the GitHub Models LLM service singleton.

    Returns:
        GitHubModelsLLMService: The LLM service instance
    """
    global _llm_service
    if _llm_service is None:
        api_key = os.getenv("GITHUB_TOKEN")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4000"))
        timeout = int(os.getenv("LLM_TIMEOUT", "600"))

        _llm_service = GitHubModelsLLMService(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
    return _llm_service
