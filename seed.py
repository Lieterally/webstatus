# seed_itk_sites.py
from flask import Flask
from sqlalchemy import text
from models import db, Website, Page, Kategori
from config import SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- kategori -------------------------------------------------------
KATEGORI_LIST = [
    "Website Akademik",
    "Website Non Akademik",
    "Others"
]


def ensure_kategori(nama):
    kategori = Kategori.query.filter_by(kategori=nama).one_or_none()
    if not kategori:
        kategori = Kategori(kategori=nama)
        db.session.add(kategori)
        db.session.flush()
    return kategori


# --- data -----------------------------------------------------------
WEBSITES = [
    {"nama_web": "Prodi Teknik Sipil", "link_web": "https://ce.itk.ac.id",
        "slug_web": "prodi-teknik-sipil", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Kimia", "link_web": "https://che.itk.ac.id",
        "slug_web": "prodi-teknik-kimia", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Elektro", "link_web": "https://ee.itk.ac.id",
        "slug_web": "prodi-teknik-elektro", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Lingkungan", "link_web": "https://enviro.itk.ac.id",
        "slug_web": "prodi-teknik-lingkungan", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Industri", "link_web": "https://ie.itk.ac.id",
        "slug_web": "prodi-teknik-industri", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Informatika", "link_web": "https://if.itk.ac.id",
        "slug_web": "prodi-teknik-informatika", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Sistem Informasi", "link_web": "https://is.itk.ac.id",
        "slug_web": "prodi-sistem-informasi", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Matematika", "link_web": "https://math.itk.ac.id",
        "slug_web": "prodi-matematika", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Mesin", "link_web": "https://me.itk.ac.id",
        "slug_web": "prodi-teknik-mesin", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Material Metalurgi", "link_web": "https://mme.itk.ac.id",
        "slug_web": "prodi-teknik-material-metalurgi", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Perkapalan", "link_web": "https://na.itk.ac.id",
        "slug_web": "prodi-teknik-perkapalan", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Kelautan", "link_web": "https://oe.itk.ac.id",
        "slug_web": "prodi-teknik-kelautan", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Fisika", "link_web": "https://phy.itk.ac.id",
        "slug_web": "prodi-fisika", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Perencanaan Wilayah dan Kota", "link_web": "https://urp.itk.ac.id",
        "slug_web": "prodi-perencanaan-wilayah-dan-kota", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Arsitektur", "link_web": "https://ars.itk.ac.id",
        "slug_web": "prodi-arsitektur", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Statistika", "link_web": "https://stat.itk.ac.id",
        "slug_web": "prodi-statistika", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Ilmu Aktuaria", "link_web": "https://actsci.itk.ac.id",
        "slug_web": "prodi-ilmu-aktuaria", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Teknik Pangan", "link_web": "https://foodtech.itk.ac.id",
        "slug_web": "prodi-teknik-pangan", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Rekayasa Keselamatan", "link_web": "https://safetyeng.itk.ac.id",
        "slug_web": "prodi-rekayasa-keselamatan", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Bisnis Digital", "link_web": "https://bisnisdigital.itk.ac.id",
        "slug_web": "prodi-bisnis-digital", "kategori": "Website Akademik"},
    {"nama_web": "Prodi Desain Komunikasi Visual", "link_web": "https://dkv.itk.ac.id",
        "slug_web": "prodi-desain-komunikasi-visual", "kategori": "Website Akademik"},

    {"nama_web": "Repository", "link_web": "https://repository.itk.ac.id",
        "slug_web": "repository", "kategori": "Website Akademik"},
    {"nama_web": "Perpustakaan", "link_web": "https://perpustakaan.itk.ac.id",
        "slug_web": "perpustakaan", "kategori": "Website Akademik"},
    {"nama_web": "Learning Management Systems", "link_web": "https://kuliah.itk.ac.id",
        "slug_web": "learning-management-systems", "kategori": "Website Akademik"},
    {"nama_web": "Dokumen Mutu", "link_web": "https://dokumen-mutu.itk.ac.id",
        "slug_web": "dokumen-mutu", "kategori": "Website Akademik"},
    {"nama_web": "Penerimaan Mahasiswa Baru", "link_web": "https://pmb.itk.ac.id",
        "slug_web": "penerimaan-mahasiswa-baru", "kategori": "Website Akademik"},

    {"nama_web": "SIM Manajemen", "link_web": "https://simmanajemen.itk.ac.id",
        "slug_web": "sim-manajemen", "kategori": "Website Non Akademik"},
    {"nama_web": "SIPEKA", "link_web": "https://sipeka.itk.ac.id",
        "slug_web": "sipeka", "kategori": "Website Non Akademik"},
    {"nama_web": "SPEAK", "link_web": "https://speak.itk.ac.id",
        "slug_web": "speak", "kategori": "Website Non Akademik"},
    {"nama_web": "SUMMIT", "link_web": "https://summit.itk.ac.id",
        "slug_web": "summit", "kategori": "Website Non Akademik"},
    {"nama_web": "SIMPAS", "link_web": "https://simpas.itk.ac.id",
        "slug_web": "simpas", "kategori": "Website Non Akademik"},
    {"nama_web": "JAMU", "link_web": "https://jamu.itk.ac.id",
        "slug_web": "jamu", "kategori": "Website Non Akademik"},
    {"nama_web": "Short Link ITK", "link_web": "https://s.itk.ac.id",
        "slug_web": "short-link-itk", "kategori": "Website Non Akademik"},
    {"nama_web": "SIRAMA", "link_web": "https://sirama.itk.ac.id",
        "slug_web": "sirama", "kategori": "Website Non Akademik"},
    {"nama_web": "SIM Banding", "link_web": "https://simbanding.itk.ac.id",
        "slug_web": "sim-banding", "kategori": "Website Non Akademik"},
    {"nama_web": "Gerbang", "link_web": "https://gerbang.itk.ac.id",
        "slug_web": "gerbang", "kategori": "Website Non Akademik"},
    {"nama_web": "Host to Host BNI", "link_web": "https://h2hbni.itk.ac.id",
        "slug_web": "host-to-host-bni", "kategori": "Website Non Akademik"},
    {"nama_web": "Host to Host BRI", "link_web": "https://h2hbri.itk.ac.id",
        "slug_web": "host-to-host-bri", "kategori": "Website Non Akademik"},
    {"nama_web": "Host to Host Mandiri", "link_web": "https://h2hmandiri.itk.ac.id",
        "slug_web": "host-to-host-mandiri", "kategori": "Website Non Akademik"},
    {"nama_web": "Tracer Study", "link_web": "https://tracer.itk.ac.id",
        "slug_web": "tracer-study", "kategori": "Website Non Akademik"},
    {"nama_web": "Feeder Gerbang", "link_web": "https://feeder-gerbang.itk.ac.id",
        "slug_web": "feeder-gerbang", "kategori": "Website Non Akademik"},
    {"nama_web": "CCTV", "link_web": "http://nvr.itk.ac.id",
        "slug_web": "cctv", "kategori": "Website Non Akademik"},
    {"nama_web": "SIAKAD", "link_web": "http://siakad.itk.ac.id",
        "slug_web": "siakad", "kategori": "Website Non Akademik"},
    {"nama_web": "SIKAP", "link_web": "http://sikap.itk.ac.id",
        "slug_web": "sikap", "kategori": "Website Non Akademik"},
    {"nama_web": "Sepakat", "link_web": "http://sepakat.itk.ac.id",
        "slug_web": "sepakat", "kategori": "Website Non Akademik"},
    {"nama_web": "SIMKUR", "link_web": "http://kurikulum.itk.ac.id",
        "slug_web": "simkur", "kategori": "Website Non Akademik"},
    {"nama_web": "Lab Terpadu", "link_web": "http://labterpadu.itk.ac.id",
        "slug_web": "lab-terpadu", "kategori": "Website Non Akademik"},

    {"nama_web": "PPID", "link_web": "https://ppid.itk.ac.id",
        "slug_web": "ppid", "kategori": "Others"},
    {"nama_web": "DPM ITK", "link_web": "https://dpm.itk.ac.id",
        "slug_web": "dpm-itk", "kategori": "Others"},
    {"nama_web": "Open House ITK", "link_web": "https://openhouse.itk.ac.id",
        "slug_web": "open-house-itk", "kategori": "Others"},
    {"nama_web": "Kerjasama ITK", "link_web": "https://kerjasama.itk.ac.id",
        "slug_web": "kerjasama-itk", "kategori": "Others"},
    {"nama_web": "Pilrek ITK", "link_web": "https://pilrek.itk.ac.id",
        "slug_web": "pilrek-itk", "kategori": "Others"},
    {"nama_web": "Unit Layanan Terpadu", "link_web": "https://ult.itk.ac.id",
        "slug_web": "unit-layanan-terpadu", "kategori": "Others"},
    {"nama_web": "Web Profil ITK", "link_web": "https://itk.ac.id",
        "slug_web": "web-profil-itk", "kategori": "Others"},
    {"nama_web": "SPI", "link_web": "https://spi.itk.ac.id",
        "slug_web": "spi", "kategori": "Others"},
    {"nama_web": "UPA TIK", "link_web": "https://ict.itk.ac.id",
        "slug_web": "upa-tik", "kategori": "Others"},
    {"nama_web": "UPA Bahasa", "link_web": "https://lch.itk.ac.id",
        "slug_web": "upa-bahasa", "kategori": "Others"},
    {"nama_web": "LPPM", "link_web": "https://lppm.itk.ac.id",
        "slug_web": "lppm", "kategori": "Others"},
    {"nama_web": "Dev SCA", "link_web": "https://dev-sca.itk.ac.id",
        "slug_web": "dev-sca", "kategori": "Others"},
    {"nama_web": "Journal", "link_web": "https://journal.itk.ac.id",
        "slug_web": "journal", "kategori": "Others"},
    {"nama_web": "IAET", "link_web": "https://iaet.itk.ac.id",
        "slug_web": "iaet", "kategori": "Others"},
    {"nama_web": "SNBP", "link_web": "https://snbp.itk.ac.id",
        "slug_web": "snbp", "kategori": "Others"},
    {"nama_web": "Inkubator Bisnis", "link_web": "https://ibt.itk.ac.id",
        "slug_web": "inkubator-bisnis", "kategori": "Others"},
]

# default paths for "prodi-*" sites
DEFAULT_PRODI_PATHS = [
    "/",
    "/berita",
    "/profile",
    "/profile/sejarah",
    "/profile/visimisi",
    "/akademik/kurikulum",
    "/akademik/silabus",
    "/kemahasiswaan/ormawa",
    "/penelitian/grup_penelitian",
    "/penelitian/kontak",
    "/login",
]


def ensure_page(site_id: int, path: str):
    """Create page if missing; no-op if already exists."""
    existing = Page.query.filter_by(
        id_web=site_id, halaman_web=path).one_or_none()
    if not existing:
        db.session.add(Page(id_web=site_id, halaman_web=path))


with app.app_context():

    kategori_map = {}
    for k in KATEGORI_LIST:
        kategori_obj = ensure_kategori(k)
        kategori_map[k] = kategori_obj.id_kategori

    for w in WEBSITES:
        slug = w["slug_web"].strip().lower()
        site = Website.query.filter_by(slug_web=slug).one_or_none()
        kategori_id = kategori_map[w["kategori"]]

        if site:
            # update changed fields
            changed = False
            if site.nama_web != w["nama_web"]:
                site.nama_web = w["nama_web"]
                changed = True
            if site.url_web != w["url_web"]:
                site.url_web = w["url_web"]
                changed = True
            if site.kategori_web != kategori_id:
                site.kategori_web = kategori_id
                changed = True
            if changed:
                db.session.add(site)
        else:
            # create new
            site = Website(nama_web=w["nama_web"],
                           url_web=w["url_web"], slug_web=slug, kategori_web=kategori_id)
            db.session.add(site)
            db.session.flush()  # get site.id_web for pages

        # pages: prodi sites get full defaults, others ensure "/" exists
        paths = DEFAULT_PRODI_PATHS if slug.startswith("prodi-") else ["/"]
        # make sure we have a valid id in case of update branch
        if not site.id_web:
            db.session.flush()
        for p in paths:
            ensure_page(site.id_web, p)

    db.session.commit()
    print("✅ Upsert seeding finished (update-or-create).")
