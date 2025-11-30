@echo off
setlocal

REM Setup automatic iCloud log cleanup task on system startup

set "TASK_NAME=iCloud Log Auto Cleanup"
set "SCRIPT_PATH=%~dp0clean_icloud_logs.bat"
set "SCRIPT_DIR=%~dp0"

echo Setting up automatic iCloud log cleanup task on startup...
echo Task Name: %TASK_NAME%
echo Script Path: %SCRIPT_PATH%

REM Check if script exists
if not exist "%SCRIPT_PATH%" (
    echo ERROR: Cleanup script not found - %SCRIPT_PATH%
    pause
    exit /b 1
)

REM Create scheduled task command
set "SCHTASKS_CMD=schtasks /create /tn "%TASK_NAME%" /tr "%SCRIPT_PATH%" /sc onstart /delay 0001:00 /ru SYSTEM /f"

echo.
echo Executing command: %SCHTASKS_CMD%
echo.

REM Execute task creation
%SCHTASKS_CMD%

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Automatic cleanup task created successfully!
    echo.
    echo Task Details:
    echo - Task Name: %TASK_NAME%
    echo - Trigger: On system startup (delayed 1 minute)
    echo - Run As: SYSTEM (highest privileges)
    echo - Script: %SCRIPT_PATH%
    echo.
    echo You can manage this task through:
    echo 1. Open "Task Scheduler"
    echo 2. Select "Task Scheduler Library" in left navigation
    echo 3. Find task "%TASK_NAME%"
    echo.
    echo To delete this task, run: schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo ERROR: Task creation failed, error code: %errorlevel%
    echo Please run this script as Administrator
)

echo.
pause
