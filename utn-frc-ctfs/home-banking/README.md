# Home Banking - UTN-FRC

**Dificultad:** CTF | **Fecha:** 09/2026 | **Sistema:** Web
**Objetivo:** Obtener acceso al Home Banking
**Herramientas:** Chrome DevTools, Burp Suite
**Técnicas:** SQL Injection, Authentication Bypass

## Introducción

La aplicación de Home Banking solicita un PIN para autenticar al usuario. El objetivo del desafío es lograr acceso sin conocer el PIN legítimo.

## Reconocimiento

Inspeccionando el HTML se identifica el campo de autenticación:

```html
<input type="password" name="txtPin" autocomplete="off" placeholder="PIN">
```

El parámetro relevante es `txtPin`. Un PIN arbitrario (`1234`) es rechazado, como era de esperar.

## Análisis de la petición

Con **Chrome DevTools → Network** se captura la petición del formulario, descartando tráfico irrelevante (telemetría de Cloudflare vía `/cdn-cgi/rum`). La petición útil envía:

```text
txtPin=1234
```

## Identificación de la vulnerabilidad

Se prueban entradas para detectar fallas de validación. Al enviar una comilla simple (`1234'`) la aplicación responde de forma distinta a un PIN simplemente incorrecto, sugiriendo que el valor se concatena directamente en una consulta SQL.

Se prueba entonces el payload clásico de bypass:

```text
' OR '1'='1
```

y la aplicación otorga acceso.

Conceptualmente, la consulta vulnerable sería algo como:

```sql
SELECT * FROM usuarios WHERE pin = '$pin';
```

que con el payload queda:

```sql
SELECT * FROM usuarios WHERE pin = '' OR '1'='1';
```

Como `'1'='1'` es siempre verdadero, el `OR` hace que la consulta devuelva resultados sin importar el PIN real.

> Es una representación conceptual; no se confirma la consulta exacta usada por el backend.

## Explotación

Interceptando la petición (Burp Suite o DevTools) se modifica el parámetro:

```text
txtPin=' OR '1'='1
```

Al enviarla, se obtiene acceso al Home Banking sin conocer el PIN legítimo, confirmando el **authentication bypass** vía SQLi.

## Causa raíz

- El backend concatena el input del usuario directamente en la consulta SQL, sin parametrización.
- `type="password"` en HTML solo oculta visualmente el valor; no sanitiza ni protege el contenido enviado al servidor.

## Cadena de explotación
