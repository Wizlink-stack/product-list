# Product List Portal

A professional product portal website with:
- Modern login page with backend authentication
- Dynamic product gallery served from the backend
- Optional email alerts for successful logins
- Vercel-ready Python deployment
- Responsive design for mobile and desktop
- Professional UI with glassmorphism effects

## Quick Start

### Local Development
```bash
python server.py
```

Then open: http://localhost:8080

### Vercel Deployment
This project is prepared for Vercel's Python runtime. `server.py` exposes a top-level WSGI `app`, which matches Vercel's current Python deployment requirements.
When deployed on Vercel, visitor log writes fall back to temporary storage unless you provide a persistent `PORTAL_LOG_PATH`.

If you want email alerts for successful logins, set these environment variables first:

```bash
set PORTAL_SMTP_USERNAME=your_gmail@gmail.com
set PORTAL_SMTP_PASSWORD=your_gmail_app_password
set PORTAL_SMTP_FROM=your_gmail@gmail.com
set PORTAL_NOTIFY_TO=officemail8383510@gmail.com
python server.py
```

## Features

- Backend API for login, session, products, and logout
- Cookie-based session handling
- Dynamic product image discovery from the project folder
- Visitor login events saved to `visitor_log.jsonl`
- Optional email notifications without collecting passwords
- Responsive design
- Modern animations
- Mobile-friendly
- Glass morphism UI

## Files

- `index.html` - Login page
- `products.html` - Product portal
- `server.py` - Backend server and API
- `vercel.json` - Vercel project configuration
- `email_setup_example.bat` - Example mail configuration
- Images stored in the project folder

## Login Credentials

- Email: Any valid email format
- Password: Minimum 6 characters

Example: `user@example.com` / `password123`
