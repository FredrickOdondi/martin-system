"""
LLM Service for AI Agent Integration

This service provides an interface to connect to either a local Ollama instance
or OpenAI API based on configuration.
"""

import requests
import json
from typing import List, Dict, Optional, Any
from loguru import logger
from app.core.config import settings

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMService:
    """Base interface for LLM services"""
    def chat(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        raise NotImplementedError

    def chat_with_history(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs) -> str:
        raise NotImplementedError

    def transcribe_audio(self, file_path: str, **kwargs) -> str:
        raise NotImplementedError


class OllamaLLMService(LLMService):
    """Service for interacting with local Ollama LLM"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:0.5b",
        temperature: float = 0.7,
        timeout: int = 120
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.api_endpoint = f"{self.base_url}/api/generate"

        logger.info(f"Initialized Ollama LLM Service: {self.model} @ {self.base_url}")

    def chat(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None, max_tokens: int = 1000) -> str:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": max_tokens
            }
        }

        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Ollama Error: {str(e)}")

    def chat_with_history(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, temperature: Optional[float] = None) -> str:
        conversation = ""
        if system_prompt:
            conversation = f"{system_prompt}\n\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation += f"{role.capitalize()}: {content}\n"

        conversation += "Assistant:"

        payload = {
            "model": self.model,
            "prompt": conversation,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature
            }
        }

        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama History error: {e}")
            raise Exception(f"Ollama Error: {str(e)}")


class OpenAILLMService(LLMService):
    """Service for interacting with OpenAI API"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", temperature: float = 0.7):
        if not OpenAI:
            raise ImportError("openai package not installed. Run 'pip install openai'")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        logger.info(f"Initialized OpenAI LLM Service: {self.model}")

    def chat(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None, max_tokens: int = 2000) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI Error: {str(e)}")

    def chat_with_history(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, temperature: Optional[float] = None) -> str:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        # Ensure correct role names for OpenAI
        for m in messages:
            role = m.get("role", "user")
            if role not in ["system", "user", "assistant"]:
                role = "user"
            full_messages.append({"role": role, "content": m.get("content", "")})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature if temperature is not None else self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI History error: {e}")
            raise Exception(f"OpenAI Error: {str(e)}")

    def transcribe_audio(self, file_path: str, model: str = "whisper-1", **kwargs) -> str:
        """
        Transcribe audio file.
        Strategy: checks if Groq API key is set for faster/cheaper transcription.
        Fallback: OpenAI Whisper.
        """
        # Hybrid Approach: Try Groq first for transcription (faster/cheaper)
        if getattr(settings, "GROQ_API_KEY", None):
            try:
                # Lazy initialization to avoid circular dependency or complex init logic
                from groq import Groq
                groq_client = Groq(api_key=settings.GROQ_API_KEY)
                
                with open(file_path, "rb") as file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=(file_path, file.read()),
                        model="whisper-large-v3",
                        response_format="text",
                        temperature=0.0
                    )
                logger.info("Transcribed audio using Groq (Hybrid Provider)")
                return transcription
            except Exception as e:
                logger.warning(f"Groq transcription failed, falling back to OpenAI: {e}")
        
        # Fallback to OpenAI
        try:
            with open(file_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=file,
                    model=model,
                    response_format="text",
                    temperature=0.0
                )
            logger.info("Transcribed audio using OPENAI Whisper")
            return transcription
        except Exception as e:
            logger.error(f"OpenAI Transcription error: {e}")
            raise Exception(f"OpenAI Transcription Error: {str(e)}")


class GroqLLMService(LLMService):
    """Service for interacting with Groq API"""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", temperature: float = 0.7):
        # Use OpenAI compatibility client for Groq if available, or direct requests
        try:
            from groq import Groq
            self.client = Groq(api_key=api_key, timeout=300.0)
            self.client_type = "groq"
        except ImportError:
            # Fallback to OpenAI compatible client if groq package missing but OpenAI exists
            if OpenAI:
                self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
                self.client_type = "openai_compat"
            else:
                raise ImportError("groq package not installed. Run 'pip install groq' or 'pip install openai'")
        
        self.model = model
        self.temperature = temperature
        logger.info(f"Initialized Groq LLM Service: {self.model}")

    def chat(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None, max_tokens: int = 2000) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Groq Error: {str(e)}")

    def chat_with_history(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, temperature: Optional[float] = None) -> str:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        for m in messages:
            role = m.get("role", "user")
            # Groq supports system, user, assistant
            if role not in ["system", "user", "assistant"]:
                role = "user"
            full_messages.append({"role": role, "content": m.get("content", "")})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature if temperature is not None else self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq History error: {e}")
            raise Exception(f"Groq Error: {str(e)}")

    def transcribe_audio(self, file_path: str, model: str = "whisper-large-v3", **kwargs) -> str:
        """
        Transcribe audio file using Groq's Whisper API.
        """
        try:
            with open(file_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(file_path, file.read()),
                    model=model,
                    response_format="text",
                    temperature=0.0
                )
            return transcription
        except Exception as e:
            logger.error(f"Groq Transcription error: {e}")
            raise Exception(f"Groq Transcription Error: {str(e)}")


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """
    Get or create the LLM service singleton based on configuration.
    """
    global _llm_service
    if _llm_service is None:
        provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()
        
        if provider == "openai" and getattr(settings, "OPENAI_API_KEY", None):
            _llm_service = OpenAILLMService(
                api_key=settings.OPENAI_API_KEY,
                model=getattr(settings, "OPENAI_MODEL", "gpt-4-turbo-preview"),
                temperature=settings.LLM_TEMPERATURE
            )
        elif provider == "groq" and getattr(settings, "GROQ_API_KEY", None):
            _llm_service = GroqLLMService(
                api_key=settings.GROQ_API_KEY,
                model=getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                temperature=settings.LLM_TEMPERATURE
            )
        else:
            if provider == "openai":
                logger.warning("OpenAI provider selected but no API key found. Falling back to Ollama.")
            if provider == "groq":
                logger.warning("Groq provider selected but no API key found. Falling back to Ollama.")
            
            _llm_service = OllamaLLMService(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                timeout=settings.LLM_TIMEOUT
            )
    return _llm_service


# Create singleton instance for import
llm_service = get_llm_service()
