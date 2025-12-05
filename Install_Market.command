#!/bin/bash

echo "========================================="
echo "   INSTALLAZIONE MARKET OS - macOS"
echo "========================================="

# Cartella sorgente (dove si trova questo script)
SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Cartella destinazione (Applicazioni Utente)
INSTALL_DIR="$HOME/Applications/MarketOS"

# 1. Crea Cartella
echo "[1/4] Creazione cartella installazione..."
mkdir -p "$INSTALL_DIR"

# 2. Copia File
echo "[2/4] Copia dei file..."
cp "$SOURCE_DIR/market_os.html" "$INSTALL_DIR/"
cp "$SOURCE_DIR/server.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/desktop_app.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/updater.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/version.json" "$INSTALL_DIR/local_version.json"
cp "$SOURCE_DIR/Start_Market.command" "$INSTALL_DIR/"

# Rendi eseguibile il launcher copiato
chmod +x "$INSTALL_DIR/Start_Market.command"

# 3. Installa Dipendenze
echo "[3/4] Installazione librerie Python..."
if ! command -v python3 &> /dev/null
then
    echo "ERRORE: Python 3 non è installato. Installalo prima di continuare."
    exit 1
fi
pip3 install flask flask-cors pywebview requests pyserial

# 4. Crea Collegamento Desktop
echo "[4/4] Creazione collegamento..."
ln -sf "$INSTALL_DIR/Start_Market.command" "$HOME/Desktop/MarketOS"

echo ""
echo "✅ INSTALLAZIONE COMPLETATA!"
echo "Troverai l'icona 'MarketOS' sul tuo Desktop."
echo ""