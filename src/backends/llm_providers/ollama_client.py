"""
Ollama Client - Wrapper para Ollama (Local LLM)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client para Ollama (modelos locales sin censura)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.endpoint = config.get("api_endpoint", "http://localhost:11434")
        self.model = config.get("model", "mistral")  # Default: Mistral
        self.timeout = config.get("timeout_seconds", 120)
    
    async def health_check(self) -> bool:
        """Verificar que Ollama está running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.endpoint}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def generate(self, prompt: str, temperature: float = 0.7,
                      max_tokens: int = 2000) -> str:
        """
        Generate response using Ollama.
        
        Ollama es local, no tiene censura de contenido.
        Usado como último fallback.
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                }
                
                async with session.post(
                    f"{self.endpoint}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Ollama error: HTTP {resp.status}")
                    
                    data = await resp.json()
                    response: str = data.get("response", "")
                    return response
        
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
