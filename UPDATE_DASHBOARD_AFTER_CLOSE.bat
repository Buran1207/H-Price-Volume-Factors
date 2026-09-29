@echo off
setlocal
REM Usage: UPDATE_DASHBOARD_AFTER_CLOSE.bat "C:\path\to\V28_project"
if "%~1"=="" (
  echo Usage: %~nx0 "C:\path\to\V28_project"
  exit /b 2
)
set PROJECT_ROOT=%~1
py -3.12 "%~dp0scripts\sync_daily_outputs.py" --project-root "%PROJECT_ROOT%"
if errorlevel 1 exit /b %errorlevel%

git add dashboard_data
git commit -m "daily signal update"
if errorlevel 1 echo No data changes to commit.
git push origin main
