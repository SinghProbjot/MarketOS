; Script generato per MarketOS - Gestionale
; Richiede Inno Setup (scaricabile gratuitamente da jrsoftware.org)

#define MyAppName "MarketOS Pro"
#define MyAppVersion "6.0"
#define MyAppPublisher "Singh Probjot"
#define MyAppExeName "AVVIA_MARKET.bat"

[Setup]
; Identificativo univoco dell'app (generato casualmente, non cambiarlo dopo la prima release)
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Richiede diritti amministratore per installare Python se serve
PrivilegesRequired=admin
OutputDir=.
OutputBaseFilename=MarketOS_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Icona del setup (opzionale, se ne hai una .ico decommenta la riga sotto)
; SetupIconFile=icona_negozio.ico

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copia tutti i file necessari. Assicurati che siano nella stessa cartella di questo script .iss quando compili.
Source: "market_os.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "server.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "desktop_app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "updater.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "version.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "AVVIA_MARKET.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_env.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Crea il collegamento nel menu Start
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\server.py"; IconIndex: 0
; Crea il collegamento sul Desktop
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\server.py"; IconIndex: 0

[Run]
; Al termine dell'installazione, esegue lo script che controlla/installa Python e le librerie
Filename: "{app}\install_env.bat"; StatusMsg: "Verifica e configurazione ambiente Python..."; Flags: runhidden waituntilterminated

; Avvia l'applicazione alla fine (opzionale)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Pulisce eventuali file temporanei o log creati dopo l'installazione
Type: files; Name: "{app}\*.pyc"
Type: filesandordirs; Name: "{app}\__pycache__"
; NOTA: Non cancelliamo market.db per sicurezza, così i dati restano anche se disinstalli il software.