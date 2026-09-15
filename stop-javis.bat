@echo off
chcp 65001 >nul
title Dung Javis OS
echo Dang tim va tat Javis OS...
REM Logic giet nam trong stop-javis.ps1 (giet theo dung python cua venv + chu port 7777).
REM KHONG dung timeout o day: chay an qua VBS se loi "Input redirection is not supported".
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-javis.ps1"
REM Don cua so CMD den "Javis OS" kieu cu con sot (flow moi chay an, khong tao cua so nay).
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Javis OS*" >nul 2>&1
echo Xong.
exit /b 0
