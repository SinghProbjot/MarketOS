import os
import json
import requests
import tkinter as tk
from tkinter import messagebox
import sys

# --- CONFIGURAZIONE ---
GITHUB_BASE_URL = "https://raw.githubusercontent.com/SinghProbjot/MarketOS/refs/heads/main/"

# Ora aggiorna TUTTO il pacchetto
FILES_TO_UPDATE = [
    "market_os.html", 
    "server.py", 
    "desktop_app.py",
    "updater.py" 
]

VERSION_FILE = "version.json"
LOCAL_VERSION_FILE = "local_version.json"

def get_remote_version():
    try:
        r = requests.get(GITHUB_BASE_URL + VERSION_FILE, timeout=3)
        return r.json() if r.status_code == 200 else None
    except: return None

def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        try: return json.load(open(LOCAL_VERSION_FILE))
        except: pass
    return {"version": "0.0"}

def download_file(fname):
    print(f"Scaricando {fname}...")
    try:
        r = requests.get(GITHUB_BASE_URL + fname)
        if r.status_code == 200:
            with open(fname, 'wb') as f: 
                f.write(r.content)
            return True
        else:
            print(f"Errore download {fname}: Status {r.status_code}")
    except Exception as e: 
        print(f"Eccezione su {fname}: {e}")
    return False

def check_and_update():
    print("Controllo versione remota...")
    remote = get_remote_version()
    if not remote: 
        print("Server aggiornamenti non raggiungibile.")
        return

    local = get_local_version()
    print(f"Versione Locale: {local.get('version')} - Remota: {remote.get('version')}")

    if float(remote.get("version", 0)) > float(local.get("version", 0)):
        # GUI Popup
        root = tk.Tk()
        root.withdraw()
        
        changelog = remote.get('changelog', 'Miglioramenti vari')
        msg = f"Nuova versione {remote['version']} disponibile!\n\nNovità:\n{changelog}\n\nVuoi scaricare l'aggiornamento?"
        
        if messagebox.askyesno("MarketOS Update", msg):
            success = True
            for f in FILES_TO_UPDATE: 
                if not download_file(f):
                    success = False
                    messagebox.showerror("Errore", f"Impossibile scaricare {f}")
                    break
            
            if success:
                with open(LOCAL_VERSION_FILE, 'w') as f: json.dump(remote, f)
                messagebox.showinfo("Fatto", "Aggiornamento completato! Il programma si avvierà ora.")
            else:
                messagebox.showwarning("Attenzione", "Aggiornamento parziale. Potrebbero esserci errori.")
        
        root.destroy()
    else:
        print("Nessun aggiornamento necessario.")

if __name__ == "__main__":
    try:
        check_and_update()
    except Exception as e:
        print(f"Errore Updater Critico: {e}")
        # Non blocchiamo l'avvio se l'updater fallisce