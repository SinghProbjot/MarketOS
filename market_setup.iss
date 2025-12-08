; Script Inno Setup per MarketOS Pro v8.x

#define MyAppName "MarketOS Pro"
#define MyAppVersion "8.0"
#define MyAppPublisher "Tuo Nome"
#define MyAppExeName "AVVIA_MARKET.bat"

[Setup]
; ID Univoco dell'applicazione
AppId={{MARKET-OS-PRO-V7-UUID}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; --- ICONA DELL'INSTALLER ---
SetupIconFile=logo.ico

; --- CARTELLA DESTINAZIONE ---
; {localappdata} punta a C:\Users\Nome\AppData\Local\
DefaultDirName={localappdata}\{#MyAppName}
DisableDirPage=no

; Richiede privilegi admin solo per installare le dipendenze (Python)
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
; Copia tutti i file necessari
Source: "market_os.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "server.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "desktop_app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "updater.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "version.json"; DestDir: "{app}"; DestName: "local_version.json"; Flags: ignoreversion
Source: "AVVIA_MARKET.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_env.bat"; DestDir: "{app}"; Flags: ignoreversion

; --- FIX ICONA ---
; Importante: Copiamo il file .ico nella cartella del programma
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Icona nel Menu Start
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"

; Icona sul Desktop
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"

[Run]
; 1. Installa le dipendenze (Python + Librerie)
Filename: "{app}\install_env.bat"; StatusMsg: "Configurazione ambiente e librerie..."; Flags: runhidden waituntilterminated

; 2. Avvia il programma alla fine
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Pulizia file temporanei alla disinstallazione
Type: files; Name: "{app}\*.pyc"
Type: filesandordirs; Name: "{app}\__pycache__"
; NOTA: Non cancelliamo market.db per sicurezza dei dati