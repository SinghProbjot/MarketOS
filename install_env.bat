@echo off
:: Questo script viene eseguito da Inno Setup in modalità nascosta

:: 1. Controlla se Python esiste
python --version >NUL 2>&1
if %errorlevel% NEQ 0 (
    :: Python manca: scarica e installa (versione 3.11)
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe' -OutFile 'python_installer.exe'"
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python_installer.exe
    
    :: Aggiorna PATH per la sessione corrente
    set "PATH=%PATH%;C:\Program Files\Python311\Scripts\;C:\Program Files\Python311\"
)

:: 2. Installa le librerie necessarie
pip install flask flask-cors pywebview requests pyserial >NUL 2>&1

exit