@echo off

pyinstaller --windowed --onefile --add-data help.html;. --add-data version.txt;. --name linux-x64 src/main.py
