from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Website, Page
from flask_login import login_required

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/")
@login_required
def index():
    return render_template("index.html")
