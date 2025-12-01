import os
import json
import requests
import tkinter as tk
from tkinter import messagebox

# Sostituisci con il tuo URL RAW di GitHub
GITHUB_BASE_URL = "https://github.com/SinghProbjot/MarketOS.git"
FILES_TO_UPDATE = ["market_os.html", "server.py"]
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
    try:
        r = requests.get(GITHUB_BASE_URL + fname)
        if r.status_code == 200:
            with open(fname, 'wb') as f: f.write(r.content)
            return True
    except: pass
    return False

def check_and_update():
    remote = get_remote_version()
    if not remote: return

    local = get_local_version()
    if float(remote.get("version", 0)) > float(local.get("version", 0)):
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("Aggiornamento", f"Nuova versione {remote['version']} disponibile!\nAggiornare ora?"):
            for f in FILES_TO_UPDATE: download_file(f)
            with open(LOCAL_VERSION_FILE, 'w') as f: json.dump(remote, f)
            messagebox.showinfo("Fatto", "Aggiornamento completato! Riavvio in corso...")
        root.destroy()