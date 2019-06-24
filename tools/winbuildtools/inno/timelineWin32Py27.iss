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
AppVerName=?
OutputBaseFilename=?
;
;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

AppPublisher=Rickard Lindberg <ricli85@gmail.com>
AppPublisherURL=http://thetimelineproj.sourceforge.net/
AppSupportURL=http://thetimelineproj.sourceforge.net/
AppUpdatesURL=http://thetimelineproj.sourceforge.net/
DefaultDirName={pf}\Timeline
DefaultGroupName=Timeline
SourceDir=..\
LicenseFile=COPYING
InfoBeforeFile=WINSTALL
OutputDir=..\
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"


[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu";   Description: "Create a start menu"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "dist\icons\event_icons\*"; DestDir: "{app}\icons\event_icons"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\MSVCP90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\gdiplus.dll"; DestDir: "{app}"; Flags: ignoreversion


;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
;
; Before running this script ...
; You must check to see if there are any more po-files to add
;
;!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Source: "dist\translations\ca\LC_MESSAGES\*"; DestDir: "{app}\translations\ca\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\ca\LC_MESSAGES\*"; DestDir: "{app}\translations\ca\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\de\LC_MESSAGES\*"; DestDir: "{app}\translations\de\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\de\LC_MESSAGES\*"; DestDir: "{app}\translations\de\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\el\LC_MESSAGES\*"; DestDir: "{app}\translations\el\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\el\LC_MESSAGES\*"; DestDir: "{app}\translations\el\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\es\LC_MESSAGES\*"; DestDir: "{app}\translations\es\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\es\LC_MESSAGES\*"; DestDir: "{app}\translations\es\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\eu\LC_MESSAGES\*"; DestDir: "{app}\translations\eu\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\eu\LC_MESSAGES\*"; DestDir: "{app}\translations\eu\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\fr\LC_MESSAGES\*"; DestDir: "{app}\translations\fr\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\fr\LC_MESSAGES\*"; DestDir: "{app}\translations\fr\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\gl\LC_MESSAGES\*"; DestDir: "{app}\translations\gl\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\he\LC_MESSAGES\*"; DestDir: "{app}\translations\he\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\it\LC_MESSAGES\*"; DestDir: "{app}\translations\it\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\it\LC_MESSAGES\*"; DestDir: "{app}\translations\it\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\he\LC_MESSAGES\*"; DestDir: "{app}\translations\ko\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\lt\LC_MESSAGES\*"; DestDir: "{app}\translations\lt\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\pl\LC_MESSAGES\*"; DestDir: "{app}\translations\pl\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\pl\LC_MESSAGES\*"; DestDir: "{app}\translations\pl\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\pt\LC_MESSAGES\*"; DestDir: "{app}\translations\pt\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\pt\LC_MESSAGES\*"; DestDir: "{app}\translations\pt\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\pt_BR\LC_MESSAGES\*"; DestDir: "{app}\translations\pt_BR\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\pt_BR\LC_MESSAGES\*"; DestDir: "{app}\translations\pt_BR\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\ru\LC_MESSAGES\*"; DestDir: "{app}\translations\ru\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\ru\LC_MESSAGES\*"; DestDir: "{app}\translations\ru\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\sv\LC_MESSAGES\*"; DestDir: "{app}\translations\sv\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\sv\LC_MESSAGES\*"; DestDir: "{app}\translations\sv\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\tr\LC_MESSAGES\*"; DestDir: "{app}\translations\tr\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\tr\LC_MESSAGES\*"; DestDir: "{app}\translations\tr\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\vi\LC_MESSAGES\*"; DestDir: "{app}\translations\vi\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\vi\LC_MESSAGES\*"; DestDir: "{app}\translations\vi\LC_MESSAGES"; Flags: ignoreversion

Source: "dist\translations\zh_CN\LC_MESSAGES\*"; DestDir: "{app}\translations\zh_CN\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Pgm\Python27\lib\site-packages\wx-3.0-msw\wx\locale\zh_CN\LC_MESSAGES\*"; DestDir: "{app}\translations\zh_CN\LC_MESSAGES"; Flags: ignoreversion



[UninstallDelete]
Type: files; Name: "{app}\*.log"


[Icons]
Name: "{commondesktop}\Timeline"; Filename:"{app}\timeline.exe"; IconFilename: "{app}\icons\Timeline.ico"; Tasks: desktopicon
Name: "{group}\Timeline";         Filename:"{app}\timeline.exe"; IconFilename: "{app}\icons\Timeline.ico"; WorkingDir: "{app}"; Tasks: startmenu




[Run]
Filename: "{app}\timeline.exe"; Description: "{cm:LaunchProgram,Timeline}"; Flags: shellexec postinstall skipifsilent;

