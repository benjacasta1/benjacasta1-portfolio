# Home Banking - UTN-FRC

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

El desafío consiste en acceder a una aplicación de Home Banking que solicita un PIN para permitir el ingreso.

La aplicación presenta un formulario de autenticación donde el usuario debe introducir un PIN.

Durante el análisis se busca determinar cómo procesa el servidor el valor proporcionado y comprobar si existen mecanismos de validación adecuados.

El objetivo es conseguir acceso al sistema sin conocer el PIN legítimo.

## Reconocimiento

Al acceder a la aplicación se observa un formulario de autenticación que solicita un PIN.

Mediante la inspección del HTML se identifica un campo similar a:

```html
<input type="password" name="txtPin" autocomplete="off" placeholder="PIN">
```

El atributo:

```text
name="txtPin"
```

permite identificar el nombre del parámetro utilizado para enviar el PIN al servidor.

También se observa un botón para enviar el formulario:

```text
Ingresar
```

Inicialmente se prueba un PIN arbitrario para observar el comportamiento de la aplicación.

Por ejemplo:

```text
1234
```

La aplicación no permite el acceso con este valor.

## Análisis de la petición

Utilizando **Chrome DevTools → Network** se analiza la comunicación generada al enviar el formulario.

Durante el reconocimiento aparecen peticiones automáticas de Cloudflare, entre ellas:

```text
/cdn-cgi/rum
```

Estas peticiones corresponden a mecanismos de telemetría y no forman parte de la validación del PIN.

Por lo tanto, se ignoran y se continúa buscando la petición que contiene el parámetro:

```text
txtPin
```

La petición relevante corresponde al formulario de autenticación.

El parámetro enviado por el cliente contiene el valor introducido en el campo PIN:

```text
txtPin=1234
```

Esto permite analizar directamente cómo responde la aplicación ante diferentes entradas.

## Análisis del parámetro PIN

Se realizan distintas pruebas modificando únicamente el valor de:

```text
txtPin
```

Por ejemplo:

```text
1234
```

Posteriormente se prueban caracteres especiales y expresiones utilizadas habitualmente para comprobar posibles problemas de validación.

Entre las pruebas realizadas se encuentra:

```text
1234'
```

y posteriormente:

```text
' OR '1'='1
```

La segunda entrada permite observar un comportamiento diferente respecto de un PIN incorrecto.

## Identificación de SQL Injection

La entrada:

```text
' OR '1'='1
```

permite obtener acceso a la aplicación.

El comportamiento indica que el valor proporcionado por el usuario probablemente está siendo incorporado directamente dentro de una consulta SQL sin utilizar una validación o parametrización adecuada.

Conceptualmente, una consulta vulnerable podría tener una estructura similar a:

```sql
SELECT *
FROM usuarios
WHERE pin = '$pin';
```

Si el valor recibido fuera:

```text
' OR '1'='1
```

la consulta podría terminar teniendo una estructura equivalente a:

```sql
SELECT *
FROM usuarios
WHERE pin = '' OR '1'='1';
```

La condición:

```sql
'1'='1'
```

siempre resulta verdadera.

Por este motivo, la condición original utilizada para comprobar el PIN puede quedar invalidada y la aplicación puede considerar válida la autenticación.

> La consulta anterior es una representación conceptual de cómo podría producirse la vulnerabilidad. No se afirma que sea exactamente la consulta utilizada internamente por la aplicación.

## Explotación

Se intercepta o modifica la petición correspondiente al formulario de autenticación utilizando las herramientas del navegador o **Burp Suite**.

En el parámetro:

```text
txtPin
```

se introduce:

```text
' OR '1'='1
```

La petición queda conceptualmente de la siguiente manera:

```text
txtPin=' OR '1'='1
```

Al enviar la petición, la aplicación permite el acceso sin proporcionar el PIN legítimo.

Esto demuestra que el mecanismo de autenticación puede ser evadido mediante una inyección SQL.

## Bypass de autenticación

El payload utilizado fue:

```text
' OR '1'='1
```

La estructura puede interpretarse de la siguiente manera:

```text
'
```

Cierra el valor que originalmente esperaba la consulta.

```text
OR
```

Agrega una condición alternativa.

```text
'1'='1'
```

Introduce una condición que siempre es verdadera.

El resultado es que la comprobación del PIN deja de depender exclusivamente del valor correcto introducido por el usuario.

## Vulnerabilidad

La aplicación presenta una vulnerabilidad de **SQL Injection** en el parámetro:

```text
txtPin
```

Esta vulnerabilidad afecta directamente al mecanismo de autenticación, permitiendo realizar un **Authentication Bypass**.

El problema se produce cuando los datos proporcionados por el usuario son utilizados para construir una consulta SQL sin utilizar mecanismos seguros de parametrización.

Un campo HTML de tipo:

```html
type="password"
```

no proporciona protección contra este tipo de ataque.

La restricción únicamente afecta a la forma en que el navegador muestra el valor introducido, pero el contenido sigue siendo controlable por el usuario.

## Cadena de explotación

```text
Inspección del formulario
        ↓
Identificación del parámetro txtPin
        ↓
Análisis de la petición HTTP
        ↓
Pruebas de manipulación del parámetro
        ↓
Identificación de comportamiento anómalo
        ↓
SQL Injection
        ↓
' OR '1'='1
        ↓
Bypass de autenticación
        ↓
Acceso al Home Banking
```

## Evidencia

Durante el análisis se identifican las siguientes evidencias:

### Campo de autenticación

El formulario contiene el parámetro:

```text
txtPin
```

que representa el PIN introducido por el usuario.

### Prueba con PIN incorrecto

Se utiliza:

```text
1234
```

y la aplicación no concede acceso.

### Prueba de SQL Injection

Se utiliza:

```text
' OR '1'='1
```

La aplicación responde permitiendo el acceso.

### Resultado

El acceso conseguido demuestra que el mecanismo de autenticación puede ser evadido sin conocer el PIN legítimo.

## Conclusión

El desafío demuestra cómo una vulnerabilidad de **SQL Injection** puede comprometer directamente un mecanismo de autenticación.

El parámetro:

```text
txtPin
```

es controlado por el usuario y la aplicación no realiza una separación adecuada entre los datos proporcionados y la consulta SQL.

El payload:

```text
' OR '1'='1
```

permite alterar la lógica de la consulta y conseguir un bypass de autenticación.

Para evitar esta vulnerabilidad, el servidor debería utilizar **consultas preparadas o parametrizadas**, evitando concatenar directamente los valores proporcionados por el usuario dentro de consultas SQL.

También deberían implementarse validaciones del lado del servidor y mecanismos adecuados de gestión de autenticación.

## Evidencias

> Agregar aquí las capturas correspondientes al proceso:
>
> * Formulario de autenticación.
> * Campo `txtPin`.
> * Petición HTTP del login.
> * Prueba con PIN incorrecto.
> * Petición modificada con `' OR '1'='1`.
> * Resultado del bypass de autenticación.
> * Acceso final al Home Banking.
