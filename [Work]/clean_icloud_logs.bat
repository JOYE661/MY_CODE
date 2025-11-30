@echo off
setlocal enabledelayedexpansion

REM iCloud Log Cleanup Script
REM Target Directory: C:\Users\17529\AppData\Local\Packages\AppleInc.iCloud_nzyj5cx40ttqa\LocalCache\Local\Logs

set "LOG_DIR=C:\Users\17529\AppData\Local\Packages\AppleInc.iCloud_nzyj5cx40ttqa\LocalCache\Local\Logs"
set "LOG_FILE=%TEMP%\icloud_cleanup.log"
set "TIMESTAMP=%DATE% %TIME%"

echo ========================================== >> "%LOG_FILE%"
echo Cleanup Start Time: %TIMESTAMP% >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

REM Check if directory exists
if not exist "%LOG_DIR%" (
    echo ERROR: Directory does not exist - %LOG_DIR% >> "%LOG_FILE%"
    echo ERROR: Directory does not exist - %LOG_DIR%
    exit /b 1
)

REM Display start information
echo Starting iCloud log file cleanup...
echo Target Directory: %LOG_DIR%

REM Count files before deletion
set /a file_count=0
for /f %%i in ('dir "%LOG_DIR%\*.log" /b /s 2^>nul ^| find /c /v ""') do set /a file_count=%%i
echo Found %file_count% log files to clean up >> "%LOG_FILE%"
echo Found %file_count% log files to clean up

REM Delete all .log files in main directory
echo. >> "%LOG_FILE%"
echo Deleting .log files in main directory: >> "%LOG_FILE%"
for /r "%LOG_DIR%" %%f in (*.log) do (
    echo Deleting: %%f >> "%LOG_FILE%"
    del "%%f" >nul 2>&1
    if !errorlevel! equ 0 (
        echo Successfully deleted: %%f >> "%LOG_FILE%"
    ) else (
        echo Failed to delete: %%f >> "%LOG_FILE%"
    )
)

REM Delete .log files in subdirectories (recursive)
echo. >> "%LOG_FILE%"
echo Deleting .log files in subdirectories: >> "%LOG_FILE%"
for /d /r "%LOG_DIR%" %%d in (*) do (
    if exist "%%d\*.log" (
        echo Processing subdirectory: %%d >> "%LOG_FILE%"
        for %%f in ("%%d\*.log") do (
            echo Deleting: %%f >> "%LOG_FILE%"
            del "%%f" >nul 2>&1
            if !errorlevel! equ 0 (
                echo Successfully deleted: %%f >> "%LOG_FILE%"
            ) else (
                echo Failed to delete: %%f >> "%LOG_FILE%"
            )
        )
    )
)

REM Count files after deletion
set /a remaining_count=0
for /f %%i in ('dir "%LOG_DIR%\*.log" /b /s 2^>nul ^| find /c /v ""') do set /a remaining_count=%%i
set /a deleted_count=file_count-remaining_count

echo. >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"
echo Cleanup Completion Time: %DATE% %TIME% >> "%LOG_FILE%"
echo Total files deleted: %deleted_count% >> "%LOG_FILE%"
echo Remaining files: %remaining_count% >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

echo.
echo Cleanup completed!
echo Total files deleted: %deleted_count%
echo Remaining files: %remaining_count%
echo Detailed log saved at: %LOG_FILE%

REM Pause to view results (only when run manually)
if "%1"=="" pause

exit /b 0
