@echo off
chcp 65001 > nul
title Twitch Timestamp Bot

echo [INFO] Starting Twitch Timestamp Bot...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please create it using: python -m venv venv ^&^& .\venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

.\venv\Scripts\python.exe bot.py
if errorlevel 1 (
    echo.
    echo [ERROR] Bot exited with an error.
    pause
)
