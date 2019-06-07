#!/usr/bin/env bash

pyinstaller --windowed --onefile --add-data help.html:. --add-data version.txt:. --name linux-x64 src/main.py
