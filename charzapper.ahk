#NoEnv
#Warn
#SingleInstance Force
SendMode Input
SetWorkingDir %A_ScriptDir%
SetTitleMatchMode, 1

~RAlt::
if (A_PriorHotkey = "~RAlt" && A_TimeSincePriorHotkey < 400)
{
    IfWinNotExist, CharZapper
    {
        Run "C:\Python313\pythonw.exe" "charzapper.py"
        WinWait, CharZapper
        WinWaitClose, CharZapper
        Send {Ctrl down}{v}
        Send {Ctrl up}
    }
    return
}
