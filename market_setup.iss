; Script Inno Setup per MarketOS Pro
; Configurato per installazione in AppData (Nessun problema di permessi)

#define MyAppName "MarketOS Pro"
#define MyAppVersion "6.0"
#define MyAppPublisher "Tuo Nome"
#define MyAppExeName "AVVIA_MARKET.bat"

[Setup]
; ID Univoco dell'applicazione
AppId={{MARKET-OS-PRO-V6-UUID}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; --- CARTELLA DESTINAZIONE ---
; {localappdata} punta a C:\Users\Nome\AppData\Local\
; Qui abbiamo sempre i permessi di scrittura per gli update!
DefaultDirName={localappdata}\{#MyAppName}

; Non disabilitiamo la pagina della cartella, così l'utente può cambiarla se vuole,
; ma il default è sicuro.
DisableDirPage=no

; L'installer richiede privilegi admin solo per installare le dipendenze globali (Python)
PrivilegesRequired=admin

OutputDir=.
OutputBaseFilename=MarketOS_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; I file del programma (Assicurati che siano nella stessa cartella quando compili)
Source: "market_os.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "server.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "desktop_app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "updater.py"; DestDir: "{app}"; Flags: ignoreversion

; --- FIX FONDAMENTALE QUI SOTTO ---
; Copia "version.json" (sorgente) ma lo rinomina in "local_version.json" (destinazione)
Source: "version.json"; DestDir: "{app}"; DestName: "local_version.json"; Flags: ignoreversion

Source: "AVVIA_MARKET.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_env.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Icona nel Menu Start
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\server.py"; IconIndex: 0
; Icona sul Desktop
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\server.py"; IconIndex: 0

[Run]
; 1. Installa le dipendenze (Python + Librerie)
Filename: "{app}\install_env.bat"; StatusMsg: "Configurazione ambiente e librerie..."; Flags: runhidden waituntilterminated

; 2. Avvia il programma alla fine
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Pulizia file temporanei alla disinstallazione
Type: files; Name: "{app}\*.pyc"
Type: filesandordirs; Name: "{app}\__pycache__"
; NOTA: Non cancelliamo market.db per sicurezza dei dati.