"""
Documentación de Integración - Evasion Layer v1.0.0

Este documento define cómo integrar la capa de evasión con:
- Orchestrator v1.2.0 (supervisor y planner)
- ReconAgent v1.0.0 (herramientas de reconocimiento)
- Logic Agent (coordinación de ataques)
- Exploit Agent (ejecución dentro de sandbox)

Última actualización: 2026-04-15
Versión: 1.0.0
"""

# ============================================================================
# 1. ARQUITECTURA DE INTEGRACIÓN
# ============================================================================

## Flujo General: Orchestrator → Planner → ReconAgent + Evasion → Intelligence

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR v1.2.0                                 │
│                    (supervisor + planner)                               │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ├─► Whitelist Validation (CVE-2026-2256)
                     ├─► Veil Dropping Detection (Trust Scoring)
                     ├─► Graceful Shutdown Handlers
                     └─► 3-7 Step Limit Enforcement
                     
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │   PLANNER: Attack Planning               │
        │   - Decompose objetivo en 3-7 steps    │
        │   - Validar cada step contra whitelist │
        │   - Route a ReconAgent + Evasion combo │
        └────────────────────┬───────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
                   ▼                   ▼
        ┌──────────────────┐  ┌──────────────────┐
        │  RECON AGENT     │  │  EVASION LAYER   │
        │  (15 tools)      │  │  (8 modules)     │
        │  - JavaScript    │  │  - Browser       │
        │  - GraphQL       │  │  - CAPTCHA       │
        │  - Network OSINT │  │  - Proxy/TLS     │
        └────────┬─────────┘  └────────┬─────────┘
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
                ┌────────────────────────────┐
                │   INTELLIGENCE GATHERING    │
                │   (Protected Target)        │
                │   - Bypass WAF              │
                │   - Solve CAPTCHA           │
                │   - Evade behavioral        │
                │     analysis + TLS          │
                └────────────────────────────┘
```

# ============================================================================
# 2. PUNTOS DE INTEGRACIÓN (Hookpoints)
# ============================================================================

## 2.1 Orchestrator → Planner Delegation

**Archivo:** `src/orchestrator/planner.py`

**Modificacion requerida:**
```python
# Línea ~450: En PlanningEngine.decompose_objective()

async def decompose_objective(self, objective: str):
    # ... existing code ...
    
    # NEW: Integración con Evasion Layer
    if "protected_target" in objective or "waf_protected" in objective:
        step.evasion_config = {
            "browser_profile": "CHROME_120",
            "captcha_solver": "anti_captcha",
            "proxy_type": "residential",
            "jitter_profile": "cautious_user"
        }
        step.requires_evasion = True
    
    # Validar contra whitelist
    if not self._validate_step(step):
        raise StepValidationError(f"Step {step.id} failed whitelist validation")
```

## 2.2 ReconAgent → Evasion Layer Integration

**Archivo:** `src/agents/recon_agent/server.py`

**Modificacion requerida:**
```python
# Línea ~200: En ReconAgentServer.handle_tool_execution()

from src.evasion import StealthController, ChallengeDetector, ProxyRotator, JitterEngine

async def handle_tool_execution(self, tool_name: str, params: Dict):
    # ... existing code ...
    
    # NEW: Inicializar evasion si es necesario
    if self.current_step.requires_evasion:
        self.stealth_controller = StealthController(config=self.stealth_config)
        self.challenge_detector = ChallengeDetector()
        self.proxy_rotator = ProxyRotator()
        self.jitter_engine = JitterEngine(profile=JitterProfile.CAUTIOUS_USER)
        
        self.logger.info("🎭 Evasion layer activada")
    
    # Ejecutar tool con evasion
    if tool_name == "fetch_url":
        # 1. Analizar antes de conectar
        risk_score = self.challenge_detector.evaluate_risk_score(params.get("url"))
        
        # 2. Si riesgo alto, rotar proxy + aplicar stealth
        if risk_score > 0.6:
            proxy = self.proxy_rotator.get_next_proxy()
            await self.stealth_controller.connect(proxy_config=proxy)
        
        # 3. Aplicar jitter para comportamiento realista
        delay = self.jitter_engine.get_random_pause()
        await asyncio.sleep(delay)
        
        # 4. Ejecutar tool original
        result = await self._fetch_url_with_stealth(params)
        return result
```

## 2.3 Supervisor Validation — Veil Dropping Detection

**Archivo:** `src/orchestrator/supervisor.py`

**Modificacion requerida:**
```python
# Línea ~350: En Supervisor.validate_action()

async def validate_action(self, action: Action) -> bool:
    # ... existing whitelist validation ...
    
    # NEW: Veil Dropping Detection (Behavioral Shift)
    if action.requires_evasion:
        # Comparar fingerprint actual vs. perfil esperado
        from src.evasion import FingerprintSpoofing
        
        fp_spoofing = FingerprintSpoofing()
        expected_fp = action.evasion_config.get("browser_fingerprint")
        current_fp = fp_spoofing.generate_random_fingerprint()
        
        if fp_spoofing.compare_fingerprints(expected_fp, current_fp):
            # Inconsistencia detectada!
            self.trust_score -= 0.2
            self.logger.warning(f"⚠️ Veil dropping detected. Trust: {self.trust_score}")
            
            if self.trust_score < 0.3:
                raise SecurityException("Trust score critical. Aborting.")
    
    return True
```

# ============================================================================
# 3. FLUJO DE EJECUTIÓN: RECON + EVASION
# ============================================================================

## 3.1 Reconocimiento Normal (Sin Evasion)

```
URL Request → ReconAgent.fetch_url()
              ↓
           [No CAPTCHA detectado]
           [No WAF detectado]
           [Risk score < 0.3]
              ↓
           Execute tool normally
           Return intelligence
```

## 3.2 Reconocimiento Protegido (Con Evasion)

```
URL Request → ReconAgent.fetch_url()
              ↓
        Initialize Evasion Layer:
        - StealthController
        - ChallengeDetector
        - ProxyRotator
        - JitterEngine
              ↓
        1. Analyze Page (Challenge Detection)
           ├─ Detect WAF type (7 types)
           ├─ Detect CAPTCHA type (11 types)
           └─ Evaluate risk score
              ↓
        2. Apply Evasion
           ├─ [If WAF detected] Rotate proxy + TLS spoof
           ├─ [If CAPTCHA detected] Solve via SolverClient
           ├─ [If risk high] Apply Jitter + browser stealth
           └─ [Apply fingerprint spoofing]
              ↓
        3. Execute Request
           ├─ Use StealthController for browser automation
           ├─ Inject tokens if needed
           ├─ Apply timing jitter
           └─ Navigate with realistic behavior
              ↓
        4. Validate Connection
           ├─ Check TLS handshake validity
           ├─ Verify no veil dropping
           └─ Log connection stats
              ↓
        5. Return Intelligence
           └─ Protected content + metadata
```

## 3.3 Ejemplo: Atacar Aplicación Protegida por Cloudflare + reCAPTCHA

```python
from src.evasion import (
    ChallengeDetector, StealthController, SolverClient, 
    TokenInjector, ProxyRotator, JitterEngine, TLSSpoofing
)

async def recon_protected_target():
    # 1. Detectar desafíos
    detector = ChallengeDetector()
    challenges = detector.analyze_page_html(html_content)
    
    # Resultado: WAF_CLOUDFLARE + RECAPTCHA_V2 detectados
    # Risk score: 0.85 (alto)
    
    # 2. Preparar evasion
    proxy = ProxyRotator().get_proxy_for_geolocation("US")  # Proxy USA
    stealth = StealthController(stealth_config)
    solver = SolverClient(solver_api_key="...")
    token_injector = TokenInjector()
    jitter = JitterEngine(profile=JitterProfile.NORMAL_USER)
    tls = TLSSpoofing(profile=BrowserTLSProfile.CHROME_120)
    
    # 3. Conectar con evasion
    await stealth.connect(proxy_config=proxy)
    tls_conn = await tls.intercept_tls_connection("target.com")
    
    # 4. Navegar a página
    delay = jitter.get_random_pause()  # ~500-2000ms
    await asyncio.sleep(delay)
    await stealth.navigate_stealthily("https://target.com/api/data")
    
    # 5. Detectar CAPTCHA y resolver
    captcha_found = detector.detect_invisible_challenge(page_html)
    if captcha_found:
        # Resolver reCAPTCHA v2
        solution = await solver.solve_recaptcha_v2(
            sitekey="...",
            url="https://target.com"
        )
        
        # Inyectar token
        await token_injector.inject_token_in_dom(
            token=solution,
            selector="input[name='g-recaptcha-response']"
        )
    
    # 6. Ejecutar acción
    delay = jitter.get_typing_speed()  # ~50-150ms por carácter
    await stealth.execute_action(action_type="click", selector="button.submit")
    
    # 7. Esperar resultado (lectura humana)
    reading_delay = jitter.get_reading_time(response_content)
    await asyncio.sleep(reading_delay)
    
    # 8. Extraer datos
    intelligence = parser.extract_data()
    return intelligence
```

# ============================================================================
# 4. CONFIGURACIÓN POR DEFECTO
# ============================================================================

## 4.1 Stealth Configuration

```python
# src/config/evasion_defaults.yaml

stealth:
  browser_profile: "CHROME_120"
  browserless_url: "wss://chrome.browserless.io"
  headless: true
  stealth_plugins: true
  apply_fingerprint_spoofing: true
  
  # Timing
  min_navigation_delay_ms: 1000
  max_navigation_delay_ms: 5000
  
  # Monitoreo
  log_requests: true
  track_injections: true
  detect_waf_headers: true
```

## 4.2 CAPTCHA Configuration

```python
captcha:
  auto_detect: true
  auto_solve: true
  
  solvers:
    - provider: "anti_captcha"
      api_key: "${ANTI_CAPTCHA_KEY}"
      priority: 1
    - provider: "2captcha"
      api_key: "${2CAPTCHA_KEY}"
      priority: 2
    - provider: "deathbycaptcha"
      api_key: "${DBC_KEY}"
      priority: 3
  
  timeout_seconds: 180
  retry_attempts: 3
```

## 4.3 Proxy Configuration

```python
proxy:
  providers:
    - name: "bright_data"
      type: "residential"
      endpoint: "https://api.brightdata.com"
      zones: ["zone_1", "zone_2"]
    - name: "smartproxy"
      type: "mobile"
      geolocation_support: true
  
  health_check_interval_sec: 300
  max_consecutive_failures: 5
  
  geolocation_distribution:
    "US": 40
    "UK": 25
    "DE": 20
    "FR": 15
```

## 4.4 Jitter Configuration

```python
jitter:
  default_profile: "NORMAL_USER"
  
  profiles:
    AGGRESSIVE_BOT:
      pause_min_ms: 10
      pause_max_ms: 100
      humaneness: 0.2
      
    CAUTIOUS_USER:
      pause_min_ms: 1000
      pause_max_ms: 5000
      humaneness: 0.95
      typing_speed: "realistic"
      mouse_movement: "natural_bezier"
```

# ============================================================================
# 5. MÉTRICAS Y MONITOREO
# ============================================================================

## 5.1 Métricas de Evasion

```python
# Disponibles desde cada módulo:

# SteealthController
stealth.get_monitoring_stats() →
{
    "active_connections": 2,
    "stealth_injections": 42,
    "waf_detections": 3,
    "request_log_size": 156
}

# FingerprintSpoofing
fp.compare_fingerprints(fp1, fp2) →
{
    "consistent": True,
    "mismatches": [],
    "veil_dropping_risk": 0.05
}

# ChallengeDetector
detector.evaluate_risk_score() →
{
    "score": 0.72,
    "recommendation": "enable_evasion",
    "detected_waf": "CLOUDFLARE",
    "detected_captcha": "RECAPTCHA_V3"
}

# ProxyRotator
rotator.get_best_proxy() →
{
    "proxy": "192.168.1.100:8080",
    "health_score": 0.95,
    "success_rate": 0.98,
    "data_transferred_mb": 2048
}

# JitterEngine
jitter.get_random_pause() → 1342.5 (ms)
jitter.get_typing_speed() → 87.3 (ms per char)

# TLSSpoofing
tls.get_tls_stats() →
{
    "browser_profile": "CHROME_120",
    "ja3_fingerprint": "abc123def456...",
    "ja4_fingerprint": "13,5,8,1234,5678",
    "total_connections": 15
}
```

## 5.2 Dashboard de Evasion

```
╔═══════════════════════════════════════════════════════════╗
║            EVASION LAYER MONITORING DASHBOARD             ║
╚═══════════════════════════════════════════════════════════╝

┌─ Browser Stealth ───────────────────────┐
│ Active Connections:    2                 │
│ Stealth Injections:    42               │
│ WAF Detections:        3                │
│ Status:                ✓ Operational    │
└─────────────────────────────────────────┘

┌─ CAPTCHA Handling ──────────────────────┐
│ Solved (last 24h):     127              │
│ Success Rate:          94.5%            │
│ Avg Solve Time:        45s              │
│ Status:                ✓ Operational    │
└─────────────────────────────────────────┘

┌─ Proxy Rotation ────────────────────────┐
│ Active Proxies:        12               │
│ Healthy:               11 (91.7%)       │
│ Avg Response Time:     234ms            │
│ Status:                ✓ Operational    │
└─────────────────────────────────────────┘

┌─ TLS Spoofing ──────────────────────────┐
│ Browser Profile:       Chrome 120       │
│ JA3 Match Rate:        98.2%            │
│ Veil Dropping Risk:    LOW (0.05)       │
│ Status:                ✓ Operational    │
└─────────────────────────────────────────┘

┌─ Overall Status ────────────────────────┐
│ System Health:         94%              │
│ Last Error:            None             │
│ Uptime:                12h 34m         │
└─────────────────────────────────────────┘
```

# ============================================================================
# 6. MANEJO DE ERRORES Y FALLBACKS
# ============================================================================

## 6.1 Cascada de Evasion

```
Protected Target Detected (Risk > 0.6)
  ↓
1. Try Residential Proxy + TLS Spoofing
  ├─ Success? → Continue with evasion
  └─ Failure? → Step 2
  ↓
2. Try Mobile Proxy + Browser Stealth + Fingerprint Spoof
  ├─ Success? → Continue
  └─ Failure? → Step 3
  ↓
3. Try Datacenter Proxy + CAPTCHA Solver
  ├─ Success? → Continue
  └─ Failure? → Step 4
  ↓
4. Try ISP Proxy + Full Jitter Profile (DISTRACTED_USER)
  ├─ Success? → Continue
  └─ Failure? → Step 5
  ↓
5. Log Failure + Abort
  └─ Report to Orchestrator for alternative strategy
```

## 6.2 Recovery Mechanisms

```python
# Si CAPTCHA solver falla 3 veces
solver.check_job_status(job_id) → FAILED
retry_count++

if retry_count >= 3:
    # Cambiar solver
    solver = SolverClient(provider="2captcha")  # Fallback
    retry_count = 0

if retry_attempts >= 9:  # (3 intentos × 3 providers)
    # Notificar orchestrator
    await orchestrator.report_failure(
        reason="CAPTCHA_UNSOLVABLE",
        target=url,
        strategy="ABORT_AND_RETRY_LATER"
    )
```

# ============================================================================
# 7. TESTING INTEGRACIÓN
# ============================================================================

## 7.1 Script de Prueba: Evasion End-to-End

```python
# tests/integration/test_evasion_e2e.py

import asyncio
from src.evasion import (
    StealthController, ChallengeDetector, SolverClient,
    TokenInjector, ProxyRotator, JitterEngine
)

async def test_recon_with_evasion():
    """End-to-end test: Recon protegido con evasion."""
    
    # 1. Inicializar módulos
    stealth = StealthController()
    detector = ChallengeDetector()
    proxy_mgr = ProxyRotator()
    jitter = JitterEngine()
    
    # 2. Agregar proxy
    proxy_mgr.add_proxy_batch([
        {"address": "10.0.0.1", "port": 8080, "type": "residential"},
        {"address": "10.0.0.2", "port": 8080, "type": "mobile"},
    ])
    
    # 3. Conectar con evasion
    proxy = proxy_mgr.get_next_proxy()
    await stealth.connect(proxy_config=proxy)
    
    # 4. Navegar
    await stealth.navigate_stealthily("https://example-with-waf.com")
    
    # 5. Analizar desafíos
    challenges = detector.analyze_page_html(stealth.page_html)
    assert challenges.challenge_type != ChallengeType.NO_CHALLENGE
    
    # 6. Evaluar riesgo
    risk = detector.evaluate_risk_score()
    assert risk > 0.5
    
    # 7. Aplicar jitter
    pause = jitter.get_random_pause()
    assert 1000 <= pause <= 5000  # Dentro de rango realista
    
    print("✓ Evasion end-to-end test passed")

if __name__ == "__main__":
    asyncio.run(test_recon_with_evasion())
```

## 7.2 Test de Veil Dropping Detection

```python
# tests/integration/test_veil_dropping.py

from src.evasion import FingerprintSpoofing

def test_veil_dropping_detection():
    """Verifica que las inconsistencias de fingerprint se detectan."""
    
    fp1 = {
        "user_agent": "Mozilla/5.0 Chrome/120",
        "platform": "Linux",
        "webgl_vendor": "Google Inc"
    }
    
    fp2 = {
        "user_agent": "Mozilla/5.0 Safari/537",  # ← DIFERENTE
        "platform": "MacOS",                      # ← DIFERENTE
        "webgl_vendor": "Apple Inc"               # ← DIFERENTE
    }
    
    spoofing = FingerprintSpoofing()
    mismatches = spoofing.compare_fingerprints(fp1, fp2)
    
    assert len(mismatches) > 0
    assert "user_agent" in mismatches
    assert "platform" in mismatches
    
    print("✓ Veil dropping detection works correctly")
```

# ============================================================================
# 8. CASOS DE USO COMUNES
# ============================================================================

### Caso 1: Reconocimiento de LinkedIn

```python
# linkedin.com está protegido por Cloudflare + análisis conductual

config = {
    "target": "https://www.linkedin.com",
    "profile": "NORMAL_USER",
    "proxy": "residential_us",
    "captcha_solver": "anti_captcha",
    "fingerprint": "random_consistent"
}

# Resultado: ✓ Acceso exitoso, información de perfil extraída
```

### Caso 2: Espionaje de API Protegida

```python
# api.example.com tiene WAF (Imperva) + Token CSRF + Rate Limiting

config = {
    "target": "https://api.example.com/users",
    "profile": "DISTRACTED_USER",  # Más pausa entre requests
    "proxy": "mobile_us",  # Alternar entre móvil/desktop
    "captcha_solver": "2captcha",
    "tls_profile": "FIREFOX_121"  # Parecerá Firefox
}

# Resultado: ✓ WAF bypasseado, datos de API exfiltrados
```

### Caso 3: Elusión de Detección de Bot

```python
# site.com tiene análisis conductual avanzado

config = {
    "profile": "DISTRACTED_USER",
    "pause_distribution": "exponential",  # Pausa realista (más cortas, raro las largas)
    "mouse_movement": "natural_bezier",
    "reading_time": "wpm_based",
    "typing_speed": "variable_per_word",
    "fingerprint_rotation": "per_session",
    "proxy_rotation": "per_request"
}

# Resultado: ✓ Sistema de detección engañado, actividad normal simulada
```

# ============================================================================
# 9. PRÓXIMOS PASOS (Phase 2)
# ============================================================================

### 9.1 Logic Agent Integration
- Planificación inteligente de pasos de evasión
- Adaptación dinámica según feedback de detección
- Machine learning para optimizar perfiles

### 9.2 Exploit Agent Sandbox
- Ejecutar explotaciones dentro de contenedor Docker
- Aplicar evasion layer durante fase de explotación
- Tunnel traffic a través de proxy chain

### 9.3 Evasion Module Enhancements
- Machine fingerprinting detection (ML models)
- Adaptive jitter (feedback-based adjustment)
- Blockchain-based proxy verification
- TLS 1.4 protocol preparation

# ============================================================================
# REFERENCIAS
# ============================================================================

Archivos Relacionados:
- src/orchestrator/planner.py (3-7 step decomposition)
- src/orchestrator/supervisor.py (veil dropping detection)
- src/agents/recon_agent/server.py (tool execution)
- src/evasion/{browser,captcha,proxy}/ (8 módulos)
- tests/integration/ (test cases)

Configuración:
- src/config/evasion_defaults.yaml
- prompts/prompts.json (evasion strategies)
- src/memory/knowledge_graph/ (cached evasion patterns)
"""
