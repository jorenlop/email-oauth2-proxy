# 📧 Email OAuth2 Proxy (SMTP Relay con Office 365)Docker

[![Docker](https://badgen.net/badge/icon/docker?icon=docker&label)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/tuusuario/email-oauth2-proxy)](LICENSE)

## 📝 Descripción

**Email OAuth2 Proxy** es un servidor SMTP relay que reenvía correos electrónicos autenticándose en **Office 365** con OAuth2 (MSAL). Permite el uso de autenticación segura sin almacenar contraseñas, renovando automáticamente los tokens de acceso.

📌 **Características principales:**
- 🔐 **Autenticación OAuth2** con Microsoft Office 365.
- 📩 **SMTP Relay** en el puerto `1025`.
- 🔄 **Renovación automática de token** sin intervención manual.
- 🐳 **Ejecutable con Docker y Docker Compose**.

---

## 🚀 Instalación

### **1️⃣ Clonar el repositorio**
```sh
git https://github.com/jorenlop/email-oauth2-proxy.git
cd email-oauth2-proxy
```

### **2️⃣ Configurar variables de entorno**
Crea un archivo `.env` y agrega las credenciales de Azure:

```sh
TENANT_ID="tu-tenant-id"
CLIENT_ID="tu-client-id"
USERNAME="tu-correo@tudominio.com"
```

### **3️⃣ Construir y ejecutar con Docker**
```sh
docker-compose build --no-cache
docker-compose up -d
```

Verifica los logs para asegurarte de que el servicio está corriendo:
```sh
docker logs -f smtp-relay
```

Si es la primera vez que ejecutas el contenedor, aparecerá un **código de autenticación**:
```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code XXXXXXX to authenticate.
```
📌 **Accede al enlace, introduce el código y autentica tu cuenta de Office 365**.

---

## 🛠 Uso

### **1️⃣ Configurar tu aplicación para usar el relay**
Apunta tu servidor SMTP a `127.0.0.1:1025` sin autenticación:

```
SMTP Server: 127.0.0.1
Puerto: 1025
TLS: No
Usuario/Contraseña: No requerido
```

### **2️⃣ Probar con `sendmail`**
```sh
echo "Subject: Test Email" | sendmail -v -f "tu-correo@tudominio.com" -S 127.0.0.1:1025 destinatario@ejemplo.com
```

### **3️⃣ Probar con `telnet`**
```sh
telnet 127.0.0.1 1025
```
Luego, sigue los pasos para enviar un correo manualmente.

---

## ⚙ Configuración

### **📌 Variables de entorno (`.env`)**
| Variable    | Descripción |
|-------------|------------|
| `TENANT_ID` | ID del tenant en Azure |
| `CLIENT_ID` | ID del cliente registrado en Azure |
| `USERNAME`  | Dirección de correo electrónico de la cuenta |

### **📌 Docker Compose (`docker-compose.yml`)**
```yaml
version: '3'
services:
  smtp-relay:
    build: .
    ports:
      - "1025:1025"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./token_cache.json:/app/token_cache.json
```

---

## ❌ Solución de Problemas

### 🚨 **El servicio no arranca**
Verifica los logs:
```sh
docker logs -f smtp-relay
```
Si ves:
```
ModuleNotFoundError: No module named 'msal'
```
Asegúrate de que `requirements.txt` no está vacío y reconstruye el contenedor:

```sh
docker-compose build --no-cache
docker-compose up -d
```

### 🚨 **No se está autenticando en Office 365**
Si en los logs aparece:
```
AADSTS70016: OAuth 2.0 device flow error. Authorization is pending.
```
Debes completar la autenticación en **https://microsoft.com/devicelogin**.

---

## 👨‍💻 Contribuir

¡Contribuciones son bienvenidas! Para colaborar:

1. **Fork** este repositorio 🍴
2. Crea una rama nueva: `git checkout -b feature-nueva`
3. Haz tus cambios y confirma: `git commit -m "Añadida nueva funcionalidad"`
4. Sube los cambios: `git push origin feature-nueva`
5. Abre un **Pull Request** 🚀

---

## 📄 Licencia
Este proyecto está bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más información.

---

## 🎯 Autor
Proyecto desarrollado por **[@jorenlop](https://github.com/jorenlop/email-oauth2-proxy.git)**.  
📩 Contacto: **jorgeenriquelopezing@gmail.com**
