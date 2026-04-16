"""
Jitter Engine - Introducción de variabilidad temporal para emular comportamiento humano.

Responsabilidades:
- Generar pausas estocásticas (jitter)
- Emular cinemática humana (aceleración, desaceleración)
- Variación de velocidad de escritura/lectura
- Fluctuaciones en latencia de navegación
- Prevenir patrones detectables en análisis de comportamiento
"""

import logging
import random
import math
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class JitterProfile(Enum):
    """Perfiles de jitter predefinidos."""
    AGGRESSIVE_BOT = "aggressive_bot"  # Muy rápido, sin variación
    MODERATE_BOT = "moderate_bot"  # Rápido pero con algo de variación
    CAUTIOUS_USER = "cautious_user"  # Lento y cuidadoso
    NORMAL_USER = "normal_user"  # Comportamiento típico
    DISTRACTED_USER = "distracted_user"  # Pausas largas, lectura lenta


@dataclass
class JitterConfig:
    """Configuración de jitter."""
    
    profile: JitterProfile = JitterProfile.NORMAL_USER
    
    # Rangos de pausa (ms)
    min_pause: int = 100
    max_pause: int = 2000
    
    # Pausa entre acciones (ms)
    inter_action_delay: int = 500
    
    # Velocidad de escritura (ms por carácter)
    typing_speed_min: int = 30
    typing_speed_max: int = 150
    
    # Distribución: "uniform", "gaussian", "exponential"
    distribution: str = "gaussian"
    
    # Factor de comportamiento suspicious (0.0 = muy sospechoso, 1.0 = muy humano)
    humaneness_factor: float = 0.8
    
    # Variabilidad (0.0 = constante, 1.0 = muy variable)
    variability: float = 0.7


class JitterEngine:
    """Motor de generación de jitter y variabilidad temporal."""
    
    def __init__(self, config: Optional[JitterConfig] = None) -> None:
        """Inicializa el motor de jitter."""
        self.logger = logging.getLogger(__name__)
        self.config = config or JitterConfig()
        
        # Aplicar perfil predefinido
        self._apply_profile(self.config.profile)
        
        # Estadísticas
        self.total_pauses_generated = 0
        self.total_pause_time_ms = 0
        self.action_sequence: List[Dict[str, Any]] = []
        
        self.logger.info(f"✓ Jitter Engine inicializado (Perfil: {self.config.profile.value})")

    def _apply_profile(self, profile: JitterProfile) -> None:
        """Aplica configuración predefinida según perfil."""
        profiles = {
            JitterProfile.AGGRESSIVE_BOT: {
                "min_pause": 10,
                "max_pause": 100,
                "inter_action_delay": 50,
                "typing_speed_min": 5,
                "typing_speed_max": 20,
                "distribution": "uniform",
                "humaneness_factor": 0.2,
                "variability": 0.1
            },
            JitterProfile.MODERATE_BOT: {
                "min_pause": 50,
                "max_pause": 500,
                "inter_action_delay": 200,
                "typing_speed_min": 15,
                "typing_speed_max": 50,
                "distribution": "gaussian",
                "humaneness_factor": 0.4,
                "variability": 0.3
            },
            JitterProfile.CAUTIOUS_USER: {
                "min_pause": 1000,
                "max_pause": 5000,
                "inter_action_delay": 2000,
                "typing_speed_min": 80,
                "typing_speed_max": 200,
                "distribution": "exponential",
                "humaneness_factor": 0.95,
                "variability": 0.9
            },
            JitterProfile.NORMAL_USER: {
                "min_pause": 300,
                "max_pause": 2000,
                "inter_action_delay": 700,
                "typing_speed_min": 40,
                "typing_speed_max": 120,
                "distribution": "gaussian",
                "humaneness_factor": 0.85,
                "variability": 0.7
            },
            JitterProfile.DISTRACTED_USER: {
                "min_pause": 500,
                "max_pause": 5000,
                "inter_action_delay": 1500,
                "typing_speed_min": 60,
                "typing_speed_max": 180,
                "distribution": "exponential",
                "humaneness_factor": 0.9,
                "variability": 0.9
            }
        }
        
        if profile in profiles:
            profile_config = profiles[profile]
            for key, value in profile_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

    def get_random_pause(self) -> int:
        """Genera pausa aleatoria en ms."""
        if self.config.distribution == "uniform":
            pause = random.randint(self.config.min_pause, self.config.max_pause)
        
        elif self.config.distribution == "gaussian":
            # Distribución normal centrada en la media
            mean = (self.config.min_pause + self.config.max_pause) / 2
            std_dev = (self.config.max_pause - self.config.min_pause) / 4
            pause = int(random.gauss(mean, std_dev))
            pause = max(self.config.min_pause, min(self.config.max_pause, pause))
        
        elif self.config.distribution == "exponential":
            # Distribución exponencial (más pausas cortas, pocas largas)
            lambda_param = 1.0 / ((self.config.max_pause - self.config.min_pause) / 2)
            pause = int(self.config.min_pause + random.expovariate(lambda_param))
            pause = max(self.config.min_pause, min(self.config.max_pause, pause))
        
        else:
            pause = random.randint(self.config.min_pause, self.config.max_pause)
        
        # Aplicar factor de variabilidad
        variance_range = int(pause * (1 - self.config.variability))
        pause = pause + random.randint(-variance_range, variance_range)
        pause = max(self.config.min_pause, min(self.config.max_pause, pause))
        
        self.total_pauses_generated += 1
        self.total_pause_time_ms += pause
        
        return pause

    def get_action_delay(self) -> int:
        """Retorna delay entre acciones (más corto que pausa general)."""
        base_delay = self.config.inter_action_delay
        
        # Agregar variabilidad
        variance = int(base_delay * self.config.variability * 0.5)
        delay = base_delay + random.randint(-variance, variance)
        
        return max(0, delay)

    def get_typing_speed(self, text_length: int = 1) -> int:
        """Retorna delay en ms por carácter (cinemática de escritura)."""
        base_speed = random.randint(self.config.typing_speed_min, self.config.typing_speed_max)
        
        # Reducir velocidad en palabras largas
        if text_length > 10:
            base_speed = int(base_speed * 0.9)
        
        return base_speed

    async def apply_human_like_navigation(
        self, 
        page_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aplica jitter a secuencia de acciones."""
        self.logger.info(f"🎭 Aplicando jitter a {len(page_actions)} acciones...")
        
        enhanced_actions = []
        
        for i, action in enumerate(page_actions):
            # Agregar pausa antes de cada acción (excepto la primera)
            if i > 0:
                pause = self.get_random_pause()
                enhanced_actions.append({
                    "type": "pause",
                    "duration_ms": pause,
                    "reason": "inter_action_delay"
                })
            
            # Procesar acción específica
            if action.get("type") == "click":
                # Click con pequeña pausa previa
                enhanced_actions.append({
                    **action,
                    "pre_delay_ms": self.get_action_delay(),
                    "enhanced": True
                })
            
            elif action.get("type") == "type":
                # Escritura con jitter por carácter
                typing_delays = [
                    self.get_typing_speed() 
                    for _ in range(len(action.get("text", "")))
                ]
                enhanced_actions.append({
                    **action,
                    "character_delays": typing_delays,
                    "total_typing_time": sum(typing_delays),
                    "enhanced": True
                })
            
            elif action.get("type") == "scroll":
                # Scroll con aceleración gradual
                scroll_profile = self._generate_scroll_profile(
                    distance=action.get("distance", 500),
                    duration_ms=self.get_random_pause()
                )
                enhanced_actions.append({
                    **action,
                    "scroll_profile": scroll_profile,
                    "enhanced": True
                })
        
        self.action_sequence.extend(enhanced_actions)
        self.logger.info(f"  ✓ {len(enhanced_actions)} acciones con jitter aplicadas")
        
        return enhanced_actions

    def get_network_jitter(self, base_latency_ms: int = 100) -> int:
        """Simula jitter de red (latencia variable)."""
        # Fluctuación típica de conexión real
        jitter = int(base_latency_ms * random.uniform(-0.1, 0.3))
        return max(0, base_latency_ms + jitter)

    def get_reading_time(self, text_length: int, words_per_minute: int = 200) -> int:
        """Calcula tiempo realista de lectura."""
        # Estimación: ~5 caracteres por palabra en promedio
        estimated_words = text_length / 5
        reading_time_minutes = estimated_words / words_per_minute
        
        # Agregar variabilidad
        reading_time_ms = int(reading_time_minutes * 60 * 1000)
        variance = int(reading_time_ms * 0.3)
        
        return reading_time_ms + random.randint(-variance, variance)

    def get_mouse_movement_profile(
        self, 
        start_x: int, 
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: int = 500
    ) -> List[Dict[str, Any]]:
        """Genera perfil de movimiento del ratón (bezier curves, no línea recta)."""
        self.logger.info(f"🖱️ Generando perfil de movimiento del ratón...")
        
        # Calcular distancia
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        # Generar puntos de control para curva bezier
        control_x = (start_x + end_x) / 2 + random.randint(-100, 100)
        control_y = (start_y + end_y) / 2 + random.randint(-100, 100)
        
        # Muestrear el movimiento
        points = []
        steps = max(10, int(distance / 50))  # Más pasos para distancias largas
        
        for i in range(steps + 1):
            t = i / steps
            
            # Bezier quadratic
            x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * end_y
            
            # Timing con easing
            time_offset = int((t**2) * duration_ms)  # ease-out quadratic
            
            points.append({
                "x": int(x),
                "y": int(y),
                "time_offset_ms": time_offset
            })
        
        return points

    async def simulate_realistic_session(
        self, 
        session_duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """Simula sesión realista completa con pausas y comportamiento."""
        self.logger.info(f"📊 Simulando sesión realista de {session_duration_minutes} minutos...")
        
        session_start = datetime.now()
        session_end = session_start + timedelta(minutes=session_duration_minutes)
        
        events = []
        current_time = session_start
        
        # Generar eventos durante la sesión
        while current_time < session_end:
            pause_duration = timedelta(milliseconds=self.get_random_pause())
            
            # Ocasionalmente: lectura/navegación
            if random.random() < 0.3:
                events.append({
                    "type": "read",
                    "duration_ms": self.get_reading_time(3000),
                    "timestamp": current_time.isoformat()
                })
            
            # Ocasionalmente: acción (click, scroll, etc)
            elif random.random() < 0.4:
                action_type = random.choice(["click", "scroll", "type"])
                events.append({
                    "type": action_type,
                    "delay_ms": self.get_action_delay(),
                    "timestamp": current_time.isoformat()
                })
            
            else:
                # Pausa pura
                events.append({
                    "type": "pause",
                    "duration_ms": self.get_random_pause(),
                    "timestamp": current_time.isoformat()
                })
            
            current_time += pause_duration
        
        return {
            "timestamp": session_start.isoformat(),
            "session_duration_minutes": session_duration_minutes,
            "total_events": len(events),
            "profile": self.config.profile.value,
            "events_sample": events[:10] if events else [],
            "stats": self.get_jitter_stats()
        }

    def get_jitter_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de jitter."""
        avg_pause = (
            self.total_pause_time_ms / self.total_pauses_generated
            if self.total_pauses_generated > 0 else 0
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "profile": self.config.profile.value,
            "total_pauses": self.total_pauses_generated,
            "total_pause_time_ms": self.total_pause_time_ms,
            "average_pause_ms": avg_pause,
            "total_actions_enhanced": len(self.action_sequence),
            "config": {
                "distribution": self.config.distribution,
                "humaneness_factor": self.config.humaneness_factor,
                "variability": self.config.variability
            }
        }

    def _generate_scroll_profile(self, distance: int, duration_ms: int) -> List[Dict[str, Any]]:
        """Genera perfil de scroll con aceleración natural."""
        # Scroll con easing: comienza lento, acelera, luego desacelera
        profile = []
        steps = max(5, int(duration_ms / 50))
        
        for i in range(steps):
            t = i / steps
            
            # Easing function: ease-in-out
            if t < 0.5:
                eased_t = 2 * t * t
            else:
                eased_t = -1 + (4 - 2 * t) * t
            
            pixel_offset = int(distance * eased_t)
            time_offset = int(t * duration_ms)
            
            profile.append({
                "pixel_offset": pixel_offset,
                "time_offset_ms": time_offset
            })
        
        return profile
