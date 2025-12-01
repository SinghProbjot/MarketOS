import webview
import threading
import time
import sys
import server
import updater 

def start_flask():
    server.start_server_thread()

def on_closed():
    sys.exit()

if __name__ == '__main__':
    try:
        updater.check_and_update()
    except: pass

    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()
    
    time.sleep(1)

    window = webview.create_window(
        'MarketOS Pro', 
        'http://127.0.0.1:5000', 
        width=1280, 
        height=800,
        confirm_close=True
    )
    webview.start(on_closed)