@echo off
setlocal
REM Start backend server for Product List Portal

cd /d "c:\Users\MY PC\Desktop\product list"

echo.
echo ================================================
echo   Product List Portal - Local Server
echo ================================================
echo.
echo Starting backend server on port 8080...
echo Access the website at: http://www.productlist:8080
echo OR: http://localhost:8080
echo.
echo Press Ctrl+C to stop the server
echo.

python server.py
