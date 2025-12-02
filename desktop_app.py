import webview
import threading
import time
import sys
import urllib.request
import os
import traceback
import server # Importa il server locale

# --- CONFIGURAZIONE ---
PORT = 5500
SERVER_URL = f'http://127.0.0.1:{PORT}'

# Percorso Sicuro per i Log (AppData)
app_data_dir = os.getenv('APPDATA')
log_dir = os.path.join(app_data_dir, 'MarketOS')
if not os.path.exists(log_dir):
    try: os.makedirs(log_dir)
    except: log_dir = '.' 

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

    log(f"--- AVVIO MARKETOS (Log in: {LOG_FILE}) ---")

    # 1. Lancia il Server in background
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    # 2. Aspetta che il server sia vivo
    if wait_for_server(SERVER_URL):
        try:
            log("Creazione finestra webview...")
            # VERSIONE SENZA PARAMETRO 'ICON' PER MASSIMA COMPATIBILITÀ
            window = webview.create_window(
                'MarketOS Pro', 
                SERVER_URL, 
                width=1280, 
                height=800,
                confirm_close=True,
                text_select=False
            )
            
            # Colleghiamo l'evento di chiusura
            window.events.closed += on_closed
            
            log("Webview start...")
            webview.start()
            
        except Exception as e:
            log(f"ERRORE GUI CRITICO: {e}\n{traceback.format_exc()}")
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Errore Grafico:\n{e}", "Errore MarketOS", 16)
    else:
        log("Chiusura per mancata risposta server.")
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"Il server non risponde sulla porta {PORT}.\nControlla il file di log in:\n{LOG_FILE}", "Errore Avvio", 16)
        sys.exit(1)