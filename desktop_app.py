import webview
import threading
import time
import sys
import urllib.request
import server # Importa il tuo server.py locale
import os

# PORTA CONFIGURATA: 5500
SERVER_URL = 'http://127.0.0.1:5500'

def start_flask():
    try:
        server.start_server_thread()
    except Exception as e:
        print(f"Errore Server Thread: {e}")

def wait_for_server(url, timeout=20):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200: return True
        except:
            time.sleep(0.5)
    return False

def on_closed():
    # Uccide brutalmente i processi python alla chiusura per pulire la porta
    os._exit(0)

if __name__ == '__main__':
    # 1. Avvia Server in background
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    # 2. Aspetta che risponda
    if wait_for_server(SERVER_URL):
        # 3. Apri Finestra
        window = webview.create_window(
            'MarketOS Pro', 
            SERVER_URL, 
            width=1280, 
            height=800,
            confirm_close=True,
            text_select=False
        )
        webview.start(on_closed)
    else:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, "Errore Critico: Il server database non risponde sulla porta 5500.", "Errore MarketOS", 16)
        sys.exit(1)