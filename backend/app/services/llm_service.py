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



class SimpleFunction:
    """Mimics OpenAI Function object."""
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments

class SimpleToolCall:
    """Mimics OpenAI ToolCall object."""
    def __init__(self, id: str, type: str, function: SimpleFunction):
        self.id = id
        self.type = type
        self.function = function

class SimpleMessage:
    """Simple wrapper to mimic OpenAI Message object for compatibility."""
    def __init__(self, content: str = None, tool_calls: List[SimpleToolCall] = None):
        self.content = content
        self.tool_calls = tool_calls or []

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

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", temperature: float = 0.7, base_url: Optional[str] = None):
        if not OpenAI:
            raise ImportError("openai package not installed. Run 'pip install openai'")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        logger.info(f"Initialized OpenAI LLM Service: {self.model} (Base URL: {base_url or 'Default'})")

    def chat(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None, max_tokens: int = 2000, tools: Optional[List[Dict]] = None) -> Any:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Filter out invalid or unsupported arguments if needed, but OpenAI client generally handles valid kwargs
        # We need to pass tools if present
        
        create_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            # Convert tools to standard OpenAI format if they aren't already
            # Assuming incoming tools are already in OpenAI JSON schema format as per LangGraph
            create_kwargs["tools"] = tools

        try:
            response = self.client.chat.completions.create(**create_kwargs)
            
            message = response.choices[0].message
            # If tool calls are present, we should probably return the message object or a custom wrapper
            # For backward compatibility with string return type expectations in basic chat, we handle carefully
            if message.tool_calls:
                 # We return a SimpleMessage-like structure or the raw message if feasible
                 # NOTE: LangGraph expectation is likely an object with .content and .tool_calls
                 # SimpleMessage is defined in llm_service.py for Gemini, we can reuse or just return the OpenAI message object if it has compatible attributes
                 return message
            
            return message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI Error: {str(e)}")

    def chat_with_history(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, temperature: Optional[float] = None, tools: Optional[List[Dict]] = None) -> Any:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        
        # Ensure correct role names for OpenAI
        for m in messages:
            role = m.get("role", "user")
            if role not in ["system", "user", "assistant", "tool", "function"]:
                 # Map non-standard roles if necessary, or default to user
                 if role == "model": role = "assistant"
                 else: role = "user"
            
            # OpenAI message structure
            msg_obj = {"role": role, "content": m.get("content", "")}
            
            if "tool_calls" in m and m["tool_calls"]:
                msg_obj["tool_calls"] = m["tool_calls"]
            if "tool_call_id" in m:
                msg_obj["tool_call_id"] = m["tool_call_id"]
            if "name" in m:
                 msg_obj["name"] = m["name"]
                 
            full_messages.append(msg_obj)

        create_kwargs = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature if temperature is not None else self.temperature
        }
        
        if tools:
            create_kwargs["tools"] = tools

        try:
            response = self.client.chat.completions.create(**create_kwargs)
            message = response.choices[0].message
            
            if message.tool_calls:
                 return message
                 
            return message.content.strip()
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


class GeminiLLMService(LLMService):
    """Service for interacting with Google Gemini API via REST"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", temperature: float = 0.7):
        self.api_key = api_key
        # Ensure model has 'models/' prefix only if missing
        self.model = model if model.startswith("models/") else f"models/{model}"
        self.temperature = temperature
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        logger.info(f"Initialized Gemini LLM Service: {self.model}")

    def _convert_tools_to_gemini(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool definitions to Gemini FunctionDeclarations."""
        if not tools:
            return None
            
        gemini_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                gemini_tool = {
                    "name": func.get("name"),
                    "description": func.get("description"),
                    "parameters": func.get("parameters")
                }
                gemini_tools.append(gemini_tool)
        
        return [{"function_declarations": gemini_tools}]

    def _parse_gemini_response(self, data: Dict) -> Any:
        """Parse Gemini response into SimpleMessage or string."""
        if not data.get("candidates"):
            return ""
            
        candidate = data["candidates"][0]
        if candidate.get("finishReason") == "SAFETY":
            return "[Response Blocked due to Safety Settings]"
            
        content_parts = candidate.get("content", {}).get("parts", [])
        if not content_parts:
             return ""
             
        # Check for function calls
        tool_calls = []
        text_content = ""
        
        for part in content_parts:
            if "text" in part:
                text_content += part["text"]
            
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(SimpleToolCall(
                    id=f"call_{fc['name']}",
                    type="function",
                    function=SimpleFunction(
                        name=fc["name"],
                        arguments=json.dumps(fc.get("args", {}))
                    )
                ))
        
        if tool_calls:
            # Return object with tool_calls attribute
            return SimpleMessage(content=text_content, tool_calls=tool_calls)
            
        return text_content.strip()

    def chat(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None, max_tokens: int = 2000, tools: Optional[List[Dict]] = None) -> Any:
        messages = []
        if system_prompt:
            messages.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}"}]})
            messages.append({"role": "model", "parts": [{"text": "Understood."}]})
        
        messages.append({"role": "user", "parts": [{"text": prompt}]})

        return self._generate(messages, temperature, max_tokens, tools)

    def chat_with_history(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, temperature: Optional[float] = None, tools: Optional[List[Dict]] = None) -> Any:
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}"}]})
            formatted_messages.append({"role": "model", "parts": [{"text": "Understood."}]})

        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            
            parts = []
            if content:
                parts.append({"text": content})
                
            # Handle tool calls in history (if any)
            if "tool_calls" in m and m["tool_calls"]:
                # Gemini expects functionCall in model parts
                # We simply approximate by adding text description since we can't easily reconstruct the exact functionCall object structure accepted by API for history mostly
                # OR we try to skip precise reconstruction if it's too complex. 
                # For now, let's append tool calls as text to context to avoid schema validation errors in history
                 parts.append({"text": f"[System: Previous Tool Call: {json.dumps(m['tool_calls'])}]"})

            if role == "assistant":
                gemini_role = "model"
            elif role == "tool":
                # Gemini expects 'functionResponse' role but it's tricky via REST without proper context.
                # Treat tool outputs as user messages for simplicity
                gemini_role = "user" 
                parts = [{"text": f"Tool Output: {content}"}]
            elif role == "system":
                gemini_role = "user" 
                parts = [{"text": f"System Update: {content}"}]
            else:
                gemini_role = "user"
                
            formatted_messages.append({"role": gemini_role, "parts": parts})

        return self._generate(formatted_messages, temperature, max_tokens=2000, tools=tools)

    def _generate(self, contents: List[Dict], temperature: float, max_tokens: int, tools: Optional[List[Dict]] = None) -> Any:
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        generation_config = {
            "temperature": temperature if temperature is not None else self.temperature,
            "maxOutputTokens": max_tokens
        }
        
        gemini_tools = self._convert_tools_to_gemini(tools)
        
        payload = {
            "contents": contents,
            "generationConfig": generation_config
        }
        
        if gemini_tools:
            payload["tools"] = gemini_tools
        
        # Retry parameters
        max_retries = 3
        base_delay = 5  # Start with 5 seconds as Gemini 429 usually asks for ~5s wait
        
        import time
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
                
                if response.status_code == 429:
                    logger.warning(f"Gemini Rate Limit hit (429). Attempt {attempt+1}/{max_retries}. Retrying in {base_delay}s...")
                    time.sleep(base_delay)
                    base_delay *= 2  # Exponential backoff
                    continue
                    
                if response.status_code != 200:
                    logger.error(f"Gemini API Error {response.status_code}: {response.text}")
                    raise Exception(f"Gemini API Error: {response.text}")
                    
                data = response.json()
                return self._parse_gemini_response(data)
                
            except Exception as e:
                # If it's a connection error, maybe retry? For now, re-raise only on final attempt or non-retriable 
                if attempt == max_retries - 1:
                    logger.error(f"Gemini Request failed after {max_retries} attempts: {e}")
                    raise Exception(f"Gemini Error after retries: {str(e)}")
                
                logger.warning(f"Gemini request failed: {e}. Retrying...")
                time.sleep(base_delay)
                base_delay *= 2
                
        raise Exception("Gemini API Request failed after max retries")

    def transcribe_audio(self, file_path: str, **kwargs) -> str:
        raise NotImplementedError("Audio transcription not implemented for Gemini REST yet")
# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """
    Get or create the LLM service singleton based on configuration.
    """
    global _llm_service
    if _llm_service is None:
        provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()
        logger.info(f"Selecting LLM Provider: {provider}")
        
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
        elif provider == "gemini" and getattr(settings, "GEMINI_API_KEY", None):
             _llm_service = GeminiLLMService(
                api_key=settings.GEMINI_API_KEY,
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"),
                temperature=settings.LLM_TEMPERATURE
            )
        elif provider == "custom" and getattr(settings, "CUSTOM_LLM_BASE_URL", None):
             _llm_service = OpenAILLMService(
                api_key=settings.CUSTOM_LLM_API_KEY,
                model=settings.CUSTOM_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                base_url=settings.CUSTOM_LLM_BASE_URL
            )
        elif provider == "github" and getattr(settings, "GITHUB_TOKEN", None):
             _llm_service = OpenAILLMService(
                api_key=settings.GITHUB_TOKEN,
                model=getattr(settings, "GITHUB_MODEL", "gpt-4o-mini").replace("openai/", ""),
                temperature=settings.LLM_TEMPERATURE,
                base_url=settings.GITHUB_BASE_URL
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
