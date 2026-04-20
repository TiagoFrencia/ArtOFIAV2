# 🔧 GUÍA DE CORRECCIONES TÉCNICAS - RIOCUARTO.GOB.AR

**Objetivo:** Mejorar score de seguridad de 14.3% a +70% en 1 semana  
**Audiencia:** Administradores de Sistemas / DevOps / Webmasters

---

## 1️⃣ IMPLEMENTAR HEADERS DE SEGURIDAD

### Opción A: Nginx

**Archivo:** `/etc/nginx/conf.d/riocuarto.conf` o `/etc/nginx/sites-available/riocuarto.gob.ar`

```nginx
# Security Headers Configuration for riocuarto.gob.ar
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name riocuarto.gob.ar www.riocuarto.gob.ar;

    # ============================================================
    # 1. HSTS (Ya implementado - mantener)
    # ============================================================
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # ============================================================
    # 2. Content Security Policy (CRÍTICO - Agregar)
    # ============================================================
    # Esta es una política RESTRICTIVA por defecto
    # Ajustar según necesidades específicas del sitio
    add_header Content-Security-Policy "
        default-src 'self';
        script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com;
        style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com fonts.googleapis.com;
        img-src 'self' data: https: cdn-contenidos.riocuarto.gob.ar;
        font-src 'self' cdnjs.cloudflare.com fonts.gstatic.com;
        connect-src 'self' api.riocuarto.gob.ar;
        frame-ancestors 'self';
        base-uri 'self';
        form-action 'self';
        upgrade-insecure-requests;
    " always;

    # ============================================================
    # 3. X-Frame-Options (Clickjacking Protection)
    # ============================================================
    add_header X-Frame-Options "SAMEORIGIN" always;

    # ============================================================
    # 4. X-Content-Type-Options (MIME Sniffing Protection)
    # ============================================================
    add_header X-Content-Type-Options "nosniff" always;

    # ============================================================
    # 5. X-XSS-Protection (XSS Protection - Navegadores antiguos)
    # ============================================================
    add_header X-XSS-Protection "1; mode=block" always;

    # ============================================================
    # 6. Referrer-Policy (Control de Referrer)
    # ============================================================
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # ============================================================
    # 7. Permissions-Policy (Feature Policy - Acceso a APIs)
    # ============================================================
    add_header Permissions-Policy "
        geolocation=(),
        microphone=(),
        camera=(),
        payment=(),
        usb=(),
        magnetometer=(),
        gyroscope=(),
        accelerometer=()
    " always;

    # ============================================================
    # Headers Adicionales Recomendados
    # ============================================================
    
    # No permitir uso en iframes
    add_header X-Content-Type-Options "nosniff" always;
    
    # DNS Prefetch Control
    add_header X-DNS-Prefetch-Control "off" always;
    
    # Evitar MIME type sniffing
    add_header X-Content-Type-Options "nosniff" always;

    # ============================================================
    # Resto de configuración nginx
    # ============================================================
    ssl_certificate /etc/ssl/certs/riocuarto.crt;
    ssl_certificate_key /etc/ssl/private/riocuarto.key;
    
    location / {
        proxy_pass http://localhost:3000;  # Si usa Next.js
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Aplicar cambios:**
```bash
# Validar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx

# Verificar cambios
curl -I https://riocuarto.gob.ar | grep -i "strict\|csp\|frame\|content-type\|xss\|referrer\|permissions"
```

### Opción B: Apache (.htaccess)

**Archivo:** `/.htaccess` o `/etc/apache2/conf-available/riocuarto-security.conf`

```apache
# Security Headers for Apache
# Habilitar mod_headers: a2enmod headers

<IfModule mod_headers.c>
    # 1. HSTS
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
    
    # 2. Content Security Policy
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: cdn-contenidos.riocuarto.gob.ar; font-src 'self' cdnjs.cloudflare.com; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self';"
    
    # 3. X-Frame-Options
    Header always set X-Frame-Options "SAMEORIGIN"
    
    # 4. X-Content-Type-Options
    Header always set X-Content-Type-Options "nosniff"
    
    # 5. X-XSS-Protection
    Header always set X-XSS-Protection "1; mode=block"
    
    # 6. Referrer-Policy
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    
    # 7. Permissions-Policy
    Header always set Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()"
</IfModule>
```

**Aplicar cambios:**
```bash
# Validar configuración
sudo apache2ctl configtest

# Recargar Apache
sudo systemctl reload apache2
```

### Opción C: Node.js / Express

**Archivo:** `server.js` o `middleware/security.js`

```javascript
// Instalación: npm install helmet
const helmet = require('helmet');
const express = require('express');
const app = express();

// Aplicar Helmet con configuración personalizada
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com"],
            styleSrc: ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com"],
            imgSrc: ["'self'", "data:", "https:", "cdn-contenidos.riocuarto.gob.ar"],
            fontSrc: ["'self'", "cdnjs.cloudflare.com"],
            connectSrc: ["'self'"],
            frameAncestors: ["'self'"],
            baseUri: ["'self'"],
            formAction: ["'self'"],
            upgradeInsecureRequests: [],
        },
    },
    hsts: {
        maxAge: 63072000,
        includeSubDomains: true,
        preload: true,
    },
    frameguard: { action: 'sameorigin' },
    noSniff: true,
    xssFilter: true,
    referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
    permissionsPolicy: {
        geolocation: [],
        microphone: [],
        camera: [],
        payment: [],
    },
}));

app.listen(3000, () => console.log('Server running on port 3000'));
```

---

## 2️⃣ FILTRAR EMAILS DEL SITIO

### Opción A: Remover completamente

**Método 1: Buscar y reemplazar en HTML**

```bash
# Backup del sitio
cp -r /var/www/riocuarto-gob-ar /var/www/riocuarto-gob-ar.backup

# Remover patrón de emails
find /var/www/riocuarto-gob-ar -name "*.html" -exec sed -i 's/[a-zA-Z0-9._%+-]*@riocuarto\.[a-z]*\.[a-z]*/contacto@riocuarto.gob.ar/g' {} \;

# Verificar cambios
grep -r "@riocuarto" /var/www/riocuarto-gob-ar | head -20
```

**Método 2: Si usa CMS (WordPress/Drupal)**

```php
// WordPress: Agregar a functions.php
function hide_emails($content) {
    $pattern = '/[a-zA-Z0-9._%+-]+@riocuarto\.[a-z]*\.[a-z]*/';
    $replacement = 'contacto@riocuarto.gob.ar';
    return preg_replace($pattern, $replacement, $content);
}
add_filter('the_content', 'hide_emails');
add_filter('the_excerpt', 'hide_emails');
```

### Opción B: Crear página de contactos filtrada

**Archivo:** `/contact-us.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <title>Contactos - Gobierno de Río Cuarto</title>
</head>
<body>
    <h1>Centro de Contactos</h1>
    
    <section>
        <h2>Para Consultas Generales</h2>
        <p>
            <strong>Email:</strong> contacto@riocuarto.gob.ar<br>
            <strong>Teléfono:</strong> +54-358-4XXXXXX<br>
            <strong>Horario:</strong> Lunes a Viernes 8:00 - 17:00
        </p>
    </section>

    <section>
        <h2>Por Departamento</h2>
        <p>
            Si desea contactarse con un departamento específico, 
            por favor use el formulario de contacto indicando el departamento 
            y le redireccionaremos apropiadamente.
        </p>
        <form>
            <label>Departamento:</label>
            <select>
                <option>Seleccionar...</option>
                <option value="protocolo">Protocolo y Ceremonial</option>
                <option value="presupuesto">Presupuesto Participativo</option>
                <option value="comunicacion">Comunicación</option>
                <option value="desarrollo">Desarrollo Estratégico</option>
            </select>
            
            <label>Mensaje:</label>
            <textarea></textarea>
            
            <button type="submit">Enviar</button>
        </form>
    </section>
</body>
</html>
```

### Opción C: Actualizar robots.txt

**Archivo:** `/robots.txt`

```
User-agent: *
Disallow: /admin/
Disallow: /private/
Disallow: /wp-admin/
Disallow: /wp-login.php

# Permitir solo páginas públicas
Allow: /
Allow: /contacto/
Allow: /tramites/
Allow: /noticias/

# Proteger información sensible
Disallow: /*?*email*
Disallow: /*?*contact*
```

---

## 3️⃣ IMPLEMENTAR SUBRESOURCE INTEGRITY (SRI)

### Paso 1: Obtener Hash SRI

**Para Font Awesome 6.5.2:**

```bash
# Opción A: Usar sitio SRI
# https://www.srihash.org/

# Opción B: Generar localmente
curl -s https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/js/all.min.js | \
  openssl dgst -sha384 -binary | \
  openssl enc -base64 -A
```

**Resultado esperado:**
```
sha384-[LARGO STRING DE 88 CARACTERES]
```

### Paso 2: Actualizar HTML

**Antes:**
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/js/all.min.js"></script>
```

**Después:**
```html
<script 
  src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/js/all.min.js"
  integrity="sha384-L129pY6N/HXnvSn/6LzGz52JsKlXfHmRjcvHj5U2PBKuKUBCaJoTEW+YQKs7w7eFl"
  crossorigin="anonymous">
</script>
```

### Paso 3: Aplicar a todos los scripts externos

```html
<!-- Cloudflare -->
<script 
  src="https://cdnjs.cloudflare.com/ajax/libs/..."
  integrity="sha384-[HASH]"
  crossorigin="anonymous">
</script>

<!-- Google Fonts -->
<link 
  href="https://fonts.googleapis.com/..."
  rel="stylesheet"
  integrity="sha384-[HASH]"
  crossorigin="anonymous">
```

---

## 4️⃣ VERIFICAR IMPLEMENTACIÓN

### Script de Validación

```bash
#!/bin/bash
# verify_security.sh

DOMAIN="riocuarto.gob.ar"
echo "🔍 Verificando headers de seguridad para $DOMAIN..."

# Array de headers esperados
HEADERS=("Strict-Transport-Security" "Content-Security-Policy" "X-Frame-Options" \
         "X-Content-Type-Options" "X-XSS-Protection" "Referrer-Policy" "Permissions-Policy")

RESPONSE=$(curl -s -I https://$DOMAIN)

for HEADER in "${HEADERS[@]}"; do
    if echo "$RESPONSE" | grep -i "$HEADER" > /dev/null; then
        echo "✅ $HEADER: PRESENTE"
    else
        echo "❌ $HEADER: FALTA"
    fi
done

echo ""
echo "📊 Score de Seguridad Esperado:"
COUNT=$(echo "$RESPONSE" | grep -ci -E "(Strict-Transport|Content-Security|X-Frame|X-Content-Type|X-XSS|Referrer-Policy|Permissions-Policy)")
SCORE=$((COUNT * 100 / 7))
echo "   Antes: 14.3%"
echo "   Después: $SCORE% (Expected: ~85-100%)"
```

**Ejecución:**
```bash
chmod +x verify_security.sh
./verify_security.sh
```

### Verificación Online

1. **SSL Labs:**
   - Ir a: https://www.ssllabs.com/ssltest/analyze.html?d=riocuarto.gob.ar
   - Esperar análisis (5-10 min)
   - Score esperado: A+ o A

2. **Security Headers:**
   - Ir a: https://securityheaders.com/?q=riocuarto.gob.ar
   - Score esperado: A o B (antes era F)

3. **Observatory Mozilla:**
   - Ir a: https://observatory.mozilla.org/analyze/riocuarto.gob.ar
   - Score esperado: 800+ (antes era <200)

---

## 5️⃣ IMPLEMENTACIÓN PASO A PASO (CHECKLIST)

### Día 1: Preparación
- [ ] Hacer backup del sitio actual
- [ ] Revisar configuración actual (nginx/apache)
- [ ] Documentar cambios a realizar
- [ ] Notificar a equipo de posibles cambios

### Día 2: Headers de Seguridad
- [ ] Editar archivo de configuración (nginx.conf o .htaccess)
- [ ] Agregar todos los 7 headers
- [ ] Validar sintaxis
- [ ] Probar en servidor de staging
- [ ] Recargar servidor
- [ ] Verificar con `curl -I`

### Día 3: Limpieza de Datos
- [ ] Hacer backup de archivos HTML
- [ ] Ejecutar script para remover emails
- [ ] Verificar resultado
- [ ] Actualizar página de contactos
- [ ] Probar enlaces

### Día 4: Subresource Integrity
- [ ] Generar hashes SRI para cada script externo
- [ ] Actualizar etiquetas `<script>`
- [ ] Actualizar etiquetas `<link>`
- [ ] Probar en navegador (verificar console)
- [ ] Confirmar que no hay errores CORS

### Día 5: Validación
- [ ] Ejecutar script de verificación local
- [ ] Validar en SSL Labs
- [ ] Validar en Security Headers
- [ ] Validar en Observatory
- [ ] Documentar score final
- [ ] Presentar resultados

---

## 6️⃣ TROUBLESHOOTING

### Problema: CSP bloqueando scripts

**Síntoma:** Console muestra `Refused to load the script`

**Solución:**
```
1. Revisar la URL exacta del script bloqueado
2. Agregar el dominio a la directiva script-src en CSP
3. Usar 'unsafe-inline' solo como última opción
4. Preferir usar nonces en lugar de 'unsafe-inline'
```

**Ejemplo:**
```nginx
# Antes (bloqueará scripts inline)
script-src 'self' cdnjs.cloudflare.com;

# Después (permitirá scripts inline con nonce)
script-src 'self' cdnjs.cloudflare.com 'nonce-random123';
```

### Problema: SRI causando errores CORS

**Síntoma:** Error en console: `SRI hash validation failed`

**Solución:**
```
1. Verificar que el hash es correcto
2. Confirmar que el archivo no cambió en CDN
3. Regenerar hash
4. Asegurar crossorigin="anonymous"
```

### Problema: Redirects o redirecciones no funcionan

**Síntoma:** Algunos enlaces externos no abren

**Solución:**
```
1. Revisar Referrer-Policy (podría bloquear información)
2. Ajustar a 'no-referrer' si es necesario
3. Verificar frame-ancestors si está dentro de iframes
```

---

## 7️⃣ MONITOREO CONTINUO

### Script de Monitoreo Automático

```bash
#!/bin/bash
# monitor_security.sh - Ejecutar cada día con cron

DOMAIN="riocuarto.gob.ar"
LOG_FILE="/var/log/security_monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Verificando $DOMAIN" >> $LOG_FILE

# Verificar cada header
curl -s -I https://$DOMAIN | grep -E "(Strict-Transport|Content-Security|X-Frame|X-Content-Type|X-XSS|Referrer-Policy|Permissions-Policy)" >> $LOG_FILE

echo "---" >> $LOG_FILE
```

**Configurar Cron:**
```bash
# Ejecutar diariamente a las 9 AM
0 9 * * * /opt/security_scripts/monitor_security.sh

# Verificar logs
tail -f /var/log/security_monitor.log
```

---

## 📞 SOPORTE

Si encuentra problemas durante la implementación:

1. **Revisar logs del servidor:**
   ```bash
   # Nginx
   tail -f /var/log/nginx/error.log
   
   # Apache
   tail -f /var/log/apache2/error.log
   ```

2. **Probar localmente:**
   ```bash
   # Curl detallado
   curl -v -I https://riocuarto.gob.ar
   
   # Wget
   wget --debug https://riocuarto.gob.ar
   ```

3. **Consultar documentación:**
   - OWASP: https://owasp.org/
   - MDN: https://developer.mozilla.org/

---

**Última actualización:** 20 de Abril de 2026  
**Generado por:** ArtOfIAV2 v2.0

