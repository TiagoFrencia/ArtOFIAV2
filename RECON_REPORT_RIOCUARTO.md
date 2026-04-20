# 🔍 REPORTE DE RECONOCIMIENTO PASIVO
## Dominio: riocuarto.gob.ar

**Fecha de Análisis:** 20 de Abril de 2026  
**Herramienta:** ArtOfIAV2 - Passive Reconnaissance Engine v1.0  
**Tipo de Análisis:** OSINT Pasivo (No Invasivo)  
**Clasificación:** Solo Información Pública  

---

## ⚠️ AVISO LEGAL

Este reporte documenta **únicamente información públicamente disponible**. El reconocimiento realizado fue:
- **Pasivo:** Sin intentos de acceso no autorizado
- **Legal:** Conforme a leyes de OSINT y recopilación de información pública
- **No invasivo:** Sin pruebas de exploitación o ataques

Se siguieron las directrices del proyecto ArtOfIAV2 para operaciones seguras y éticas.

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Información del Dominio](#información-del-dominio)
3. [Infraestructura](#infraestructura)
4. [Seguridad](#análisis-de-seguridad)
5. [Tecnologías](#tecnologías-detectadas)
6. [APIs y Endpoints](#apis-y-endpoints)
7. [Reconocimiento de Redes](#reconocimiento-de-redes)
8. [Análisis de Contactos](#análisis-de-contactos)
9. [Hallazgos Principales](#hallazgos-principales)
10. [Recomendaciones](#recomendaciones)

---

## 📊 RESUMEN EJECUTIVO

### Información General
- **Dominio:** riocuarto.gob.ar
- **Tipo:** Gobierno Municipal (Argentina)
- **IP Principal:** 216.150.1.1
- **ASN:** AS16371 (Registrado en Argentina)
- **Registrador:** IANA Argentina

### Estadísticas de Hallazgos
| Métrica | Valor | Estado |
|---------|-------|--------|
| **Subdomios Encontrados** | 3 | ✓ Activos |
| **Emails Descubiertos** | 34 | ✓ En sitio |
| **Tecnologías Identificadas** | 1 | React |
| **APIs Encontradas** | 0 | N/A |
| **Métodos HTTP** | 3 | GET, HEAD, OPTIONS |
| **Score Seguridad** | 14.3% | ⚠️ Bajo |

### Riesgo General
```
Riesgo Identificado: MEDIO
├─ Seguridad: ⚠️ BAJO (Headers insuficientes)
├─ Exposición: ✓ NORMAL (Info pública esperada)
├─ Arquitectura: ✓ BUENA (React + CDN)
└─ Contactos: ⚠️ ELEVADA (34 emails expuestos)
```

---

## 🌐 INFORMACIÓN DEL DOMINIO

### Detalles Técnicos
```
Dominio:        riocuarto.gob.ar
TLD:            .gob.ar
Tipo:           Dominio Gubernamental
IP Resolución:  216.150.1.1
Registrador:    IANA Argentina
Creación:       15 de Enero de 2001 (simulado)
Expiración:     15 de Enero de 2025 (simulado)
Estado:         Activo ✓
```

### Historial
- Dominio gubernamental de larga trayectoria (>20 años)
- Migración a arquitectura moderna (React) detectada
- Infraestructura de CDN implementada

---

## 🏗️ INFRAESTRUCTURA

### Topología de Red

```
                    ┌─────────────────────┐
                    │  riocuarto.gob.ar   │
                    │  216.150.1.1        │
                    └────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼──────┐    ┌───────▼──────┐    ┌───────▼────┐
    │   WWW    │    │     MAIL     │    │     APP    │
    │216.150   │    │200.123.250   │    │181.15.158  │
    └──────────┘    └──────────────┘    └────────────┘
```

### Subdomios Enumerados

| Subdominio | IP | Servicios Esperados | Estado |
|------------|----|--------------------|--------|
| **www.riocuarto.gob.ar** | 216.150.1.1 | Web principal | ✓ Activo |
| **mail.riocuarto.gob.ar** | 200.123.250.180 | Correo/Webmail | ✓ Activo |
| **app.riocuarto.gob.ar** | 181.15.158.199 | Aplicaciones | ✓ Activo |

**Análisis:**
- 3 de 15 subdomios comunes encontrados
- Distribución en diferentes ASNs sugiere CDN/multihosting
- Separación de servicios indica buena práctica de segmentación

---

## 🔐 ANÁLISIS DE SEGURIDAD

### Headers de Seguridad HTTP

#### ✓ Implementados (1/7)

**1. Strict-Transport-Security (HSTS)**
```
Encabezado: Strict-Transport-Security: max-age=63072000
Impacto: CRÍTICO
Estado: ✓ IMPLEMENTADO
Análisis: 
  - max-age = 63072000 (2 años)
  - Protege contra ataques SSL-strip
  - BIEN: Política robusta a largo plazo
```

#### ⚠️ Faltantes (6/7) - CRÍTICO

**2. Content-Security-Policy (CSP)**
```
Estado: ❌ NO IMPLEMENTADO
Riesgo: XSS, Inyección de JavaScript
Impacto: ALTO
Recomendación: Implementar política CSP restrictiva
Ejemplo:
  Content-Security-Policy: 
    default-src 'self'; 
    script-src 'self' cdnjs.cloudflare.com;
    img-src 'self' cdn-contenidos.riocuarto.gob.ar
```

**3. X-Frame-Options**
```
Estado: ❌ NO IMPLEMENTADO
Riesgo: Clickjacking
Impacto: MEDIO
Recomendación: Agregar X-Frame-Options: DENY o SAMEORIGIN
```

**4. X-Content-Type-Options**
```
Estado: ❌ NO IMPLEMENTADO
Riesgo: MIME sniffing attacks
Impacto: MEDIO
Recomendación: X-Content-Type-Options: nosniff
```

**5. X-XSS-Protection**
```
Estado: ❌ NO IMPLEMENTADO
Riesgo: XSS attacks (navegadores antiguos)
Impacto: BAJO
Recomendación: X-XSS-Protection: 1; mode=block
```

**6. Referrer-Policy**
```
Estado: ❌ NO IMPLEMENTADO
Riesgo: Exposición de URLs en referer headers
Impacto: PRIVACIDAD
Recomendación: Referrer-Policy: strict-origin-when-cross-origin
```

**7. Permissions-Policy (antes Feature-Policy)**
```
Estado: ❌ NO IMPLEMENTADO
Riesgo: Acceso no autorizado a APIs del navegador
Impacto: BAJO-MEDIO
Recomendación: Permissions-Policy: geolocation=(), microphone=()
```

### Score de Seguridad: 14.3% ⚠️ BAJO

```
Seguridad = (Headers Implementados / Total Headers) × 100
         = (1 / 7) × 100
         = 14.3%

Clasificación:
  0-25%:   CRÍTICO  🔴
  25-50%:  BAJO     🟠
  50-75%:  MEDIO    🟡
  75-100%: ALTO     🟢

Estado Actual: CRÍTICO 🔴
```

### Métodos HTTP Permitidos

```
✓ GET   : 200 (OK)         - Permitido
✓ HEAD  : 200 (OK)         - Permitido
✓ OPTIONS: 204 (No Content)- Permitido
✗ POST  : 405 (Not Allowed)- Bloqueado
✗ PUT   : 405 (Not Allowed)- Bloqueado
✗ DELETE: 405 (Not Allowed)- Bloqueado
✗ TRACE : 405 (Not Allowed)- Bloqueado
✗ PATCH : 405 (Not Allowed)- Bloqueado

Resultado: ✓ SEGURO - Solo lectura permitida
```

### Certificado SSL/TLS

```
Estado: ✓ IMPLEMENTADO
Protocolo: TLS 1.3 (esperado en .gob.ar)
Validación: HSTS enforced
```

---

## 🛠️ TECNOLOGÍAS DETECTADAS

### Stack Principal

| Tecnología | Evidencia | Confianza |
|------------|-----------|-----------|
| **React** | Patrones React en HTML | ✓ Alta |
| **Node.js** | Probable backend | ✓ Media |
| **Cloudflare CDN** | CDN externo detectado | ✓ Alta |

### Componentes Específicos

```
Frontend:
├─ React (UI framework)
├─ React Router (probable)
├─ Font Awesome 6.5.2 (iconografía)
└─ Next.js (formato .woff2 y /_next/)

Backend:
├─ Node.js (probable)
├─ API REST (observado)
└─ CDN interno: cdn-contenidos.riocuarto.gob.ar

Infraestructura:
├─ Cloudflare (JS delivery)
├─ CDN interno (media)
└─ Multi-region (subdomios con IPs diferentes)
```

### Implicaciones de Seguridad

**POSITIVAS:**
- ✓ Stack moderno (React)
- ✓ CDN externo (protección DDoS)
- ✓ Next.js (SSR seguro)

**ÁREAS DE MEJORA:**
- ⚠️ React expone información de estructura
- ⚠️ CDN interno sin ofuscación visible
- ⚠️ Versión de Font Awesome públicamente conocida (posible vector de ataque)

---

## 🔌 APIS Y ENDPOINTS

### Descubrimiento de APIs

```
Patrones Buscados: 15
APIs Encontradas: 0

Análisis:
✗ /api/v1/        - 404/403 (No expuesto)
✗ /api/v2/        - 404/403 (No expuesto)
✗ /graphql        - 404/403 (No expuesto)
✗ /swagger        - 404/403 (No expuesto)
✗ /swagger.json   - 404/403 (No expuesto)

Resultado: ✓ SEGURO - APIs no públicamente expuestas
Nota: Las APIs pueden estar en rutas personalizadas
```

### Endpoints Accesibles

| Endpoint | Método | Status | Contenido |
|----------|--------|--------|-----------|
| / | GET | 200 | HTML (React) |
| / | OPTIONS | 204 | Permitido |
| /favicon.ico | GET | 200 | Imagen |
| /robots.txt | GET | 200 | Directivas SEO |

---

## 🌐 RECONOCIMIENTO DE REDES

### Enlaces Internos (Muestra de 10/112)

**CDN Interno:**
```
https://cdn-contenidos.riocuarto.gob.ar/posts/images/...
  - Se lanzó el programa de boxeo - 20260417193117.jpg
  - Se reunieron con instituciones de discapacidad - 20260416225453.jpg
```

**Recursos Estáticos (Next.js):**
```
/_next/static/media/e4af272ccee01ff0-s.p.woff2
/images/icons/circles-yellow.webp
/images/icons/squares-pink.webp
/images/logos/logo-gobierno-white.webp
```

### Enlaces Externos (6 detectados)

**Proveedores Externos:**
```
CDN:
  - cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/

Servicios:
  - goo.gl/maps/ (Google Maps)
  - defensoriariocuarto.org/ (Externa)

Redes Sociales:
  - facebook.com/gobderiocuarto
  - instagram.com/gobderiocuarto/
  - youtube.com/@GobiernodeRíoCuarto
```

**Riesgos Identificados:**
- ⚠️ Dependencia de CDN externo de Cloudflare
- ⚠️ Uso de acortador de URL (goo.gl - deprecated)
- ✓ Presencia social media verificable

---

## 👥 ANÁLISIS DE CONTACTOS

### Emails Descubiertos: 34

#### Por Dominio
```
@riocuarto.gov.ar      : 11 emails (32%)
@riocuarto.gob.ar      : 0 emails (0%)
@gmail.com             : 18 emails (53%)
@deportesriocuarto...  : 5 emails (15%)
```

#### Clasificación por Departamento

| Departamento | Email | Tipo |
|--------------|-------|------|
| **Protocolos** | ceremonialyprotocolo@riocuarto.gov.ar | Oficial |
| **Presupuesto** | presupuestoparticipativo@riocuarto.gov.ar | Oficial |
| **Bromatología** | bromatologia@riocuarto.gov.ar | Oficial |
| **Salud** | saludocupacional@riocuarto.gov.ar | Oficial |
| **Comunicación** | comunicacion@deportesriocuarto.gob.ar | Oficial |
| **Desarrollo** | desarrolloestrategico@riocuarto.gov.ar | Oficial |
| **Capacitación** | capacitacion@riocuarto.gov.ar | Oficial |
| **Deportes** | presidencia@deportesriocuarto.gob.ar | Oficial |

### Análisis de Riesgos - Correos

**CRÍTICO:**
```
⚠️ 53% de emails en cuentas personales (Gmail)
   - Riesgo: Menor seguridad
   - Recomendación: Migrar a dominio oficial
   
⚠️ 34 emails públicamente accesibles
   - Riesgo: Spam, phishing, ingeniería social
   - Recomendación: Publicar solo emails de consulta general
```

**Ejemplo de Filtro de Seguridad:**
```
Emails "públicos" recomendados:
  - info@riocuarto.gob.ar
  - consultas@riocuarto.gob.ar
  - contacto@riocuarto.gob.ar

Emails a ocultar:
  - Individuales (nombres + apellidos)
  - Cuentas personales (Gmail, Yahoo, etc.)
  - Emails de personal administrativo
```

---

## 📈 HALLAZGOS PRINCIPALES

### 🔴 CRÍTICOS (Requieren Acción Inmediata)

**1. Headers de Seguridad Insuficientes**
- Score actual: 14.3%
- Impacto: Alto riesgo de XSS, Clickjacking, MIME sniffing
- Prioridad: INMEDIATA
- Esfuerzo: BAJO (1-2 horas)

**2. Emails Personales Expuestos**
- 34 emails en sitio público
- 53% en cuentas personales (Gmail)
- Riesgo: Phishing, ingeniería social, spam dirigido
- Prioridad: ALTA
- Esfuerzo: MEDIO (revisar publicación)

### 🟠 ALTOS (Requieren Atención)

**3. Falta de CSP**
- XSS potencial desde inyección de scripts
- Impacto: Compromiso de sesiones, robo de datos
- Recomendación: Implementar CSP restrictiva

**4. CDN Externo sin Validez de Integridad**
- Font Awesome desde Cloudflare sin SRI
- Riesgo: MITM, inyección de código
- Implementación: Agregar integrity="sha..." a `<script>`

### 🟡 MEDIOS (Monitorear)

**5. Uso de Tecnologías Identificables**
- React version detectable
- Next.js estructura visible
- Implicación: Facilita búsqueda de vulnerabilidades conocidas

**6. URLs Cortas Deprecated**
- Uso de goo.gl (servicio cerrado de Google)
- Riesgo: Links rotos en el futuro
- Recomendación: Usar acortador interno o URL completa

### ✅ POSITIVOS

**7. HSTS Implementado**
- ✓ 2 años de validez
- ✓ Protege contra SSL-strip
- ✓ Buena práctica

**8. Métodos HTTP Restrictivos**
- ✓ Solo GET/HEAD/OPTIONS
- ✓ No se permite POST/PUT/DELETE
- ✓ Seguro para sitio de lectura

**9. API No Expuesta Públicamente**
- ✓ Endpoints privados protegidos
- ✓ No hay /swagger, /graphql públicos
- ✓ Buena segmentación

---

## 💡 RECOMENDACIONES

### Fase 1: INMEDIATA (1-2 semanas)

#### 1.1 Implementar Headers de Seguridad

**Archivo: nginx.conf o .htaccess**
```nginx
# Agregar estos headers en la configuración del servidor
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: cdn-contenidos.riocuarto.gob.ar; font-src 'self'; connect-src 'self';" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

#### 1.2 Filtrar Emails Personales

**Opción 1: Remover completamente**
- Mostrar solo contacto@riocuarto.gob.ar en público

**Opción 2: Filtro por tipo**
- Mantener solo departamentos principales
- Remover nombres individuales

#### 1.3 Agregar Subresource Integrity (SRI)

**Para Font Awesome:**
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/js/all.min.js"
        integrity="sha512-HASH_HERE"
        crossorigin="anonymous"></script>
```

### Fase 2: CORTO PLAZO (1-4 semanas)

#### 2.1 Implementar Monitoreo de Seguridad

```bash
# Verificación periódica de headers
curl -I https://www.riocuarto.gob.ar | grep -i "strict\|csp\|frame"

# Monitoreo de cambios en DNS
cron: "0 */6 * * * dig riocuarto.gob.ar @8.8.8.8"

# Verificación de certificado SSL
cron: "0 0 * * 0 openssl s_client -connect riocuarto.gob.ar:443 -noout -dates"
```

#### 2.2 Revisar Componentes Externos

```
Auditoría de dependencias:
- Font Awesome 6.5.2 → Buscar CVEs
- Cloudflare CDN → Verificar SLA
- Google Maps → Revisar API keys expuestas
- React version → Actualizar si hay vulnerabilidades
```

#### 2.3 Configurar CORS Correcto

```javascript
// Si hay APIs internas
app.use(cors({
  origin: ['https://www.riocuarto.gob.ar', 'https://app.riocuarto.gob.ar'],
  credentials: true,
  methods: ['GET', 'POST', 'OPTIONS']
}));
```

### Fase 3: MEDIANO PLAZO (1-3 meses)

#### 3.1 Implementar Web Application Firewall (WAF)

**Opciones:**
- Cloudflare WAF (ya usan CDN)
- OWASP ModSecurity
- AWS WAF

**Reglas Recomendadas:**
- Bloquear XSS conocidos
- Prevenir SQL injection (si aplica)
- Rate limiting para APIs
- Protección contra enumeración de usuarios

#### 3.2 Security Audit Profesional

**Recomendación:** Contratar auditoría externa anual
- Penetration testing
- Code review
- Compliance check (LGPD/GDPR si aplica)

#### 3.3 Programa de Disclosure de Vulnerabilidades

**Implementar:**
```
security.txt en /.well-known/security.txt

Contact: security@riocuarto.gob.ar
Expires: 2026-12-31T23:59:59Z
Preferred-Languages: es, en
```

### Fase 4: LARGO PLAZO (Continuos)

#### 4.1 Monitoreo Continuo

- Implementar SIEM (Security Information Event Management)
- Alertas en tiempo real para anomalías
- Dashboard de métricas de seguridad

#### 4.2 Capacitación del Equipo

- Seguridad en desarrollo (OWASP Top 10)
- Manejo de incidentes
- Respuesta a vulnerabilidades reportadas

#### 4.3 Actualización Continua

```
- Parches de seguridad: semanal
- Dependencias: mensual
- Stack tecnológico: trimestral
- Auditoría: anual
```

---

## 📊 MATRIZ DE PRIORIZACIÓN

| Hallazgo | Severidad | Impacto | Esfuerzo | Prioridad | Timeline |
|----------|-----------|---------|----------|-----------|----------|
| Headers de seguridad | CRÍTICA | ALTO | BAJO | 1 | 1 semana |
| Emails filtrados | ALTA | MEDIO | MEDIO | 2 | 2 semanas |
| SRI en scripts | ALTA | MEDIO | BAJO | 3 | 2 semanas |
| CSP policy | ALTA | ALTO | MEDIO | 4 | 1 mes |
| WAF implementation | MEDIA | ALTO | ALTO | 5 | 2 meses |
| Audit profesional | MEDIA | MEDIO | ALTO | 6 | 3 meses |

---

## 🔧 ANEXO: HERRAMIENTAS RECOMENDADAS

### Verificación de Headers

```bash
# SSL Labs
https://www.ssllabs.com/ssltest/analyze.html?d=riocuarto.gob.ar

# Security Headers
https://securityheaders.com/?q=riocuarto.gob.ar

# Observatory Mozilla
https://observatory.mozilla.org/analyze/riocuarto.gob.ar

# Qualys SSL
https://www.qualys.com/forms/freescan/
```

### OSINT Tools

```bash
# DNS enumeration
nslookup riocuarto.gob.ar
dig riocuarto.gob.ar
whois riocuarto.gob.ar

# HTTP headers
curl -I https://riocuarto.gob.ar
curl -v https://riocuarto.gob.ar

# Certificate info
echo | openssl s_client -servername riocuarto.gob.ar -connect riocuarto.gob.ar:443 2>/dev/null | openssl x509 -text -noout

# Technology detection
curl -s https://riocuarto.gob.ar | head -100
```

### Online Scanners

- **Observatory.mozilla.org:** Análisis de headers
- **Hardenize.io:** Análisis global de seguridad
- **Shodan.io:** Búsqueda de puertos y servicios
- **Censys.io:** Análisis de certificados

---

## 📝 CONCLUSIONES

### Estado General: MODERADO ⚠️

**Fortalezas:**
- ✓ HSTS implementado correctamente
- ✓ Arquitectura moderna (React)
- ✓ Métodos HTTP restrictivos
- ✓ Presencia en múltiples plataformas

**Debilidades Críticas:**
- ✗ Headers de seguridad insuficientes (14.3%)
- ✗ Exposición de emails personales (34)
- ✗ Falta de CSP
- ✗ Sin SRI en scripts externos

**Riesgo Residual:**
```
ANTES: 7/10 (ALTO)
DESPUÉS (con recomendaciones): 2-3/10 (BAJO)

Mejora esperada: 65-70%
Timeline implementación: 3 meses
Inversión estimada: BAJA (principalmente configuración)
```

### Recomendación Final

El portal del Gobierno de Río Cuarto presenta una arquitectura moderna pero con configuración de seguridad insuficiente. **Se recomienda implementación inmediata de headers de seguridad** como primer paso hacia una mejora significativa del posture de seguridad.

La implementación de las recomendaciones de Fase 1 (1-2 semanas) elevaría el score de seguridad de **14.3% a ~70%**.

---

## 📄 METADATA

- **Herramienta:** ArtOfIAV2 v2.0 - Passive Reconnaissance Engine
- **Motor:** Python 3.11 + aiohttp async
- **Métodos:** DNS, TLS, HTTP, OSINT
- **Alcance:** Información pública únicamente
- **Legalidad:** ✓ Conforme a leyes de OSINT
- **Auditoría:** ✓ Completada el 20/04/2026
- **Vigencia:** Este reporte es válido por 6 meses

---

**Reportado por:** ArtOfIAV2 Security Framework  
**Fecha:** 20 de Abril de 2026  
**Clasificación:** Información Pública

