"""
EVASION QUICKSTART - Guía Rápida de Uso (v1.0.0)

Ejemplos prácticos para usar cada módulo de la capa de evasion.
Última actualización: 2026-04-15
"""

# ============================================================================
# 1. QUICKSTART: Browser Stealth
# ============================================================================

## Ejemplo 1.1: Conexión Sigilosa Básica

```python
import asyncio
from src.evasion.browser import StealthController, StealthConfig

async def example_basic_stealth():
    # Crear configuración
    config = StealthConfig(
        browserless_url="wss://chrome.browserless.io",
        headless=True,
        stealth_plugins=True
    )
    
    # Inicializar controller
    stealth = StealthController(config=config)
    
    # Conectar
    await stealth.connect()
    
    # Navegar sigilosamente
    page_html = await stealth.navigate_stealthily("https://example.com")
    
    # Rellenar formulario (con timing realista)
    await stealth.execute_action(
        action_type="type",
        selector="input[name='username']",
        text="admin"
    )
    
    # Hacer clic
    await stealth.execute_action(
        action_type="click",
        selector="button.login"
    )
    
    # Obtener datos
    result = await stealth.wait_for_condition(
        condition_type="selector",
        selector="div.dashboard"
    )
    
    print(f"✓ Página obtenida: {len(page_html)} bytes")
    
asyncio.run(example_basic_stealth())
```

**Output Esperado:**
```
StealthController initialized (profile: chrome_120)
🔗 Navigating to https://example.com
  ✓ WebDriver evasion injected
  ✓ Fingerprint spoofing applied
  ✓ Permissions override injected
  ✓ Chrome mask applied
✓ Página obtenida: 45287 bytes
```

---

## Ejemplo 1.2: Cambiar Perfil de Navegador

```python
from src.evasion.browser import StealthController, StealthConfig, BrowserFingerprint

async def example_profile_switching():
    stealth = StealthController()
    
    # Opción 1: Chrome Windows
    stealth.config.browser_profile = "chrome_120"
    await stealth.connect()
    fp1 = stealth.fingerprint_spoofing.generate_random_fingerprint()
    print(f"Chrome UA: {fp1.user_agent}")
    
    # Opción 2: Firefox Linux
    stealth.config.browser_profile = "firefox_121"
    fp2 = stealth.fingerprint_spoofing.generate_random_fingerprint()
    print(f"Firefox UA: {fp2.user_agent}")
    
    # Opción 3: Safari macOS
    stealth.config.browser_profile = "safari_17"
    fp3 = stealth.fingerprint_spoofing.generate_random_fingerprint()
    print(f"Safari UA: {fp3.user_agent}")
```

**Output Esperado:**
```
Chrome UA: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
Firefox UA: Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0
Safari UA: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15...
```

---

## Ejemplo 1.3: Obtener Estadísticas de Evasion

```python
from src.evasion.browser import StealthController

async def example_monitoring():
    stealth = StealthController()
    await stealth.connect()
    
    # Navegar a varios sitios
    await stealth.navigate_stealthily("https://example1.com")
    await stealth.navigate_stealthily("https://example2.com")
    
    # Obtener estadísticas
    stats = stealth.get_monitoring_stats()
    
    print(f"🔐 Stealth Statistics:")
    print(f"  Active Connections: {stats['active_connections']}")
    print(f"  Stealth Injections: {stats['stealth_injections']}")
    print(f"  WAF Detections: {stats['waf_detections']}")
    print(f"  Request Log Size: {stats['request_log_size']} KB")
```

---

# ============================================================================
# 2. QUICKSTART: CAPTCHA Detection & Solving
# ============================================================================

## Ejemplo 2.1: Detectar Tipo de CAPTCHA

```python
from src.evasion.captcha import ChallengeDetector, ChallengeType

def example_detect_captcha():
    detector = ChallengeDetector()
    
    # HTML de ejemplo con reCAPTCHA v2
    html = """
    <html>
        <script src="https://www.google.com/recaptcha/api.js"></script>
        <div class="g-recaptcha" data-sitekey="6Led..."></div>
    </html>
    """
    
    # Analizar
    challenges = detector.analyze_page_html(html)
    
    print(f"Challenge Type: {challenges.challenge_type}")
    print(f"Risk Score: {challenges.risk_score}")
    print(f"WAF Detected: {challenges.waf_type}")
    
    # Evaluar riesgo global
    risk = detector.evaluate_risk_score()
    print(f"\nGlobal Assessment:")
    print(f"  Risk Level: {risk}")
    print(f"  Recommendation: {detector.get_risk_recommendation(risk)}")

example_detect_captcha()
```

**Output Esperado:**
```
Challenge Type: ChallengeType.RECAPTCHA_V2
Risk Score: 0.65
WAF Detected: WAFType.CLOUDFLARE

Global Assessment:
  Risk Level: 0.65 (MEDIUM)
  Recommendation: enable_evasion
```

---

## Ejemplo 2.2: Resolver reCAPTCHA automáticamente

```python
import asyncio
from src.evasion.captcha import SolverClient, CaptchaType

async def example_solve_recaptcha():
    # Inicializar con claves de API
    solver = SolverClient(
        providers={
            "anti_captcha": "your_anti_captcha_key",
            "2captcha": "your_2captcha_key"
        }
    )
    
    # Resolver reCAPTCHA v2
    solution = await solver.solve_recaptcha_v2(
        sitekey="6Led7CcbAAA...",  # Desde HTML
        url="https://example.com/login"
    )
    
    print(f"✓ CAPTCHA resuelto!")
    print(f"  Token: {solution[:20]}...")
    print(f"  Tiempo: {solver.get_job_history()[-1]['solve_time']}s")
    
    # Obtener estadísticas
    stats = solver.get_solver_stats()
    print(f"\nSolver Stats:")
    print(f"  Success Rate: {stats['success_rate']:.1%}")
    print(f"  Avg Cost: ${stats['avg_cost']:.3f}")
    print(f"  Total Solved (session): {stats['total_solved']}")

asyncio.run(example_solve_recaptcha())
```

**Output Esperado:**
```
✓ CAPTCHA resuelto!
  Token: 03AHJ_AuuUF5iY...
  Tiempo: 38.2s

Solver Stats:
  Success Rate: 94.5%
  Avg Cost: $0.002
  Total Solved (session): 12
```

---

## Ejemplo 2.3: Auto-detectar e Inyectar Tokens

```python
import asyncio
from src.evasion.captcha import TokenInjector, SolverClient, ChallengeDetector

async def example_auto_captcha_solve():
    detector = ChallengeDetector()
    solver = SolverClient(providers={"anti_captcha": "key"})
    injector = TokenInjector()
    
    # Obtener página
    html = """<html>...
        <div class="g-recaptcha" data-sitekey="6Led..."></div>
    </html>"""
    
    # 1. Detectar
    challenges = detector.analyze_page_html(html)
    if challenges.challenge_type != ChallengeType.RECAPTCHA_V2:
        return print("No CAPTCHA detected")
    
    # 2. Auto-descubrir puntos de inyección
    injection_points = await injector.auto_discover_injection_points(html)
    print(f"✓ Found {len(injection_points)} injection points")
    
    # 3. Resolver
    token = await solver.solve_recaptcha_v2(
        sitekey=challenges.sitekey,
        url="https://example.com"
    )
    
    # 4. Inyectar automáticamente
    for point in injection_points:
        if point.method == "dom":
            script = injector.generate_dom_injection_script(
                token_value=token,
                target_selector=point.selector
            )
            print(f"✓ Inyectó token en {point.selector}")

asyncio.run(example_auto_captcha_solve())
```

---

# ============================================================================
# 3. QUICKSTART: Proxy Rotation
# ============================================================================

## Ejemplo 3.1: Rotación Básica de Proxies

```python
import asyncio
from src.evasion.proxy import ProxyRotator, ProxyType

async def example_proxy_rotation():
    rotator = ProxyRotator()
    
    # Agregar proxies
    rotator.add_proxy_batch([
        {
            "address": "proxy1.example.com",
            "port": 8080,
            "type": ProxyType.RESIDENTIAL,
            "geolocation": "US"
        },
        {
            "address": "proxy2.example.com",
            "port": 8080,
            "type": ProxyType.MOBILE,
            "geolocation": "UK"
        },
        {
            "address": "proxy3.example.com",
            "port": 8080,
            "type": ProxyType.MOBILE,
            "geolocation": "DE"
        }
    ])
    
    # Obtener proxies secuencialmente (round-robin)
    for i in range(5):
        proxy = rotator.get_next_proxy()
        print(f"{i+1}. {proxy.address}:{proxy.port} ({proxy.geolocation})")
    
    # Reportar fallo
    rotator.report_proxy_failure(rotator.proxies[0].id)
    
    # Health check
    await rotator.health_check_all_proxies()
    stats = rotator.get_best_proxy()
    print(f"\n✓ Best proxy: {stats.address} (health: {stats.health_score})")

asyncio.run(example_proxy_rotation())
```

**Output Esperado:**
```
1. proxy1.example.com:8080 (US)
2. proxy2.example.com:8080 (UK)
3. proxy3.example.com:8080 (DE)
4. proxy1.example.com:8080 (US)
5. proxy2.example.com:8080 (UK)

✓ Best proxy: proxy3.example.com:8080 (health: 0.98)
```

---

## Ejemplo 3.2: Proxy por Geolocalización

```python
from src.evasion.proxy import ProxyRotator

def example_geo_proxy():
    rotator = ProxyRotator()
    
    # Agregar muchos proxies
    proxies = [
        {"address": f"proxy{i}.us", "port": 8080, "geolocation": "US"}
        for i in range(10)
    ] + [
        {"address": f"proxy{i}.uk", "port": 8080, "geolocation": "UK"}
        for i in range(5)
    ] + [
        {"address": f"proxy{i}.de", "port": 8080, "geolocation": "DE"}
        for i in range(3)
    ]
    
    rotator.add_proxy_batch(proxies)
    
    # Obtener proxies de país específico
    us_proxy = rotator.get_proxy_for_geolocation("US")
    uk_proxy = rotator.get_proxy_for_geolocation("UK")
    
    print(f"✓ US Proxy: {us_proxy.address} ({us_proxy.geolocation})")
    print(f"✓ UK Proxy: {uk_proxy.address} ({uk_proxy.geolocation})")

example_geo_proxy()
```

---

# ============================================================================
# 4. QUICKSTART: Jitter Engine (Comportamiento Humano)
# ============================================================================

## Ejemplo 4.1: Pausas Realistas

```python
from src.evasion.proxy import JitterEngine, JitterProfile

def example_jitter_pauses():
    # Crear motores con diferentes perfiles
    bot_jitter = JitterEngine(profile=JitterProfile.MODERATE_BOT)
    user_jitter = JitterEngine(profile=JitterProfile.NORMAL_USER)
    distracted_jitter = JitterEngine(profile=JitterProfile.DISTRACTED_USER)
    
    print("Bot Pauses (aggressive):")
    for _ in range(3):
        pause = bot_jitter.get_random_pause()
        print(f"  {pause:.0f}ms")
    
    print("\nNormal User Pauses:")
    for _ in range(3):
        pause = user_jitter.get_random_pause()
        print(f"  {pause:.0f}ms")
    
    print("\nDistracted User Pauses (realistic):")
    for _ in range(3):
        pause = distracted_jitter.get_random_pause()
        print(f"  {pause:.0f}ms")

example_jitter_pauses()
```

**Output Esperado:**
```
Bot Pauses (aggressive):
  87ms
  45ms
  92ms

Normal User Pauses:
  1245ms
  827ms
  1876ms

Distracted User Pauses (realistic):
  2103ms
  567ms
  4234ms
```

---

## Ejemplo 4.2: Tipeo Realista

```python
import asyncio
from src.evasion.proxy import JitterEngine, JitterProfile

async def example_realistic_typing():
    jitter = JitterEngine(profile=JitterProfile.NORMAL_USER)
    
    text_to_type = "password123"
    total_time = 0
    
    print(f"Typing: {text_to_type}")
    print("Character timing:")
    
    for char in text_to_type:
        typing_speed = jitter.get_typing_speed()
        total_time += typing_speed
        print(f"  '{char}': +{typing_speed:.0f}ms (total: {total_time:.0f}ms)")
        await asyncio.sleep(typing_speed / 1000)  # Convertir a segundos
    
    print(f"\nTotal typing time: {total_time:.0f}ms ({total_time/1000:.1f}s)")

asyncio.run(example_realistic_typing())
```

**Output Esperado:**
```
Typing: password123
Character timing:
  'p': +87ms (total: 87ms)
  'a': +45ms (total: 132ms)
  's': +92ms (total: 224ms)
  ...

Total typing time: 1203ms (1.2s)
```

---

## Ejemplo 4.3: Movimiento de Mouse Realista

```python
from src.evasion.proxy import JitterEngine

def example_mouse_movement():
    jitter = JitterEngine()
    
    # Punto inicial → Fin (click en botón)
    start = (100, 200)
    end = (500, 350)
    
    # Obtener perfil de movimiento (bezier + easing)
    profile = jitter.get_mouse_movement_profile(start, end)
    
    print(f"Mouse Movement Profile:")
    print(f"  Start: {start}")
    print(f"  End: {end}")
    print(f"  Path points: {len(profile['path'])}")
    print(f"  Duration: {profile['duration_ms']:.0f}ms")
    print(f"  Easing: {profile['easing_function']}")
    
    # Visualizar ruta
    for i, point in enumerate(profile['path'][:5]):
        print(f"    Step {i}: {point}")

example_mouse_movement()
```

---

# ============================================================================
# 5. QUICKSTART: TLS Spoofing
# ============================================================================

## Ejemplo 5.1: Generar TLS Fingerprints

```python
from src.evasion.proxy import TLSSpoofing, BrowserTLSProfile

def example_tls_fingerprints():
    # Chrome 120
    tls_chrome = TLSSpoofing(profile=BrowserTLSProfile.CHROME_120)
    ja3_chrome = tls_chrome.get_ja3_fingerprint()
    
    # Firefox 121
    tls_firefox = TLSSpoofing(profile=BrowserTLSProfile.FIREFOX_121)
    ja3_firefox = tls_firefox.get_ja3_fingerprint()
    
    # Safari 17
    tls_safari = TLSSpoofing(profile=BrowserTLSProfile.SAFARI_17)
    ja3_safari = tls_safari.get_ja3_fingerprint()
    
    print("TLS JA3 Fingerprints:")
    print(f"  Chrome:  {ja3_chrome}")
    print(f"  Firefox: {ja3_firefox}")
    print(f"  Safari:  {ja3_safari}")
    
    print("\nTLS JA4 Fingerprints:")
    print(f"  Chrome:  {tls_chrome.get_ja4_fingerprint()}")
    print(f"  Firefox: {tls_firefox.get_ja4_fingerprint()}")
    print(f"  Safari:  {tls_safari.get_ja4_fingerprint()}")

example_tls_fingerprints()
```

---

## Ejemplo 5.2: Cambiar Perfil TLS

```python
import asyncio
from src.evasion.proxy import TLSSpoofing, BrowserTLSProfile

async def example_tls_profile_switch():
    tls = TLSSpoofing(profile=BrowserTLSProfile.CHROME_120)
    
    # Conexión 1: Chrome
    print("Connection 1 (Chrome)")
    conn1 = await tls.intercept_tls_connection("api.example.com")
    print(f"  Profile: {conn1['browser_profile']}")
    
    # Cambiar a Firefox
    tls.change_browser_profile(BrowserTLSProfile.FIREFOX_121)
    
    # Conexión 2: Firefox
    print("\nConnection 2 (Firefox)")
    conn2 = await tls.intercept_tls_connection("api.example.com")
    print(f"  Profile: {conn2['browser_profile']}")
    
    # Obtener histórico
    stats = tls.get_tls_stats()
    print(f"\nTotal Connections: {stats['total_connections']}")

asyncio.run(example_tls_profile_switch())
```

---

# ============================================================================
# 6. ESCENARIO COMPLETO: Reconocimiento de Sitio Protegido
# ============================================================================

## Escenario: Target Protegido por Cloudflare + hCaptcha

```python
import asyncio
from src.evasion.browser import StealthController
from src.evasion.captcha import ChallengeDetector, SolverClient, TokenInjector
from src.evasion.proxy import ProxyRotator, JitterEngine

async def recon_protected_site():
    """Recon completo de sitio con Cloudflare + hCaptcha."""
    
    print("=" * 60)
    print("SCENARIO: Recon Protected Target (Cloudflare + hCaptcha)")
    print("=" * 60)
    
    # 1. Inicializar módulos
    print("\n[1/6] Inicializando módulos...")
    stealth = StealthController()
    detector = ChallengeDetector()
    proxy_mgr = ProxyRotator()
    jitter = JitterEngine()
    solver = SolverClient(providers={"anti_captcha": "api_key"})
    injector = TokenInjector()
    
    # 2. Agregar proxies
    print("[2/6] Agregando pool de proxies...")
    proxy_mgr.add_proxy_batch([
        {"address": "proxy1.residential.com", "port": 8080, "geolocation": "US", "type": "residential"},
        {"address": "proxy2.mobile.com", "port": 8080, "geolocation": "US", "type": "mobile"},
    ])
    
    # 3. Obtener proxy y conectar
    print("[3/6] Conectando con proxy...")
    proxy = proxy_mgr.get_next_proxy()
    await stealth.connect(proxy_config=proxy)
    
    # 4. Navegar a target
    print("[4/6] Navegando a target...")
    target_url = "https://protected-site.example.com"
    page_html = await stealth.navigate_stealthily(target_url)
    
    # 5. Detectar desafíos
    print("[5/6] Detectando desafíos...")
    challenges = detector.analyze_page_html(page_html)
    risk = detector.evaluate_risk_score()
    
    print(f"    Challenge: {challenges.challenge_type}")
    print(f"    WAF: {challenges.waf_type}")
    print(f"    Risk: {risk:.1%}")
    
    # 6. Resolver CAPTCHA si es necesario
    if challenges.challenge_type.value.startswith("HCAPTCHA"):
        print("[6/6] Resolviendo hCaptcha...")
        token = await solver.solve_hcaptcha(
            sitekey=challenges.sitekey,
            url=target_url
        )
        
        # Inyectar token
        await injector.inject_token_in_dom(
            token=token,
            selector="input[name='h-captcha-response']"
        )
        print(f"    ✓ Token inyectado")
    
    # 7. Aplicar jitter realista
    print("\nAplicando timing realista...")
    pause = jitter.get_random_pause()
    await asyncio.sleep(pause / 1000)
    
    print(f"\n✓ Reconocimiento completado!")
    print(f"   Datos obtenidos: {len(page_html)} bytes")
    print(f"   Tiempo total: ~{pause/1000:.1f}s")

asyncio.run(recon_protected_site())
```

**Output Esperado:**
```
============================================================
SCENARIO: Recon Protected Target (Cloudflare + hCaptcha)
============================================================

[1/6] Inicializando módulos...
[2/6] Agregando pool de proxies...
[3/6] Conectando con proxy...
[4/6] Navegando a target...
[5/6] Detectando desafíos...
    Challenge: ChallengeType.HCAPTCHA
    WAF: WAFType.CLOUDFLARE
    Risk: 78.5%
[6/6] Resolviendo hCaptcha...
    ✓ Token inyectado

Aplicando timing realista...

✓ Reconocimiento completado!
   Datos obtenidos: 54321 bytes
   Tiempo total: ~2.3s
```

---

# ============================================================================
# 7. DEBUGGING & TROUBLESHOOTING
# ============================================================================

## Problema 1: CAPTCHA No Se Resuelve

```python
# Solución: Verificar API key y ensamblador

solver = SolverClient(
    providers={
        "anti_captcha": "YOUR_KEY_HERE"
    },
    debug=True  # ← Habilita logs detallados
)

# Ver logs de intento
job = solver.get_job_history()[-1]
print(f"Status: {job['status']}")
print(f"Error: {job.get('error_message', 'None')}")

# Cambiar a solver alternativo
solution = await solver.solve_recaptcha_v2(
    sitekey="...",
    url="...",
    provider_fallback="2captcha"  # Fallback automático
)
```

---

## Problema 2: Proxy Bloqueado

```python
# Solución: Reportar fallo y rotar

proxy = rotator.get_next_proxy()

try:
    response = await request_with_proxy(url, proxy)
except ProxyError as e:
    print(f"Proxy {proxy.address} failed!")
    
    # Reportar fallo
    rotator.report_proxy_failure(proxy.id)
    
    # Obtener siguiente
    proxy = rotator.get_next_proxy()
    response = await request_with_proxy(url, proxy)
```

---

## Problema 3: Fingerprint Inconsistent (Veil Dropping)

```python
# Solución: Regenerar fingerprint consistente

fp_spoofing = FingerprintSpoofing()

# Usar fingerprint con seed para consistencia
seed = "my_consistent_seed"
fp1 = fp_spoofing.generate_consistent_fingerprint(seed=seed)
fp2 = fp_spoofing.generate_consistent_fingerprint(seed=seed)

# Verificar que sean iguales
mismatches = fp_spoofing.compare_fingerprints(fp1, fp2)
assert len(mismatches) == 0, "Fingerprints should be identical!"
```

---

# ============================================================================
# 8. REFERENCIAS RÁPIDAS
# ============================================================================

### Instalación

```bash
# Instalar dependencias
pip install -r requirements/evasion.txt

# Dependencias clave
pip install playwright asio cryptography pyOpenSSL
```

### Configuración

```python
# Archivo: src/config/evasion_defaults.yaml
# Personalizar antes de usar

stealth:
  browserless_url: "wss://chrome.browserless.io"
  headless: true

captcha:
  auto_detect: true
  solvers:
    - provider: "anti_captcha"
      api_key: "${ANTI_CAPTCHA_KEY}"

proxy:
  providers:
    - name: "bright_data"
      zones: ["zone_us_1", "zone_uk_1"]
```

### Imports Comunes

```python
# Browser
from src.evasion import StealthController, FingerprintSpoofing

# CAPTCHA
from src.evasion import ChallengeDetector, SolverClient, TokenInjector

# Proxy
from src.evasion import ProxyRotator, JitterEngine, TLSSpoofing
```

### Documentación Completa

Ver `docs/EVASION_INTEGRATION.md` para:
- Integración con Orchestrator
- Casos de uso avanzados
- Métricas y monitoreo
- Testing end-to-end

"""
