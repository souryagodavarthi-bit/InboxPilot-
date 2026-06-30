import http.server
import socketserver
import json
import os
import urllib.parse
import sys
import datetime
from email.utils import parsedate_to_datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_UI_DIR = os.path.join(BASE_DIR, "web_ui")
CATEGORIES_CONFIG_FILE = os.path.join(BASE_DIR, "categories_config.json")
TRIAGE_HISTORY_FILE = os.path.join(BASE_DIR, "triage_history.json")

PORT = 8050

sys.path.append(BASE_DIR)
import InboxPilot

def load_categories():
    if os.path.exists(CATEGORIES_CONFIG_FILE):
        try:
            with open(CATEGORIES_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return InboxPilot.load_categories_config()

def save_categories(cats):
    with open(CATEGORIES_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cats, f, indent=2)

def parse_date_sort(date_str):
    if not date_str:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    try:
        dt = parsedate_to_datetime(str(date_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        pass
    return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

class InboxPilotHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve static files from web_ui
        parsed = urllib.parse.urlparse(path).path
        if parsed in ("/", "/index.html"):
            return os.path.join(WEB_UI_DIR, "index.html")
        elif parsed.startswith("/api/"):
            return super().translate_path(path)
        else:
            rel_path = parsed.lstrip("/")
            local_path = os.path.join(WEB_UI_DIR, rel_path)
            if os.path.exists(local_path):
                return local_path
            return super().translate_path(path)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/auth/google-url":
            google_creds_path = os.path.join(BASE_DIR, "google_creds.json")
            auth_url = "#"
            if os.path.exists(google_creds_path):
                try:
                    with open(google_creds_path, "r", encoding="utf-8") as f:
                        creds = json.load(f)
                    client_id = creds.get("client_id")
                    redirect_uri = creds.get("redirect_uri", "http://localhost:8501/")
                    scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.send"
                    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={urllib.parse.quote(scope)}&state=state&access_type=offline&prompt=consent"
                except Exception as e:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"url": auth_url}).encode("utf-8"))
            return

        elif path == "/api/categories":
            cats = load_categories()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(cats).encode("utf-8"))
            return

        elif path == "/api/emails":
            queue = query.get("queue", ["Queries"])[0]
            cats = load_categories()
            enabled = [c for c in cats if c.get("enabled", True) and not c.get("archived", False)]
            
            records = []
            if os.path.exists(TRIAGE_HISTORY_FILE):
                try:
                    with open(TRIAGE_HISTORY_FILE, "r", encoding="utf-8") as f:
                        records = json.load(f)
                except Exception:
                    pass

            if queue == "Escalated":
                filtered = [r for r in records if r.get("escalated", False)]
            else:
                cat_obj = next((c for c in enabled if c["label"] == queue), None)
                cat_name = cat_obj["name"] if cat_obj else queue
                filtered = [r for r in records if r.get("category") == cat_name and not r.get("escalated", False)]

            # Sort strictly from most to least recent
            filtered.sort(key=lambda x: parse_date_sort(x.get("date", "")), reverse=True)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(filtered).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        data = json.loads(body) if body else {}

        if path == "/api/categories/toggle":
            cats = load_categories()
            cat_name = data.get("name")
            enable_state = data.get("enabled", True)
            archive_state = data.get("archived", False)

            enabled_count = sum(1 for c in cats if c.get("enabled", True) and not c.get("archived", False))

            if archive_state and enabled_count <= 1:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Cannot remove category. At least 1 active category is required."}).encode("utf-8"))
                return

            for c in cats:
                if c["name"] == cat_name:
                    if archive_state:
                        c["archived"] = True
                        c["enabled"] = False
                    else:
                        c["enabled"] = enable_state
            save_categories(cats)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": f"Category {cat_name} updated."}).encode("utf-8"))
            return

        elif path == "/api/categories/add":
            cats = load_categories()
            enabled_count = sum(1 for c in cats if c.get("enabled", True) and not c.get("archived", False))
            if enabled_count >= 8:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Maximum limit of 8 active categories reached."}).encode("utf-8"))
                return

            name = data.get("name", "").strip()
            desc = data.get("description", "").strip()
            mode = data.get("automation_mode", "semi_automated")

            if not name or not desc:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Name and description are required."}).encode("utf-8"))
                return

            safe_key = "".join(x for x in name.title() if x.isalnum())
            safe_dir = name.replace(" ", "_")

            new_cat = {
                "name": safe_key,
                "label": name,
                "dir_name": safe_dir,
                "description": desc,
                "is_standard": False,
                "enabled": True,
                "automation_mode": mode,
                "has_auto_reply": (mode == "automated"),
                "escalate_on_reply": (mode == "manual")
            }
            cats.append(new_cat)
            save_categories(cats)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": f"Category '{name}' added successfully!"}).encode("utf-8"))
            return

        elif path == "/api/triage":
            # Run local triage process
            try:
                InboxPilot.process_all_incoming_files()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "AI Triage executed on all incoming files."}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), InboxPilotHandler) as httpd:
        print(f"InboxPilot+ Modern UI Server running at http://localhost:{PORT}")
        httpd.serve_forever()
