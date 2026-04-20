@echo off
REM Copy these commands into your terminal before running the server.
REM For Gmail, use a Gmail App Password, not your regular Gmail password.

set PORTAL_SMTP_USERNAME=your_gmail@gmail.com
set PORTAL_SMTP_PASSWORD=your_16_character_app_password
set PORTAL_SMTP_FROM=your_gmail@gmail.com
set PORTAL_NOTIFY_TO=officemail8383510@gmail.com

python server.py
