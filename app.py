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
from models import db, Website, Page, User, TelegramTarget
from routes.websites import websites_bp  # import the blueprint
from routes.dashboard import dashboard_bp  # import the blueprint
from routes.auth import auth_bp  # import the blueprint
from routes.monitoring import monitoring_bp  # import the blueprint
from routes.profile import profile_bp  # import the blueprint
from routes.telegram_targets import telegram_targets_bp  # import the blueprint

from notifWhatsapp import notifWhatsapp
from notifTelegram import notifTelegram
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from threading import Thread
from datetime import timedelta
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, PHONE_NUM
from telegram_chat import run_telegram_bot

migrate = Migrate()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f'{SQLALCHEMY_DATABASE_URI}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = f'{SECRET_KEY}'


db.init_app(app)
migrate.init_app(app, db)

# Register blueprint
app.register_blueprint(websites_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(telegram_targets_bp)


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
IS_REFRESHING = False


INTERVAL_SECONDS = 600  # 10 minutes
LATEST_STATUS = {"last_check": None, "monitored": []}
NEXT_RUN_AT = None
_bg_state_lock = Lock()
_scheduler_started = False


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
    return str(site.get("id_web") or site["url_web"])


def _rehydrate_state_for_sites(state: dict, sites: list[dict]) -> dict:
    """
    Project the cache to only current sites AND carry display fields.
    Each entry now stores: nama_web, url_web, last_status, cycles_since_last_notif.
    """
    new_state = {}
    for s in sites:
        key = _site_key(s)
        prev = state.get(key, {})
        new_state[key] = {
            "nama_web": s["nama_web"],                         # <-- stored
            # (optional but handy)
            "url_web": s["url_web"],
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
                "url_web": site.url_web,
                "halaman_web": [page.halaman_web for page in site.pages]
            })
        return sites


def count_sites():

    websites = Website.query.all()
    sites = len(websites)
    return sites


def check_site(url_web, halaman_web):
    statuses = []
    total_time = 0
    count = 0
    # down_detected = False
    down_pages = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    for halaman in halaman_web:
        url = url_web + halaman
        try:

            r = requests.get(url, headers=headers, timeout=(2, 5), verify=False)

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

        print(statuses)

    # overall_status = "✅ UP" if not down_detected else "❌ DOWN"

    if not down_pages:
        overall_status = "✅ UP"
    else:
        down_list = ", ".join(down_pages)
        overall_status = f"❌ DOWN ({down_list})"
    avg_response_time = round(total_time / count, 3) if count > 0 else "N/A"

    return statuses, overall_status, avg_response_time


def check_site_multi(url_web, halaman_web, repeats=CHECK_REPEATS, per_attempt_pause=1):
    """
    Run N checks in a row (default 3). The cycle's final result is whatever the
    Nth (third) check returns. Earlier attempts are ignored for UP/DOWN decision.
    """
    last_statuses = None
    last_overall_status = None
    last_avg_response_time = None

    for i in range(repeats):
        statuses, overall_status, avg_response_time = check_site(
            url_web, halaman_web)
        last_statuses = statuses
        last_overall_status = overall_status
        last_avg_response_time = avg_response_time

        # small pause between attempts, but not after the last one
        if per_attempt_pause and i < repeats - 1:
            time.sleep(per_attempt_pause)

    # Return ONLY the final (third) attempt's results
    return last_statuses, last_overall_status, last_avg_response_time


def monitor_and_notify_once():
    # === this is literally your current /status body, but returning a snapshot ===
    global IS_REFRESHING, LATEST_STATUS, NEXT_RUN_AT
    try:
        with _bg_state_lock:
            IS_REFRESHING = True
        sites = load_sites()
        print("✅ sites loaded")

        # Keep cache aligned each cycle
        state = _load_state()
        state = _rehydrate_state_for_sites(state, sites)
        _save_state(state)

        def monitor(site):
            # OLD:
            # statuses, overall_status, avg_response_time = check_site_multi(
            #     site["url_web"], site["halaman_web"])

            # NEW (one check only):
            statuses, overall_status, avg_response_time = check_site(
                site["url_web"], site["halaman_web"]
            )

            return {
                "site_key": _site_key(site),
                "nama_web": site["nama_web"],
                "url_web": site["url_web"],
                "overall_status": overall_status,
                "avg_response_time": avg_response_time,
                "statuses": statuses,
            }

        with ThreadPoolExecutor(max_workers=30) as executor:
            monitored = list(executor.map(monitor, sites))

        sites_to_notify_down = []
        sites_recovered = []

        current_state = _load_state()
        current_state = _rehydrate_state_for_sites(current_state, sites)

        for web in monitored:
            key = web["site_key"]
            url_web = web["url_web"]
            name = web["nama_web"]
            is_down = "❌" in web["overall_status"]

            prev = current_state.get(key, {
                "last_status": "UNKNOWN",
                "cycles_since_last_notif": NOTIF_COOLDOWN_CYCLES,
            })
            last_status = prev.get("last_status", "UNKNOWN")
            since = int(
                prev.get("cycles_since_last_notif", NOTIF_COOLDOWN_CYCLES))

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
                "url_web": url_web,
                "last_status": "DOWN" if is_down else "UP",
                "cycles_since_last_notif": since
            })

            if should_notify_down:
                sites_to_notify_down.append({
                    "nama_web": name,
                    "url_web": url_web,
                    "overall_status": web["overall_status"]
                })
            if should_notify_recovered:
                sites_recovered.append({
                    "nama_web": name,
                    "url_web": url_web,
                    "overall_status": "✅ UP"
                })

        _save_state(current_state)

        # Notifs

        with app.app_context():
            telegram_targets = TelegramTarget.query.filter_by(
                is_active=True).all()

        chat_ids = [t.chat_id for t in telegram_targets]

        if sites_to_notify_down:
            phone_number = f'{PHONE_NUM}'
            description_down = "⚠️⚠️ Website Down ⚠️⚠️"
            status_wa_down = ", ".join(
                [f"{s['nama_web']} ({s['url_web']})" for s in sites_to_notify_down])
            list_web_tele_down = "\n".join(
                [f"{s['nama_web']} ({s['url_web']})" for s in sites_to_notify_down])
            # notifWhatsapp(phone_number, description_down, status_wa_down)

            notifTelegram(chat_ids, description_down, list_web_tele_down)

        if sites_recovered:
            phone_number = f'{PHONE_NUM}'
            description_up = "✅ Website UP ✅"
            status_wa_up = ", ".join(
                [f"{s['nama_web']} ({s['url_web']})" for s in sites_recovered])
            list_web_tele_up = "\n".join(
                [f"{s['nama_web']} ({s['url_web']})" for s in sites_recovered])
            # notifWhatsapp(phone_number, description_up, status_wa_up)

            notifTelegram(chat_ids, description_up, list_web_tele_up)

        # Save snapshot for the UI to read
        snapshot = {
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "monitored": monitored,
        }
        # with _bg_state_lock:
        #     LATEST_STATUS = snapshot
        #     NEXT_RUN_AT = datetime.now() + timedelta(seconds=INTERVAL_SECONDS)

        with _bg_state_lock:
            LATEST_STATUS = snapshot

            # Only reset schedule if it's missing or already passed
            if NEXT_RUN_AT is None or datetime.now() >= NEXT_RUN_AT:
                NEXT_RUN_AT = datetime.now() + timedelta(seconds=INTERVAL_SECONDS)
    finally:
        with _bg_state_lock:
            IS_REFRESHING = False    # <— clear the flag


# === helpers for single-site refresh ===

def _compute_seconds_until_next():
    with _bg_state_lock:
        nra = NEXT_RUN_AT
    if nra is None:
        return None
    return max(0, int((nra - datetime.now()).total_seconds()))


def _ensure_site_in_state(state: dict, site: dict) -> str:
    """
    Make sure `state` has an entry for this site, and keep ALL other sites.
    Also keep `nama_web` / `url_web` in sync.
    Returns the key for the site.
    """
    key = _site_key(site)
    entry = state.get(key)
    if entry is None:
        state[key] = {
            "nama_web": site["nama_web"],
            "url_web": site["url_web"],
            "last_status": "UNKNOWN",
            "cycles_since_last_notif": NOTIF_COOLDOWN_CYCLES,
        }
    else:
        # keep display fields fresh
        entry["nama_web"] = site["nama_web"]
        entry["url_web"] = site["url_web"]
    return key


def _refresh_one_site(site_dict):
    """
    Run ONE check for a single site, apply notify throttling, update status_cache.json,
    and build the refreshed payload for this site.
    """
    # Single probe (you’ve switched to 1x per cycle)
    statuses, overall_status, avg_response_time = check_site(
        site_dict["url_web"], site_dict["halaman_web"]
    )

    refreshed = {
        "site_key": _site_key(site_dict),
        "nama_web": site_dict["nama_web"],
        "url_web": site_dict["url_web"],
        "overall_status": overall_status,
        "avg_response_time": avg_response_time,
        "statuses": statuses,
    }

    # Load + update cached notify state for THIS site only
    current_state = _load_state()

    key = _site_key(site_dict)
    entry = current_state.get(key, {
        "nama_web": site_dict["nama_web"],
        "url_web": site_dict["url_web"],
        "last_status": "UNKNOWN",
        "cycles_since_last_notif": NOTIF_COOLDOWN_CYCLES,
    })

    is_down = "❌" in refreshed["overall_status"]
    last_status = entry.get("last_status", "UNKNOWN")
    since = int(entry.get("cycles_since_last_notif", NOTIF_COOLDOWN_CYCLES))

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

    # --- Update ONLY this site's entry ---
    current_state[key] = {
        "nama_web": site_dict["nama_web"],
        "url_web": site_dict["url_web"],
        "last_status": "DOWN" if is_down else "UP",
        "cycles_since_last_notif": since,
    }

    # --- Save the merged state (preserving others) ---
    _save_state(current_state)

    # --- Notifications ---

    with app.app_context():
        telegram_targets = TelegramTarget.query.filter_by(
            is_active=True).all()

    chat_ids = [t.chat_id for t in telegram_targets]

    if should_notify_down:
        description_down = "⚠️⚠️ Website Down ⚠️⚠️"
        # notifWhatsapp(f"{PHONE_NUM}", description_down,
        #               f"{site_dict['nama_web']} ({site_dict['url_web']})")

        notifTelegram(chat_ids, description_down,
                      f"{site_dict['nama_web']} ({site_dict['url_web']})")

    if should_notify_recovered:
        description_up = "✅ Website UP ✅"
        # notifWhatsapp(f"{PHONE_NUM}", description_up,
        #               f"{site_dict['nama_web']} ({site_dict['url_web']})")

        notifTelegram(chat_ids, description_up,
                      f"{site_dict['nama_web']} ({site_dict['url_web']})")

    return refreshed


# def _background_runner():
#     # Run once immediately so the UI has data
#     try:
#         monitor_and_notify_once()
#     except Exception as e:
#         print("❌ initial background cycle error:", e)

#     # Then wait full interval between subsequent runs
#     while True:
#         time.sleep(INTERVAL_SECONDS)
#         try:
#             monitor_and_notify_once()
#         except Exception as e:
#             print("❌ background cycle error:", e)

def _background_runner():
    global NEXT_RUN_AT

    # Run once immediately so the UI has data
    try:
        monitor_and_notify_once()
    except Exception as e:
        print("❌ initial background cycle error:", e)

    while True:
        try:
            now = datetime.now()

            with _bg_state_lock:
                if NEXT_RUN_AT is None:
                    NEXT_RUN_AT = now + timedelta(seconds=INTERVAL_SECONDS)

                wait_seconds = max(0, (NEXT_RUN_AT - now).total_seconds())

            # sleep until the exact scheduled time
            time.sleep(wait_seconds)

            monitor_and_notify_once()

        except Exception as e:
            print("❌ background cycle error:", e)


def _start_background_once():
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True
    Thread(target=_background_runner, daemon=True).start()


def _start_telegram_bot():
    Thread(target=run_telegram_bot, daemon=True).start()


# helper
def _prime_next_run_if_needed():
    global NEXT_RUN_AT
    if NEXT_RUN_AT is None:
        # don't run a full monitor cycle here; just give the UI a countdown
        NEXT_RUN_AT = datetime.now() + timedelta(seconds=INTERVAL_SECONDS)


def _ensure_next_run():
    global NEXT_RUN_AT
    if NEXT_RUN_AT is None:
        NEXT_RUN_AT = datetime.now() + timedelta(seconds=INTERVAL_SECONDS)


def _seconds_until_next():
    _ensure_next_run()
    return max(0, int((NEXT_RUN_AT - datetime.now()).total_seconds()))


@app.route("/status")
def status():
    _ensure_next_run()
    with _bg_state_lock:
        data = dict(LATEST_STATUS)
        refreshing = IS_REFRESHING
        nra = NEXT_RUN_AT

    data["next_run_at"] = nra.strftime("%Y-%m-%d %H:%M:%S") if nra else None
    data["seconds_until_next"] = _seconds_until_next()
    data["refreshing"] = refreshing

    resp = make_response(jsonify(data))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["X-Accel-Buffering"] = "no"
    return resp


@csrf.exempt
@app.route("/status/refresh", methods=["GET"])
def status_refresh():
    """
    Force-run a monitoring cycle NOW, then return the same payload shape as /status.
    CSRF-exempt so the button can call it without a token.
    """
    try:
        monitor_and_notify_once()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    with _bg_state_lock:
        data = dict(LATEST_STATUS)
        nra = NEXT_RUN_AT
        data["refreshing"] = IS_REFRESHING

    if nra is not None:
        seconds_left = max(0, int((nra - datetime.now()).total_seconds()))
        data["next_run_at"] = nra.strftime("%Y-%m-%d %H:%M:%S")
        data["seconds_until_next"] = seconds_left
    else:
        data["next_run_at"] = None
        data["seconds_until_next"] = None

    data["ok"] = True
    return make_response(jsonify(data), 200)


# @app.route("/")
# def index():
#     return render_template("index.html")


@csrf.exempt
@app.route("/status/refresh/<path:site_key>", methods=["GET"])
def status_refresh_one(site_key):
    """ Refresh ONE site now (single probe), update status_cache.json + notifications, and merge into LATEST_STATUS so the UI sees it immediately. """
    try:
        # Find the target site from DB
        sites = load_sites()
        target = None
        for s in sites:
            if _site_key(s) == site_key:
                target = s
                break

        if target is None:
            return jsonify({"ok": False, "error": "site_key not found"}), 404

        refreshed = _refresh_one_site(target)

        with _bg_state_lock:
            if not isinstance(LATEST_STATUS, dict) or "monitored" not in LATEST_STATUS:
                monitored_list = []
            else:
                monitored_list = list(LATEST_STATUS.get("monitored") or [])

            replaced = False

            for i, item in enumerate(monitored_list):
                if item.get("site_key") == refreshed["site_key"]:
                    monitored_list[i] = refreshed
                    replaced = True
                    break

            if not replaced:
                monitored_list.append(refreshed)

            LATEST_STATUS.update({
                "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "monitored": monitored_list,
            })

            _ensure_next_run()

            resp_payload = dict(LATEST_STATUS)
            resp_payload["refreshing"] = IS_REFRESHING
            resp_payload["next_run_at"] = NEXT_RUN_AT.strftime(
                "%Y-%m-%d %H:%M:%S")
            resp_payload["seconds_until_next"] = _seconds_until_next()
            resp_payload["ok"] = True
            resp_payload["refreshed_site_key"] = site_key

        return make_response(jsonify(resp_payload), 200)

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/dashboard-test")
def dashboardtest():
    return render_template("dashboard.html")


@app.route("/full")
def indexFull():
    return render_template("indexFull.html")


@app.before_request
def _kick_off_bg():
    global _scheduler_started
    if not _scheduler_started:
        _start_background_once()


_services_started = False


def start_services():
    global _services_started
    if _services_started:
        return

    _services_started = True
    _start_background_once()
    _start_telegram_bot()


## bot tele ensure run in server
@app.before_first_request
def init_services():
    start_services()

if __name__ == "__main__":
    start_services()
    # _prime_next_run_if_needed()
    # _start_background_once()
    # _start_telegram_bot()
    app.run(debug=True, use_reloader=False)
