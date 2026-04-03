from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Website, Page, Kategori
from slugify import slugify
from flask_login import login_required

websites_bp = Blueprint("websites", __name__)


@websites_bp.route("/websites")
@login_required
def websites():
    websites = Website.query.all()
    kategoris = Kategori.query.all()
    return render_template("websites/index.html", websites=websites, kategoris=kategoris, active_page="websites")


@websites_bp.route("/add_website", methods=["POST"])
@login_required
def add_website():
    nama_web = request.form.get("nama_web")
    kategori_web = request.form.get("kategori_web")
    url_web = request.form.get("url_web")
    deskripsi_web = request.form.get("deskripsi_web")
    halaman_list = request.form.getlist("halaman_web[]")

    website = Website(nama_web=nama_web, url_web=url_web, kategori_web=kategori_web,
                      deskripsi_web=deskripsi_web, slug_web=slugify(nama_web))
    db.session.add(website)
    db.session.commit()

    pages = [Page(id_web=website.id_web, halaman_web=halaman)
             for halaman in halaman_list]
    db.session.add_all(pages)
    db.session.commit()

    flash(f"Website '{nama_web}' berhasil ditambahkan.", "success")
    return redirect(url_for("websites.websites"))


@websites_bp.route("/websites/edit/<int:id_web>", methods=["POST"])
@login_required
def edit_website(id_web):
    website = Website.query.get_or_404(id_web)
    website.nama_web = request.form.get("nama_web")
    website.url_web = request.form.get("url_web")
    website.kategori_web = request.form.get("kategori_web")
    website.deskripsi_web = request.form.get("deskripsi_web")

    Page.query.filter_by(id_web=id_web).delete()
    halaman_webs = request.form.getlist("halaman_web[]")
    for halaman in halaman_webs:
        db.session.add(Page(id_web=id_web, halaman_web=halaman))

    db.session.commit()
    flash(f"Website '{website.nama_web}' berhasil diupdate.", "success")
    return redirect(url_for("websites.websites"))


@websites_bp.route('/websites/delete/<int:id_web>')
@login_required
def delete_website(id_web):
    website = Website.query.get_or_404(id_web)
    Page.query.filter_by(id_web=id_web).delete()
    db.session.delete(website)
    db.session.commit()

    flash(f"Website '{website.nama_web}' berhasil dihapus.", "success")
    return redirect(url_for("websites.websites"))
