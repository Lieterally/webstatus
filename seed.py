# seed_itk_sites.py
from flask import Flask
from sqlalchemy import text
from models import db, Website, Page
from config import SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- data -----------------------------------------------------------
WEBSITES = [
    {"nama_web":"Prodi Teknik Sipil","link_web":"https://ce.itk.ac.id","slug_web":"prodi-teknik-sipil"},
    {"nama_web":"Prodi Teknik Kimia","link_web":"https://che.itk.ac.id","slug_web":"prodi-teknik-kimia"},
    {"nama_web":"Prodi Teknik Elektro","link_web":"https://ee.itk.ac.id","slug_web":"prodi-teknik-elektro"},
    {"nama_web":"Prodi Teknik Lingkungan","link_web":"https://enviro.itk.ac.id","slug_web":"prodi-teknik-lingkungan"},
    {"nama_web":"Prodi Teknik Industri","link_web":"https://ie.itk.ac.id","slug_web":"prodi-teknik-industri"},
    {"nama_web":"Prodi Teknik Informatika","link_web":"https://if.itk.ac.id","slug_web":"prodi-teknik-informatika"},
    {"nama_web":"Prodi Sistem Informasi","link_web":"https://is.itk.ac.id","slug_web":"prodi-sistem-informasi"},
    {"nama_web":"Prodi Matematika","link_web":"https://math.itk.ac.id","slug_web":"prodi-matematika"},
    {"nama_web":"Prodi Teknik Mesin","link_web":"https://me.itk.ac.id","slug_web":"prodi-teknik-mesin"},
    {"nama_web":"Prodi Teknik Material Metalurgi","link_web":"https://mme.itk.ac.id","slug_web":"prodi-teknik-material-metalurgi"},
    {"nama_web":"Prodi Teknik Perkapalan","link_web":"https://na.itk.ac.id","slug_web":"prodi-teknik-perkapalan"},
    {"nama_web":"Prodi Teknik Kelautan","link_web":"https://oe.itk.ac.id","slug_web":"prodi-teknik-kelautan"},
    {"nama_web":"Prodi Fisika","link_web":"https://phy.itk.ac.id","slug_web":"prodi-fisika"},
    {"nama_web":"Prodi Perencanaan Wilayah dan Kota","link_web":"https://urp.itk.ac.id","slug_web":"prodi-perencanaan-wilayah-dan-kota"},
    {"nama_web":"Prodi Arsitektur","link_web":"https://ars.itk.ac.id","slug_web":"prodi-arsitektur"},
    {"nama_web":"Prodi Statistika","link_web":"https://stat.itk.ac.id","slug_web":"prodi-statistika"},
    {"nama_web":"Prodi Ilmu Aktuaria","link_web":"https://actsci.itk.ac.id","slug_web":"prodi-ilmu-aktuaria"},
    {"nama_web":"Prodi Teknik Pangan","link_web":"https://foodtech.itk.ac.id","slug_web":"prodi-teknik-pangan"},
    {"nama_web":"Prodi Rekayasa Keselamatan","link_web":"https://safetyeng.itk.ac.id","slug_web":"prodi-rekayasa-keselamatan"},
    {"nama_web":"Prodi Bisnis Digital","link_web":"https://bisnisdigital.itk.ac.id","slug_web":"prodi-bisnis-digital"},
    {"nama_web":"Prodi Desain Komunikasi Visual","link_web":"https://dkv.itk.ac.id","slug_web":"prodi-desain-komunikasi-visual"},
    {"nama_web":"Repository","link_web":"https://repository.itk.ac.id","slug_web":"repository"},
    {"nama_web":"Perpustakaan","link_web":"https://perpustakaan.itk.ac.id","slug_web":"perpustakaan"},
    {"nama_web":"Learning Management Systems","link_web":"https://kuliah.itk.ac.id","slug_web":"learning-management-systems"},
    {"nama_web":"Dokumen Mutu","link_web":"https://dokumen-mutu.itk.ac.id","slug_web":"dokumen-mutu"},
    {"nama_web":"Penerimaan Mahasiswa Baru","link_web":"https://pmb.itk.ac.id","slug_web":"penerimaan-mahasiswa-baru"},
    {"nama_web":"SIM Manajemen","link_web":"https://simmanajemen.itk.ac.id","slug_web":"sim-manajemen"},
    {"nama_web":"SIPEKA","link_web":"https://sipeka.itk.ac.id","slug_web":"sipeka"},
    {"nama_web":"SPEAK","link_web":"https://speak.itk.ac.id","slug_web":"speak"},
    {"nama_web":"SUMMIT","link_web":"https://summit.itk.ac.id","slug_web":"summit"},
    {"nama_web":"SIMPAS","link_web":"https://simpas.itk.ac.id","slug_web":"simpas"},
    {"nama_web":"JAMU","link_web":"https://jamu.itk.ac.id","slug_web":"jamu"},
    {"nama_web":"Short Link ITK","link_web":"https://s.itk.ac.id","slug_web":"short-link-itk"},
    {"nama_web":"SIRAMA","link_web":"https://sirama.itk.ac.id","slug_web":"sirama"},
    {"nama_web":"SIM Banding","link_web":"https://simbanding.itk.ac.id","slug_web":"sim-banding"},
    {"nama_web":"Gerbang","link_web":"https://gerbang.itk.ac.id","slug_web":"gerbang"},
    {"nama_web":"Host to Host BNI","link_web":"https://h2hbni.itk.ac.id","slug_web":"host-to-host-bni"},
    {"nama_web":"Host to Host BRI","link_web":"https://h2hbri.itk.ac.id","slug_web":"host-to-host-bri"},
    {"nama_web":"Host to Host Mandiri","link_web":"https://h2hmandiri.itk.ac.id","slug_web":"host-to-host-mandiri"},
    {"nama_web":"Tracer Study","link_web":"https://tracer.itk.ac.id","slug_web":"tracer-study"},
    {"nama_web":"Feeder Gerbang","link_web":"https://feeder-gerbang.itk.ac.id","slug_web":"feeder-gerbang"},
    {"nama_web":"PPID","link_web":"https://ppid.itk.ac.id","slug_web":"ppid"},
    {"nama_web":"DPM ITK","link_web":"https://dpm.itk.ac.id","slug_web":"dpm-itk"},
    {"nama_web":"Open House ITK","link_web":"https://openhouse.itk.ac.id","slug_web":"open-house-itk"},
    {"nama_web":"Kerjasama ITK","link_web":"https://kerjasama.itk.ac.id","slug_web":"kerjasama-itk"},
    {"nama_web":"Pilrek ITK","link_web":"https://pilrek.itk.ac.id","slug_web":"pilrek-itk"},
    {"nama_web":"Unit Layanan Terpadu","link_web":"https://ult.itk.ac.id","slug_web":"unit-layanan-terpadu"},
    {"nama_web":"Web Profil ITK","link_web":"https://itk.ac.id","slug_web":"web-profil-itk"},
    {"nama_web":"SPI","link_web":"https://spi.itk.ac.id","slug_web":"spi"},
    {"nama_web":"UPA TIK","link_web":"https://ict.itk.ac.id","slug_web":"upa-tik"},
    {"nama_web":"UPA Bahasa","link_web":"https://lch.itk.ac.id","slug_web":"upa-bahasa"},
    {"nama_web":"LPPM","link_web":"https://lppm.itk.ac.id","slug_web":"lppm"},
    {"nama_web":"Dev SCA","link_web":"https://dev-sca.itk.ac.id","slug_web":"dev-sca"},
    {"nama_web":"Journal","link_web":"https://journal.itk.ac.id","slug_web":"journal"},
    {"nama_web":"IAET","link_web":"https://iaet.itk.ac.id","slug_web":"iaet"},
    {"nama_web":"SNBP","link_web":"https://snbp.itk.ac.id","slug_web":"snbp"},
    {"nama_web":"Inkubator Bisnis","link_web":"https://ibt.itk.ac.id","slug_web":"inkubator-bisnis"},
    {"nama_web":"CCTV","link_web":"http://nvr.itk.ac.id","slug_web":"cctv"},
    {"nama_web":"SIAKAD","link_web":"http://siakad.itk.ac.id","slug_web":"siakad"},
    {"nama_web":"SIKAP","link_web":"http://sikap.itk.ac.id","slug_web":"sikap"},
    {"nama_web":"Sepakat","link_web":"http://sepakat.itk.ac.id","slug_web":"sepakat"},
    {"nama_web":"SIMKUR","link_web":"http://kurikulum.itk.ac.id","slug_web":"simkur"},
    {"nama_web":"Lab Terpadu","link_web":"http://labterpadu.itk.ac.id","slug_web":"lab-terpadu"},
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
    existing = Page.query.filter_by(id_web=site_id, halaman_web=path).one_or_none()
    if not existing:
        db.session.add(Page(id_web=site_id, halaman_web=path))

with app.app_context():
    # ---- NO mass delete, NO auto-increment reset ----
    for w in WEBSITES:
        slug = w["slug_web"].strip().lower()
        site = Website.query.filter_by(slug_web=slug).one_or_none()

        if site:
            # update changed fields
            changed = False
            if site.nama_web != w["nama_web"]:
                site.nama_web = w["nama_web"]; changed = True
            if site.link_web != w["link_web"]:
                site.link_web = w["link_web"]; changed = True
            if changed:
                db.session.add(site)
        else:
            # create new
            site = Website(nama_web=w["nama_web"], link_web=w["link_web"], slug_web=slug)
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
