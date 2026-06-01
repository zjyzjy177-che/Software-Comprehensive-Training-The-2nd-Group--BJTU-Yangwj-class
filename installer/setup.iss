; BJTU 食堂就餐流量仿真系统 - Windows 安装器
; 使用 Inno Setup 6 编译: ISCC setup.iss

#define MyAppName "BJTU Canteen Simulation"
#define MyAppNameCN "BJTU 食堂就餐流量仿真系统"
#define MyAppVersion "3.4"
#define MyAppPublisher "BJTU 软件综合实训 第二小组"
#define MyAppURL "https://www.bjtu.edu.cn"
#define MyAppExeName "BJTU_Canteen_Simulation.exe"

[Setup]
AppId={{B3D2F8A1-6C5E-4F92-AE41-9D7E5B3C8F12}
AppName={#MyAppNameCN}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppNameCN}
DisableProgramGroupPage=no
OutputDir=..\dist
OutputBaseFilename=BJTU_Canteen_Simulation_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardImageFile=..\assets\WizardImage.bmp
WizardSmallImageFile=..\assets\WizardSmallImage.bmp
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinese"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppNameCN}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppNameCN}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppNameCN}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppNameCN}}"; Flags: nowait postinstall skipifsilent
