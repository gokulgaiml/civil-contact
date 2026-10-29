@echo off
title Cloudflare Tunnel - Civil Lead Extractor
cd /d "%~dp0"
echo ========================================================
echo  Launching Cloudflare Tunnel for Civil Lead Extractor...
echo ========================================================
python tunnel.py
pause
