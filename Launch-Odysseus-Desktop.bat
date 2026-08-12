@echo off
title Launching Odysseus AI Suite Desktop App...
echo Starting Odysseus Python FastAPI Server & Electron Desktop Window...

cd /d "%~dp0"
npx electron .

pause
