@echo off
setlocal

REM This script optionally maps www.productlist and then starts the backend.

echo.
echo ================================================
echo   Product List Portal - Setup and Launch
echo ================================================
echo.

cd /d "c:\Users\MY PC\Desktop\product list"

set "HOSTS_FILE=C:\Windows\System32\drivers\etc\hosts"
set "HOST_ENTRY=127.0.0.1 www.productlist"

echo Checking optional local domain mapping...
findstr /I /C:"www.productlist" "%HOSTS_FILE%" >nul 2>&1
if errorlevel 1 (
    openfiles >nul 2>&1
    if errorlevel 1 (
        echo Skipping hosts file update because this window is not running as Administrator.
        echo You can still use: http://localhost:8080
    ) else (
        echo Adding www.productlist to hosts file...
        >>"%HOSTS_FILE%" echo %HOST_ENTRY%
    )
) else (
    echo www.productlist is already mapped.
)

echo.
if defined PORTAL_SMTP_USERNAME (
    echo Email notifications are configured for: %PORTAL_NOTIFY_TO%
) else (
    echo Email notifications are not configured yet.
    echo Optional variables:
    echo   set PORTAL_SMTP_USERNAME=your_gmail@gmail.com
    echo   set PORTAL_SMTP_PASSWORD=your_gmail_app_password
    echo   set PORTAL_SMTP_FROM=your_gmail@gmail.com
    echo   set PORTAL_NOTIFY_TO=officemail8383510@gmail.com
    echo.
    echo The site will still run normally without email alerts.
)

echo.
echo ================================================
echo   Backend Server Starting...
echo ================================================
echo.
echo Open one of these URLs:
echo   http://localhost:8080
echo   http://www.productlist:8080
echo.
echo Press Ctrl+C to stop the server
echo.

python server.py
