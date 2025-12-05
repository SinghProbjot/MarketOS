import webview
import threading
import time
import sys
import urllib.request
import os
import traceback
import platform # Necessario per l'OS
import server   # Importa il server locale

# --- CONFIGURAZIONE ---
PORT = 5500
SERVER_URL = f'http://127.0.0.1:{PORT}'

# --- PERCORSI LOG CROSS-PLATFORM ---
system_os = platform.system()
base_log_dir = ''

if system_os == 'Windows':
    base_log_dir = os.getenv('APPDATA')
elif system_os == 'Darwin': # macOS
    base_log_dir = os.path.expanduser('~/Library/Application Support')
else: # Linux
    base_log_dir = os.path.expanduser('~/.local/share')

log_dir = os.path.join(base_log_dir, 'MarketOS')

if not os.path.exists(log_dir):
    try: os.makedirs(log_dir)
    except: log_dir = '.' # Fallback locale

LOG_FILE = os.path.join(log_dir, 'startup_log.txt')

def log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} - {msg}\n")
        print(f"[LOG] {msg}")
    except Exception as e:
        print(f"Errore scrittura log: {e}")

def start_flask():
    try:
        log("Avvio thread Flask...")
        server.start_server_thread()
    except Exception as e:
        log(f"ERRORE CRITICO FLASK: {e}")

def wait_for_server(url, timeout=30):
    start_time = time.time()
    log(f"Check server su {url}...")
    
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    log("Server RISPONDE! Status 200.")
                    return True
        except Exception as e:
            time.sleep(0.5)
            
    log("TIMEOUT: Il server non ha risposto in tempo.")
    return False

def on_closed():
    log("Finestra chiusa dall'utente. Arresto sistema.")
    os._exit(0)

if __name__ == '__main__':
    # Pulisci log precedente
    if os.path.exists(LOG_FILE): 
        try: os.remove(LOG_FILE)
        except: pass

    log(f"--- AVVIO MARKETOS su {system_os} (Log: {LOG_FILE}) ---")

    # 1. Lancia il Server
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    # 2. Aspetta il server
    if wait_for_server(SERVER_URL):
        try:
            log("Creazione finestra webview...")
            # Senza icona specifica per compatibilità Mac/Linux immediata
            window = webview.create_window(
                'MarketOS Pro', 
                SERVER_URL, 
                width=1280, 
                height=800,
                confirm_close=True,
                text_select=False
            )
            
            window.events.closed += on_closed
            
            log("Webview start...")
            webview.start()
            
        except Exception as e:
            msg = f"Errore Grafico:\n{e}\n{traceback.format_exc()}"
            log(msg)
            # Popup di errore specifico per OS
            if system_os == 'Windows':
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, msg, "Errore MarketOS", 16)
            else:
                print("CRITICAL GUI ERROR:", msg)
    else:
        msg = f"Il server non risponde sulla porta {PORT}.\nControlla il file di log in:\n{LOG_FILE}"
        log("Chiusura per mancata risposta server.")
        
        if system_os == 'Windows':
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "Errore Avvio", 16)
        else:
            print("CRITICAL STARTUP ERROR:", msg)
        
        sys.exit(1)