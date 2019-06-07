@echo off

pyinstaller --windowed --onefile --icon icon.ico --add-data help.html;. --add-data version.txt;. --name windows-x64 src/main.py
