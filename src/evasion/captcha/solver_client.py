"""
CAPTCHA Solver Client - Interfaz con servicios de resolución de CAPTCHAs.

Responsabilidades:
- Comunicar con servicios de resolución (2Captcha, Anti-Captcha, etc)
- Enviar desafíos (imágenes, tokens)
- Recibir y validar soluciones
- Manejo de errores y reintentos
- Tracking de costo y tasa de éxito
"""

import logging
import asyncio
import json
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


class CaptchaType(Enum):
    """Tipos de CAPTCHAs soportados."""
    IMAGE_CAPTCHA = "ImageCaptcha"
    RECAPTCHA_V2 = "NoCaptchaTaskProxyless"
    RECAPTCHA_V3 = "RecaptchaV3TaskProxyless"
    HCAPTCHA = "HCaptchaTaskProxyless"
    FUNCAPTCHA = "FunCaptchaTaskProxyless"
    GEETEST = "GeeTestTaskProxyless"
    TURNSTILE = "TurnstileTaskProxyless"
    TOKEN = "Token"


@dataclass
class CaptchaJob:
    """Representa un trabajo de resolución de CAPTCHA."""
    
    job_id: str
    captcha_type: CaptchaType
    status: str = "pending"  # pending, solving, solved, failed
    created_at: str = ""
    solved_at: Optional[str] = None
    solution: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    confidence_score: float = 0.0
    cost: float = 0.0


class SolverClient:
    """Cliente para servicios de resolución de CAPTCHAs."""
    
    # Servicios soportados
    ANTI_CAPTCHA_API = "https://api.anti-captcha.com/createTask"
    TWO_CAPTCHA_API = "http://2captcha.com/api/upload"
    DEATHBYCAPTCHA_API = "http://deathbycaptcha.com/api/captcha"
    
    def __init__(
        self, 
        provider: str = "anti-captcha",
        api_key: str = "demo_key",
        timeout: int = 300
    ) -> None:
        """Inicializa el cliente solver."""
        self.logger = logging.getLogger(__name__)
        self.provider = provider
        self.api_key = api_key
        self.timeout = timeout
        
        # Estado
        self.active_jobs: Dict[str, CaptchaJob] = {}
        self.completed_jobs: List[CaptchaJob] = []
        self.failed_attempts: int = 0
        self.successful_solves: int = 0
        self.total_cost: float = 0.0
        
        # Configuración de reintentos
        self.retry_delays = [5, 10, 20]  # segundos
        
        self.logger.info(f"✓ CAPTCHA Solver Client inicializado (Proveedor: {provider})")

    async def solve_recaptcha_v2(
        self, 
        sitekey: str, 
        page_url: str,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Resuelve reCAPTCHA v2."""
        self.logger.info(f"🔓 Resolviendo reCAPTCHA v2 para {page_url[:50]}...")
        
        job = CaptchaJob(
            job_id=self._generate_job_id(),
            captcha_type=CaptchaType.RECAPTCHA_V2,
            created_at=datetime.now().isoformat()
        )
        
        self.active_jobs[job.job_id] = job
        
        try:
            if self.provider == "anti-captcha":
                solution = await self._solve_anti_captcha_v2(sitekey, page_url, proxy)
            elif self.provider == "2captcha":
                solution = await self._solve_2captcha_v2(sitekey, page_url)
            else:
                solution = await self._solve_deathbycaptcha_v2(sitekey, page_url)
            
            if solution:
                job.status = "solved"
                job.solution = solution
                job.solved_at = datetime.now().isoformat()
                job.confidence_score = 0.95
                self.successful_solves += 1
                self.logger.info(f"✓ reCAPTCHA v2 resuelto (Job: {job.job_id})")
                return solution
            else:
                job.status = "failed"
                job.error = "No solution returned"
                self.failed_attempts += 1
                return None
                
        except Exception as e:
            self.logger.error(f"✗ Error resolviendo reCAPTCHA: {e}")
            job.status = "failed"
            job.error = str(e)
            self.failed_attempts += 1
            return None

    async def solve_recaptcha_v3(
        self, 
        sitekey: str, 
        page_url: str,
        action: str = "submit",
        min_score: float = 0.3,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Resuelve reCAPTCHA v3."""
        self.logger.info(f"🔓 Resolviendo reCAPTCHA v3 (action: {action}, min_score: {min_score})...")
        
        job = CaptchaJob(
            job_id=self._generate_job_id(),
            captcha_type=CaptchaType.RECAPTCHA_V3,
            created_at=datetime.now().isoformat()
        )
        
        self.active_jobs[job.job_id] = job
        
        try:
            if self.provider == "anti-captcha":
                solution = await self._solve_anti_captcha_v3(
                    sitekey, page_url, action, min_score, proxy
                )
            else:
                self.logger.warning("⚠️ Proveedor no soporta reCAPTCHA v3")
                solution = None
            
            if solution:
                job.status = "solved"
                job.solution = solution
                job.solved_at = datetime.now().isoformat()
                job.confidence_score = 0.90
                self.successful_solves += 1
                self.logger.info(f"✓ reCAPTCHA v3 resuelto")
                return solution
            else:
                job.status = "failed"
                self.failed_attempts += 1
                return None
                
        except Exception as e:
            self.logger.error(f"✗ Error: {e}")
            job.status = "failed"
            job.error = str(e)
            self.failed_attempts += 1
            return None

    async def solve_hcaptcha(
        self, 
        sitekey: str, 
        page_url: str,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Resuelve hCaptcha."""
        self.logger.info(f"🔓 Resolviendo hCaptcha para {page_url[:50]}...")
        
        job = CaptchaJob(
            job_id=self._generate_job_id(),
            captcha_type=CaptchaType.HCAPTCHA,
            created_at=datetime.now().isoformat()
        )
        
        self.active_jobs[job.job_id] = job
        
        try:
            if self.provider == "anti-captcha":
                solution = await self._solve_anti_captcha_hcaptcha(sitekey, page_url, proxy)
            else:
                solution = None
            
            if solution:
                job.status = "solved"
                job.solution = solution
                job.solved_at = datetime.now().isoformat()
                self.successful_solves += 1
                self.logger.info(f"✓ hCaptcha resuelto")
                return solution
            else:
                job.status = "failed"
                self.failed_attempts += 1
                return None
                
        except Exception as e:
            self.logger.error(f"✗ Error: {e}")
            job.status = "failed"
            job.error = str(e)
            self.failed_attempts += 1
            return None

    async def solve_turnstile(
        self, 
        sitekey: str, 
        page_url: str,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Resuelve Cloudflare Turnstile."""
        self.logger.info(f"🔓 Resolviendo Cloudflare Turnstile...")
        
        job = CaptchaJob(
            job_id=self._generate_job_id(),
            captcha_type=CaptchaType.TURNSTILE,
            created_at=datetime.now().isoformat()
        )
        
        self.active_jobs[job.job_id] = job
        
        try:
            if self.provider == "anti-captcha":
                solution = await self._solve_anti_captcha_turnstile(sitekey, page_url, proxy)
            else:
                solution = None
            
            if solution:
                job.status = "solved"
                job.solution = solution
                job.solved_at = datetime.now().isoformat()
                self.successful_solves += 1
                self.logger.info(f"✓ Turnstile resuelto")
                return solution
            else:
                job.status = "failed"
                self.failed_attempts += 1
                return None
                
        except Exception as e:
            self.logger.error(f"✗ Error: {e}")
            job.status = "failed"
            job.error = str(e)
            self.failed_attempts += 1
            return None

    async def check_job_status(self, job_id: str) -> Optional[CaptchaJob]:
        """Revisa el estado de un trabajo en proceso."""
        self.logger.info(f"📊 Revisando estado del job {job_id}...")
        
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        
        try:
            if self.provider == "anti-captcha":
                status = await self._check_anti_captcha_status(job_id)
            else:
                status = None
            
            if status:
                return job
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"✗ Error verificando status: {e}")
            return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancela un trabajo en proceso."""
        self.logger.info(f"🛑 Cancelando job {job_id}...")
        
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        job.status = "cancelled"
        
        # En producción: enviar cancelación al proveedor
        return True

    def get_job_history(self, limit: int = 10) -> List[CaptchaJob]:
        """Retorna historial de trabajos."""
        return self.completed_jobs[-limit:]

    def get_solver_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del solver."""
        total_attempts = self.successful_solves + self.failed_attempts
        success_rate = (self.successful_solves / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "provider": self.provider,
            "total_attempts": total_attempts,
            "successful_solves": self.successful_solves,
            "failed_attempts": self.failed_attempts,
            "success_rate_percent": success_rate,
            "total_cost": self.total_cost,
            "active_jobs": len(self.active_jobs),
            "avg_cost_per_solve": self.total_cost / self.successful_solves if self.successful_solves > 0 else 0.0
        }

    # Private methods - Anti-Captcha integration
    
    async def _solve_anti_captcha_v2(
        self, 
        sitekey: str, 
        page_url: str,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Integración Anti-Captcha para reCAPTCHA v2."""
        self.logger.info("  → Anti-Captcha API v2")
        
        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": CaptchaType.RECAPTCHA_V2.value,
                "websiteURL": page_url,
                "websiteKey": sitekey
            }
        }
        
        if proxy:
            payload["task"]["proxyType"] = proxy.get("type", "http")
            payload["task"]["proxyAddress"] = proxy.get("address")
            payload["task"]["proxyPort"] = proxy.get("port")
        
        # En producción: httpx call
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(self.ANTI_CAPTCHA_API, json=payload, timeout=self.timeout)
        
        # Simulación
        await asyncio.sleep(0.1)
        token = f"03AGdBq27{'x' * 100}"  # Simulation
        return token

    async def _solve_anti_captcha_v3(
        self, 
        sitekey: str, 
        page_url: str,
        action: str,
        min_score: float,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Integración Anti-Captcha para reCAPTCHA v3."""
        self.logger.info(f"  → Anti-Captcha API v3 (action: {action})")
        
        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": CaptchaType.RECAPTCHA_V3.value,
                "websiteURL": page_url,
                "websiteKey": sitekey,
                "pageAction": action,
                "minScore": min_score
            }
        }
        
        # En producción: httpx call
        await asyncio.sleep(0.1)
        token = f"03AGdBq27{'x' * 100}"
        return token

    async def _solve_anti_captcha_hcaptcha(
        self, 
        sitekey: str, 
        page_url: str,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Integración Anti-Captcha para hCaptcha."""
        self.logger.info("  → Anti-Captcha API hCaptcha")
        
        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": CaptchaType.HCAPTCHA.value,
                "websiteURL": page_url,
                "websiteKey": sitekey
            }
        }
        
        await asyncio.sleep(0.1)
        token = f"P0_eyJ{'x' * 100}"
        return token

    async def _solve_anti_captcha_turnstile(
        self, 
        sitekey: str, 
        page_url: str,
        proxy: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Integración Anti-Captcha para Turnstile."""
        self.logger.info("  → Anti-Captcha API Turnstile")
        
        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": CaptchaType.TURNSTILE.value,
                "websiteURL": page_url,
                "websiteKey": sitekey
            }
        }
        
        await asyncio.sleep(0.1)
        token = f"0x4AAAAA{'x' * 100}"
        return token

    async def _check_anti_captcha_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Revisa estado en Anti-Captcha."""
        await asyncio.sleep(0.1)
        return {"status": "ready", "solution": "token_value"}

    async def _solve_2captcha_v2(self, sitekey: str, page_url: str) -> Optional[str]:
        """Integración 2Captcha para reCAPTCHA v2."""
        self.logger.info("  → 2Captcha API v2")
        await asyncio.sleep(0.1)
        return f"03AGdBq27{'x' * 100}"

    async def _solve_deathbycaptcha_v2(self, sitekey: str, page_url: str) -> Optional[str]:
        """Integración Death By Captcha para reCAPTCHA v2."""
        self.logger.info("  → Death By Captcha API v2")
        await asyncio.sleep(0.1)
        return f"03AGdBq27{'x' * 100}"

    def _generate_job_id(self) -> str:
        """Genera ID único para job."""
        import uuid
        return str(uuid.uuid4())[:12]
