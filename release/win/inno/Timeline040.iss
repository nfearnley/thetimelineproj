; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
AppName=Timeline
AppVerName=Timeline 0.6.0
AppPublisher=Rickard Lindberg <ricli85@gmail.com>
AppPublisherURL=http://thetimelineproj.sourceforge.net/
AppSupportURL=http://thetimelineproj.sourceforge.net/
AppUpdatesURL=http://thetimelineproj.sourceforge.net/
DefaultDirName={pf}\Timeline
DefaultGroupName=Timeline
LicenseFile=w:\Projekt\Hg\win\timeline\COPYING
InfoBeforeFile=w:\Projekt\Hg\win\timeline\INSTALL
InfoAfterFile=w:\Projekt\Hg\win\timeline\README
OutputDir=w:\Projekt\Hg\win\bin\
OutputBaseFilename=SetupTimeline060_py25_wx28
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "w:\Projekt\Hg\win\timeline\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\timeline\help_resources\*"; DestDir: "{app}\help_resources"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "w:\Projekt\Hg\win\timeline\src\*.py"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\timeline\po\sv\LC_MESSAGES\*"; DestDir: "{app}\po\sv\LC_MESSAGES\"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\timeline\po\de\LC_MESSAGES\*"; DestDir: "{app}\po\de\LC_MESSAGES\"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\timeline\po\es\LC_MESSAGES\*"; DestDir: "{app}\po\es\LC_MESSAGES\"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\timeline\po\pt\LC_MESSAGES\*"; DestDir: "{app}\po\pt\LC_MESSAGES\"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\timeline\po\pt_BR\LC_MESSAGES\*"; DestDir: "{app}\po\pt_BR\LC_MESSAGES\"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\timeline\tests\data\*.timeline"; DestDir: "{app}\samples"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\inno\run.pyw"; DestDir: "{app}"; Flags: ignoreversion
Source: "w:\Projekt\Hg\win\inno\Timeline.ico"; DestDir: "{app}\icons"; Flags: ignoreversion

[UninstallDelete]
Type: files; Name: "{app}\src\*.pyc"

[Icons]
Name: "{commondesktop}\Timeline"; Filename:"{app}\run.pyw"; IconFilename: "{app}\icons\Timeline.ico";Tasks: desktopicon

[Run]
Filename: "{app}\run.pyw"; Description: "{cm:LaunchProgram,Timeline}"; Flags: shellexec postinstall skipifsilent

[Code]
var
  PythonPath : String;
  InstallPath : String;

function InitializeSetup(): Boolean;
var
  Names      : TArrayOfString;
  i          : Integer;
  PythonFound: Boolean;
  WxPythonFound: Boolean;
  Key        : String;
  Path       : String;
  wxs        : TArrayOfString;
begin
    Key := 'Software\Python\PythonCore\2.5';
    //
    // Try to find python registered under Current User
    //
    PythonFound :=  RegGetSubkeyNames(HKEY_CURRENT_USER, Key , Names);
    if PythonFound then
    begin
        Key := Key + '\InstallPath';
        if not RegQueryStringValue(HKEY_CURRENT_USER, Key, '', InstallPath) then
        begin
          PythonFound := False;
        end;
    end
    //
    // Try to find python registered under Local Machine
    //
    else begin
      PythonFound := RegGetSubkeyNames(HKEY_LOCAL_MACHINE, Key, Names);
      if PythonFound then
      begin
        Key := Key + '\InstallPath';
        if not RegQueryStringValue(HKEY_LOCAL_MACHINE, Key, '', InstallPath) then
        begin
          PythonFound := False;
        end;
      end
    end;

    //
    // Python found... Continue installation
    //
    if PythonFound then
    begin
      Result := True
    end;

    //
    // If Python installation not found... Continue anyway ?
    //
    if not PythonFound then
    begin
      Result := False;
      if MsgBox('Cant find python:' #13#13 'Python version 2.5 must be installed first.' #13 'Continue Setup anyway?', mbInformation, MB_YESNO)= IDYES then
      begin
        Result := True
      end
    end

    //
    // Try find wxPython if installation is to be continued
    //
    if Result then
    begin
       WxPythonFound := False;
       //MsgBox(InstallPath, mbInformation, MB_OK);
       InstallPath := InstallPath + 'Lib\site-packages'
       //
       // Hmm not so nice!
       //
       SetArrayLength(wxs, 2)
       wxs[0] := '\wx-2.8-msw-ansi' ;
       wxs[1] := '\wx-2.8-msw-unicode' ;
       for i := 0 to GetArrayLength(wxs)-1 do begin
         path := InstallPath + wxs[i]
         //MsgBox(path, mbInformation, MB_OK);
         if DirExists(path) then
         begin
           WxPythonFound := True;
         end
       end

       //
       // wxPython found... Continue installation
       //
       if WxPythonFound then
       begin
         Result := True
       end;

    //
    // If wxPython installation not found... Continue anyway ?
    //
       if not WxPythonFound then
       begin
         Result := False
         if MsgBox('Cant find wxPython:' #13#13 'wxPython version 2.8 must be installed first.' #13 'Continue Setup anyway?', mbInformation, MB_YESNO) = IDYES then
         begin
           Result := True
         end
       end
    end

end;
