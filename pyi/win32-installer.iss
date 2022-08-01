#define AppName "ArC ONE Control"
#define AppPublisher "ArC Instruments Ltd."
#define AppURL "http://www.arc-instruments.co.uk/"
#define AppExeName "ArC ONE Control.exe"

[Setup]
AppId={{F30A90CC-D585-47C0-98C7-6AEF960E4B36}
AppName={#AppName}
; Must be defined as a command line parameter /dAppVersion="..."
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
ArchitecturesInstallIn64BitMode=x64
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt
; Uncomment the following line to run in non administrative
; install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=ArC-ONE-Control-{#AppVersion}-Setup
SetupIconFile=..\arc1pyqt\Graphics\applogo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\ArC ONE Control\ArC ONE Control.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\ArC ONE Control\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

