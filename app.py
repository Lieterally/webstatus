from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from flask_wtf.csrf import CSRFProtect
from slugify import slugify
import requests
import os
from flask_migrate import Migrate
import json
import time
from statistics import median
from collections import Counter
from threading import Lock
import pathlib
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.exc import OperationalError
from datetime import datetime
import urllib3
from flask import make_response
from concurrent.futures import ThreadPoolExecutor
from models import db, Website, Page, User
from routes.websites import websites_bp  # import the blueprint
from routes.dashboard import dashboard_bp  # import the blueprint
from routes.auth import auth_bp  # import the blueprint
from notifWhatsapp import notifWhatsapp
from notifTelegram import notifTelegram
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, PHONE_NUM

migrate = Migrate()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f'{SQLALCHEMY_DATABASE_URI}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = f'{SECRET_KEY}'

# (Optional) consistent names for constraints – helps Alembic on MySQL



db.init_app(app)
migrate.init_app(app, db)

# Register blueprint
app.register_blueprint(websites_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

csrf = CSRFProtect(app)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECK_REPEATS = 3                 # run 3 checks inside each 10-minute cycle
NOTIF_COOLDOWN_CYCLES = 6         # re-notify if still down after 6 cycles
STATE_FILE = os.path.join(BASE_DIR, "status_cache.json")  # small local cache
_state_lock = Lock()


def _load_state():
    """Load or init the cache that tracks last status & notify cooldown per site."""
    try:
        if not pathlib.Path(STATE_FILE).exists():
            return {}
        with _state_lock:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f) or {}
    except Exception:
        return {}


def _save_state(state):
    try:
        with _state_lock:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    

def _site_key(site: dict) -> str:
    """Prefer a stable ID if present; otherwise fall back to link."""
    return str(site.get("id_web") or site["link_web"])

def _rehydrate_state_for_sites(state: dict, sites: list[dict]) -> dict:
    """
    Project the cache to only current sites AND carry display fields.
    Each entry now stores: nama_web, link_web, last_status, cycles_since_last_notif.
    """
    new_state = {}
    for s in sites:
        key = _site_key(s)
        prev = state.get(key, {})
        new_state[key] = {
            "nama_web": s["nama_web"],                         # <-- stored
            "link_web": s["link_web"],                         # (optional but handy)
            "last_status": prev.get("last_status", "UNKNOWN"),
            "cycles_since_last_notif": int(prev.get("cycles_since_last_notif", NOTIF_COOLDOWN_CYCLES)),
        }
    return new_state


# When using sites.json ------------------

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# def load_sites():
#     with open(os.path.join(BASE_DIR, "sites.json")) as f:
#         return json.load(f)



# When using db --------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def load_sites():
    with app.app_context():
        websites = Website.query.all()
        sites = []
        for site in websites:
            sites.append({
                "id_web": site.id_web,
                "nama_web": site.nama_web,
                "link_web": site.link_web,
                "halaman_web": [page.halaman_web for page in site.pages]
            })
        return sites
    
    
def count_sites():
    
    websites = Website.query.all()
    sites = len(websites)
    return sites



def check_site(link_web, halaman_web):
    statuses = []
    total_time = 0
    count = 0
    # down_detected = False
    down_pages = []
  
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    for halaman in halaman_web:
        url = link_web + halaman
        try:
            
            r = requests.get(url, headers=headers, timeout=5, verify=False)
            
            elapsed = r.elapsed.total_seconds()
            # print(f"⏱️ Checked {url} in {elapsed} seconds")
            total_time += elapsed
            count += 1
            if r.status_code == 200:
                status = f"✅ UP {r.status_code}"
            else:
                status = f"⚠️ {r.status_code}"
                # down_detected = True
                down_pages.append(halaman)
        except requests.RequestException:
            status = "❌ DOWN"
            elapsed = 0
            # down_detected = True
            down_pages.append(halaman)

        statuses.append({
            "url": url,
            "status": status,
            "response_time": round(elapsed, 3)
        })
        
        # print(statuses)
        
    # overall_status = "✅ UP" if not down_detected else "❌ DOWN"

    if not down_pages:
        overall_status = "✅ UP"
    else:
        down_list = ", ".join(down_pages)
        overall_status = f"❌ DOWN ({down_list})"
    avg_response_time = round(total_time / count, 3) if count > 0 else "N/A"

    return statuses, overall_status, avg_response_time

def check_site_multi(link_web, halaman_web, repeats=CHECK_REPEATS, per_attempt_pause=0.2):
    """
    Run multiple checks in a row and decide by majority (>=2 of 3).
    Pages are marked DOWN if they are DOWN in >=2 attempts.
    """
    attempt_results = []
    avg_times = []

    for _ in range(repeats):
        statuses, overall_status, avg_response_time = check_site(link_web, halaman_web)
        attempt_results.append((statuses, overall_status))
        if isinstance(avg_response_time, (int, float)):
            avg_times.append(avg_response_time)
        if per_attempt_pause:
            time.sleep(per_attempt_pause)  # tiny pause between attempts (optional)

    # Majority decision for site
    downs = sum(1 for _, overall in attempt_results if "❌" in overall)
    final_is_down = downs >= ((repeats // 2) + 1)

    # Majority decision per-page
    page_down_counter = Counter()
    for statuses, overall in attempt_results:
        # any "DOWN" or non-200 page within this attempt increments the page counter
        for s in statuses:
            st = s["status"]
            if st.startswith("❌") or st.startswith("⚠️"):
                # add by path part only (after domain), since s["url"] is full
                try:
                    page_down_counter[s["url"].replace(link_web, "", 1)] += 1
                except Exception:
                    pass

    down_pages_majority = sorted([p for p, c in page_down_counter.items() if c >= ((repeats // 2) + 1)])

    if final_is_down:
        if down_pages_majority:
            overall_status = f"❌ DOWN ({', '.join(down_pages_majority)})"
        else:
            overall_status = "❌ DOWN"
    else:
        overall_status = "✅ UP"

    # Median response time for stability
    final_avg_time = round(median(avg_times), 3) if avg_times else "N/A"

    # Merge one set of statuses to show in UI (use the last attempt for simplicity)
    statuses_for_ui = attempt_results[-1][0]

    return statuses_for_ui, overall_status, final_avg_time

def run_monitor_cycle():
    try:
        sites = load_sites()
        print("✅ sites loaded")
    except Exception as e:
        print("❌ error loading sites:", e)
        raise

    # Keep cache aligned with current sites *every cycle*
    state = _load_state()
    state = _rehydrate_state_for_sites(state, sites)
    _save_state(state)

    def monitor(site):
        statuses, overall_status, avg_response_time = check_site_multi(site["link_web"], site["halaman_web"])
        return {
            "site_key": _site_key(site),
            "nama_web": site["nama_web"],
            "link_web": site["link_web"],
            "overall_status": overall_status,
            "avg_response_time": avg_response_time,
            "statuses": statuses
        }

    with ThreadPoolExecutor(max_workers=10) as executor:
        monitored = list(executor.map(monitor, sites))

    # --- Notification throttling logic (per-site) ---
    sites_to_notify_down = []
    sites_recovered = []

    current_state = _load_state()
    current_state = _rehydrate_state_for_sites(current_state, sites)

    for web in monitored:
        key = web["site_key"]
        link_web = web["link_web"]
        name = web["nama_web"]
        is_down = "❌" in web["overall_status"]

        prev = current_state.get(key, {"last_status": "UNKNOWN", "cycles_since_last_notif": NOTIF_COOLDOWN_CYCLES})
        last_status = prev.get("last_status", "UNKNOWN")
        since = int(prev.get("cycles_since_last_notif", NOTIF_COOLDOWN_CYCLES))

        should_notify_down = False
        should_notify_recovered = False

        if is_down:
            if last_status != "DOWN":
                should_notify_down = True
                since = 0
            else:
                since += 1
                if since >= NOTIF_COOLDOWN_CYCLES:
                    should_notify_down = True
                    since = 0
        else:
            if last_status == "DOWN":
                should_notify_recovered = True
            since = NOTIF_COOLDOWN_CYCLES

        current_state[key].update({
            "nama_web": name,
            "link_web": link_web,
            "last_status": "DOWN" if is_down else "UP",
            "cycles_since_last_notif": since
        })

        if should_notify_down:
            sites_to_notify_down.append({"nama_web": name, "link_web": link_web, "overall_status": web["overall_status"]})
        if should_notify_recovered:
            sites_recovered.append({"nama_web": name, "link_web": link_web, "overall_status": "✅ UP"})

    _save_state(current_state)

    # notifications
    if sites_to_notify_down:
        status_wa_down = ", ".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_to_notify_down])
        list_web_tele_down = "\n".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_to_notify_down])
        notifWhatsapp(f"{PHONE_NUM}", "⚠️⚠️ Website Down ⚠️⚠️", status_wa_down)
        notifTelegram("⚠️⚠️ Website Down ⚠️⚠️", list_web_tele_down)

    if sites_recovered:
        status_wa_up = ", ".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_recovered])
        list_web_tele_up = "\n".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_recovered])
        notifWhatsapp(f"{PHONE_NUM}", "✅ Website UP ✅", status_wa_up)
        notifTelegram("✅ Website UP ✅", list_web_tele_up)

    return {
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "monitored": monitored
    }


@app.route("/status")
def status():
    try:
        result = run_monitor_cycle()
        response = make_response(jsonify(result))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# def status():
#     try:
#         sites = load_sites()
#         print("✅ sites loaded")
#     except Exception as e:
#         print("❌ error in /status:", e)
#         return jsonify({"error": str(e)}), 500
    
#     # Keep cache aligned with current sites *every cycle*
#     state = _load_state()
#     state = _rehydrate_state_for_sites(state, sites)
#     _save_state(state)  # optional early save

#     def monitor(site):
#         # ⬇️ use triple-check with majority vote
#         statuses, overall_status, avg_response_time = check_site_multi(site["link_web"], site["halaman_web"])
#         return {
#             "site_key": _site_key(site),  # carry resolved key forward
#             "nama_web": site["nama_web"],
#             "link_web": site["link_web"],
#             "overall_status": overall_status,
#             "avg_response_time": avg_response_time,
#             "statuses": statuses
#         }

#     # parallel per site, each site does its own 3 sequential attempts
#     with ThreadPoolExecutor(max_workers=10) as executor:
#         monitored = list(executor.map(monitor, sites))

#     # --- Notification throttling logic (per-site) ---
#     sites_to_notify_down = []   # sites that should trigger a DOWN alert this cycle
#     sites_recovered = []        # sites that transitioned DOWN -> UP this cycle
    
#     # Re-load (in case another worker wrote it), then update entries for current run
#     current_state = _load_state()
#     current_state = _rehydrate_state_for_sites(current_state, sites)

#     for web in monitored:
#         key = web["site_key"]
#         link_web = web["link_web"]
#         name = web["nama_web"]
#         is_down = "❌" in web["overall_status"]

#         prev = current_state.get(key, {
#             "last_status": "UNKNOWN",
#             "cycles_since_last_notif": NOTIF_COOLDOWN_CYCLES,
#         })
        
#         last_status = prev.get("last_status", "UNKNOWN")
#         since = int(prev.get("cycles_since_last_notif", NOTIF_COOLDOWN_CYCLES))

#         should_notify_down = False
#         should_notify_recovered = False

#         if is_down:
#             if last_status != "DOWN":
#                 # First time (or after being UP): alert immediately
#                 should_notify_down = True
#                 since = 0
#             else:
#                 # Still DOWN: only re-alert every N cycles
#                 since += 1
#                 if since >= NOTIF_COOLDOWN_CYCLES:
#                     should_notify_down = True
#                     since = 0
#         else:
#             # Site is UP now
#             if last_status == "DOWN":
#                 # Recovered message
#                 should_notify_recovered = True
#             # Reset so next DOWN alerts immediately
#             since = NOTIF_COOLDOWN_CYCLES

#         current_state[key].update({
#     "nama_web": name,                         # <-- keep name synced
#     "link_web": link_web,                         # (optional)
#     "last_status": "DOWN" if is_down else "UP",
#     "cycles_since_last_notif": since
# })

#         if should_notify_down:
#             sites_to_notify_down.append({
#                 "nama_web": name,
#                 "link_web": link_web,
#                 "overall_status": web["overall_status"]
#             })

#         if should_notify_recovered:
#             sites_recovered.append({
#                 "nama_web": name,
#                 "link_web": link_web,
#                 "overall_status": "✅ UP"
#             })

#     _save_state(current_state)

#     # --- Send NOTIF for DOWN (if any) ---
#     if sites_to_notify_down:
#         phone_number = f'{PHONE_NUM}'  # WA

#         description_down = "⚠️⚠️ Website Down ⚠️⚠️"
#         # WA: inline comma-separated
#         status_wa_down = ", ".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_to_notify_down])
#         # Telegram: one per line
#         list_web_tele_down = "\n".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_to_notify_down])

#         notifWhatsapp(phone_number, description_down, status_wa_down)
#         notifTelegram(description_down, list_web_tele_down)

#     # --- Send NOTIF for RECOVERED (if any) ---
#     if sites_recovered:
#         phone_number = f'{PHONE_NUM}'  # WA

#         description_up = "✅ Website UP ✅"
#         status_wa_up = ", ".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_recovered])
#         list_web_tele_up = "\n".join([f"{s['nama_web']} ({s['link_web']})" for s in sites_recovered])

#         notifWhatsapp(phone_number, description_up, status_wa_up)
#         notifTelegram(description_up, list_web_tele_up)

#     response = make_response(jsonify({
#         "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "monitored": monitored
#     }))
#     response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
#     return response

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard-test")
def dashboardtest():
    return render_template("dashboard.html")

@app.route("/full")
def indexFull():
    return render_template("indexFull.html")


if __name__ == "__main__":
    app.run(debug=True)