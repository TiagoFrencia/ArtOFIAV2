"""
Proxy Rotator - Gestión de rotación de proxies residenciales y móviles.

Responsabilidades:
- Mantener pool de proxies
- Rotación dinámica de IPs
- Coincidir geolocalización
- Distribuir tráfico para evadir rate limiting
- Monitoreo de salud de proxies
"""

import logging
import random
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum


class ProxyType(Enum):
    """Tipos de proxies."""
    RESIDENTIAL = "residential"
    MOBILE = "mobile"
    DATACENTER = "datacenter"
    ISP = "isp"


class ProxyProvider(Enum):
    """Proveedores de proxies."""
    BRIGHT_DATA = "bright_data"
    SMARTPROXY = "smartproxy"
    OXYLABS = "oxylabs"
    LUMINATI = "luminati"
    RESIDENTIAL_PROXY = "residential_proxy"


@dataclass
class ProxyConfig:
    """Configuración de proxy."""
    
    id: str
    address: str
    port: int
    type: ProxyType
    provider: ProxyProvider
    username: Optional[str] = None
    password: Optional[str] = None
    geolocation: Optional[str] = None  # "US", "DE", "JP", etc
    bandwidth_limit_gb: float = 100.0
    rotation_interval: int = 60  # segundos
    is_active: bool = True
    failure_count: int = 0
    last_used: Optional[str] = None
    created_at: str = ""


@dataclass
class ProxyStats:
    """Estadísticas de uso de proxy."""
    
    proxy_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    data_transferred_mb: float = 0.0
    avg_response_time_ms: float = 0.0
    consecutive_failures: int = 0
    last_status_check: str = ""
    health_score: float = 1.0  # 0.0-1.0


class ProxyRotator:
    """Gestor de rotación de proxies."""
    
    def __init__(self) -> None:
        """Inicializa el rotador de proxies."""
        self.logger = logging.getLogger(__name__)
        
        # Pool de proxies
        self.proxy_pool: Dict[str, ProxyConfig] = {}
        self.proxy_stats: Dict[str, ProxyStats] = {}
        
        # Configuración de rotación
        self.rotation_index = 0
        self.geolocation_targets: Dict[str, List[str]] = {}
        
        # Historial
        self.rotation_history: List[Dict[str, Any]] = []
        
        # Proxies activos/inactivos
        self.active_proxies: List[str] = []
        
        self.logger.info("✓ Proxy Rotator inicializado")

    def add_proxy(self, config: ProxyConfig) -> bool:
        """Agrega proxy al pool."""
        self.logger.info(f"➕ Agregando proxy: {config.address}:{config.port}")
        
        config.created_at = datetime.now().isoformat()
        self.proxy_pool[config.id] = config
        
        # Inicializar estadísticas
        self.proxy_stats[config.id] = ProxyStats(proxy_id=config.id)
        
        if config.is_active:
            self.active_proxies.append(config.id)
        
        # Registrar por geolocalización
        if config.geolocation:
            if config.geolocation not in self.geolocation_targets:
                self.geolocation_targets[config.geolocation] = []
            self.geolocation_targets[config.geolocation].append(config.id)
        
        self.logger.info(f"  ✓ Proxy {config.id} agregado ({len(self.active_proxies)} activos)")
        return True

    def add_proxy_batch(self, configs: List[ProxyConfig]) -> int:
        """Agrega múltiples proxies."""
        self.logger.info(f"📦 Agregando lote de {len(configs)} proxies...")
        
        added = 0
        for config in configs:
            if self.add_proxy(config):
                added += 1
        
        self.logger.info(f"  ✓ {added} proxies agregados")
        return added

    async def get_next_proxy(
        self, 
        geolocation: Optional[str] = None,
        avoid_recent: bool = True
    ) -> Optional[ProxyConfig]:
        """Obtiene siguiente proxy para usar (rotación round-robin)."""
        
        if not self.active_proxies:
            self.logger.warning("⚠️ No hay proxies activos disponibles")
            return None
        
        # Filtrar por geolocalización si se especifica
        available = self.active_proxies
        if geolocation and geolocation in self.geolocation_targets:
            available = [
                p for p in self.geolocation_targets[geolocation]
                if self.proxy_pool[p].is_active
            ]
        
        if not available:
            self.logger.warning(f"⚠️ No hay proxies disponibles en {geolocation}")
            available = self.active_proxies
        
        # Round-robin
        self.rotation_index = (self.rotation_index + 1) % len(available)
        proxy_id = available[self.rotation_index]
        proxy = self.proxy_pool[proxy_id]
        
        # Registrar uso
        proxy.last_used = datetime.now().isoformat()
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "proxy_id": proxy_id,
            "address": proxy.address,
            "geolocation": proxy.geolocation,
            "type": proxy.type.value
        }
        self.rotation_history.append(history_entry)
        
        self.logger.info(f"🔄 Proxy seleccionado: {proxy.address}:{proxy.port} "
                        f"({proxy.geolocation or 'global'})")
        
        return proxy

    async def get_proxy_for_geolocation(self, country_code: str) -> Optional[ProxyConfig]:
        """Obtiene proxy específico para país/región."""
        self.logger.info(f"🌍 Buscando proxy para {country_code}...")
        
        if country_code not in self.geolocation_targets:
            self.logger.warning(f"⚠️ No hay proxies para {country_code}")
            return None
        
        available_proxies = [
            p for p in self.geolocation_targets[country_code]
            if self.proxy_pool[p].is_active
        ]
        
        if not available_proxies:
            self.logger.warning(f"⚠️ Todos los proxies para {country_code} están inactivos")
            return None
        
        proxy = random.choice([self.proxy_pool[p] for p in available_proxies])
        self.logger.info(f"  ✓ Proxy encontrado: {proxy.address} ({country_code})")
        
        return proxy

    async def report_proxy_failure(self, proxy_id: str) -> None:
        """Reporta fallo de proxy."""
        self.logger.warning(f"❌ Fallo de proxy reportado: {proxy_id}")
        
        if proxy_id not in self.proxy_pool:
            return
        
        proxy = self.proxy_pool[proxy_id]
        stats = self.proxy_stats[proxy_id]
        
        proxy.failure_count += 1
        stats.consecutive_failures += 1
        stats.failed_requests += 1
        
        # Desactivar si hay demasiados fallos
        if stats.consecutive_failures >= 5:
            self.logger.error(f"  🔴 Proxy {proxy_id} desactivado tras {stats.consecutive_failures} fallos")
            proxy.is_active = False
            if proxy_id in self.active_proxies:
                self.active_proxies.remove(proxy_id)
            return
        
        # Ajustar health score
        stats.health_score = max(0.0, stats.health_score - 0.1)
        self.logger.info(f"  Health score: {stats.health_score:.1f}")

    async def report_proxy_success(self, proxy_id: str, response_time_ms: float = 0.0) -> None:
        """Reporta éxito de proxy."""
        if proxy_id not in self.proxy_pool:
            return
        
        stats = self.proxy_stats[proxy_id]
        stats.successful_requests += 1
        stats.total_requests += 1
        stats.consecutive_failures = 0
        
        # Resetear health score
        if stats.health_score < 1.0:
            stats.health_score = min(1.0, stats.health_score + 0.05)
        
        # Actualizar response time
        if response_time_ms > 0:
            stats.avg_response_time_ms = (
                (stats.avg_response_time_ms * (stats.successful_requests - 1) + response_time_ms)
                / stats.successful_requests
            )

    def get_proxy_url(self, proxy_config: ProxyConfig) -> str:
        """Genera URL de proxy para usar en requests."""
        scheme = "http"  # Típicamente HTTP para proxies residenciales
        
        if proxy_config.username and proxy_config.password:
            return f"{scheme}://{proxy_config.username}:{proxy_config.password}@{proxy_config.address}:{proxy_config.port}"
        else:
            return f"{scheme}://{proxy_config.address}:{proxy_config.port}"

    async def health_check_all_proxies(self) -> Dict[str, bool]:
        """Verifica salud de todos los proxies."""
        self.logger.info("🏥 Verificando salud de proxies...")
        
        health_results = {}
        
        for proxy_id, proxy in self.proxy_pool.items():
            # En producción: hacer request de prueba a través del proxy
            # Aquí: simular
            is_healthy = random.random() > 0.1  # 90% de tasa de "salud"
            
            health_results[proxy_id] = is_healthy
            
            stats = self.proxy_stats[proxy_id]
            stats.last_status_check = datetime.now().isoformat()
            
            if is_healthy:
                if not proxy.is_active:
                    proxy.is_active = True
                    if proxy_id not in self.active_proxies:
                        self.active_proxies.append(proxy_id)
                    self.logger.info(f"  ✓ {proxy_id} recuperado")
            else:
                await self.report_proxy_failure(proxy_id)
        
        return health_results

    def get_rotation_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de rotación."""
        proxy_stats_list = []
        
        for proxy_id, stats in self.proxy_stats.items():
            proxy_info = {
                "proxy_id": proxy_id,
                "address": self.proxy_pool[proxy_id].address,
                "type": self.proxy_pool[proxy_id].type.value,
                "geolocation": self.proxy_pool[proxy_id].geolocation,
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "success_rate": (
                    stats.successful_requests / stats.total_requests * 100
                    if stats.total_requests > 0 else 0
                ),
                "health_score": stats.health_score,
                "avg_response_time_ms": stats.avg_response_time_ms
            }
            proxy_stats_list.append(proxy_info)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_proxies": len(self.proxy_pool),
            "active_proxies": len(self.active_proxies),
            "total_rotations": len(self.rotation_history),
            "proxies": proxy_stats_list,
            "geolocation_coverage": list(self.geolocation_targets.keys())
        }

    def get_best_proxy(self) -> Optional[ProxyConfig]:
        """Retorna proxy con mejor health score."""
        if not self.active_proxies:
            return None
        
        best_id = max(
            self.active_proxies,
            key=lambda p: self.proxy_stats[p].health_score
        )
        
        return self.proxy_pool[best_id]

    def get_worst_proxy(self) -> Optional[ProxyConfig]:
        """Retorna proxy con peor health score."""
        if not self.active_proxies:
            return None
        
        worst_id = min(
            self.active_proxies,
            key=lambda p: self.proxy_stats[p].health_score
        )
        
        return self.proxy_pool[worst_id]

    async def reset_proxy(self, proxy_id: str) -> bool:
        """Reset completo de proxy."""
        self.logger.info(f"🔄 Reseteando proxy {proxy_id}...")
        
        if proxy_id not in self.proxy_pool:
            return False
        
        proxy = self.proxy_pool[proxy_id]
        proxy.failure_count = 0
        proxy.is_active = True
        
        if proxy_id not in self.active_proxies:
            self.active_proxies.append(proxy_id)
        
        # Reset también de estadísticas
        self.proxy_stats[proxy_id] = ProxyStats(proxy_id=proxy_id)
        
        self.logger.info(f"  ✓ Proxy {proxy_id} reseteado")
        return True

    def get_rotation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retorna historial de rotaciones."""
        return self.rotation_history[-limit:]
