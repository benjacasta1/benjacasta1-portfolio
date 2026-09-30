# Home Banking - SoftwareSeguro

**Dificultad:** CTF  
**Fecha:** 09/2026  
**Sistema:** Web  
**Objetivo:** Obtener acceso al Home Banking  
**Acceso inicial:** Análisis de formulario + manipulación del parámetro PIN + SQL Injection  

## Herramientas

`Chrome DevTools` `Burp Suite`

## Técnicas

`Web Enumeration` `HTTP Request Analysis` `Parameter Manipulation` `SQL Injection` `Authentication Bypass`

## Introducción

El desafío consiste en acceder a una aplicación de Home Banking que solicita un PIN para autenticar al usuario. El objetivo es conseguir acceso al sistema sin conocer el PIN legítimo.

## Reconocimiento

Al acceder a la aplicación se observa un formulario de autenticación. Mediante la inspección del HTML se identifica el campo:

```html
<input type="password" name="txtPin" autocomplete="off" placeholder="PIN">
```

El atributo `name="txtPin"` identifica el parámetro utilizado para enviar el PIN al servidor. Se prueba inicialmente un PIN arbitrario (`1234`), y la aplicación no permite el acceso — comportamiento esperado.

## Análisis de la petición

Con **Chrome DevTools → Network** se analiza la comunicación generada al enviar el formulario. Durante el reconocimiento aparecen peticiones automáticas de Cloudflare (`/cdn-cgi/rum`), correspondientes a telemetría y ajenas a la validación del PIN; se descartan.

La petición relevante corresponde al envío del formulario de autenticación, con el parámetro:

```text
txtPin=1234
```

## Identificación de la vulnerabilidad

Se prueban distintas entradas sobre el parámetro `txtPin` para detectar fallas de validación. Al enviar una comilla simple (`1234'`) la aplicación responde de forma distinta a la de un PIN simplemente incorrecto, lo cual sugiere que el valor se concatena directamente en una consulta SQL sin sanitización.

Se prueba entonces el payload clásico de bypass de autenticación:

```text
' OR '1'='1
```

y la aplicación otorga acceso sin que el PIN introducido sea el correcto.

### Vulnerabilidad identificada

**SQL Injection con bypass de autenticación (CWE-89: SQL Injection)**

El valor de `txtPin` es incorporado directamente en la consulta SQL utilizada para validar el PIN, sin parametrización ni sanitización. Conceptualmente, la consulta vulnerable tendría una estructura similar a:

```sql
SELECT * FROM usuarios WHERE pin = '$pin';
```

que con el payload `' OR '1'='1` queda:

```sql
SELECT * FROM usuarios WHERE pin = '' OR '1'='1';
```

Como `'1'='1'` es siempre verdadero, la condición `OR` hace que la consulta devuelva resultados independientemente del PIN real, invalidando por completo el propósito de la comprobación.

> Nota: la consulta mostrada es una representación conceptual del comportamiento observado; no se confirma que sea exactamente la sentencia ejecutada por el backend.

Adicionalmente, el campo HTML `type="password"` no aporta ninguna protección contra este ataque: solo afecta la forma en que el navegador oculta visualmente el valor introducido, pero el contenido enviado al servidor sigue siendo completamente controlable por el usuario.

## Explotación

Se intercepta/modifica la petición del formulario de autenticación (Burp Suite o DevTools), introduciendo en el parámetro `txtPin`:

```text
txtPin=' OR '1'='1
```

Al enviar la petición, la aplicación concede acceso al Home Banking sin que se haya proporcionado el PIN legítimo, confirmando el **authentication bypass** vía SQL Injection.

## Impacto

La vulnerabilidad permite a cualquier usuario no autenticado obtener acceso completo a la aplicación de Home Banking sin conocer ninguna credencial válida, simplemente enviando un payload de SQL Injection conocido y ampliamente documentado. En un escenario real, esto equivaldría a un compromiso total del mecanismo de autenticación de una aplicación bancaria: acceso a cuentas, operaciones y datos de cualquier usuario sin necesidad de robar ni adivinar un PIN.

## Evidencia

### Campo de autenticación

```html
<input type="password" name="txtPin" autocomplete="off" placeholder="PIN">
```

### Prueba con PIN incorrecto

```text
txtPin=1234  -> acceso denegado
```

### Payload de SQL Injection

```text
txtPin=' OR '1'='1
```

### Resultado

```text
Acceso concedido al Home Banking sin conocer el PIN legítimo
```

## Conclusión

El desafío demuestra cómo una vulnerabilidad de SQL Injection puede comprometer directamente un mecanismo de autenticación. El parámetro `txtPin` es controlado por el usuario, y la aplicación no realiza una separación adecuada entre los datos proporcionados y la consulta SQL ejecutada. El payload `' OR '1'='1` permite alterar la lógica de la consulta y conseguir un bypass de autenticación completo.

## Mitigación

1. Utilizar siempre consultas preparadas/parametrizadas, evitando concatenar directamente los valores proporcionados por el usuario dentro de sentencias SQL.
2. No depender de `type="password"` como medida de seguridad — es únicamente una convención de UI que oculta el valor visualmente, no protege el dato enviado al servidor.
3. Implementar validaciones y manejo de errores del lado del servidor que no revelen diferencias de comportamiento entre una entrada malformada y un PIN simplemente incorrecto (evitar canales de información que faciliten la detección de la inyección).
4. Aplicar mecanismos de gestión de autenticación robustos (rate limiting, bloqueo tras intentos fallidos, hashing seguro de credenciales) como defensa en profundidad adicional.
