
import os
import json
import requests
import tkinter as tk
from tkinter import messagebox
import sys

# --- CONFIGURAZIONE ---
# Sostituisci con il tuo URL RAW di GitHub (quello che finisce con /main/)
GITHUB_BASE_URL = "https://raw.githubusercontent.com/SinghProbjot/MarketOS/refs/heads/main/"

FILES_TO_UPDATE = [
    "market_os.html", 
    "server.py", 
    "desktop_app.py",
    "updater.py" 
]

VERSION_FILE = "version.json"      # File remoto su GitHub
LOCAL_VERSION_FILE = "local_version.json" # File locale sul PC

def get_remote_info():
    try:
        # Scarica il JSON completo da GitHub
        r = requests.get(GITHUB_BASE_URL + VERSION_FILE, timeout=3)
        if r.status_code == 200:
            return r.json()
        return None
    except: return None

def get_local_version():
    # Legge la versione installata
    if os.path.exists(LOCAL_VERSION_FILE):
        try: 
            data = json.load(open(LOCAL_VERSION_FILE))
            return data.get("version", "0.0")
        except: pass
    return "0.0"

def download_file(fname):
    print(f"Scaricando {fname}...")
    try:
        r = requests.get(GITHUB_BASE_URL + fname)
        if r.status_code == 200:
            with open(fname, 'wb') as f: 
                f.write(r.content)
            return True
    except Exception as e: 
        print(f"Errore download {fname}: {e}")
    return False

def check_and_update():
    print("Controllo aggiornamenti...")
    
    remote_data = get_remote_info()
    if not remote_data: 
        print("Server offline o irraggiungibile.")
        return

    # Estrae l'ultima versione dal nuovo formato JSON
    remote_ver_str = remote_data.get("latest_version", "0.0")
    local_ver_str = get_local_version()
    
    print(f"Versione Locale: {local_ver_str} -> Remota: {remote_ver_str}")

    try:
        if float(remote_ver_str) > float(local_ver_str):
            # Trova il changelog dell'ultima versione dalla storia
            changelog = "Aggiornamento disponibile"
            if "history" in remote_data:
                for release in remote_data["history"]:
                    if release["version"] == remote_ver_str:
                        changelog = release.get("changelog", "")
                        break
            
            # GUI Popup
            root = tk.Tk()
            root.withdraw()
            
            msg = f"È disponibile la versione {remote_ver_str}!\n\nNovità:\n{changelog}\n\nVuoi aggiornare ora?"
            
            if messagebox.askyesno("MarketOS Update", msg):
                success = True
                for f in FILES_TO_UPDATE: 
                    if not download_file(f):
                        success = False
                        messagebox.showerror("Errore", f"Impossibile scaricare {f}")
                        break
                
                if success:
                    # Aggiorna il file locale scrivendo solo la versione corrente
                    with open(LOCAL_VERSION_FILE, 'w') as f: 
                        json.dump({"version": remote_ver_str}, f)
                        
                    messagebox.showinfo("Fatto", "Aggiornamento installato! Il programma si riavvierà.")
            
            root.destroy()
        else:
            print("Nessun aggiornamento necessario.")
            
    except Exception as e:
        print(f"Errore nel confronto versioni: {e}")

if __name__ == "__main__":
    try:
        check_and_update()
    except Exception as e:
        print(f"Errore Updater: {e}")