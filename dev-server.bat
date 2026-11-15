@echo off
REM Date Versioning - local dev server (Windows): builds the site, then serves _site/
REM Usage: dev-server.bat [port] [--no-dev-mode] [--lan]
REM   port            default: 8080
REM   --no-dev-mode   don't force DEV_MODE on for this run (see scripts\dev-server.py)
REM   --lan           listen on all interfaces so phones/tablets on your network can
REM                   connect (prints the addresses to open); default is 127.0.0.1 only
REM Needs Python 3 and: pip install -r requirements.txt
setlocal
set "DIR=%~dp0"
python "%DIR%scripts\dev-server.py" %*
