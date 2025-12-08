@echo off
TITLE MarketOS - Pulizia Processi
COLOR 0C

echo.
echo      KILL SWITCH - MARKET OS
echo.
echo Sto chiudendo forzatamente tutti i processi Python/MarketOS bloccati...
echo.

:: Chiude tutti i processi Python (attenzione: chiude anche altri script python se ne hai aperti)
taskkill /F /IM python.exe /T >NUL 2>&1
taskkill /F /IM pythonw.exe /T >NUL 2>&1

echo.
echo Processi terminati. Porta 5000 liberata.
echo Ora puoi riprovare ad avviare "AVVIA_MARKET.bat".
echo.
pause