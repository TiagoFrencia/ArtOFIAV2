"""
Anthropic Client - Wrapper para Claude
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class AnthropicClient:
    """Client para Anthropic API (Claude)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.model = "claude-3-sonnet-20240229"  # Default
        self.timeout = config.get("timeout_seconds", 60)
        self.base_url = "https://api.anthropic.com/v1"
    
    async def health_check(self) -> bool:
        """Verificar que API es accesible"""
        try:
            # Intentar un request vacío para validar key
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                }
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status in [200, 404]  # 404 es OK, significa API respondió
        except Exception as e:
            logger.error(f"Anthropic health check failed: {e}")
            return False
    
    async def generate(self, prompt: str, temperature: float = 0.7,
                      max_tokens: int = 2000) -> str:
        """
        Generate response using Claude.
        """
        
        if not self.api_key:
            raise ValueError("API key not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                
                payload = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                }
                
                async with session.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    data = await resp.json()
                    
                    if resp.status != 200:
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        raise Exception(f"Anthropic API error: {error_msg}")
                    
                    return data["content"][0]["text"]
        
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise
