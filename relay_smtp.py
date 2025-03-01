import asyncio
import msal
import os
import sqlite3
import base64
import smtplib
import ssl
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import AsyncMessage
from dotenv import load_dotenv
from email.message import EmailMessage

DB_FILE = "tokens.db"  # Base de datos para almacenar tokens

def init_db():
    """Inicializa la base de datos SQLite si no existe."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            access_token TEXT,
            refresh_token TEXT,
            expires_at INTEGER
        )
    ''')
    conn.commit()
    conn.close()

class RelayHandler(AsyncMessage):
    def __init__(self, get_token_func, username):
        super().__init__()
        self.get_token_func = get_token_func
        self.username = username

    async def handle_message(self, message):
        mailfrom = message['From']
        rcpttos = message.get_all('To', []) + message.get_all('Cc', []) + message.get_all('Bcc', [])
        rcpttos = [addr.strip() for addr in rcpttos if addr.strip()]
        
        access_token = self.get_token_func()
        
        server = smtplib.SMTP("smtp.office365.com", 587)
        context = ssl.create_default_context()
        server.starttls(context=context)
        server.ehlo()

        auth_string = f"user={self.username}\x01auth=Bearer {access_token}\x01\x01"
        auth_encoded = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        code, response = server.docmd("AUTH", "XOAUTH2 " + auth_encoded)

        if code != 235:
            print("Error en autenticación SMTP:", code, response)
            server.quit()
            return

        server.send_message(message, from_addr=mailfrom, to_addrs=rcpttos)
        server.quit()
        print("Correo reenviado exitosamente a través de Office 365.")

def get_device_code_token(app, scopes):
    """Obtiene un token a través del Device Code Flow."""
    flow = app.initiate_device_flow(scopes=scopes)
    if 'user_code' not in flow:
        raise ValueError("Error al iniciar Device Code Flow.", flow)
    
    print(flow['message'])
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        save_token(result)
        return result
    else:
        raise Exception("No se obtuvo access_token:", result.get("error_description", "Desconocido"))

def save_token(token):
    """Guarda el token en la base de datos SQLite."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tokens")  # Limpia tokens anteriores
    c.execute("INSERT INTO tokens (access_token, refresh_token, expires_at) VALUES (?, ?, ?)",
              (token["access_token"], token.get("refresh_token", ""), token.get("expires_in", 0)))
    conn.commit()
    conn.close()

def load_token():
    """Carga el token desde la base de datos SQLite."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT access_token, refresh_token, expires_at FROM tokens")
    row = c.fetchone()
    conn.close()
    if row:
        return {"access_token": row[0], "refresh_token": row[1], "expires_in": row[2]}
    return None

def main():
    load_dotenv()
    init_db()
    
    TENANT_ID = os.getenv("TENANT_ID")
    CLIENT_ID = os.getenv("CLIENT_ID")
    USERNAME = os.getenv("USERNAME")
    
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.PublicClientApplication(client_id=CLIENT_ID, authority=authority)
    scopes = ["https://outlook.office365.com/.default"]
    
    token_result = load_token()
    if not token_result:
        token_result = get_device_code_token(app, scopes)
    
    def get_current_access_token():
        """Devuelve un access_token válido, renovándolo si es necesario."""
        nonlocal token_result
        accounts = app.get_accounts()
        new_result = app.acquire_token_silent(scopes, account=accounts[0] if accounts else None)
        
        if new_result:
            token_result = new_result
        else:
            print("Token expirado. Renovando...")
            token_result = get_device_code_token(app, scopes)
        
        save_token(token_result)
        return token_result["access_token"]
    
    handler = RelayHandler(get_token_func=get_current_access_token, username=USERNAME)
    controller = Controller(handler, hostname='0.0.0.0', port=1025)
    controller.start()
    print("✅ SMTP relay iniciado en puerto 1025.")
    
    try:
        asyncio.run(asyncio.sleep(3600))
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
