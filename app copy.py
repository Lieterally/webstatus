from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from flask_wtf.csrf import CSRFProtect
from slugify import slugify
import requests
import os
import json
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

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/monitoring_web_itk'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = "alit123"

# Register blueprint
app.register_blueprint(websites_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)


db.init_app(app)
csrf = CSRFProtect(app)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
                "nama_web": site.nama_web,
                "link_web": site.link_web,
                "halaman_web": [page.halaman_web for page in site.pages]
            })
        return sites
    
    
def count_sites():
    
    websites = Website.query.all()
    sites = len(websites)
    return sites


# def check_site_old(link_web, halaman_web):
#     statuses = []
#     total_time = 0
#     count = 0
#     login_down = False
#     utama_down = False
  
#     headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
#     }

#     for halaman in halaman_web:
#         url = link_web + halaman
#         try:
            
#             r = requests.get(url, headers=headers, timeout=5, verify=False)
            
#             elapsed = r.elapsed.total_seconds()
#             # print(f"⏱️ Checked {url} in {elapsed} seconds")
#             total_time += elapsed
#             count += 1
#             if r.status_code == 200:
#                 status = "✅ UP"
#             else:
#                 status = f"⚠️ {r.status_code}"
#                 if halaman == "/login":
#                     login_down = True
#                 else:
#                     utama_down = True
#         except requests.RequestException:
#             status = "❌ DOWN"
#             if halaman == "/login":
#                 login_down = True
#             else:
#                 utama_down = True
#             elapsed = 0

#         statuses.append({
#             "url": url,
#             "status": status,
#             "response_time": round(elapsed, 3)
#         })
        
#         # print(statuses)

#     if not login_down and not utama_down:
#         overall_status = "✅ UP"
#     else:
#         details = []
#         if utama_down:
#             details.append("Utama")
#         if login_down:
#             details.append("Login")
#         overall_status = f"❌ {' & '.join(details)}"

#     avg_response_time = round(total_time / count, 3) if count > 0 else "N/A"

#     return statuses, overall_status, avg_response_time

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

@app.route("/status")
def status():
    try:
        sites = load_sites()
        print("✅ sites loaded")
    except Exception as e:
        print("❌ error in /status:", e)
        return jsonify({"error": str(e)}), 500

    def monitor(site):
        statuses, overall_status, avg_response_time = check_site(site["link_web"], site["halaman_web"])
        
        return {
            "nama_web": site["nama_web"],
            "link_web": site["link_web"],
            "overall_status": overall_status,
            "avg_response_time": avg_response_time,
            "statuses": statuses
        }

    with ThreadPoolExecutor(max_workers=10) as executor:
        monitored = list(executor.map(monitor, sites))
        
    down_list = []
    up_list = []
    
        
    for web in monitored:
        nama_web = web['nama_web']
        overall_status = web['overall_status']
        link_web= web['link_web']
        
        if "❌" in overall_status:
            
            down_list.append({
            'nama_web': nama_web,
            'link_web': link_web,
            'overall_status': overall_status
            })
            
        else:
            up_list.append({
            'nama_web': nama_web,
            'link_web': link_web,
            'overall_status': overall_status
            })
    
    if down_list:
        phone_number = "6287840272518"  # for WA
        
        # for Tele
        BOT_TOKEN = "7586001603:AAGaJ1l0jllBcnzMRuc29nBFIY2I3W4RAqY"
        CHAT_ID = 981874873
        
        description = "⚠️⚠️ Website Down ⚠️⚠️"
        
        # Build the status message
        # WA
        status = ", ".join([f"{web['nama_web']} ({web['link_web']})" for web in down_list])
        
        
        # Tele
        list_web = "\n".join([f"{web['nama_web']} ({web['link_web']})" for web in down_list])
        
        # print(status)
        
        notifWhatsapp(phone_number, description, status)
        notifTelegram(BOT_TOKEN, CHAT_ID, description, list_web)
        
            

    response = make_response(jsonify({
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "monitored": monitored
    }))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@app.route("/")
def index():
    return render_template("index.html")

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]

#         user = User.query.filter_by(username=username).first()

#         if user and user.check_password(password):
#             login_user(user)
#             flash("Login successful!", "success")
#             return redirect(url_for("dashboard.dashboard"))  # Redirect after login
#         else:
#             flash("Invalid username or password", "danger")

#     return render_template("login.html")

# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     flash("You have been logged out.", "info")
#     return redirect(url_for("login"))

@app.route("/dashboard-test")
def dashboardtest():
    return render_template("dashboard.html")

@app.route("/full")
def indexFull():
    return render_template("indexFull.html")


if __name__ == "__main__":
    app.run(debug=True)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

