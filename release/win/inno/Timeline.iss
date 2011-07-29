; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
AppName=Timeline
;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
;
; Before running this script ...
; The two lines below must be uncommented and text changed to reflect
; the version number of the executable to be built.
;
AppVerName= 
OutputBaseFilename=
;
;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

AppPublisher=Rickard Lindberg <ricli85@gmail.com>
AppPublisherURL=http://thetimelineproj.sourceforge.net/
AppSupportURL=http://thetimelineproj.sourceforge.net/
AppUpdatesURL=http://thetimelineproj.sourceforge.net/
DefaultDirName={pf}\Timeline
DefaultGroupName=Timeline
SourceDir=..\..\..\
LicenseFile=COPYING
InfoBeforeFile=release\win\inno\WINSTALL
OutputDir=..\bin\
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"


[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu";   Description: "Create a start menu"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\help_resources\*"; DestDir: "{app}\help_resources"; Flags: ignoreversion
Source: "dist\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "C:\Program Files\Python25\lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Program Files\Python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll"; DestDir: "{app}"; Flags: ignoreversion


;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
;
; Before running this script ...
; You must check to see if there are any more po-files to add
;
;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Source: "dist\po\ca\LC_MESSAGES\*"; DestDir: "{app}\po\ca\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\de\LC_MESSAGES\*"; DestDir: "{app}\po\de\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\es\LC_MESSAGES\*"; DestDir: "{app}\po\es\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\fr\LC_MESSAGES\*"; DestDir: "{app}\po\fr\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\he\LC_MESSAGES\*"; DestDir: "{app}\po\he\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\it\LC_MESSAGES\*"; DestDir: "{app}\po\it\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\lt\LC_MESSAGES\*"; DestDir: "{app}\po\lt\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\pl\LC_MESSAGES\*"; DestDir: "{app}\po\pl\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\pt\LC_MESSAGES\*"; DestDir: "{app}\po\pt\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\pt_BR\LC_MESSAGES\*"; DestDir: "{app}\po\pt_BR\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\ru\LC_MESSAGES\*"; DestDir: "{app}\po\ru\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\sv\LC_MESSAGES\*"; DestDir: "{app}\po\sv\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\tr\LC_MESSAGES\*"; DestDir: "{app}\po\tr\LC_MESSAGES"; Flags: ignoreversion
Source: "dist\po\vi\LC_MESSAGES\*"; DestDir: "{app}\po\vi\LC_MESSAGES"; Flags: ignoreversion


[UninstallDelete]
Type: files; Name: "{app}\*.log"


[Icons]
Name: "{commondesktop}\Timeline"; Filename:"{app}\timeline.exe"; IconFilename: "{app}\icons\Timeline.ico"; Tasks: desktopicon
Name: "{group}\Timeline";         Filename:"{app}\timeline.exe"; IconFilename: "{app}\icons\Timeline.ico"; WorkingDir: "{app}"; Tasks: startmenu




[Run]
Filename: "{app}\timeline.exe"; Description: "{cm:LaunchProgram,Timeline}"; Flags: shellexec postinstall skipifsilent;

