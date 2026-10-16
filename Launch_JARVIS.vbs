Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\pothi\OneDrive\Documents\Jarvis"
WshShell.Run "c:\Users\pothi\OneDrive\Documents\Jarvis\.venv\Scripts\pythonw.exe main.py", 0, False
