; Instalador do Kyra Tube (Inno Setup 6).
; Gerado pelo GitHub Actions a cada versão:
;   iscc /DAppVersion=3.0.0 installer\kyra-tube.iss
;
; Instala só para o usuário (não pede administrador). Na atualização
; automática o app roda este instalador em modo silencioso: ele fecha o
; Kyra Tube, troca os arquivos e abre o app de novo, sem janela de terminal.

#define AppName "Kyra Tube"
#define AppExe "KyraTube.exe"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
; Este identificador nunca muda: é o que faz uma versão nova atualizar a anterior.
AppId={{8F3C2B4A-5D6E-4F7A-9B1C-3E2D1A0B9C8D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=KaueFSS
AppPublisherURL=https://github.com/KaueFSS/Kyra-Tube
AppSupportURL=https://github.com/KaueFSS/Kyra-Tube/issues
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Kyra-Tube-Setup
SetupIconFile=..\assets\kyra-tube.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\KyraTube\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
; Instalação normal: caixinha "Abrir o Kyra Tube" no final.
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; Atualização silenciosa: abre o app sozinho.
Filename: "{app}\{#AppExe}"; Flags: nowait skipifnotsilent
