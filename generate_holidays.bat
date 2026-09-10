@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo  Holiday data generator (update_holidays.py)
echo ==================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] python not found. Install it from https://www.python.org and retry.
    set RESULT=1
    goto :report
)

python -c "import requests" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 'requests' package missing. Run: pip install requests
    set RESULT=1
    goto :report
)

python update_holidays.py
set RESULT=%ERRORLEVEL%

:report
echo.
echo ==================================================
if "%RESULT%"=="0" (
    echo  RESULT: OK
) else (
    echo  RESULT: NOK - check the log above
)
echo ==================================================
echo.
echo Next: git add -A ^&^& git commit ^&^& git push
echo.
pause
exit /b %RESULT%
