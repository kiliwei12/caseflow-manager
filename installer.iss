#define MyAppName "CaseFlow"
#define MyAppVersion "1.1.1"
#define MyAppPublisher "CaseFlow"
#define MyAppExeName "CaseFlow.exe"

[Setup]
AppId={{48D28C53-8C45-43D7-BBC0-2431077A54ED}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\CaseFlow
DefaultGroupName=CaseFlow
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=CaseFlow-Windows-Setup-v{#MyAppVersion}
SetupIconFile=build_assets\CaseFlow.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\CaseFlow.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\CaseFlow"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\CaseFlow"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标："; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 CaseFlow"; Flags: nowait postinstall skipifsilent
