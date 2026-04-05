from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
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


@profile_bp.route('/update-password', methods=['POST'])
@login_required
def update_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('new_password_confirmation')

    if not check_password_hash(current_user.password, old_password):
        flash('Password lama salah!', 'danger')
        return redirect(url_for('profile.profile'))  # adjust route

    if new_password != confirm_password:
        flash('Konfirmasi password tidak cocok!', 'danger')
        return redirect(url_for('profile.profile'))

    if not new_password or len(new_password) < 6:
        flash('Password baru minimal 6 karakter!', 'danger')
        return redirect(url_for('profile.profile'))

    current_user.password = generate_password_hash(new_password)
    db.session.commit()

    flash('Password berhasil diperbarui!', 'success')
    return redirect(url_for('profile.profile'))


@profile_bp.route('/update-phone', methods=['POST'])
@login_required
def update_phone():
    phone = request.form.get('phone')

    current_user.telegram_number = phone
    db.session.commit()
    flash('Nomor telepon berhasil diperbarui!', 'success')
    return redirect(url_for('profile.profile'))
