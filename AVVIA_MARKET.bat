@echo off
TITLE MarketOS Launcher
COLOR 0B

:: 1. Posizionati nella cartella corretta (Cruciale se lanciato da Desktop)
cd /d "%~dp0"

:: 2. Controllo Aggiornamenti (Prima di avviare qualsiasi altra cosa)
echo Controllo aggiornamenti in corso...
python updater.py

:: 3. Avvio Applicazione
echo Avvio MarketOS...
start /B pythonw desktop_app.py

exit