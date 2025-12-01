import webview
import threading
import time
import sys
import server
import urllib.request
# Non importiamo più updater qui per evitare conflitti di file lock

def start_flask():
    """Avvia il server in un thread e gestisce eventuali errori silenziosi"""
    try:
        server.start_server_thread()
    except Exception as e:
        print(f"Errore critico server: {e}")

def wait_for_server(url, timeout=15):
    """Bussa al server finché non risponde o scade il tempo"""
    start_time = time.time()
    print(f"In attesa del server su {url}...")
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    print("Server pronto!")
                    return True
        except:
            time.sleep(0.5) 
    return False

def on_closed():
    print("Chiusura applicazione...")
    sys.exit()

if __name__ == '__main__':
    # L'aggiornamento è delegato al file .bat che lancia updater.py PRIMA di questo script.
    # Questo evita errori di "Permesso Negato" su Windows.

    # 1. Avvia Server Database
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    server_url = 'http://127.0.0.1:5000'

    # 2. CONTROLLO ATTIVO
    if wait_for_server(server_url):
        window = webview.create_window(
            'MarketOS Pro', 
            server_url, 
            width=1280, 
            height=800,
            confirm_close=True,
            text_select=False
        )
        webview.start(on_closed)
    else:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, "Errore Critico: Il Database non si è avviato.", "Errore MarketOS", 16)
        sys.exit(1)