```python
#!/usr/bin/env python3
"""
Genera automáticamente las secciones del README principal de UTN-FRC CTFs,
leyendo los README.md de cada CTF.

Estructura esperada:

    utn-frc-ctfs/
    ├── README.md
    ├── generate_main_readme.py
    │
    ├── aldeas-inseguras/
    │   └── README.md
    │
    ├── home-banking/
    │   └── README.md
    │
    ├── uso-inspector/
    │   └── README.md
    │
    └── nsa/
        └── README.md

Cada README.md de CTF debería tener un formato similar a:

    # Aldeas inseguras - UTN-FRC

    **Dificultad:** CTF
    **Fecha:** 09/2026
    **Sistema:** Web
    **Objetivo:** Conseguir al menos 5000 de oro
    **Acceso inicial:** Manipulación de parámetros + abuso de lógica de negocio

    ## Herramientas

    `Chrome DevTools` `Burp Suite`

    ## Técnicas

    `Web Enumeration` `HTTP Request Analysis`
    `Parameter Manipulation` `Business Logic Abuse`

Uso:

    python generate_main_readme.py

El README principal debe contener:

    <!-- AUTO-START -->
    <!-- AUTO-END -->

Todo lo que esté fuera de esos marcadores se conserva sin modificar.
"""

import os
import re
import sys


# ============================================================
# CONFIGURACIÓN
# ============================================================

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MAIN_README = os.path.join(REPO_ROOT, "README.md")

START_MARKER = "<!-- AUTO-START -->"
END_MARKER = "<!-- AUTO-END -->"


# ============================================================
# UTILIDADES
# ============================================================

def extract_backtick_items(text):
    """
    Extrae elementos escritos entre backticks.

    Ejemplo:
        `Nmap` `Burp Suite` `curl`

    Devuelve:
        ["Nmap", "Burp Suite", "curl"]
    """
    return re.findall(r"`([^`]+)`", text)


def extract_field(content, field):
    """
    Extrae un campo del tipo:

        **Dificultad:** CTF

    Devuelve solamente el valor.
    """

    pattern = rf"\*\*{re.escape(field)}:\*\*\s*(.+)"

    match = re.search(pattern, content, re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return ""


# ============================================================
# PARSEO DE CADA CTF
# ============================================================

def parse_ctf_readme(path):
    """
    Lee un README.md individual y extrae:

    - nombre
    - dificultad
    - sistema
    - objetivo
    - acceso inicial
    - herramientas
    - técnicas
    """

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # --------------------------------------------------------
    # Nombre
    # --------------------------------------------------------

    name_match = re.search(
        r"^#\s+(.+?)(?:\s*-\s*UTN-FRC)?\s*$",
        content,
        re.MULTILINE | re.IGNORECASE,
    )

    if name_match:
        name = name_match.group(1).strip()
    else:
        name = os.path.basename(os.path.dirname(path))

    # --------------------------------------------------------
    # Campos principales
    # --------------------------------------------------------

    difficulty = extract_field(content, "Dificultad")
    system = extract_field(content, "Sistema")
    objective = extract_field(content, "Objetivo")
    initial_access = extract_field(content, "Acceso inicial")

    # --------------------------------------------------------
    # Herramientas
    # --------------------------------------------------------

    tools_match = re.search(
        r"##\s*Herramientas\s*\n+(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )

    tools = (
        extract_backtick_items(tools_match.group(1))
        if tools_match
        else []
    )

    # --------------------------------------------------------
    # Técnicas
    # --------------------------------------------------------

    techniques_match = re.search(
        r"##\s*T[eé]cnicas\s*\n+(.+?)(?=\n##|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )

    techniques = (
        extract_backtick_items(techniques_match.group(1))
        if techniques_match
        else []
    )

    return {
        "name": name,
        "difficulty": difficulty,
        "system": system,
        "objective": objective,
        "initial_access": initial_access,
        "tools": tools,
        "techniques": techniques,
    }


# ============================================================
# RECORRER TODOS LOS CTF
# ============================================================

def collect_all_ctfs():
    """
    Recorre todas las subcarpetas del repositorio y busca:

        <carpeta>/README.md

    Ignora:
        - el README principal
        - generate_main_readme.py
        - archivos que no sean README.md

    Devuelve una lista ordenada de CTFs.
    """

    ctfs = []

    for entry in sorted(os.listdir(REPO_ROOT)):

        path = os.path.join(REPO_ROOT, entry)

        # Solo nos interesan carpetas
        if not os.path.isdir(path):
            continue

        # Ignorar carpetas ocultas
        if entry.startswith("."):
            continue

        readme_path = os.path.join(path, "README.md")

        if not os.path.isfile(readme_path):
            continue

        ctf = parse_ctf_readme(readme_path)

        ctf["directory"] = entry
        ctf["rel_link"] = f"{entry}/README.md"

        ctfs.append(ctf)

    return ctfs


# ============================================================
# TABLA DE PROGRESO
# ============================================================

def build_progress(ctfs):
    """
    Genera:

    ## Progreso

    | Estado | Cantidad |
    |---|---:|
    | Resueltos | 4 |
    | En progreso | 0 |
    """

    total = len(ctfs)

    return "\n".join([
        "## Progreso",
        "",
        "| Estado | Cantidad |",
        "|---|---:|",
        f"| Resueltos | {total} |",
        "| En progreso | 0 |",
    ])


# ============================================================
# TABLA DE CTF
# ============================================================

def build_ctfs_table(ctfs):
    """
    Genera la tabla principal de CTFs.
    """

    lines = [
        "## CTFs resueltos",
        "",
        "| CTF | Sistema | Técnicas principales | Writeup |",
        "|---|---|---|---|",
    ]

    for ctf in ctfs:

        techniques = ctf["techniques"]

        if techniques:
            techniques_preview = ", ".join(techniques[:3])

            if len(techniques) > 3:
                techniques_preview += "..."
        else:
            techniques_preview = "-"

        lines.append(
            f"| {ctf['name']} "
            f"| {ctf['system'] or '-'} "
            f"| {techniques_preview} "
            f"| [Ver writeup]({ctf['rel_link']}) |"
        )

    return "\n".join(lines)


# ============================================================
# HERRAMIENTAS
# ============================================================

def build_tools_list(ctfs):
    """
    Junta todas las herramientas utilizadas y elimina duplicados.
    """

    all_tools = set()

    for ctf in ctfs:
        all_tools.update(ctf["tools"])

    if not all_tools:
        return "## Herramientas utilizadas\n\n- -"

    lines = [
        "## Herramientas utilizadas",
        "",
    ]

    for tool in sorted(all_tools, key=str.lower):
        lines.append(f"- {tool}")

    return "\n".join(lines)


# ============================================================
# MATRIZ DE TÉCNICAS
# ============================================================

def build_skills_matrix(ctfs):
    """
    Genera una matriz:

    | Técnica | CTFs |
    |---|---:|
    | SQL Injection | 2 |
    | Parameter Manipulation | 1 |
    """

    counts = {}

    for ctf in ctfs:

        # set() evita contar dos veces la misma técnica
        # dentro del mismo CTF.
        for technique in set(ctf["techniques"]):

            counts[technique] = counts.get(technique, 0) + 1

    if not counts:
        return ""

    lines = [
        "## Skills Matrix",
        "",
        "| Técnica | CTFs |",
        "|---|---:|",
    ]

    for technique, count in sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0].lower()),
    ):
        lines.append(
            f"| {technique} | {count} |"
        )

    return "\n".join(lines)


# ============================================================
# SECCIÓN AUTOMÁTICA COMPLETA
# ============================================================

def build_auto_section(ctfs):

    parts = []

    parts.append(build_progress(ctfs))
    parts.append("")
    parts.append(build_ctfs_table(ctfs))
    parts.append("")
    parts.append(build_tools_list(ctfs))

    skills_matrix = build_skills_matrix(ctfs)

    if skills_matrix:
        parts.append("")
        parts.append(skills_matrix)

    return "\n".join(parts)


# ============================================================
# ACTUALIZAR README PRINCIPAL
# ============================================================

def update_main_readme():

    if not os.path.isfile(MAIN_README):

        print(
            f"No se encontró el README principal:\n"
            f"{MAIN_README}"
        )

        sys.exit(1)

    with open(MAIN_README, encoding="utf-8") as f:
        content = f.read()

    # --------------------------------------------------------
    # Verificar marcadores
    # --------------------------------------------------------

    if START_MARKER not in content or END_MARKER not in content:

        print(
            "El README principal no tiene los marcadores:\n\n"
            "<!-- AUTO-START -->\n"
            "<!-- AUTO-END -->\n\n"
            "Agregalos donde quieras insertar "
            "el contenido generado."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Recopilar CTFs
    # --------------------------------------------------------

    ctfs = collect_all_ctfs()

    # --------------------------------------------------------
    # Generar contenido
    # --------------------------------------------------------

    auto_section = build_auto_section(ctfs)

    # --------------------------------------------------------
    # Reemplazar sección automática
    # --------------------------------------------------------

    pattern = (
        re.escape(START_MARKER)
        + r".*?"
        + re.escape(END_MARKER)
    )

    replacement = (
        START_MARKER
        + "\n\n"
        + auto_section
        + "\n\n"
        + END_MARKER
    )

    new_content = re.sub(
        pattern,
        replacement,
        content,
        flags=re.DOTALL,
    )

    # --------------------------------------------------------
    # Guardar README
    # --------------------------------------------------------

    with open(MAIN_README, "w", encoding="utf-8") as f:
        f.write(new_content)

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print("README.md actualizado correctamente.")
    print(f"CTFs encontrados: {len(ctfs)}")

    if ctfs:
        print("\nCTFs:")
        for ctf in ctfs:
            print(f"  - {ctf['name']}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    update_main_readme()
```
