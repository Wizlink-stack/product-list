import base64
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from http import HTTPStatus
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
import shutil
import tempfile


ROOT = Path(__file__).resolve().parent
HOST = os.getenv("PORTAL_HOST", "127.0.0.1")
PORT = 8080
SESSION_COOKIE = "product_portal_session"
SESSION_SECRET = os.getenv("PORTAL_SESSION_SECRET", "change-this-session-secret")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VISITOR_LOG_PATH = Path(os.getenv("PORTAL_LOG_PATH", "/tmp/visitor_log.jsonl" if os.getenv("VERCEL") else str(ROOT / "visitor_log.jsonl")))
PRODUCTS_DB = ROOT / "products.json"

MAIL_TO = os.getenv("PORTAL_NOTIFY_TO", "officemail8383510@gmail.com")
MAIL_FROM = os.getenv("PORTAL_SMTP_FROM", os.getenv("PORTAL_SMTP_USERNAME", ""))
MAIL_USERNAME = os.getenv("PORTAL_SMTP_USERNAME", "")
MAIL_PASSWORD = os.getenv("PORTAL_SMTP_PASSWORD", "")
MAIL_HOST = os.getenv("PORTAL_SMTP_HOST", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("PORTAL_SMTP_PORT", "587"))


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_products():
    products = []
    db_products = {}
    if PRODUCTS_DB.exists():
        with PRODUCTS_DB.open('r', encoding='utf-8') as f:
            db_products_list = json.load(f)
            for p in db_products_list:
                db_products[p['id']] = p

    # Scan images
    image_files = sorted(
        file_path
        for file_path in ROOT.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS
    )
    image_by_name = {file_path.name: file_path for file_path in image_files}

    # Build full list
    all_ids = set(db_products.keys())
    for i, file_path in enumerate(image_files, start=1):
        img_name = file_path.name
        if i in db_products:
            # DB entry with image
            db_p = db_products[i].copy()
            db_p['imageUrl'] = f"/api/product-images/{i}"
            products.append(db_p)
        else:
            # Image-only fallback
            products.append({
                "id": i,
                "name": file_path.stem or f"Image {i}",
                "image": img_name,
                "imageUrl": f"/api/product-images/{i}",
                "description": "",
                "price": 0.0,
                "status": "Available",
                "sku": f"IMG-{i:03d}",
            })
        all_ids.add(i)

    # Sort by id
    products.sort(key=lambda p: p['id'])
    return products


def get_product_image_path(product_id):
    image_files = sorted(
        file_path
        for file_path in ROOT.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS
    )

    if product_id < 1 or product_id > len(image_files):
        return None

    return image_files[product_id - 1]


def save_products(products):
    PRODUCTS_DB.parent.mkdir(parents=True, exist_ok=True)
    tmp = PRODUCTS_DB.with_suffix('.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(products, f, indent=2)
    shutil.move(tmp, PRODUCTS_DB)


def filter_products(products, query):
    if not query:
        return products
    q = query.lower()
    return [p for p in products if q in p['name'].lower() or q in (p.get('description', '') or '').lower()]


def append_visitor_log(entry):
    VISITOR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VISITOR_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry) + "\n")


def email_notifications_enabled():
    return all([MAIL_TO, MAIL_FROM, MAIL_USERNAME, MAIL_PASSWORD, MAIL_HOST, MAIL_PORT])


def send_login_notification(details):
    if not email_notifications_enabled():
        return False, "Email notifications are not configured"

    message = EmailMessage()
    message["Subject"] = f"Product Portal Login Alert: {details['email']}"
    message["From"] = MAIL_FROM
    message["To"] = MAIL_TO
    message.set_content(
        "\n".join(
            [
                "A user logged into the Product Portal.",
                "",
                f"Email: {details['email']}",
                f"Display name: {details['name']}",
                f"Login time (UTC): {details['loginTime']}",
                f"IP address: {details['ipAddress']}",
                f"User agent: {details['userAgent']}",
            ]
        )
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(MAIL_HOST, MAIL_PORT, timeout=20) as smtp:
        smtp.starttls(context=context)
        smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
        smtp.send_message(message)

    return True, "Notification sent"


def sign_data(value):
    return hmac.new(SESSION_SECRET.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def encode_session(session_data):
    payload = json.dumps(session_data, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("utf-8")
    signature = sign_data(encoded)
    return f"{encoded}.{signature}"


def decode_session(cookie_value):
    if not cookie_value or "." not in cookie_value:
        return None

    encoded, signature = cookie_value.rsplit(".", 1)
    expected_signature = sign_data(encoded)
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = base64.urlsafe_b64decode(encoded.encode("utf-8"))
        return json.loads(payload.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None


def parse_cookies(environ):
    cookie = SimpleCookie()
    raw = environ.get("HTTP_COOKIE", "")
    if raw:
        cookie.load(raw)
    return cookie


def get_session(environ):
    cookies = parse_cookies(environ)
    session_cookie = cookies.get(SESSION_COOKIE)
    if not session_cookie:
        return None
    return decode_session(session_cookie.value)


def read_json_body(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError:
        length = 0

    raw = environ["wsgi.input"].read(length) if length else b"{}"
    try:
        return json.loads(raw.decode("utf-8-sig") or "{}")
    except json.JSONDecodeError:
        form_data = parse_qs(raw.decode("utf-8", errors="ignore"))
        return {key: values[0] for key, values in form_data.items()}


def json_response(start_response, payload, status=HTTPStatus.OK, headers=None):
    body = json.dumps(payload).encode("utf-8")
    response_headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
    ]
    if headers:
        response_headers.extend(headers)
    start_response(f"{status.value} {status.phrase}", response_headers)
    return [body]


def text_response(start_response, payload, status=HTTPStatus.OK, headers=None):
    body = payload.encode("utf-8")
    response_headers = [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    if headers:
        response_headers.extend(headers)
    start_response(f"{status.value} {status.phrase}", response_headers)
    return [body]


def file_response(start_response, path):
    if not path.exists() or not path.is_file():
        return text_response(start_response, "Not Found", status=HTTPStatus.NOT_FOUND)

    mime_type, _ = mimetypes.guess_type(str(path))
    content = path.read_bytes()
    start_response(
        f"{HTTPStatus.OK.value} {HTTPStatus.OK.phrase}",
        [
            ("Content-Type", mime_type or "application/octet-stream"),
            ("Content-Length", str(len(content))),
        ],
    )
    return [content]


def build_api_cors_headers(environ):
    origin = environ.get("HTTP_ORIGIN")
    headers = [
        ("Vary", "Origin"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
        ("Access-Control-Allow-Credentials", "true"),
    ]
    if origin:
        headers.append(("Access-Control-Allow-Origin", origin))
    else:
        headers.append(("Access-Control-Allow-Origin", "*"))
    return headers


def with_api_headers(start_response, environ, path):
    if not path.startswith("/api/"):
        return start_response

    api_headers = build_api_cors_headers(environ)

    def wrapped_start_response(status, headers, exc_info=None):
        return start_response(status, headers + api_headers, exc_info)

    return wrapped_start_response


def safe_static_path(request_path):
    relative_path = request_path.lstrip("/") or "index.html"
    target = (ROOT / relative_path).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return None
    return target


def make_session_cookie(session_data):
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE] = encode_session(session_data)
    cookie[SESSION_COOKIE]["path"] = "/"
    cookie[SESSION_COOKIE]["httponly"] = True
    cookie[SESSION_COOKIE]["samesite"] = "Lax"
    if os.getenv("VERCEL"):
        cookie[SESSION_COOKIE]["secure"] = True
    return ("Set-Cookie", cookie.output(header="").strip())


def clear_session_cookie():
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE] = ""
    cookie[SESSION_COOKIE]["path"] = "/"
    cookie[SESSION_COOKIE]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
    cookie[SESSION_COOKIE]["max-age"] = 0
    return ("Set-Cookie", cookie.output(header="").strip())


def handle_health(start_response):
    return json_response(
        start_response,
        {
            "ok": True,
            "emailNotificationsConfigured": email_notifications_enabled(),
            "productCount": len(load_products()),
        },
    )


def handle_session(start_response, environ):
    session = get_session(environ)
    if not session:
        return json_response(start_response, {"authenticated": False}, status=HTTPStatus.UNAUTHORIZED)
    return json_response(start_response, {"authenticated": True, "user": session})


def handle_products(start_response, environ):
    session = get_session(environ)
    if not session:
        return json_response(
            start_response,
            {"error": "Authentication required"},
            status=HTTPStatus.UNAUTHORIZED,
        )
    query_string = environ.get('QUERY_STRING', '')
    query_params = parse_qs(query_string)
    search_query = query_params.get('search', [''])[0]
    products = load_products()
    filtered = filter_products(products, search_query)
    return json_response(start_response, {"products": filtered})


def handle_product_image(start_response, environ, product_id):
    session = get_session(environ)
    if not session:
        return json_response(
            start_response,
            {"error": "Authentication required"},
            status=HTTPStatus.UNAUTHORIZED,
        )

    image_path = get_product_image_path(product_id)
    if image_path is None:
        return text_response(start_response, "Not Found", status=HTTPStatus.NOT_FOUND)

    return file_response(start_response, image_path)


def handle_login(start_response, environ):
    payload = read_json_body(environ)
    email = (payload.get("email") or "").strip() or "anonymous"
    _password = (payload.get("password") or "").strip()

    session_data = {
        "email": email,
        "name": email.split("@", 1)[0].replace(".", " ").title() or "User",
        "loginTime": utc_now_iso(),
    }

    visitor_event = {
        "event": "login",
        "email": session_data["email"],
        "name": session_data["name"],
        "loginTime": session_data["loginTime"],
        "ipAddress": environ.get("HTTP_X_FORWARDED_FOR", environ.get("REMOTE_ADDR", "Unknown")).split(",")[0].strip(),
        "userAgent": environ.get("HTTP_USER_AGENT", "Unknown"),
    }

    log_saved = True
    try:
        append_visitor_log(visitor_event)
    except OSError:
        log_saved = False

    notification_sent = False
    notification_error = None
    try:
        notification_sent, notification_error = send_login_notification(visitor_event)
    except Exception as exc:
        notification_error = str(exc)

    return json_response(
        start_response,
        {
            "message": "Login successful",
            "user": session_data,
            "logSaved": log_saved,
            "notificationSent": notification_sent,
            "notificationStatus": notification_error,
        },
        headers=[make_session_cookie(session_data)],
    )


def handle_logout(start_response):
    return json_response(
        start_response,
        {"message": "Logged out"},
        headers=[clear_session_cookie()],
    )


def handle_create_product(start_response, environ):
    session = get_session(environ)
    if not session:
        return json_response(start_response, {"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
    payload = read_json_body(environ)
    name = payload.get('name', '').strip()
    if not name:
        return json_response(start_response, {"error": "Name required"}, status=HTTPStatus.BAD_REQUEST)
    products = load_products()
    new_id = max((p['id'] for p in products), default=0) + 1
    new_product = {
        "id": new_id,
        "name": name,
        "description": payload.get('description', ''),
        "price": float(payload.get('price', 0.0)),
        "status": payload.get('status', 'Available'),
        "sku": payload.get('sku', f"PROD-{new_id:03d}"),
        "image": ''
    }
    products.append(new_product)
    save_products(products)
    new_product["imageUrl"] = f"/api/product-images/{new_id}"
    return json_response(start_response, {"product": new_product}, status=HTTPStatus.CREATED)


def handle_update_product(start_response, environ, product_id):
    session = get_session(environ)
    if not session:
        return json_response(start_response, {"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
    if not str(product_id).isdigit():
        return json_response(start_response, {"error": "Invalid ID"}, status=HTTPStatus.BAD_REQUEST)
    product_id = int(product_id)
    payload = read_json_body(environ)
    products = load_products()
    for i, p in enumerate(products):
        if p['id'] == product_id:
            products[i]['name'] = payload.get('name', p['name']).strip()
            products[i]['description'] = payload.get('description', p['description'])
            products[i]['price'] = float(payload.get('price', p['price']))
            products[i]['status'] = payload.get('status', p['status'])
            products[i]['sku'] = payload.get('sku', p['sku'])
            # products[i]['image'] = payload.get('image', p['image'])  # update later
            save_products(products)
            products[i]['imageUrl'] = f"/api/product-images/{product_id}"
            return json_response(start_response, {"product": products[i]})
    return json_response(start_response, {"error": "Product not found"}, status=HTTPStatus.NOT_FOUND)


def handle_delete_product(start_response, environ, product_id):
    session = get_session(environ)
    if not session:
        return json_response(start_response, {"error": "Authentication required"}, status=HTTPStatus.UNAUTHORIZED)
    if not str(product_id).isdigit():
        return json_response(start_response, {"error": "Invalid ID"}, status=HTTPStatus.BAD_REQUEST)
    product_id = int(product_id)
    products = load_products()
    products = [p for p in products if p['id'] != product_id]
    save_products(products)
    return json_response(start_response, {"message": "Product deleted"})


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    start_response_with_api_headers = with_api_headers(start_response, environ, path)

    if method == "OPTIONS" and path.startswith("/api/"):
        return text_response(start_response_with_api_headers, "", status=HTTPStatus.NO_CONTENT)

    if method == "GET" and path == "/api/health":
        return handle_health(start_response_with_api_headers)
    if method == "GET" and path == "/api/session":
        return handle_session(start_response_with_api_headers, environ)
    if method == "GET" and path == "/api/products":
        return handle_products(start_response_with_api_headers, environ)
    if method == "GET" and path.startswith("/api/product-images/"):
        product_id = path.removeprefix("/api/product-images/")
        if not product_id.isdigit():
            return text_response(start_response_with_api_headers, "Not Found", status=HTTPStatus.NOT_FOUND)
        return handle_product_image(start_response_with_api_headers, environ, int(product_id))
    if method == "POST" and path == "/api/products":
        return handle_create_product(start_response_with_api_headers, environ)
    if method == "PUT" and path.startswith("/api/products/"):
        product_id = path.removeprefix("/api/products/")
        return handle_update_product(start_response_with_api_headers, environ, product_id)
    if method == "DELETE" and path.startswith("/api/products/"):
        product_id = path.removeprefix("/api/products/")
        return handle_delete_product(start_response_with_api_headers, environ, product_id)
    if method == "POST" and path == "/api/login":
        return handle_login(start_response_with_api_headers, environ)
    if method == "POST" and path == "/api/logout":
        return handle_logout(start_response_with_api_headers)

    if path == "/":
        return file_response(start_response, ROOT / "index.html")

    target = safe_static_path(path)
    if target is None:
        return text_response(start_response, "Forbidden", status=HTTPStatus.FORBIDDEN)

    return file_response(start_response, target)


def run():
    print(f"Product Portal backend running at http://{HOST}:{PORT}")
    print(f"Email notifications configured: {'yes' if email_notifications_enabled() else 'no'}")
    with make_server(HOST, PORT, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    run()
