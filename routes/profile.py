from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Website, Page, Kategori
from slugify import slugify
from flask_login import current_user, login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def profile():
    user = current_user
    # websites = Website.query.filter_by(id_user=user.id_user).all()
    
    return render_template("profile/index.html", user=user, active_page="profile")



