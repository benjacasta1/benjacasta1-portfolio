#!/usr/bin/env python3
"""
Genera automáticamente las secciones de Progreso, Máquinas resueltas,
Herramientas y Técnicas del README principal, leyendo los headers de
cada writeup individual (muy-facil/, facil/, medio/, dificil/).

Cada README.md de máquina debe tener este formato al principio:

    # NombreMaquina - DockerLabs (Dificultad)

    **Dificultad:** Muy Fácil
    ...

    ## Herramientas

    `Nmap` `Gobuster` `Hydra`

    ## Técnicas

    `Network Enumeration` `SSH Brute Force`

Uso:
    python3 generate_main_readme.py

Requiere que el README.md principal tenga estos marcadores donde se
quiere insertar el contenido generado:

    <!-- AUTO-START -->
    <!-- AUTO-END -->

Todo lo que esté fuera de esos marcadores (introducción, disclaimer,
etc.) se conserva tal cual.
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DIFFICULTY_FOLDERS = ["muy-facil", "facil", "medio", "dificil"]
DIFFICULTY_LABELS = {
    "muy-facil": "Muy Fácil",
    "facil": "Fácil",
    "medio": "Medio",
    "dificil": "Difícil",
}
MAIN_README = os.path.join(REPO_ROOT, "README.md")
START_MARKER = "<!-- AUTO-START -->"
END_MARKER = "<!-- AUTO-END -->"


def extract_backtick_items(text):
    """Extrae todos los `items` entre backticks de un bloque de texto."""
    return re.findall(r"`([^`]+)`", text)


def parse_machine_readme(path):
    """Lee un README.md de máquina y extrae nombre, herramientas y técnicas."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Nombre: primera línea que empieza con "# "
    name_match = re.search(r"^#\s+(.+?)\s*-\s*DockerLabs", content, re.MULTILINE | re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else os.path.basename(os.path.dirname(path))

    # Bloque de Herramientas: desde "## Herramientas" hasta el siguiente "##"
    tools_match = re.search(r"##\s*Herramientas\s*\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    tools = extract_backtick_items(tools_match.group(1)) if tools_match else []

    # Bloque de Técnicas: desde "## Técnicas" hasta el siguiente "##"
    tech_match = re.search(r"##\s*T[eé]cnicas\s*\n+(.+?)(?=\n##|\Z)", content, re.DOTALL)
    techniques = extract_backtick_items(tech_match.group(1)) if tech_match else []

    return name, tools, techniques


def collect_all_machines():
    """Recorre todas las carpetas de dificultad y arma la info de cada máquina."""
    data = {}  # difficulty_folder -> list of (machine_dir, name, tools, techniques)
    for folder in DIFFICULTY_FOLDERS:
        folder_path = os.path.join(REPO_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue
        machines = []
        for machine_dir in sorted(os.listdir(folder_path)):
            readme_path = os.path.join(folder_path, machine_dir, "README.md")
            if os.path.isfile(readme_path):
                name, tools, techniques = parse_machine_readme(readme_path)
                rel_link = f"{folder}/{machine_dir}/README.md"
                machines.append((machine_dir, name, tools, techniques, rel_link))
        if machines:
            data[folder] = machines
    return data


def build_progress_table(data):
    lines = ["| Dificultad | Completadas |", "|------------|-------------|"]
    for folder in DIFFICULTY_FOLDERS:
        count = len(data.get(folder, []))
        lines.append(f"| {DIFFICULTY_LABELS[folder]}  | {count}           |")
    return "\n".join(lines)


def build_machines_tables(data):
    out = []
    for folder in DIFFICULTY_FOLDERS:
        machines = data.get(folder)
        if not machines:
            continue
        out.append(f"### {DIFFICULTY_LABELS[folder]}\n")
        out.append("| Máquina | Técnicas principales | Writeup |")
        out.append("|---|---|---|")
        for machine_dir, name, tools, techniques, rel_link in machines:
            techs_preview = ", ".join(techniques[:3]) + ("..." if len(techniques) > 3 else "")
            out.append(f"| {name} | {techs_preview} | [Ver writeup]({rel_link}) |")
        out.append("")
    return "\n".join(out)


def build_tools_list(data):
    all_tools = set()
    for machines in data.values():
        for _, _, tools, _, _ in machines:
            all_tools.update(tools)
    return "\n".join(f"- {t}" for t in sorted(all_tools))


def build_skills_matrix(data):
    counts = {}
    for machines in data.values():
        for _, _, _, techniques, _ in machines:
            for t in techniques:
                counts[t] = counts.get(t, 0) + 1
    if not counts:
        return ""
    lines = ["## Skills Matrix\n", "| Técnica | Máquinas |", "|---|---|"]
    for tech, count in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {tech} | {count} |")
    return "\n".join(lines)


def build_auto_section(data):
    parts = []
    parts.append("## Progreso\n")
    parts.append(build_progress_table(data))
    parts.append("\n\n## Máquinas resueltas\n")
    parts.append(build_machines_tables(data))
    parts.append("\n## Herramientas utilizadas\n")
    parts.append(build_tools_list(data))
    skills = build_skills_matrix(data)
    if skills:
        parts.append("\n\n" + skills)
    return "\n".join(parts)


def update_main_readme():
    if not os.path.isfile(MAIN_README):
        print(f"No se encontró {MAIN_README}")
        sys.exit(1)

    with open(MAIN_README, encoding="utf-8") as f:
        content = f.read()

    if START_MARKER not in content or END_MARKER not in content:
        print("El README principal no tiene los marcadores <!-- AUTO-START --> y <!-- AUTO-END -->.")
        print("Agregalos donde quieras que se inserte el contenido generado y volvé a correr el script.")
        sys.exit(1)

    data = collect_all_machines()
    auto_section = build_auto_section(data)

    new_content = re.sub(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        START_MARKER + "\n\n" + auto_section + "\n\n" + END_MARKER,
        content,
        flags=re.DOTALL,
    )

    with open(MAIN_README, "w", encoding="utf-8") as f:
        f.write(new_content)

    total = sum(len(m) for m in data.values())
    print(f"README.md actualizado. Total de máquinas: {total}")


if __name__ == "__main__":
    update_main_readme()
