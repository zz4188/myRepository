; TicketMaster NSIS 安装脚本
; 生成 Windows 安装程序

!define APP_NAME "TicketMaster"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "TicketMaster Team"
!define APP_URL "https://github.com/yourusername/TicketMaster"

; 安装程序配置
Name "${APP_NAME} v${APP_VERSION}"
OutFile "TicketMaster-${APP_VERSION}-setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallPath"
RequestExecutionLevel admin

; 安装程序图标
Icon "icons\app_icon.ico"
UninstallIcon "icons\app_icon.ico"

; 现代化界面
!include "MUI2.nsh"

; 页面设置
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言设置
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装节
Section "主程序" SecMain
    SectionIn RO

    SetOutPath $INSTDIR

    ; 复制所有文件
    File /r "dist\TicketMaster\*.*"

    ; 创建快捷方式
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\TicketMaster.exe" "" "$INSTDIR\TicketMaster.exe" 0
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\TicketMaster.exe" "" "$INSTDIR\TicketMaster.exe" 0

    ; 创建卸载快捷方式
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\卸载.lnk" "$INSTDIR\uninstall.exe"

    ; 写入注册表
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallPath" $INSTDIR
    WriteRegStr HKLM "Software\${APP_NAME}" "Version" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "QuietUninstallString" "$INSTDIR\uninstall.exe /S"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1

    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"

SectionEnd

; 卸载节
Section "Uninstall"
    ; 删除文件和目录
    RMDir /r "$INSTDIR"

    ; 删除快捷方式
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\卸载.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"

    ; 删除注册表项
    DeleteRegKey HKLM "Software\${APP_NAME}"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

SectionEnd
