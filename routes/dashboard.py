from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Website, Page
from flask_login import login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    websites = Website.query.all()
    count_sites = Website.query.count()
    return render_template("dashboard/index.html", websites=websites, count_sites=count_sites, active_page = "dashboard")


