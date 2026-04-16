"""
OpenAI Client - Wrapper para GPT-4 / GPT-3.5
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client para OpenAI API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.model = "gpt-4"  # Default
        self.timeout = config.get("timeout_seconds", 60)
        self.base_url = "https://api.openai.com/v1"
    
    async def health_check(self) -> bool:
        """Verificar que API es accesible"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
    
    async def generate(self, prompt: str, temperature: float = 0.7,
                      max_tokens: int = 2000) -> str:
        """
        Generate response using GPT-4.
        """
        
        if not self.api_key:
            raise ValueError("API key not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    data = await resp.json()
                    
                    if resp.status != 200:
                        error = data.get("error", {})
                        raise Exception(f"OpenAI API error: {error.get('message', 'Unknown')}")
                    
                    return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
