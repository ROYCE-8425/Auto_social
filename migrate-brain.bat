@echo off
chcp 65001 >nul
title Chuan hoa cau truc Brain Default
cd /d "%~dp0"
echo.
echo  ==========================================
echo   Chuan hoa cau truc project brain
echo   brain  ->  Brain Default  (phang: agents/ workflows/ memory/ skills/)
echo  ==========================================
echo.
echo  [!] Hay chac chan da TAT server (stop-javis.bat) truoc khi chay.
echo.
pause

REM 1. Doi ten brain -> Brain Default (chi khi chua co Brain Default)
if exist "brain" if not exist "Brain Default" (
  echo   - Doi ten: brain  ->  Brain Default
  ren "brain" "Brain Default"
)

REM 2. Lam phang cau truc ben trong (chi move khi dich chua ton tai)
if exist "Brain Default\Javis\agents" if not exist "Brain Default\agents" (
  echo   - Move: Javis\agents  ->  agents
  move "Brain Default\Javis\agents" "Brain Default\agents" >nul
)
if exist "Brain Default\Javis\workflows" if not exist "Brain Default\workflows" (
  echo   - Move: Javis\workflows  ->  workflows
  move "Brain Default\Javis\workflows" "Brain Default\workflows" >nul
)
if exist "Brain Default\Memory" if not exist "Brain Default\memory" (
  echo   - Move: Memory  ->  memory
  move "Brain Default\Memory" "Brain Default\memory" >nul
)
if not exist "Brain Default\skills" (
  echo   - Tao: skills\  ^(noi dat skill chia nhom^)
  mkdir "Brain Default\skills"
)

echo.
echo  Xong. Bay gio chay setup.bat de bat lai server.
echo.
pause
