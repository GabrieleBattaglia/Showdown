; MESS, l'installatore con Inno Setup 6.
; Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
; 23/10/2026: nasce con la tappa 14, sul modello di MeTeOra.iss, per la richiesta di Gabriele del
; 23 ottobre 2026: il pacchetto ha l'installatore, e l'installatore chiede di accettare la licenza.
;
; Si compila con python setup_maker.py, dopo PyInstaller e zip_maker.py: lo script passa la
; versione di version.py. L'installatore affianca lo zip dell'aggiornamento automatico, che usa
; sempre lo zip; si installa per utente, senza amministratore, perché MESS scrive il mondo accanto
; all'eseguibile e l'aggiornamento automatico sostituisce i file nella sua cartella; alla
; disinstallazione chiede se cancellare anche il mondo e le impostazioni.

#ifndef Versione
  #error Manca la versione: si compila con python setup_maker.py
#endif

[Setup]
; L'identità dell'installazione: non cambia mai.
AppId={{C442DC21-A3A1-4E14-844C-645899A77571}
AppName=MESS
AppVersion={#Versione}
AppVerName=MESS {#Versione}
AppPublisher=Gabriele Battaglia (IZ4APU)
AppPublisherURL=https://github.com/GabrieleBattaglia/Showdown
AppSupportURL=https://github.com/GabrieleBattaglia/Showdown/issues
AppUpdatesURL=https://github.com/GabrieleBattaglia/Showdown/releases
VersionInfoVersion={#Versione}
; La licenza GPL 3, da accettare prima di installare.
LicenseFile=LICENSE
; Per utente: con PrivilegesRequired=lowest {autopf} è la cartella Programs di AppData\Local.
PrivilegesRequired=lowest
DefaultDirName={autopf}\MESS
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=.
OutputBaseFilename=MESS-Setup-{#Versione}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no
UninstallDisplayName=MESS
UninstallDisplayIcon={app}\MESS.exe
; MESS aperto tiene questo mutex (istanza.py): installazione e disinstallazione chiedono di chiuderlo.
AppMutex=MESS
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "italiano"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; Prima di installare, via le cartelle del programma lasciate da una versione precedente. Un MESS
; aggiornato da solo ha in _internal il manifesto dello zip: se restasse, al primo avvio
; pulisci_residui cancellerebbe tutti i file nuovi che quel manifesto non elenca. I dati
; dell'utente stanno fuori da _internal, accanto all'eseguibile, e restano dove sono.
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\_internal_vecchio"

[Files]
; Il pacchetto a cartella di PyInstaller, senza i dati che una prova avesse lasciato in dist, come fa zip_maker.py.
; Ogni motivo comincia con la barra rovesciata, che lo lega alla cartella dell'eseguibile: senza,
; formule.json toglierebbe anche _internal\dati\tornei\formule.json, le formule predefinite.
Source: "dist\MESS\*"; DestDir: "{app}"; Excludes: "\mess_mondo.json*,\mess_impostazioni.json,\formule.json,\*.log,\*.log.1,\*.tmp,\tornei\*,\cronache\*,\salvataggi_illeggibili\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\MESS"; Filename: "{app}\MESS.exe"
Name: "{autodesktop}\MESS"; Filename: "{app}\MESS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MESS.exe"; Description: "{cm:LaunchProgram,MESS}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; L'aggiornamento automatico può portare in _internal file che l'installatore non conosce: la
; cartella del programma si toglie intera. I dati stanno fuori da _internal, accanto all'eseguibile.
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\_internal_vecchio"

[Code]
// I dati di MESS: il mondo e la sua copia, le impostazioni, i modelli e le formule dei tornei,
// le cronache, i salvataggi illeggibili e i registri.
procedure CancellaIDati(const Cartella: String);
begin
  DeleteFile(Cartella + '\mess_mondo.json.gz');
  DeleteFile(Cartella + '\mess_mondo.json.gz.bak');
  DeleteFile(Cartella + '\mess_mondo.json');
  DeleteFile(Cartella + '\mess_mondo.json.bak');
  DeleteFile(Cartella + '\mess_mondo.json.gz.tmp');
  DeleteFile(Cartella + '\mess_impostazioni.json');
  DeleteFile(Cartella + '\formule.json');
  DeleteFile(Cartella + '\vecchie_glorie.log');
  DeleteFile(Cartella + '\auto_updater_error.log');
  DeleteFile(Cartella + '\MESS - Errori.log');
  DeleteFile(Cartella + '\MESS - Errori.log.1');
  DeleteFile(Cartella + '\MESS - Crash.log');
  DeleteFile(Cartella + '\MESS - Crash precedente.log');
  DelTree(Cartella + '\tornei', True, True, True);
  DelTree(Cartella + '\cronache', True, True, True);
  DelTree(Cartella + '\salvataggi_illeggibili', True, True, True);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent then
  begin
    if MsgBox('Cancello anche i dati di MESS? Il mondo, la sua copia di sicurezza, le impostazioni, i tornei e le cronache. ' +
        'Con No restano nella cartella, e reinstallando MESS ritrovi il tuo mondo.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      CancellaIDati(ExpandConstant('{app}'));
    // La cartella si toglie solo se è rimasta vuota.
    RemoveDir(ExpandConstant('{app}'));
  end;
end;
