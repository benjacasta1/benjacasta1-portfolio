# DockerLabs Writeups

Repositorio donde documento mi práctica de pentesting mediante máquinas vulnerables de [DockerLabs](https://dockerlabs.es/).

El objetivo es desarrollar y documentar habilidades en reconocimiento, enumeración, explotación y escalada de privilegios en entornos controlados.

## Progreso

| Dificultad | Completadas |
|------------|-------------|
| Muy Fácil  | 5           |
| Fácil      | 0           |
| Medio      | 0           |
| Difícil    | 0           |

## Máquinas resueltas

### Muy Fácil

| Máquina | Vector principal | Writeup |
|---|---|---|
| Tproot | Backdoor vsftpd 2.3.4 (CVE-2011-2523) | [Ver writeup](muy-facil/tproot/README.md) |
| Obsession | FTP anónimo, fuerza bruta SSH, sudo abuse (Vim) | [Ver writeup](muy-facil/obsession/README.md) |
| Vacaciones | Pista web, fuerza bruta SSH, correo local, sudo abuse (Ruby) | [Ver writeup](muy-facil/vacaciones/README.md) |
| BorazuwaraCTF | Esteganografía (EXIF/steghide), fuerza bruta SSH, sudo sin restricciones | [Ver writeup](muy-facil/borazuwarahctf/README.md) |
| Trust | Enumeración web (wildcard response), fuerza bruta SSH, sudo abuse (Vim) | [Ver writeup](muy-facil/trust/README.md) |

## Herramientas utilizadas

- Kali Linux
- Nmap
- Gobuster
- Hydra
- Steghide
- ExifTool
- Binwalk
- Foremost
- Searchsploit
- Metasploit
- LinPEAS
- Netcat
- FTP
- SSH
- Vim
- Ruby
- Wget
- Curl
- arp-scan

## Técnicas practicadas

| Área | Técnicas practicadas |
|---|---|
| Reconocimiento | Network Discovery, Network Enumeration, Service Version Enumeration |
| Web | Web Enumeration, Information Disclosure, Wildcard Response Handling |
| Credenciales | Credential Discovery, SSH Brute Force |
| Explotación | Vulnerability Identification, Exploit Research, Remote Code Execution, Reverse Shell |
| Linux | Local Enumeration, Sudo Privilege Escalation |
| Post-Explotación | Automated Enumeration, Local Mail Enumeration |
| Técnicas específicas | Steganography, EXIF Metadata Analysis |

## Disclaimer

Todas las actividades documentadas en este repositorio fueron realizadas en entornos de laboratorio autorizados y controlados, con fines educativos.
