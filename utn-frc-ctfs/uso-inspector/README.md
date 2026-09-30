# Uso Inspector - SoftwareSeguro

**Dificultad:** CTF  
**Fecha:** 09/2026  
**Sistema:** Web  
**Objetivo:** Obtener el código del desafío  
**Acceso inicial:** Análisis del HTML + inspección de peticiones HTTP + manipulación de campo hidden  

## Herramientas

`Chrome DevTools`

## Técnicas

`Web Enumeration` `HTTP Request Analysis` `HTML Inspection` `Parameter Manipulation` `Client-Side Trust Bypass`

## Introducción

El desafío consiste en obtener un código generado por la aplicación mediante el análisis de las peticiones HTTP realizadas por el navegador.

La aplicación indica explícitamente que es necesario utilizar el inspector de un navegador web para encontrar una petición cuya respuesta contenga un header `X-CODE`, copiar su valor, introducirlo en un campo `hidden` presente en el HTML, y enviar el formulario para obtener el código final por consola.

## Reconocimiento

Al acceder a la aplicación se observa un formulario con un botón de envío. Mediante la inspección del HTML se identifica un campo oculto sin valor:

```html
<input type="hidden" id="code" value="">
```

Al ser de tipo `hidden`, su contenido no es visible en la interfaz pero sí es inspeccionable y modificable mediante las herramientas de desarrollo del navegador.

## Análisis de las peticiones

Se abre **Chrome DevTools → Network** para analizar las peticiones HTTP realizadas por la aplicación. Se identifica una petición relevante:

```text
POST /src/ctl/validate.php
```

con respuesta `200 OK`. Entre los datos enviados por el navegador se observa un parámetro `token=bef93704e7050f99dce733f3978dcf08`, que corresponde a los datos enviados en la petición y no al código solicitado por el desafío.

Dentro de los **headers de respuesta** de esa misma petición se identifica el header indicado por el desafío:

```text
X-CODE: f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2
```

Es importante diferenciar este valor (el que debe utilizarse) de otros datos presentes en la petición, como el parámetro `token`.

## Vulnerabilidad identificada

**Exposición de información sensible en headers HTTP + confianza excesiva en datos controlados por el cliente (CWE-200 / CWE-602)**

El servidor filtra en un header de respuesta (`X-CODE`) un valor que debería tratarse como secreto de validación, en una petición no directamente relacionada con la obtención del código. Adicionalmente, el mecanismo de validación se apoya en un campo `hidden` del formulario, cuyo valor es enviado por el cliente sin ningún control de integridad (no hay firma, HMAC ni verificación server-side que impida que el valor sea alterado desde el navegador antes del envío). Esto constituye un caso de "Client-Side Enforcement of Server-Side Security": el servidor confía en un dato que el cliente puede modificar libremente.

## Explotación

Con el valor de `X-CODE` obtenido, se vuelve a la pestaña **Elements** de Chrome DevTools y se modifica manualmente el atributo `value` del campo oculto:

```html
<input type="hidden" id="code" value="f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2">
```

La modificación se realiza directamente desde el inspector del navegador y afecta únicamente al HTML que está siendo utilizado por esa sesión del navegador; no es necesario modificar nada del lado del servidor.

Con el campo `hidden` modificado, se vuelve a la página principal y se presiona el botón **Enviar**. La aplicación procesa el valor introducido y realiza la validación correspondiente.

## Obtención del código

Tras presionar **Enviar**, se abre **Chrome DevTools → Console**. La aplicación muestra en la consola el código correspondiente al desafío:

```text
MDliNDZiZGMyMDA2NTU2ZGZmNThjNTM3MTZjNmMwYjk=
```

El formato del valor, con `=` al final, es compatible con una representación **Base64**. Para completar el desafío no es necesario decodificarlo: el objetivo es obtener el código mostrado por la aplicación en consola.

![Código obtenido](resources/codigo.png)

## Impacto

Cualquier usuario capaz de inspeccionar el tráfico de red (cualquier visitante de la aplicación, sin necesidad de credenciales) puede obtener el valor de validación filtrado en el header `X-CODE` y utilizarlo para satisfacer el control del lado del cliente, sin haber resuelto ninguna lógica real del desafío. En un escenario real, este patrón (secreto de validación expuesto en un header + verificación dependiente de un campo manipulable por el cliente) permitiría bypassear controles de validación pensados para impedir el acceso o la manipulación no autorizada.

## Evidencia

### Campo hidden inicial

```html
<input type="hidden" id="code" value="">
```

### Petición de validación

```text
POST /src/ctl/validate.php -> 200 OK
```

### Header X-CODE

```text
f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2
```

### Campo modificado

```html
<input type="hidden" id="code" value="f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2">
```

### Código obtenido

```text
MDliNDZiZGMyMDA2NTU2ZGZmNThjNTM3MTZjNmMwYjk=
```

## Conclusión

El desafío demuestra la utilidad de las herramientas de desarrollo del navegador para analizar el funcionamiento de una aplicación web, y cómo un mecanismo de validación que depende de datos controlados por el cliente (un campo `hidden`) no aporta ninguna garantía de seguridad si el servidor no verifica su integridad de forma independiente.

## Mitigación

1. No exponer valores de validación en headers de respuesta accesibles al cliente; cualquier secreto usado para validar debe permanecer exclusivamente en el servidor.
2. No confiar en campos `hidden` ni en ningún dato enviado por el cliente como mecanismo de control de seguridad — un campo `hidden` no es más que una convención de UI, no un control de acceso.
3. Implementar la validación completa en el servidor, asociando el estado del desafío a la sesión autenticada en lugar de a un valor viajando en el HTML.
