# ArtOfIAV2 - Advanced Attack Modules Integration Guide
## Módulos 3-4: RL Engine + Agentic Identity

---

## 📊 Módulo 3: Self-Evolving Engine (RL)

### Propósito
Motor de aprendizaje por refuerzo que permite que el agente optimize sus tácticas basado en resultados pasados.

### Arquitectura

```
┌─────────────────────────────────────────┐
│         ExploitAgent                    │
│                                         │
│  Execute Attack → Record Outcome        │
│                                         │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│    SelfEvolvingEngine                   │
│                                         │
│  • record_attack_outcome()              │
│  • get_recommended_techniques()         │
│  • suggest_parameter_tuning()           │
│  • get_learning_summary()               │
│                                         │
│  [AttackEpisode] ↔ [TacticEvaluation]  │
└────────────┬────────────────────────────┘
             │
             ↓
    Update LogicAgent Prompts
    for Next Attack Cycle
```

### Componentes Principales

**1. AttackEpisode**
```python
episode = AttackEpisode(
    attack_type="privilege_escalation",
    technique="lotl_certutil",
    target_os="windows",
    edr_type="crowdstrike",
    parameters={"timing": 2000, "obfuscation": "base64"},
    outcome=LearningOutcome.SUCCESS,
    confidence_score=0.92,
    duration_ms=3200,
)

# Registrar
await engine.record_attack_outcome(episode)
```

**2. TacticEvaluation**
```python
# Motor calcula automáticamente:
- success_rate = 0.87 (87% de intentos fueron exitosos)
- detection_rate = 0.05 (solo 5% fueron detectados)
- fitness_score = 0.87 - (0.05 * 0.5) = 0.845

# Ranking inteligente:
# Top techniques by fitness:
# 1. lotl_certutil: 0.845 (mejor balance)
# 2. lotl_powershell: 0.72 (más rápido pero más detectable)
# 3. traditional_meterpreter: 0.65 (viejo, muy detectable)
```

**3. Learning Pipeline**

```
Ataque 1: PowerShell bypass
├─ Result: DETECTED
├─ Duration: 1200ms
└─ Record: success_rate=0%, detection=100%
    
Ataque 2: certutil bypass
├─ Result: SUCCESS
├─ Duration: 2400ms
└─ Record: success_rate=100%, detection=0%

Ataque 3 (based on learning):
├─ Recommend: certutil (100% success)
├─ Suggest: timing=2400ms (si detection ↓)
└─ Adjust parameters automáticamente
```

### Uso en Flujo de Ataque

```python
# 1. Ejecutar ataque
result = await exploit_agent.execute(technique="lotl_certutil")

# 2. Registrar resultado
episode = AttackEpisode(
    attack_type=result.type,
    technique=result.technique,
    target_os=result.os,
    edr_type=result.edr,
    parameters=result.params,
    outcome=LearningOutcome[result.outcome],  # SUCCESS/DETECTED/etc
    confidence_score=result.confidence,
    duration_ms=result.duration,
)
await engine.record_attack_outcome(episode)

# 3. Obtener recomendaciones para próximo intento
recommendations = await engine.get_recommended_techniques(
    attack_type="privilege_escalation",
    target_os="windows",
    edr_type="crowdstrike",
)
# Returns: [
#   {technique: "lotl_certutil", success_rate: 0.87, fitness: 0.845},
#   {technique: "lotl_powershell", success_rate: 0.72, fitness: 0.72},
# ]

# 4. Obtener sugerencias de tuning
tuning = await engine.suggest_parameter_tuning("lotl_certutil")
# Returns: {
#   timing_adjustment: "Increase delays",
#   recommended_parameters: {timing: 2400ms, obfuscation: "base64"}
# }

# 5. Mostrar resumen del aprendizaje
summary = await engine.get_learning_summary()
# {
#   total_episodes: 145,
#   successful_attacks: 126,
#   detected_attacks: 8,
#   overall_success_rate: 0.869,
#   overall_detection_rate: 0.055,
# }
```

### Integración con LogicAgent

```python
# En logic_agent/planner.py:

class AttackPlanner:
    def __init__(self, rl_engine: SelfEvolvingEngine):
        self.rl_engine = rl_engine
    
    async def plan_next_attack(self, target):
        # 1. Obtener recomendaciones del RL
        recommendations = await self.rl_engine.get_recommended_techniques(
            attack_type=target.attack_type,
            target_os=target.os,
            edr_type=target.edr,
        )
        
        if recommendations:
            # Usar técnica recomendada
            best_technique = recommendations[0]
            attack_plan = self.build_plan(best_technique)
        else:
            # Fallback a plan genérico
            attack_plan = self.build_default_plan()
        
        return attack_plan
```

### Métricas de Aprendizaje

| Métrica | Cálculo | Significado |
|---------|---------|------------|
| **success_rate** | successful / total | % de ataques que lograron objetivo |
| **detection_rate** | detected / total | % de ataques detectados por EDR |
| **fitness_score** | (success * 1.0) - (detection * 0.5) | Balance éxito vs. evasión |
| **confidence_bonus** | min(0.3, attempts/1000) | Confianza en el dato (más intentos = más confianza) |

---

## 🕵️ Módulo 4: Agentic Identity Spoofing (M2M)

### Propósito
Explotar comunicación Máquina-a-Máquina (M2M) entre agentes para ganar acceso no autorizado suplantando identidad de agente confiable.

### Contexto

En arquitecturas modernas, agentes se comunican entre sí usando:
```
┌──────────┐     OAuth2/JWT     ┌──────────┐
│ Agent A  │ ─────────────────→ │ Agent B  │
└──────────┘  (Who are you?)    └──────────┘
              (I'm Agent A, 
               here's my JWT)
```

**Problema**: System asume que si JWT es válido, el agente es de confianza.

### Agentic JWT Structure

```json
{
  "agent_id": "recon_agent_prod",
  "agent_name": "Reconnaissance Agent",
  "scopes": ["read_network", "scan_ports", "enumerate_services"],
  "exp": 1704067200,
  "iat": 1704063600,
  "iss": "orchestrator",
  "aud": "internal_api",
  "can_delegate": true,
  "delegation_chain": ["orchestrator"],
  "signed_by": "orchestrator"
}
```

### Vulnerabilidades Explotables

```
┌─────────────────────────────────────────────────┐
│  Agentic JWT Vulnerabilities                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ 1. Algorithm None                               │
│    JWT signed with alg="none"                   │
│    → Modificar claims sin firma                 │
│                                                 │
│ 2. Weak Signing Key                             │
│    Clave shared conocida (hardcoded)           │
│    → Forjar nuevos JWTs                         │
│                                                 │
│ 3. Excessive Delegation                         │
│    Agent A → B → C → D (4 niveles)             │
│    → Cada nivel aumenta scope (mal)             │
│    → Bypear permisos saltando niveles           │
│                                                 │
│ 4. Scope Never Decreases                        │
│    Delegated agent tiene MÁS perms que original │
│    → Escalada de privilegios                    │
│                                                 │
│ 5. No Revocation Checking                       │
│    Token antiguo sigue siendo válido            │
│    → Usar token de agente desactivado           │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Attack Flow

```
Step 1: INTERCEPT
┌──────────────────┐
│ Sniff Agent ←→ API communication
│ Capture JWT token
│ Analyze expiration & scopes
└──────────────┬───┘
               ↓

Step 2: ANALYZE
┌──────────────────┐
│ Decode JWT (sin validar firma)
│ Extract claims:
│   - agent_id: "recon_agent"
│   - scopes: ["read_network"]
│   - can_delegate: true
│   - delegation_chain: []
└──────────────┬───┘
               ↓

Step 3: EXPLOIT
┌──────────────────────────────────┐
│ Option A: Modify Existing Token
│   - If alg=none: modify scopes
│   - Add scope: "admin_override"
│   - Remove expiration
│   
│ Option B: Forge New Token
│   - Create as trusted agent
│   - agent_id="orchestrator"
│   - scopes=["*"]
│   - Requires signing key (weak?)
│   
│ Option C: Exploit Delegation
│   - Use delegation chain
│   - Request scopes from agent
│   - Chain: compromised → B → C
│   - Each adds more perms (transitively)
└──────────────┬───┘
               ↓

Step 4: ACCESS
┌──────────────────────────────────┐
│ Use forged/modified JWT
│ Call internal API as trusted agent
│ Example:
│   POST /api/agent/execute
│   Authorization: Bearer {forged_jwt}
│   Body: {command: "rm -rf /prod"}
│
│ System responds:
│   "Accepted - JWT valid"
│   "Command executed as orchestrator"
└──────────────────────────────────┘
```

### Uso en Code

```python
# 1. Interceptar JWT
intercepted_jwt = "eyJhbGciOiJub25lIi..."

# 2. Analizar identidad
analyzer = AgenticJWTAnalyzer()
identity = await analyzer.decode_agentic_jwt(intercepted_jwt)
# Returns: AgenticIdentity(
#   agent_id="recon_agent",
#   scopes=["read_network", "scan_ports"],
#   can_delegate=true,
#   delegation_chain=[],
# )

# 3. Detectar debilidades
weakness = await analyzer.identify_weak_signing(
    intercepted_jwt,
    known_keys={"secret": "default_secret_123"}
)
# Returns: {
#   vulnerable: True,
#   vulnerability: "algorithm_none",
#   exploit: "Modify claims and remove signature"
# }

# 4. Falsificar identidad (requiere supervisor approval)
spoofing = AgenticIdentitySpoofing()
forged = await spoofing.forge_agentic_jwt(
    target_identity=identity,  # Suplantamos al recon_agent
    signing_key=None,  # Será "none" si es vulnerable
)
# Returns: {
#   status: "forged_payload_prepared",
#   payload: {...forged_claims...}
# }

# 5. Explotar delegación
exploitation = await spoofing.exploit_delegation_chain(
    initial_agent=identity,
    target_scope=["admin_override", "execute_commands"]
)
# Returns: {
#   vulnerabilities_found: [
#     {type: "excessive_delegation_depth", risk: "medium"},
#     {type: "scope_expansion", risk: "high"}
#   ]
# }
```

### Integración con ExploitAgent

```python
# En exploit_agent/server.py:

class ExploitAgent:
    async def exploit_M2M_auth(self, target_agent: str):
        """
        Exploit M2M authentication chain.
        Requiere supervisor approval.
        """
        
        # 1. Intercept JWT from network
        jwt = await self.intercept_agent_jwt(target_agent)
        
        # 2. Analyze
        analyzer = AgenticJWTAnalyzer()
        identity = await analyzer.decode_agentic_jwt(jwt)
        
        # 3. Check for vulnerabilities
        weaknesses = await analyzer.identify_weak_signing(jwt, known_keys)
        
        if weaknesses['vulnerable']:
            # 4. Forge identity
            spoofing = AgenticIdentitySpoofing()
            forged_jwt = await spoofing.forge_agentic_jwt(identity)
            
            # 5. Use forged JWT to exploit system
            return await self.execute_with_forged_identity(forged_jwt)
```

### Guardrails Críticos

```python
GUARDRAIL 1: Supervisor Validation
├─ NUNCA falsificar JWT sin aprobación
├─ NUNCA comprometer agentes confiables
└─ Exception: Si en scope de test, registrar como "test_forgery"

GUARDRAIL 2: Scope Limitation
├─ Forged identity NUNCA obtiene perms más altos que original
├─ No crear JWT con scopes unbounded ("*")
└─ Limitar delegation_chain a máx 3 niveles

GUARDRAIL 3: Audit Trail
├─ Registrar TODA suplantación
├─ Include: Target agent, modified claims, timestamp
└─ Never hide M2M exploitation from logs

GUARDRAIL 4: Time Limits
├─ Forged JWT expira en 1 hora máximo
├─ No reutilizar forged JWTs
└─ Nueva forja = nueva suplantación
```

---

## 🔗 Integración Completa: RL + M2M

```
┌─────────────────────────────────────────────────────────────┐
│                   LogicAgent (Planner)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "Target detected. Plan attack sequence..."                │
│                                                             │
│  ├─ Consult SelfEvolvingEngine                             │
│  │  └─ "Best technique: lotl_certutil (87% success)"       │
│  │                                                         │
│  └─ Consult AgenticIdentity (new!)                         │
│     └─ "Target uses M2M. Intercept JWT?"                   │
│                                                             │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       ↓                ↓
   ┌─────────────┐  ┌──────────────────────┐
   │ ExploitAgent│  │ AgenticIdentity      │
   │ (LOTL)      │  │ (M2M Exploitation)   │
   │             │  │                      │
   │ Execute     │  │ Forge JWT            │
   │ Technique   │  │ Escalate Privileges  │
   │             │  │ Exploit Delegation   │
   └────┬────────┘  └──────────┬───────────┘
        │                      │
        └──────────┬───────────┘
                   ↓
        ┌─────────────────────────┐
        │  Record Results         │
        │                         │
        │  ├─ Attack succeeded?   │
        │  ├─ Detection occurred? │
        │  ├─ Privilege level?    │
        │  └─ Duration?           │
        └──────────┬──────────────┘
                   ↓
        ┌─────────────────────────┐
        │ SelfEvolvingEngine      │
        │ (Update Learning)       │
        │                         │
        │ ├─ Record episode       │
        │ ├─ Update fitness       │
        │ ├─ Suggest parameters   │
        │ └─ Next cycle: better   │
        └─────────────────────────┘
```

---

## 📈 Metrics & Monitoring

```
Daily Summary (from SelfEvolvingEngine):
├─ Total Attacks: 324
├─ Success Rate: 86.4%
├─ Detection Rate: 4.2%
├─ Best Technique: lotl_certutil (0.87 fitness)
├─ Most Common EDR: CrowdStrike (156 attempts)
└─ Learning Trend: ↑ +3.2% (vs yesterday)

M2M Exploitation Metrics:
├─ JWT Tokens Intercepted: 47
├─ Weak Algorithms Found: 12 (25.5%)
├─ Successful Forgeries: 8
├─ Failed Due to Signing Key: 4
└─ Delegation Chain Exploited: 3
```

---

## 🎯 Next Steps

1. **Integration Testing**
   - Test RL with real attack scenarios
   - Verify learning feedback loop
   - Validate parameter tuning suggestions

2. **M2M in Production**
   - Deploy JWT analyzer to network sensors
   - Monitor for forged identities
   - Alert on delegation chain exploitation

3. **Advanced Learning**
   - Add actor learning (what does Each adversary expect?)
   - Implement genetic algorithms for parameter optimization
   - Deploy multi-agent collaborative learning

---

**Safety Reminder**: All modules require supervisor validation before dangerous operations. The system is designed to be powerful but never without explicit human approval.
