from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, TelegramTarget
from flask_login import login_required
import requests
from config import TELEGRAM_BOT_TOKEN

BOT_TOKEN = f'{TELEGRAM_BOT_TOKEN}'
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

telegram_targets_bp = Blueprint("telegram_targets", __name__)


@telegram_targets_bp.route("/telegram_targets")
@login_required
def telegram_targets():
    telegram_targets = TelegramTarget.query.all()
    return render_template("telegram_targets/index.html", telegram_targets=telegram_targets, active_page="telegram_targets")


@telegram_targets_bp.route("/add_telegram_target", methods=["POST"])
@login_required
def add_telegram_target():
    try:
        chat_id = request.form.get("chat_id", "").strip()
        name = request.form.get("name", "").strip()
        is_active = request.form.get("is_active", "1") == "1"

        if not chat_id or not name:
            flash("Nama dan Chat ID wajib diisi.", "danger")
            return redirect(url_for("telegram_targets.telegram_targets"))

        elif TelegramTarget.query.filter_by(chat_id=chat_id).first():
            flash("Chat ID sudah terdaftar.", "danger")
            return redirect(url_for("telegram_targets.telegram_targets"))
        elif TelegramTarget.query.filter_by(name=name).first():
            flash("Nama target sudah terdaftar.", "danger")
            return redirect(url_for("telegram_targets.telegram_targets"))

        telegram_target = TelegramTarget(
            chat_id=chat_id,
            name=name,
            is_active=is_active
        )

        db.session.add(telegram_target)
        db.session.commit()

        flash(f"Telegram target '{name}' berhasil ditambahkan.", "success")

    except SQLAlchemyError:
        db.session.rollback()
        flash("Terjadi kesalahan saat menambahkan data.", "danger")

    return redirect(url_for("telegram_targets.telegram_targets"))


@telegram_targets_bp.route("/telegram_targets/edit/<int:id>", methods=["POST"])
@login_required
def edit_telegram_target(id):
    telegram_target = TelegramTarget.query.get_or_404(id)

    try:
        # Retrieve and sanitize form data
        chat_id = request.form.get("chat_id", "").strip()
        name = request.form.get("name", "").strip()
        is_active = request.form.get("is_active", "0") == "1"

        # Validation: Required fields
        if not chat_id or not name:
            flash("Nama dan Chat ID wajib diisi.", "danger")
            return redirect(url_for("telegram_targets.telegram_targets"))

        # Validation: Duplicate Chat ID (exclude current record)
        existing_chat_id = TelegramTarget.query.filter(
            TelegramTarget.chat_id == chat_id,
            TelegramTarget.id_telegram_target != id
        ).first()
        if existing_chat_id:
            flash("Chat ID sudah terdaftar.", "danger")
            return redirect(url_for("telegram_targets.telegram_targets"))

        # Validation: Duplicate Name (exclude current record)
        existing_name = TelegramTarget.query.filter(
            TelegramTarget.name == name,
            TelegramTarget.id_telegram_target != id
        ).first()
        if existing_name:
            flash("Nama target sudah terdaftar.", "danger")
            return redirect(url_for("telegram_targets.telegram_targets"))

        # Update data
        telegram_target.chat_id = chat_id
        telegram_target.name = name
        telegram_target.is_active = is_active

        db.session.commit()

        flash(
            f"Telegram target '{telegram_target.name}' berhasil diupdate.",
            "success"
        )

    except SQLAlchemyError:
        db.session.rollback()
        flash("Terjadi kesalahan saat memperbarui data.", "danger")

    return redirect(url_for("telegram_targets.telegram_targets"))


@telegram_targets_bp.route("/telegram_targets/delete/<int:id>", methods=["POST"])
@login_required
def delete_telegram_target(id):
    telegram_target = TelegramTarget.query.get_or_404(id)
    db.session.delete(telegram_target)
    db.session.commit()

    flash(
        f"Telegram target '{telegram_target.name}' berhasil dihapus.", "success")
    return redirect(url_for("telegram_targets.telegram_targets"))


@telegram_targets_bp.route("/telegram_targets/check/<int:id>", methods=["GET"])
@login_required
def check_telegram_target(id):
    telegram_target = TelegramTarget.query.get_or_404(id)

    bot_token = BOT_TOKEN
    chat_id = telegram_target.chat_id

    if not bot_token:
        flash("Token Telegram Bot belum dikonfigurasi.", "danger")
        return redirect(url_for("telegram_targets.telegram_targets"))

    url = f"{BASE_URL}/getChat"
    params = {"chat_id": chat_id}

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("ok"):
            chat_info = data.get("result", {})
            chat_name = (
                chat_info.get("title")
                or chat_info.get("username")
                or chat_info.get("first_name")
                or "Tidak diketahui"
            )

            flash(
                f"Target '{telegram_target.name}' valid. Terhubung dengan: {chat_name}.",
                "success"
            )
        else:
            flash(
                f"Target '{telegram_target.name}' tidak valid: {data.get('description', 'Chat tidak ditemukan.')}",
                "danger"
            )

    except requests.RequestException as e:
        flash(f"Gagal menghubungi Telegram API: {str(e)}", "danger")

    return redirect(url_for("telegram_targets.telegram_targets"))
