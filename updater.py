
import os
import json
import requests
import tkinter as tk
from tkinter import messagebox

# --- CONFIGURAZIONE ---
# Sostituisci con il tuo URL RAW di GitHub corretto
GITHUB_BASE_URL = "https://raw.githubusercontent.com/SinghProbjot/MarketOS/refs/heads/main/"

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
        try: 
            with open(LOCAL_VERSION_FILE, 'r') as f:
                data = json.load(f)
                # FIX: Cerca prima 'latest_version', se non c'è cerca 'version'
                return data.get("latest_version", data.get("version", "0.0"))
        except: pass
    return "0.0"

def download_file(fname):
    try:
        r = requests.get(GITHUB_BASE_URL + fname)
        if r.status_code == 200:
            with open(fname, 'wb') as f: f.write(r.content)
            return True
    except: pass
    return False

def check_and_update():
    # Ottieni informazioni
    remote = get_remote_version()
    if not remote: return # Niente internet o GitHub giù

    local_ver = get_local_version()
    # Anche qui leggiamo 'latest_version' dal remoto
    remote_ver = remote.get("latest_version", remote.get("version", "0.0"))

    print(f"Versione Installata: {local_ver} | Versione Online: {remote_ver}")

    # Confronto numerico
    if float(remote_ver) > float(local_ver):
        root = tk.Tk()
        root.withdraw()
        
        # Cerca il changelog specifico nella history se esiste
        changelog = "Miglioramenti generali"
        if "history" in remote:
            for item in remote["history"]:
                if item.get("version") == remote_ver:
                    changelog = item.get("changelog", changelog)
                    break

        msg = f"È disponibile la versione {remote_ver}!\n\nNovità:\n{changelog}\n\nVuoi aggiornare ora?"
        
        if messagebox.askyesno("Aggiornamento MarketOS", msg):
            success = True
            for f in FILES_TO_UPDATE: 
                if not download_file(f): success = False
            
            if success:
                # Salva il nuovo file di versione locale identico a quello remoto
                with open(LOCAL_VERSION_FILE, 'w') as f: json.dump(remote, f, indent=2)
                messagebox.showinfo("Fatto", "Aggiornamento completato! Il programma si riavvierà.")
            else:
                messagebox.showwarning("Errore", "Errore durante il download. Riprova più tardi.")
        
        root.destroy()

if __name__ == "__main__":
    check_and_update()