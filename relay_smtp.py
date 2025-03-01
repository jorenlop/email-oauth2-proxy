import asyncio
import msal
import os
import json
import base64
import smtplib
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import AsyncMessage
from dotenv import load_dotenv
from email.message import EmailMessage

TOKEN_FILE = "/app/token_cache.json"  # Ruta del archivo de token dentro del contenedor

class RelayHandler(AsyncMessage):
    """
    Handler que recibe los mensajes SMTP y los reenvía a Office 365
    usando autenticación OAuth2 (MSAL).
    """
    def __init__(self, get_token_func, username):
        super().__init__()
        self.get_token_func = get_token_func
        self.username = username

    async def handle_message(self, message):
        print("📩 Correo recibido, procesando...", flush=True)
        
        mailfrom = message['From']
        rcpttos = (
            message.get_all('To', []) +
            message.get_all('Cc', []) +
            message.get_all('Bcc', [])
        )
        rcpttos = [addr.strip() for addr in rcpttos if addr.strip()]
        
        access_token = self.get_token_func()

        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.ehlo()

        # Autenticación OAuth2
        auth_string = f"user={self.username}\x01auth=Bearer {access_token}\x01\x01"
        auth_encoded = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        code, response = server.docmd("AUTH", "XOAUTH2 " + auth_encoded)

        if code != 235:
            print(f"❌ Error en autenticación SMTP: {code}, {response}", flush=True)
            server.quit()
            return

        server.send_message(message, from_addr=mailfrom, to_addrs=rcpttos)
        server.quit()
        print("✅ Correo reenviado exitosamente a través de Office 365.", flush=True)

def get_device_code_token(app, scopes):
    """Realiza el Device Code Flow y devuelve el token de acceso y refresh_token."""
    flow = app.initiate_device_flow(scopes=scopes)
    
    if 'user_code' not in flow:
        raise ValueError("No se pudo iniciar el Device Code Flow.", flow)
    
    print(flow['message'], flush=True)  # Muestra el código de autenticación
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        with open(TOKEN_FILE, "w") as f:
            json.dump(result, f)  # Guardamos el token
        return result
    else:
        raise Exception("No se obtuvo access_token:", result.get("error_description", "Desconocido"))

def load_token_cache():
    """Carga el token desde el archivo cache si existe y es válido."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = f.read().strip()
                if not data:  # Si el archivo está vacío
                    return None
                return json.loads(data)  # Decodifica JSON
        except json.JSONDecodeError:
            print("⚠ Error: token_cache.json está corrupto. Se regenerará.", flush=True)
            return None
    return None

def main():
    load_dotenv()
    TENANT_ID = os.getenv("TENANT_ID")
    CLIENT_ID = os.getenv("CLIENT_ID")
    USERNAME = os.getenv("USERNAME")

    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.PublicClientApplication(client_id=CLIENT_ID, authority=authority)
    scopes = ["https://outlook.office365.com/.default"]

    token_result = load_token_cache()

    if not token_result:
        token_result = get_device_code_token(app, scopes)

    def get_current_access_token():
        """Maneja la renovación automática del token."""
        nonlocal token_result
        accounts = app.get_accounts()
        new_result = app.acquire_token_silent(scopes, account=accounts[0] if accounts else None)

        if new_result:
            token_result = new_result
        else:
            print("⚠ Token expirado, obteniendo nuevo...", flush=True)
            token_result = get_device_code_token(app, scopes)

        with open(TOKEN_FILE, "w") as f:
            json.dump(token_result, f)  # Guardar el token actualizado
        return token_result["access_token"]

    handler = RelayHandler(get_token_func=get_current_access_token, username=USERNAME)
    controller = Controller(handler, hostname='0.0.0.0', port=1025)
    controller.start()
    
    print("✅ SMTP relay iniciado en puerto 1025.", flush=True)

    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()  # Mantiene el script en ejecución
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()

if __name__ == "__main__":
    main()