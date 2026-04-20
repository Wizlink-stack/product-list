🚀 WEBSITE HOSTING INSTRUCTIONS
================================

Your Product Portal website is ready to be hosted locally!

📋 QUICK START (Easiest Method)
================================

Option 1: Using the Setup Script (Recommended)
----------------------------------------------
1. Right-click on "setup_and_start.bat" 
2. Select "Run as administrator"
3. The server will start automatically
4. Open your browser and go to: http://www.productlist:8080

✓ Login: Enter any email and password (min 6 chars)
✓ View products: See your product images in the portal


Option 2: Manual Server Start
------------------------------
1. Double-click on "start_server.bat"
2. Server starts on port 8080
3. Access via: http://localhost:8080

Note: With this option, you'll use http://localhost:8080 instead of www.productlist


🔧 TO ENABLE www.productlist DOMAIN
====================================

If you want to use www.productlist without the port number, modify your hosts file:

1. Open Notepad as Administrator
2. Go to File → Open
3. Navigate to: C:\Windows\System32\drivers\etc\
4. Change file type to "All Files (*.*)"
5. Open the file "hosts"
6. Add this line at the bottom:
   127.0.0.1       www.productlist

7. Save and close
8. Now you can access: http://www.productlist

(This requires admin privileges)


📱 ACCESS URLS
==============

After starting the server:

✓ Full URL:     http://www.productlist:8080
✓ Localhost:    http://localhost:8080
✓ Local IP:     http://127.0.0.1:8080

(You can also access from other devices on your network using your computer's IP)


🛑 TO STOP THE SERVER
=====================

Simply close the command prompt window or press Ctrl+C


📁 FOLDER STRUCTURE
===================

product list/
├── index.html              (Login page)
├── products.html           (Product portal)
├── start_server.bat        (Simple server launcher)
├── setup_and_start.bat     (Admin setup + server)
├── ,.jpg                   (Product image)
└── Indian container...jpg  (Product image)


🔐 LOGIN CREDENTIALS
====================

Email:     Any valid email format (e.g., user@example.com)
Password:  At least 6 characters
           
Example: user@example.com / password123


✅ FEATURES
===========

✓ Professional login page with validation
✓ Beautiful product gallery
✓ Responsive design (works on mobile & desktop)
✓ Modern glassmorphism UI
✓ Professional color scheme
✓ Smooth animations


💡 TIPS
======

- Keep the server running while browsing
- You can access the site from multiple browser tabs
- Images load from the product list folder
- All styling is modern and professional


Need help? Check that:
1. Python 3 is installed (run: python --version)
2. You have internet connectivity (not required, it's local)
3. Port 8080 is not blocked by firewall
4. Run batch files as Administrator for full functionality
