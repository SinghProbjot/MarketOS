#!/bin/bash

# Ottiene la cartella dove si trova questo file
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "--- AVVIO MARKET OS (macOS) ---"

# 1. Controlla se Python 3 è installato
if ! command -v python3 &> /dev/null
then
    echo "Python 3 non trovato! Installalo da python.org"
    exit 1
fi

# 2. Installa dipendenze se mancano (Silenzioso)
echo "Verifica dipendenze..."
pip3 install flask flask-cors pywebview requests > /dev/null 2>&1

# 3. Esegui Updater
echo "Controllo aggiornamenti..."
python3 updater.py

# 4. Avvia Applicazione
echo "Avvio interfaccia..."
# nohup e & servono per lanciare in background senza bloccare il terminale
nohup python3 desktop_app.py > /dev/null 2>&1 &

exit 0