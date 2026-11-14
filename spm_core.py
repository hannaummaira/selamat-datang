"""
VERSION V37 - SERAGAM WARNA BIRU PEKAT & PUTIH SAHAJA (tajuk besar/kecil, menu, sub menu, SUP/PPD/JPN)
  - Logik / fungsi / pangkalan data TIDAK diubah (hanya warna)
VERSION V36 - FLYOUT SUB MENU UNTUK SEMUA (SUP / PPD / JPN) - BUTANG PETAK BIRU, TULISAN PUTIH
  - Menu utama & sub menu = butang petak biru/tulisan putih (butang aktif biru tua + jalur kuning)
  - Menu yang ada banyak bahagian/tab sekarang papar satu bahagian sahaja ikut pilihan flyout
  - Logik / fungsi / query pangkalan data TIDAK diubah (hanya cara paparan)
VERSION BARU - APP_33 - SISTEM LANTIKAN PETUGAS SPM 2026 - JPN TEMPLATE + ZIP PUKAL + SEKOLAH ASAL
Tarikh: 2026-10-23 23:59 - UPGRADE dari app_32.py LOCKED VERSION
Status: NEW FEATURE - TEMPLATE JPN SELARAS + ZIP + HANTAR SEKOLAH ASAL

UPGRADE V33:
1. ✅ Template surat lantikan ambil dari function JPN surat_templates_jpn (get_jpn_template_for_jawatan + render_jpn_template_html)
   - PPD punya akan diganti dengan template JPN jika JPN sudah cipta
   - Guna placeholder {{NAMA}}, {{IC}}, {{JAWATAN}}, {{SEKOLAH_ASAL}}, {{PUSAT}}, {{NO_SURAT}}, {{PPD}}, {{TARIKH}}
2. ✅ Bila PPD Jana Surat - keluar 2 button terus: PDF Kolektif (Pukal) + ZIP Individu Pukal (1000 PDF dalam 1 ZIP)
   - Guna create_zip_pukal_dari_JPN + generate_surat_kolektif_pdf_bytes_JPN
3. ✅ Surat yang dijana auto sampai ke sekolah asal petugas
   - Function hantar_surat_ke_sekolah_asal_bulk() update status SURAT_SAMPAI_SEKOLAH_ASAL
   - SUP boleh nampak di dashboard tab Surat Sampai Sekolah Asal
4. ✅ Semua tab (Keseluruhan, Ikut Pusat, Ikut Sekolah Asal) upgrade guna Template JPN + ZIP

BASE: app_32.py LOCKED VERSION OK
"""

import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO
import datetime
import math
import json
import re
import logging

_log = logging.getLogger("spm2026")

# ================= CONFIGURATION =================

# ---- v39: baris tema CSS dikumpul, dipaparkan setiap rerun melalui apply_global_ui() ----
_CSS_QUEUE = []
def _css_queue(html, **kw):
    _CSS_QUEUE.append(html)

def _secret(name, default=""):
    """Baca dari st.secrets / pembolehubah persekitaran dahulu; guna nilai asal jika tiada."""
    import os
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)



# ===== HIDE FORK & GITHUB CAT BUTTON (PPD MINTA BUANG) =====
def hide_fork_github():
    try:
        import streamlit as st
        st.markdown("""
        <style>
        /* Hide Fork button and GitHub cat */
        header {visibility: hidden !important;}
        header * {visibility: hidden !important;}
        [data-testid="stHeader"] {display: none !important; visibility: hidden !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        .stAppDeployButton {display: none !important; visibility: hidden !important;}
        /* Hide GitHub icon / Fork */
        a[href*="github"] {display: none !important;}
        button[kind="header"] {display: none !important;}
        /* Hide top right menu - Fork, Share etc */
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        /* Extra: hide any element containing Fork text */
        div:has(> button:has-text("Fork")) {display: none !important;}

        /* ===== TAMBAHAN HIDE FORK GITHUB - CONFIRM HILANG ===== */
        header[data-testid="stHeader"] {display: none !important;}
        .viewerBadge_container__1QSob {display: none !important;}
        .styles_viewerBadge__1yB5_ {display: none !important;}
        a.viewerBadge_link__1S137 {display: none !important;}
        /* Streamlit Cloud Fork button */
        [data-testid="stAppViewContainer"] > header {display: none !important;}
        iframe[title="streamlitApp"] {display: none !important;}

        </style>
        """, unsafe_allow_html=True)
    except:
        pass


# ================= TEMA CANTIK =================
def apply_pretty_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], .stApp { font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important; }
    .stApp { background: linear-gradient(180deg, #eef3fb 0%, #f8fafd 40%, #ffffff 100%); }
    .block-container { padding-top: 1.6rem !important; padding-bottom: 3rem !important; max-width: 1400px; }

    h1, h2, h3, h4 { color: #0d47a1; letter-spacing: -0.3px; font-weight: 700 !important; }

    /* Butang */
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px !important; font-weight: 600 !important;
        border: 1px solid #cfd8e8 !important; transition: all .18s ease !important;
        box-shadow: 0 1px 2px rgba(13,71,161,.06);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-1px); box-shadow: 0 6px 16px rgba(13,71,161,.18) !important;
        border-color: #1565c0 !important;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
        color: #fff !important; border: none !important;
    }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: #e8eef8; padding: 6px; border-radius: 14px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 18px; font-weight: 600; color: #0d47a1; }
    .stTabs [aria-selected="true"] { background: #ffffff !important; color: #0d47a1 !important; box-shadow: 0 2px 8px rgba(13,71,161,.15); }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

    /* Kad metrik */
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e1e8f5; border-radius: 16px;
        padding: 14px 18px; box-shadow: 0 2px 10px rgba(13,71,161,.07);
    }
    [data-testid="stMetricValue"] { color: #0d47a1; font-weight: 800; }
    [data-testid="stMetricLabel"] { color: #0d47a1; font-weight: 600; }

    /* Container bersempadan, expander, jadual */
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; }
    [data-testid="stExpander"] { border: 1px solid #e1e8f5 !important; border-radius: 14px !important; background: #fff; overflow: hidden; }
    [data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1px solid #e1e8f5; }

    /* Input */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, [data-baseweb="select"] > div { border-radius: 10px !important; }

    /* Alert */
    [data-testid="stAlert"] { border-radius: 12px; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0d47a1 0%, #1565c0 100%); }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #ffffff !important; }
    [data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.12) !important; border: 1px solid rgba(255,255,255,.25) !important; color: #fff !important; }

    /* Hero log masuk */
    .hero-login {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 60%, #42a5f5 100%);
        color: #fff; border-radius: 22px; padding: 30px 24px; text-align: center; margin-bottom: 20px;
        box-shadow: 0 12px 32px rgba(13,71,161,.28);
    }
    .hero-login h1 { color: #fff !important; font-size: 1.7rem; margin: 0 0 6px 0; }
    .hero-login p { margin: 0; opacity: .92; font-size: .98rem; }
    .hero-stats { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; margin-top: 16px; }
    .hero-stats span { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28); padding: 6px 16px; border-radius: 999px; font-weight: 600; font-size: .9rem; }
    .app-footer { text-align: center; color: #0d47a1; font-size: .82rem; margin-top: 36px; padding-top: 14px; border-top: 1px solid #e1e8f5; }
    </style>
    """, unsafe_allow_html=True)


# ================= TAMBAHAN TEMA JPN SERAGAM - BIRU TUA PUTIH - TAK UBAH FUNGSI =================
JPN_COLORS = {
    "biru_tua": "#0D47A1",
    "biru_sederhana": "#1565C0",
    "biru_muda": "#E3F2FD",
    "biru_cair": "#EEF3FB",
    "biru_border": "#CFDBF0",
    "putih": "#FFFFFF",
    "hitam_teks": "#0D47A1",
    "kelabu_teks": "#0D47A1",
    "hijau_lulus": "#0D47A1",
    "hijau_bg": "#FFFFFF",
    "kuning_pending": "#0D47A1",
    "kuning_bg": "#E3F2FD",
    "merah_gagal": "#0D47A1",
    "merah_bg": "#BBDEFB",
    "jingga_need": "#0D47A1",
}

def _apply_jpn_kad_css():
    st.markdown(f'''
    <style>
    .jpn-kad {{
        background: {JPN_COLORS["putih"]};
        border: 1.5px solid {JPN_COLORS["biru_border"]};
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(13,71,161,.06);
        margin-bottom: 16px;
    }}
    .jpn-kad-biru {{
        background: linear-gradient(135deg, {JPN_COLORS["putih"]} 0%, {JPN_COLORS["biru_cair"]} 100%);
        border: 2px solid {JPN_COLORS["biru_tua"]};
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 14px rgba(13,71,161,.12);
        margin-bottom: 18px;
    }}
    .jpn-badge {{ display:inline-block; padding:4px 12px; border-radius:999px; font-weight:800; font-size:0.78rem; }}
    .jpn-badge-biru {{ background: {JPN_COLORS["biru_muda"]}; color: {JPN_COLORS["biru_tua"]}; border:1px solid {JPN_COLORS["biru_border"]}; }}
    .jpn-badge-hijau {{ background: {JPN_COLORS["hijau_bg"]}; color: {JPN_COLORS["hijau_lulus"]}; border:1px solid #FFFFFF; }}
    .jpn-badge-kuning {{ background: {JPN_COLORS["kuning_bg"]}; color: {JPN_COLORS["kuning_pending"]}; border:1px solid #E3F2FD; }}
    .jpn-no-pusat-box {{ background: {JPN_COLORS["kuning_bg"]}; border-left:4px solid {JPN_COLORS["kuning_pending"]}; padding:12px 16px; border-radius:8px; margin:12px 0; }}
    .jpn-no-pusat-label {{ font-size:0.82rem; color:{JPN_COLORS["kuning_pending"]}; font-weight:800; text-transform:uppercase; }}
    .jpn-no-pusat-value {{ font-size:1.35rem; font-weight:900; color:#0D47A1; letter-spacing:0.8px; word-spacing:6px; }}
    .surat-box img, .surat-container img, .tandatangan img {{ display:block !important; visibility:visible !important; }}
    </style>
    ''', unsafe_allow_html=True)


def jpn_kad_pusat(no_pusat_list_str, total_kelas, total_petugas, total_perlu, kod_sekolah=""):
    """v39: kad KEPERLUAN PENGAWAS gaya contoh (Dashboard SUP)."""
    import html as _h
    return (
        '<div class="sup-box">'
        f'<div class="sup-card-h"><span class="t">KEPERLUAN PENGAWAS - {_h.escape(str(kod_sekolah))}, JPN SELANGOR 2026</span>'
        f'<span class="sup-chip">NO PUSAT SEKOLAH ANDA: {_h.escape(str(no_pusat_list_str))}</span></div>'
        '<div class="sup-tiles">'
        f'<div class="sup-tile"><div class="l">JUMLAH KELAS</div><div class="n">{total_kelas}</div><div class="s">Bilik peperiksaan</div></div>'
        f'<div class="sup-tile"><div class="l">PETUGAS DIPERLUKAN</div><div class="n">{total_petugas}</div><div class="s">Termasuk simpanan</div></div>'
        f'<div class="sup-tile hl"><div class="l">SEKOLAH WAJIB CALONKAN</div><div class="n">{total_perlu} ORANG</div><div class="s">20% lebihan untuk tapisan PPD</div></div>'
        '</div></div>'
    )

def jpn_status_meter(total_pusat, total_calon, total_kelas, total_perlu, total_dicadang, ppd_code=""):
    kekurangan = total_perlu - total_dicadang
    if total_dicadang == 0:
        color = JPN_COLORS["merah_gagal"]; bg = JPN_COLORS["merah_bg"]; icon = "🔴"; teks = f"KURANG {kekurangan}"
    elif total_dicadang < total_perlu:
        color = JPN_COLORS["kuning_pending"]; bg = JPN_COLORS["kuning_bg"]; icon = "🟡"; teks = f"KURANG {kekurangan}"
    else:
        color = JPN_COLORS["hijau_lulus"]; bg = JPN_COLORS["hijau_bg"]; icon = "🟢"; teks = "CUKUP"
    return f'''
    <div style="background:{bg}; border:2px solid {color}; border-radius:12px; padding:14px 16px; margin-bottom:18px;">
        <div style="display:flex; gap:12px; align-items:center;">
            <div style="font-size:28px;">{icon}</div>
            <div>
                <div style="font-size:0.78rem; color:{JPN_COLORS["kelabu_teks"]}; font-weight:800;">RUMUSAN PPD {ppd_code} - {teks}</div>
                <div style="font-size:1rem; font-weight:800; color:{color};">{total_pusat} Pusat | {total_calon} Calon | {total_kelas} Kelas | Perlu {total_perlu} | Dicadang {total_dicadang}</div>
            </div>
        </div>
    </div>
    '''

def jpn_panduan_warna():
    return f'''
    <div class="jpn-kad" style="background:{JPN_COLORS["hijau_bg"]}; border-left:4px solid {JPN_COLORS["hijau_lulus"]}; padding:10px 14px;">
        <b>🟢 Panduan Warna:</b>
        <span class="jpn-badge jpn-badge-hijau" style="margin-left:8px;">HIJAU</span> = Sudah hantar ke PPD / Lulus
        <span class="jpn-badge jpn-badge-kuning" style="margin-left:8px;">KUNING</span> = Baru dicadangkan, belum hantar
    </div>
    '''
# ================= END TAMBAHAN TEMA =================




# ====== LOGO JATA NEGARA - MINIMAL TAMBAH (TAK KACAU LAIN) ======
JATA_B64 = """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"""
def get_jata_img_html(width=88):
    return f'<img src="data:image/png;base64,{JATA_B64}" width="{width}" style="display:block;margin:0 auto 12px auto;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.25));" />'

def show_hero_header():
    st.markdown(f"""
    <div style="background:linear-gradient(180deg,#ffffff 0%,#eef4ff 100%);border:1px solid #d6e2f5;border-radius:24px;padding:28px 20px 22px 20px;text-align:center;box-shadow:0 10px 30px rgba(13,71,161,0.08);margin-bottom:22px;">
        {get_jata_img_html(88)}
        <div style="font-family:Poppins,Inter,sans-serif;font-weight:800;font-size:1.45rem;color:#0d47a1;line-height:1.3;">SISTEM PELANTIKAN PETUGAS<br/>PEPERIKSAAN SPM TAHUN 2026</div>
        <div style="width:88px;height:4px;background:linear-gradient(90deg,#0d47a1,#1565c0);margin:14px auto 0 auto;border-radius:999px;"></div>
        <div style="font-weight:700;color:#0d47a1;font-size:0.98rem;margin-top:8px;">Jabatan Pendidikan Negeri Selangor</div>
        <div style="color:#0d47a1;font-size:0.86rem;margin-top:10px;max-width:620px;margin-left:auto;margin-right:auto;line-height:1.5;">Selamat Datang ke Portal Pelantikan — Sila pilih kategori petugas untuk log masuk. Sistem ini untuk urusan pelantikan petugas peperiksaan SPM Selangor 2026.</div>
        <div style="margin-top:16px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">
            <span style="background:#fff;border:1px solid #dbe6f8;border-radius:999px;padding:6px 14px;font-weight:700;font-size:0.82rem;color:#0d47a1;">🏫 369 Sekolah</span>
            <span style="background:#fff;border:1px solid #dbe6f8;border-radius:999px;padding:6px 14px;font-weight:700;font-size:0.82rem;color:#0d47a1;">📍 506 Pusat</span>
            <span style="background:#fff;border:1px solid #dbe6f8;border-radius:999px;padding:6px 14px;font-weight:700;font-size:0.82rem;color:#0d47a1;">🎓 71,064 Calon</span>
        </div>
    </div>
    """, unsafe_allow_html=True)



SUPABASE_URL = _secret("SUPABASE_URL", "https://gnmaijhugkkvxejvsotk.supabase.co")
SUPABASE_KEY = _secret("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdubWFpamh1Z2trdnhlanZzb3RrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI0ODc4OTcsImV4cCI6MjEwODA2Mzg5N30.1YWg71nCwnQzP-KUzTdHR4rZAVCAesbKVqvVC1-X6lw")
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=600, show_spinner=False)
def get_jpn_templates_one():
    try:
        _supa = get_supabase()
        res = _supa.table("surat_templates_jpn").select("jawatan, template_html").execute()
        return {r["jawatan"].upper(): r["template_html"] for r in res.data if not str(r.get("jawatan", "")).startswith("__ASET_")} if res.data else {}
    except:
        return {}

# ===== NEW: JPN TEMPLATE FETCHER UNTUK PDF - WAJIB GUNA INI =====
@st.cache_data(ttl=300, show_spinner=False)
def get_jpn_template_for_jawatan(jawatan_str):
    """Ambil template JPN ikut jawatan (tepat dahulu; kalau tiada, padanan nama paling panjang)."""
    try:
        jw = re.sub(r"\s+", " ", str(jawatan_str or "")).upper().strip()
        if not jw:
            return None
        all_t = get_jpn_templates_one()
        norm = {re.sub(r"\s+", " ", k).upper().strip(): v for k, v in all_t.items() if v and len(v) > 30}
        if jw in norm:
            return norm[jw]
        # padanan separa: pilih nama jawatan paling panjang yang sepadan (elak "PENGAWAS" tersalah ambil "KETUA PENGAWAS")
        cands = [k for k in norm if k in jw or jw in k]
        if cands:
            return norm[max(cands, key=len)]
        return None
    except Exception:
        return None

def render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, bilik_kebal=""):
    """Render template JPN dengan placeholder. Boleh guna {{NAMA}}, {{ nama }}, [NAMA] (huruf besar/kecil sama sahaja)."""
    try:
        tmpl = get_jpn_template_for_jawatan(jawatan)
        if not tmpl:
            return None
        nama = clean_nan(nama) or "Nama Guru"
        ic = clean_nan(ic)
        jawatan = clean_nan(jawatan) or "Petugas"
        sek_asal = clean_nan(sek_asal)
        nama_sek_asal = clean_nan(nama_sek_asal) or get_nama_sekolah_full(sek_asal, "")
        pusat = clean_nan(pusat)
        nama_pusat = clean_nan(nama_pusat) or pusat
        no_surat = clean_nan(no_surat)
        kod_ppd = clean_nan(kod_ppd)
        ppd_name = clean_nan(ppd_name) or kod_ppd
        tarikh = clean_nan(tarikh) or str(datetime.date.today().strftime("%d %B %Y"))
        bilik_kebal = clean_nan(bilik_kebal)

        sek_penuh = f"{sek_asal} - {nama_sek_asal}" if nama_sek_asal and nama_sek_asal.upper() != str(sek_asal).upper() else (nama_sek_asal or sek_asal)
        pusat_penuh = f"{pusat} - {nama_pusat}" if nama_pusat and nama_pusat.upper() != str(pusat).upper() else pusat

        replacements = {
            "NAMA": nama, "NAMA_GURU": nama,
            "IC": ic, "IC_GURU": ic,
            "JAWATAN": jawatan, "JAWATAN_CADANGAN": jawatan,
            "SEKOLAH_ASAL": sek_asal, "KOD_SEKOLAH_ASAL": sek_asal,
            "NAMA_SEKOLAH_ASAL": nama_sek_asal,
            "SEKOLAH_ASAL_PENUH": sek_penuh,
            "PUSAT": pusat, "KOD_PUSAT": pusat, "NO_PUSAT": pusat,
            "NAMA_PUSAT": nama_pusat,
            "PUSAT_PENUH": pusat_penuh,
            "BILIK_KEBAL": bilik_kebal, "KOD_BILIK_KEBAL": bilik_kebal,
            "NO_SURAT": no_surat,
            "PPD": kod_ppd, "KOD_PPD": kod_ppd,
            "PPD_NAME": ppd_name, "NAMA_PPD": ppd_name,
            "TARIKH": tarikh,
            "LOGO": _img_uri("logo"), "TANDATANGAN": _img_uri("tandatangan"), "TANDA_TANGAN": _img_uri("tandatangan"),
        }
        html = tmpl
        for k, v in replacements.items():
            v = str(v)
            esc = re.escape(k)
            html = re.sub(r"\{\{\s*" + esc + r"\s*\}\}", lambda m, v=v: v, html, flags=re.IGNORECASE)
            html = re.sub(r"\[" + esc + r"\]", lambda m, v=v: v, html, flags=re.IGNORECASE)
        return _perbaiki_img_src(html)
    except Exception as e:
        _log.debug(f"render JPN error: {e}")
        return None


def _bungkus_html_surat(html):
    """Pastikan HTML templat lengkap (A4, UTF-8) sebelum jadi PDF / dipaparkan."""
    if "<html" in html.lower():
        return html
    return ("<html><head><meta charset='UTF-8'><style>@page { size: A4; margin: 15mm; } "
            "body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; }</style></head><body>"
            + html + "</body></html>")


def enjin_pdf_templat_ada():
    try:
        import xhtml2pdf  # noqa: F401
        return True
    except Exception:
        return False


def html_to_pdf_bytes(html):
    """Tukar HTML templat JPN kepada PDF (xhtml2pdf). Pulang None jika enjin tiada / gagal."""
    try:
        from xhtml2pdf import pisa
        import io
        buf = io.BytesIO()
        res = pisa.CreatePDF(src=_bungkus_html_surat(html), dest=buf, encoding="utf-8")
        if res.err:
            _surat_err("xhtml2pdf (templat JPN)", f"{res.err} ralat semasa menjana PDF dari templat")
            return None
        return buf.getvalue()
    except Exception as e:
        _log.debug(f"html_to_pdf error: {e}"); _surat_err("xhtml2pdf (templat JPN)", e)
        return None

# ---- v39: skop daerah ----
from scoped_db import ScopedSupabase
class _SessionScope:
    """Skop daerah PER SESI PENGGUNA (satu URL dikongsi ramai pengguna serentak).
    SCOPE["ppd"] -> None = JPN (semua daerah); "BG" = Gombak sahaja. Disimpan dalam st.session_state."""
    def __getitem__(self, key):
        try:
            return st.session_state.get("_scope_ppd")
        except Exception:
            return None
    def __setitem__(self, key, value):
        st.session_state["_scope_ppd"] = value
    def get(self, key, default=None):
        return self[key] or default

SCOPE = _SessionScope()
def set_scope(kod_ppd):
    SCOPE["ppd"] = (str(kod_ppd).strip().upper() or None) if kod_ppd else None
_RAW = get_supabase()
supa = ScopedSupabase(_RAW, lambda: SCOPE["ppd"])
def scope_label():
    return PPD_MAP.get(SCOPE["ppd"], SCOPE["ppd"]) if SCOPE["ppd"] else "Selangor"

def scope_cache(**cache_kw):
    """Seperti st.cache_data tetapi KUNCI CACHE merangkumi skop daerah sesi semasa.
    Tanpa ini, data satu daerah yang di-cache boleh dipaparkan kepada pengguna daerah lain."""
    import functools
    def deco(fn):
        @st.cache_data(**cache_kw)
        def _inner(scope_key, *a, **k):          # scope_key (tanpa garis bawah) = sebahagian kunci cache
            return fn(*a, **k)
        @functools.wraps(fn)
        def _outer(*a, **k):
            return _inner(SCOPE["ppd"] or "", *a, **k)
        _outer.clear = _inner.clear
        return _outer
    return deco

# Clear cache helper - untuk refresh button cepat
def clear_all_cache():
    st.cache_data.clear()
    st.cache_resource.clear()

# ✅ FIX: Buang trailing space dari KOD_DAERAH & PPD_MAP
KOD_DAERAH = ["BA", "BB", "BC", "BD", "BE", "BF", "BG", "BH", "BJ", "BK"]
PPD_MAP = {
    "BA": "Klang", "BB": "Kuala Langat", "BC": "Kuala Selangor",
    "BD": "Hulu Langat", "BE": "Hulu Selangor", "BF": "Sabak Bernam",
    "BG": "Gombak", "BH": "Petaling Perdana", "BJ": "Sepang", "BK": "Petaling Utama"
}

# ===== PANDUAN PASSWORD UNTUK TESTING 300 USER =====
ENABLE_TESTING_GUIDE = False
MAX_PDF_KOLEKTIF = 150
MAX_ZIP_FILES = 200

def show_testing_password_guide(df_sekolah_all):
    return


# ===== HELPER: WARNA HIJAU UNTUK GURU SUDAH HANTAR KE PPD =====
def style_nama_hijau_hantar(df_input):
    """Jika STATUS HANTAR/LULUS -> NAMA_GURU jadi hijau, belum hantar kekal biasa"""
    try:
        import pandas as pd
        # Cari column status
        status_col = None
        for cand in ["STATUS","status","Status"]:
            if cand in df_input.columns:
                status_col = cand
                break
        if status_col is None:
            return df_input

        # Buat styler
        def highlight_row(row):
            status_val = str(row.get(status_col, "") or "").upper()
            is_hantar = any(x in status_val for x in ["HANTAR","LULUS","DIHANTAR","DILULUSKAN"])
            is_baru = "DICADANGKAN" in status_val or status_val.strip()=="" or "BARU" in status_val
            styles = []
            for col in row.index:
                col_str = str(col).upper()
                if "NAMA_GURU" in col_str:
                    if is_hantar:
                        styles.append('background-color: #ffffff; color: #0d47a1; font-weight: 800; border-left: 4px solid #0d47a1;')
                    elif is_baru:
                        styles.append('background-color: #e3f2fd; color: #0d47a1; font-weight: 600;')
                    else:
                        styles.append('')
                else:
                    if is_hantar:
                        styles.append('background-color: #ffffff;')
                    elif is_baru:
                        styles.append('background-color: #e3f2fd;')
                    else:
                        styles.append('')
            return styles

        return df_input.style.apply(highlight_row, axis=1)
    except Exception as e:
        return df_input

def get_status_label(status_str):
    s = str(status_str).upper()
    if "LULUS" in s:
        return "✅ SUDAH HANTAR & LULUS PPD"
    elif "HANTAR" in s or "DIHANTAR" in s:
        return "🟢 SUDAH HANTAR KE PPD"
    else:
        return "🟡 BARU DICADANGKAN (Belum Hantar)"
# ===== END HELPER =====



# ================= CSS BIRU CAIR - BACKGROUND BIRU CAIR =================
_css_queue("""
<style>
[data-testid="stSidebar"] {display: none !important;}
.stSidebar {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}

/* ===== BACKGROUND BIRU CAIR ===== */
.stApp {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #e1f5fe 100%) !important;
    background-color: #e3f2fd !important;
    background-attachment: fixed !important;
}

/* Main container */
.main .block-container {
    background: transparent !important;
}

/* Metric cards - putih atas biru cair */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #90caf9 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 2px 8px rgba(13, 71, 161, 0.1) !important;
}
[data-testid="stMetric"] label, [data-testid="stMetric"] div {
    color: #0d47a1 !important;
}
[data-testid="stMetricValue"] {
    color: #0d47a1 !important;
    font-weight: 800 !important;
}

[data-testid="stAlert"] {
    background: #ffffff !important;
    color: #0d47a1 !important;
    border: 1px solid #90caf9 !important;
    border-radius: 10px !important;
}
[data-testid="stAlert"] p, [data-testid="stAlert"] div {
    color: #0d47a1 !important;
}

[data-testid="stDataFrame"] {
    background: white !important;
    border-radius: 10px !important;
}

/* Custom sidebar - putih atas background biru cair */
.custom-sidebar {
    background: #ffffff !important;
    border-radius: 14px;
    padding: 16px;
    border: 2px solid #1976d2 !important;
    box-shadow: 0 4px 16px rgba(13, 71, 161, 0.15);
    height: fit-content;
    position: sticky;
    top: 10px;
}
.custom-sidebar h3 {
    font-size: 20px;
    color: #0d47a1 !important;
    font-weight: 800;
    margin-bottom: 4px;
}
.custom-sidebar p, .custom-sidebar span, .custom-sidebar div {
    color: #0d47a1 !important;
}
.custom-sidebar [data-testid="stCaptionContainer"] {
    color: #0d47a1 !important;
    opacity: 1 !important;
}
.custom-sidebar [data-testid="stCaptionContainer"] p {
    color: #0d47a1 !important;
    font-weight: 700 !important;
    font-size: 13px !important;
}

.no-pusat-box {
    background: #e3f2fd !important;
    border: 2px solid #0d47a1 !important;
    border-radius: 8px;
    padding: 10px 12px;
    margin: 10px 0;
}
.no-pusat-label {
    font-size: 11px;
    color: #0d47a1 !important;
    font-weight: 700;
}
.no-pusat-value {
    font-size: 18px;
    color: #0d47a1 !important;
    font-weight: 900;
}

.ppd-table {
    background: white !important;
    color: #0d47a1 !important;
}
.ppd-table th {
    background: #0d47a1 !important;
    color: white !important;
}
.ppd-table td {
    background: white !important;
    color: #0d47a1 !important;
    border-bottom: 1px solid #e0e0e0 !important;
}

.badge-merah, .badge-kuning, .badge-hijau {
    font-weight: 800 !important;
}
.badge-merah {background: #0d47a1 !important; border: 2px solid #0d47a1 !important; color: #ffffff !important;}
.badge-kuning {background: #bbdefb !important; border: 2px solid #0d47a1 !important; color: #0d47a1 !important;}
.badge-hijau {background: #ffffff !important; border: 2px solid #0d47a1 !important; color: #0d47a1 !important;}

[data-testid="stRadio"] label {
    color: #0d47a1 !important;
    font-weight: 600 !important;
}

.stButton button {
    font-weight: 700 !important;
}

[data-testid="stTabs"] button {
    color: #0d47a1 !important;
    font-weight: 600 !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #0d47a1 !important;
}

[data-testid="stCaptionContainer"] p {
    color: #0d47a1 !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

label {
    color: #0d47a1 !important;
    font-weight: 600 !important;
}

/* Card putih atas biru cair */
div[data-testid="stHorizontalBlock"] {
    background: transparent !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #90caf9 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)


# ================= V37 - SERAGAM BIRU PEKAT & PUTIH (SUP / PPD / JPN) =================
_css_queue("""
<style>
:root { --biru-pekat:#0d47a1; --biru-gelap:#002171; --biru-sederhana:#1565c0; --biru-cair:#e3f2fd; --putih:#ffffff; accent-color:#0d47a1; }

/* ---- TAJUK BESAR (header / h1 / h2): palang biru pekat, tulisan putih ---- */
.stApp h1, .stApp h2 {
    background: #0d47a1 !important; color: #ffffff !important;
    padding: 12px 18px !important; border-radius: 8px !important;
    font-size: 1.35rem !important; font-weight: 800 !important;
    margin: 6px 0 14px 0 !important; letter-spacing: 0 !important;
}
/* ---- TAJUK KECIL (subheader / h3 / h4 / h5 / h6): palang biru pekat lebih kecil ---- */
.stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    background: #0d47a1 !important; color: #ffffff !important;
    padding: 8px 14px !important; border-radius: 6px !important;
    font-size: 1.02rem !important; font-weight: 700 !important;
    margin: 6px 0 10px 0 !important; letter-spacing: 0 !important;
}
.stApp h1 *, .stApp h2 *, .stApp h3 *, .stApp h4 *, .stApp h5 *, .stApp h6 * { color: #ffffff !important; }
/* tajuk di dalam kad/palang biru sedia ada: jangan bertindan */
.stApp [style*="linear-gradient"] h1, .stApp [style*="linear-gradient"] h2,
.stApp [style*="linear-gradient"] h3, .stApp [style*="linear-gradient"] h4,
.stApp [style*="background:#0d47a1"] h1, .stApp [style*="background:#0d47a1"] h2,
.stApp [style*="background:#0d47a1"] h3, .stApp [style*="background:#0d47a1"] h4,
.main-btn h3, .hero-login h1 {
    background: transparent !important; padding: 0 !important; margin: 0 0 4px 0 !important;
    color: #ffffff !important;
}
.main-btn h3 { color: #0d47a1 !important; }
.custom-sidebar h3 { margin-top: 0 !important; }

/* ---- LABEL & KAPSYEN: biru pekat (teks biasa ikut config.toml textColor) ---- */
[data-testid="stCaptionContainer"] p { color: #0d47a1 !important; }
.custom-sidebar p, .custom-sidebar span, .custom-sidebar div { color: #0d47a1 !important; }
[data-testid="stRadio"] label, [data-testid="stTabs"] button, label { color: #0d47a1 !important; }
.hero-login, .hero-login *, .hero-stats span { color: #ffffff !important; }

/* ---- TAB: biru pekat & putih ---- */
.stTabs [data-baseweb="tab-list"] { background: #0d47a1 !important; }
.stTabs [data-baseweb="tab"], .stTabs [data-baseweb="tab"] p, [data-testid="stTabs"] button { color: #ffffff !important; }
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p { background: #ffffff !important; color: #0d47a1 !important; }

/* ---- BUTANG BIASA & MUAT TURUN: biru pekat, tulisan putih ---- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    background: #0d47a1 !important; color: #ffffff !important; border: 1px solid #002171 !important;
}
.stButton > button *, .stDownloadButton > button *, .stFormSubmitButton > button * { color: #ffffff !important; }
.stButton > button:hover, .stDownloadButton > button:hover { background: #1565c0 !important; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] { background: #002171 !important; }

/* ---- AMARAN / MAKLUMAT / BERJAYA / RALAT: putih + jalur biru ---- */
[data-testid="stAlert"] { background: #ffffff !important; border: 1px solid #0d47a1 !important; border-left: 6px solid #0d47a1 !important; }
[data-testid="stAlert"] *, [data-testid="stAlert"] svg { color: #0d47a1 !important; fill: #0d47a1 !important; }

/* ---- Metrik, delta, pill, tag, slider, progress ---- */
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * { color: #0d47a1 !important; fill: #0d47a1 !important; }
[data-baseweb="tag"] { background: #0d47a1 !important; color: #ffffff !important; }
[data-baseweb="tag"] * { color: #ffffff !important; }
[data-testid="stProgress"] > div > div > div > div { background-color: #0d47a1 !important; }
[data-testid="stSlider"] [role="slider"] { background-color: #0d47a1 !important; }
input[type="checkbox"], input[type="radio"] { accent-color: #0d47a1 !important; }
[data-baseweb="checkbox"] > span:first-child, [data-baseweb="radio"] > div:first-child { border-color: #0d47a1 !important; }
[data-baseweb="checkbox"] input:checked + span, [data-baseweb="toggle"] input:checked + div { background-color: #0d47a1 !important; }
[data-baseweb="radio"] input:checked + div { background-color: #0d47a1 !important; border-color: #0d47a1 !important; }

/* ---- Kotak No Pusat: biru cair + sempadan biru pekat ---- */
.no-pusat-box, .jpn-no-pusat-box { background: #e3f2fd !important; border: 2px solid #0d47a1 !important; border-left-width: 6px !important; }
.no-pusat-label, .jpn-no-pusat-label, .no-pusat-value, .jpn-no-pusat-value { color: #0d47a1 !important; }
.jpn-badge-hijau { background: #ffffff !important; color: #0d47a1 !important; border: 1px solid #0d47a1 !important; }
.jpn-badge-kuning { background: #bbdefb !important; color: #0d47a1 !important; border: 1px solid #0d47a1 !important; }
</style>
""", unsafe_allow_html=True)
# ================= END V37 =================

# ================= HELPER FUNCTIONS (FORMULA & LOGIC) =================

def kira_kelas_dari_calon(jumlah_calon):
    """1 kelas = 20 calon, CEIL"""
    try:
        c = int(float(str(jumlah_calon).replace(",", "").strip() or 0))
        if c <= 0: return 0
        return math.ceil(c / 20)
    except: return 0

def kira_petugas_dari_kelas(jumlah_kelas):
    """User formula: kelas + 9 = petugas diperlukan"""
    try: return int(jumlah_kelas) + 9
    except: return 0

def kira_sekolah_perlu_calonkan(jumlah_kelas):
    """Sekolah perlu calonkan = petugas (kelas+9) + 1 KP +1 TKP +1 Penyelia = kelas+12"""
    try: return kira_petugas_dari_kelas(jumlah_kelas) + 3
    except: return 0


def clean_nan(val):
    """Bersihkan nan, None, 'nan', 'None' jadi string kosong"""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null", "nat", ""):
        return ""
    return s

def get_nama_sekolah_full(kod_sek, fallback=""):
    """Dapatkan nama penuh sekolah dari kod"""
    try:
        ks = str(kod_sek).upper().strip()
        if not ks:
            return fallback
        # Cari dalam supa sekolah_master
        try:
            res = supa.table("sekolah_master").select("nama_sekolah, kod_sekolah").eq("kod_sekolah", ks).limit(1).execute()
            if res.data:
                nm = res.data[0].get("nama_sekolah") or ""
                if nm and str(nm).lower() not in ("nan","none",""):
                    return str(nm).strip()
        except:
            pass
        # Jika fallback ada nama, guna
        if fallback and str(fallback).upper().strip() != ks:
            if str(fallback).lower() not in ("nan","none",""):
                return str(fallback).strip()
        return ks
    except:
        return fallback or str(kod_sek)

def generate_surat_html(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh):
    """Generate surat - PPD punya akan diganti dengan template JPN jika ada (JPN selaraskan)"""
    # Bersihkan semua input dari nan
    nama = clean_nan(nama) or "Nama Guru"
    ic = clean_nan(ic)
    jawatan = clean_nan(jawatan) or "Petugas Peperiksaan"
    sek_asal = clean_nan(sek_asal)
    nama_sek_asal = clean_nan(nama_sek_asal)
    pusat = clean_nan(pusat)
    nama_pusat = clean_nan(nama_pusat)
    # FIX: jika nama_pusat kosong, cari dari pusat_master ikut NO PUSAT
    if not nama_pusat or nama_pusat.upper() == pusat.upper():
        try:
            _pmap = build_pusat_map_from_master()
            if pusat and str(pusat).upper().strip() in _pmap and _pmap[str(pusat).upper().strip()]:
                nama_pusat = _pmap[str(pusat).upper().strip()]
        except:
            pass
    no_surat = clean_nan(no_surat) or clean_nan(tarikh) or "JPN.SPP.HHJH/0001"
    kod_ppd = clean_nan(kod_ppd) or "BA"
    ppd_name = clean_nan(ppd_name) or kod_ppd

    # === V37: TEMPLAT JPN DIUTAMAKAN (baca dari jadual surat_templates_jpn) ===
    _h37 = render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh)
    if _h37:
        return _bungkus_html_surat(_h37)

    # === CEK TEMPLATE JPN DULU - Jika JPN dah selaraskan, guna template JPN (PPD punya diganti) ===
    try:
        # Try load from surat_templates_jpn table
        tmpl_res = supa.table("surat_templates_jpn").select("template_html").eq("jawatan", jawatan.upper().strip()).limit(1).execute()
        if tmpl_res.data and len(tmpl_res.data) > 0:
            tmpl_html = tmpl_res.data[0].get("template_html")
            if tmpl_html and len(tmpl_html) > 50:
                # Guna template JPN - ganti placeholder
                html = tmpl_html
                replacements = {
                    "NAMA": nama,
                    "IC": ic,
                    "JAWATAN": jawatan,
                    "SEKOLAH_ASAL": sek_asal,
                    "NAMA_SEKOLAH_ASAL": nama_sek_asal or get_nama_sekolah_full(sek_asal, "") if "get_nama_sekolah_full" in globals() else sek_asal,
                    "PUSAT": pusat,
                    "NAMA_PUSAT": nama_pusat or pusat,
                    "NO_SURAT": no_surat,
                    "PPD": kod_ppd,
                    "PPD_NAME": ppd_name,
                    "TARIKH": tarikh,
                    "KOD_PUSAT": pusat,
                    "KOD_PPD": kod_ppd
                }
                for k,v in replacements.items():
                    html = html.replace("{{"+k+"}}", str(v)).replace("{{ "+k+" }}", str(v)).replace("{{"+k.lower()+"}}", str(v))
                # Wrap if not html
                if "<html>" not in html.lower():
                    html = f"<html><head><meta charset='UTF-8'></head><body>{html}</body></html>"
                return html
    except Exception as e:
        # If table not exists or error, fallback to old PPD template
        pass

    try:
        # Try session state JPN templates
        if "jpn_templates" in st.session_state:
            tmpl = st.session_state.jpn_templates.get(jawatan.upper().strip()) or st.session_state.jpn_templates.get(jawatan)
            if tmpl and len(tmpl) > 50:
                html = tmpl
                for k,v in {"NAMA": nama, "IC": ic, "JAWATAN": jawatan, "SEKOLAH_ASAL": sek_asal, "PUSAT": pusat, "NO_SURAT": no_surat, "PPD": kod_ppd, "TARIKH": tarikh}.items():
                    html = html.replace("{{"+k+"}}", str(v))
                return html
    except:
        pass

    # === FALLBACK: Template lama PPD (jika JPN belum sediakan) ===
    # Dapatkan nama penuh sekolah asal - bukan sekadar kod
    if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper():
        display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
    else:
        try:
            full_nama = get_nama_sekolah_full(sek_asal, nama_sek_asal)
            if full_nama.upper() != sek_asal.upper():
                display_sek_asal = f"{sek_asal} - {full_nama}"
            else:
                display_sek_asal = sek_asal
        except:
            display_sek_asal = sek_asal or "Sekolah Asal"

    if nama_pusat and nama_pusat.upper() != pusat.upper():
        display_pusat = f"{pusat} - {nama_pusat}"
    else:
        display_pusat = pusat

    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan SPM 2026</title>'
    html += '<style>body{font-family:Times New Roman,serif;margin:40px;color:#000;}'
    html += '.surat{border:2px solid #000;padding:30px;margin-bottom:30px;page-break-after:always;background:white;}'
    html += '.header{text-align:center;border-bottom:3px double #000;padding-bottom:15px;margin-bottom:20px;}'
    html += '.kandungan{line-height:1.6;}'
    html += 'table.info{width:100%;border-collapse:collapse;margin:15px 0;}'
    html += 'table.info td{padding:5px 10px;}'
    html += 'table.info td:first-child{width:180px;font-weight:bold;}'
    html += '.tandatangan{margin-top:60px;display:flex;justify-content:space-between;}'
    html += '</style></head><body>'
    html += '<div class="surat"><div class="header">'
    html += '<h2>JABATAN PENDIDIKAN NEGERI SELANGOR</h2>'
    html += f'<h3>PEJABAT PENDIDIKAN DAERAH {kod_ppd} - {ppd_name}</h3>'
    html += f'<p>No Surat: {no_surat} | [Template JPN Selaras - Jika ada template JPN, surat ini akan diganti]</p></div>'
    html += '<div class="kandungan">'
    html += f'<p>Tarikh: {tarikh}</p>'
    html += '<p><strong>Tuan/Puan,</strong></p>'
    html += f'<p><strong>PELANTIKAN SEBAGAI {jawatan.upper()} PEPERIKSAAN SPM TAHUN 2026</strong></p>'
    html += '<p>Dengan hormatnya saya merujuk kepada perkara di atas.</p>'
    html += '<p>2. Sukacita dimaklumkan bahawa tuan/puan telah dilantik sebagai petugas peperiksaan SPM 2026 seperti butiran berikut:</p>'
    html += '<table class="info">'
    html += f'<tr><td>Nama</td><td>: {nama}</td></tr>'
    html += f'<tr><td>No. IC</td><td>: {ic}</td></tr>'
    html += f'<tr><td>Jawatan</td><td>: {jawatan}</td></tr>'
    html += f'<tr><td>Sekolah Asal</td><td>: {display_sek_asal}</td></tr>'
    html += f'<tr><td>Pusat Ditugaskan</td><td>: {display_pusat}</td></tr>'
    html += f'<tr><td>No Surat Lantikan</td><td>: {no_surat}</td></tr>'
    html += '</table>'
    html += '<p>3. Tuan/puan dikehendaki hadir bertugas di pusat peperiksaan yang telah ditetapkan mengikut jadual yang akan dimaklumkan kemudian.</p>'
    html += '<p>4. Kerjasama dan komitmen tuan/puan dalam menjayakan peperiksaan SPM 2026 amatlah dihargai dan didahului dengan ucapan terima kasih.</p>'
    html += '<p>Sekian.</p>'
    html += '<div class="footer"><p><strong>MALAYSIA MADANI</strong><br><strong>BERKHIDMAT UNTUK NEGARA</strong></p>'
    html += '<div class="tandatangan"><div><p>Yang benar,</p><br><br><br>'
    html += f'<p>_________________________<br><strong>Pegawai Pendidikan Daerah<br>PPD {kod_ppd} - {ppd_name}</strong></p></div>'
    html += '<div style="text-align:right;"><p>b.p Pengarah Pendidikan<br>Jabatan Pendidikan Negeri Selangor</p></div></div></div></div></body></html>'
    return html




def generate_surat_pdf_bytes(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, no_rujukan=""):
    """Generate surat lantikan as PDF bytes - untuk download PDF - FIX nan & sekolah asal"""
    # Bersihkan
    try:
        nama = clean_nan(nama) or "Nama Guru"
        ic = clean_nan(ic)
        jawatan = clean_nan(jawatan) or "Petugas Peperiksaan"
        sek_asal = clean_nan(sek_asal)
        nama_sek_asal = clean_nan(nama_sek_asal)
        pusat = clean_nan(pusat)
        nama_pusat = clean_nan(nama_pusat)
        no_surat = clean_nan(no_surat) or "JPN.SPP.HHJH/0001"
        kod_ppd = clean_nan(kod_ppd) or "BA"
        ppd_name = clean_nan(ppd_name) or kod_ppd
        tarikh = clean_nan(tarikh) or str(datetime.date.today())

        # Nama penuh sekolah
        if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper():
            display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
        else:
            try:
                full_nama = get_nama_sekolah_full(sek_asal, nama_sek_asal)
                display_sek_asal = full_nama if full_nama.upper() != sek_asal.upper() else f"{sek_asal} - {full_nama}" if full_nama else sek_asal
            except:
                display_sek_asal = sek_asal

        display_pusat = f"{pusat} - {nama_pusat}" if nama_pusat and nama_pusat.upper() != pusat.upper() else pusat
    except:
        display_sek_asal = sek_asal
        display_pusat = pusat

    # ===== V37: templat JPN diutamakan =====
    try:
        _h37 = render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh)
        if _h37:
            _pdf37 = html_to_pdf_bytes(_h37)
            if _pdf37:
                return _pdf37
    except Exception:
        pass

    # Cuba dengan reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('TitleCustom', parent=styles['Heading1'], fontSize=14, alignment=1, spaceAfter=6)
        style_heading = ParagraphStyle('HeadingCustom', parent=styles['Heading2'], fontSize=12, alignment=1, spaceAfter=4)
        style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=4)

        story = []
        story.append(Paragraph("JABATAN PENDIDIKAN NEGERI SELANGOR", style_title))
        story.append(Paragraph(f"PEJABAT PENDIDIKAN DAERAH {ppd_name.upper() or kod_ppd}", style_heading))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>SURAT LANTIKAN PETUGAS PEPERIKSAAN SPM 2026</b>", style_heading))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>No Rujukan: {no_surat}</b>", style_normal))
        story.append(Paragraph(f"Tarikh: {tarikh}", style_normal))
        story.append(Spacer(1, 8))

        isi = f"""
        <b>Tuan/Puan {nama} ({ic})</b><br/>
        {jawatan}<br/>
        {display_sek_asal}<br/><br/>
        Tuan/Puan,<br/><br/>
        <b>PELANTIKAN SEBAGAI {jawatan.upper()} PEPERIKSAAN SPM 2026</b><br/><br/>
        Dengan hormatnya dimaklumkan bahawa tuan/puan telah dilantik sebagai <b>{jawatan}</b> bagi Peperiksaan SPM Tahun 2026.<br/><br/>
        <b>Butiran Penempatan:</b><br/>
        - Sekolah Asal: {display_sek_asal}<br/>
        - Pusat Peperiksaan Ditugaskan: {display_pusat}<br/>
        - No Surat Lantikan: {no_surat}<br/>
        - Kod PPD: {kod_ppd} - {ppd_name}<br/><br/>
        Tuan/puan dikehendaki melapor diri di pusat peperiksaan yang ditetapkan pada tarikh dan masa yang akan dimaklumkan kelak.<br/><br/>
        Kerjasama tuan/puan amatlah dihargai dan didahului dengan ucapan terima kasih.<br/><br/>
        Sekian.<br/><br/>
        <b>"BERKHIDMAT UNTUK NEGARA"</b><br/><br/>
        Saya yang menjalankan amanah,<br/><br/><br/>
        <b>PEGAWAI PENDIDIKAN DAERAH</b><br/>
        {ppd_name}<br/>
        PPD {kod_ppd}<br/>
        """
        story.append(Paragraph(isi, style_normal))
        story.append(Spacer(1, 12))

        data_footer = [
            [f"No Surat: {no_surat}", f"Pusat: {display_pusat}"],
            [f"Sekolah Asal: {display_sek_asal}", f"Jawatan: {jawatan}"]
        ]
        t = Table(data_footer, colWidths=[85*mm, 85*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f5f5f5')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(t)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        # Fallback simple canvas
        try:
            import io
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 800, f"SURAT LANTIKAN SPM 2026 - {kod_ppd}")
            c.setFont("Helvetica", 10)
            y = 780
            lines = [
                f"No Surat: {no_surat}",
                f"Nama: {nama}",
                f"IC: {ic}",
                f"Jawatan: {jawatan}",
                f"Sekolah Asal: {display_sek_asal}",
                f"Pusat Tugas: {display_pusat}",
                f"Tarikh: {tarikh}",
                f"PPD: {kod_ppd} - {ppd_name}",
                "",
                "Tuan/Puan telah dilantik sebagai petugas peperiksaan SPM 2026.",
                f"Sila lapor diri di pusat {pusat}.",
            ]
            for line in lines:
                c.drawString(50, y, line[:100])
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 800
            c.save()
            return buffer.getvalue()
        except Exception as e2:
            # Ultimate fallback: return HTML as bytes with pdf mime (still downloadable)
            try:
                html_fallback = generate_surat_html(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh)
                return html_fallback.encode('utf-8')
            except:
                return None


def generate_surat_kolektif_pdf_bytes(surat_list, kod_ppd, ppd_name, title="SURAT LANTIKAN KESELURUHAN"):
    """Generate kolektif PDF - V37: gabung surat individu ikut templat JPN; jika gagal guna ringkasan lama"""
    try:
        _kol = generate_surat_kolektif_pdf_bytes_JPN(surat_list, kod_ppd, ppd_name, title_prefix=title)
        if _kol:
            return _kol
    except Exception:
        pass
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib import colors
        import io
        from datetime import date

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=10*mm, bottomMargin=10*mm)
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('TitleCustom', parent=styles['Heading1'], fontSize=13, alignment=1, spaceAfter=6, leading=14)
        style_heading = ParagraphStyle('HeadingCustom', parent=styles['Heading2'], fontSize=11, alignment=1, spaceAfter=6)
        style_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=4)
        style_ruj = ParagraphStyle('RujCustom', parent=styles['Normal'], fontSize=9, alignment=2, leading=11)
        style_header = ParagraphStyle('HeaderCustom', parent=styles['Normal'], fontSize=10, leading=12)

        story = []

        # HEADER RASMI - Logo tepi kiri effect
        header_text = """<b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br/>JABATAN PENDIDIKAN NEGERI SELANGOR<br/><font size=8>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam</font>"""
        story.append(Paragraph(header_text, style_header))
        story.append(Paragraph("<hr/>", style_normal))

        # Ruj Kanan = No Surat
        no_surat_kolektif = surat_list[0].get('no_surat') if surat_list and len(surat_list)>0 else f"JPN.SPP.HHJH/PPD.{kod_ppd}/0001"
        tarikh_str = date.today().strftime('%d %B %Y')
        ruj_html = f"""<font size=9>Ruj. Kami: {no_surat_kolektif}<br/>Tarikh: {tarikh_str}</font>"""
        story.append(Paragraph(ruj_html, style_ruj))
        story.append(Spacer(1, 8))

        story.append(Paragraph(f"<b>{title}</b>", style_title))
        story.append(Paragraph(f"PPD {kod_ppd} - {ppd_name} - {len(surat_list)} Guru", style_heading))
        story.append(Spacer(1, 8))

        for idx, s in enumerate(surat_list, start=1):
            nama = s.get('nama','') or s.get('NAMA','') or s.get('NAMA GURU','')
            ic = s.get('ic','') or s.get('IC','')
            jawatan = s.get('jawatan') or s.get('JAWATAN') or ''
            sek_asal = s.get('sekolah_asal') or s.get('SEKOLAH ASAL') or ''
            nama_sek_asal = s.get('nama_sekolah_asal') or s.get('NAMA SEKOLAH ASAL') or ''
            pusat = s.get('pusat') or s.get('PUSAT') or ''
            no_surat = s.get('no_surat') or s.get('NO SURAT') or s.get('NO SURAT BARU') or ''
            nama_pusat = s.get('nama_pusat') or s.get('NAMA PUSAT') or ''
            bilik_kebal = s.get('bilik_kebal') or s.get('BILIK KEBAL') or ''
            sekolah_asal_full = f"{sek_asal} - {nama_sek_asal}" if nama_sek_asal else sek_asal

            isi = f"""
            <b>{idx}. {nama} ({ic}) - {jawatan}</b><br/>
            <font size=8>
            No Surat: <b>{no_surat}</b> | Sekolah Asal: {sekolah_asal_full}<br/>
            Pusat: {pusat} - {nama_pusat} | Bilik Kebal: {bilik_kebal}<br/>
            Tuan/Puan telah dilantik sebagai <b>{jawatan}</b> SPM 2026 di pusat {pusat}. Sila lapor diri mengikut arahan.<br/>
            </font>
            """
            story.append(Paragraph(isi, style_normal))
            story.append(Spacer(1, 6))
            if idx % 5 == 0 and idx < len(surat_list):
                story.append(PageBreak())
                story.append(Paragraph(header_text, style_header))
                story.append(Paragraph("<hr/>", style_normal))
                story.append(Paragraph(ruj_html, style_ruj))
                story.append(Spacer(1, 8))

        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>MALAYSIA MADANI - BERKHIDMAT UNTUK NEGARA</b><br/><br/>(DATIN WAN NOR ASHIKIN BINTI ABU KASSIM)<br/>Pengarah Pendidikan, JPN Selangor", style_normal))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        _log.debug(f"Error kolektif: {e}")
        return None




def generate_surat_penyelia_kawasan_html(nama, ic, sek_asal, nama_sek_asal, telefon, kod_bilik_kebal, nama_bilik_kebal, alamat_bilik_kebal, pusat_jagaan_list, no_surat, kod_ppd, ppd_name, tarikh):
    """Surat khas untuk Penyelia Kawasan yang ditempatkan ke Bilik Kebal"""
    # V34: Ensure pusat_jagaan_list is not empty, fallback to kod_pusat if needed
    if not pusat_jagaan_list:
        try:
            # Try from data JSON
            if isinstance(data_dict, dict):
                pusat_jagaan_list = data_dict.get("pusat_jagaan") or data_dict.get("pusat_jagaan_str","").split(",") if isinstance(data_dict.get("pusat_jagaan_str"), str) else []
        except:
            pass
    pusat_jagaan_str = ", ".join(pusat_jagaan_list) if isinstance(pusat_jagaan_list, list) else str(pusat_jagaan_list)
    pusat_jagaan_table = ""
    if isinstance(pusat_jagaan_list, list) and pusat_jagaan_list:
        for idx, p in enumerate(pusat_jagaan_list, 1):
            pusat_jagaan_table += f"<tr><td>{idx}</td><td>{p}</td></tr>"
    else:
        pusat_jagaan_table = f"<tr><td>1</td><td>{pusat_jagaan_str}</td></tr>"

    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan Penyelia Kawasan SPM 2026</title>'
    html += '<style>body{font-family:Times New Roman,serif;margin:40px;color:#000;}'
    html += '.surat{border:3px double #0d47a1;padding:30px;margin-bottom:30px;background:white;page-break-after:always;}'
    html += '.header{text-align:center;border-bottom:3px double #0d47a1;padding-bottom:15px;margin-bottom:20px;}'
    html += '.header h2{color:#0d47a1;margin:5px 0;}'
    html += '.kandungan{line-height:1.7;font-size:14px;}'
    html += 'table.info{width:100%;border-collapse:collapse;margin:15px 0;}'
    html += 'table.info td{padding:8px 12px;border:1px solid #ddd;}'
    html += 'table.info td:first-child{width:200px;font-weight:bold;background:#e3f2fd;}'
    html += 'table.pusat{width:100%;border-collapse:collapse;margin:10px 0;}'
    html += 'table.pusat th, table.pusat td{border:1px solid #0d47a1;padding:8px;text-align:left;}'
    html += 'table.pusat th{background:#0d47a1;color:white;}'
    html += '.tandatangan{margin-top:60px;display:flex;justify-content:space-between;}'
    html += '.penting{background:#e3f2fd;border-left:5px solid #0d47a1;padding:12px;margin:15px 0;}'
    html += '</style></head><body>'
    html += '<div class="surat"><div class="header">'
    html += '<h2>JABATAN PENDIDIKAN NEGERI SELANGOR</h2>'
    html += f'<h3>PEJABAT PENDIDIKAN DAERAH {kod_ppd} - {ppd_name}</h3>'
    html += '<h3 style="color:#0d47a1;">SURAT LANTIKAN PENYELIA KAWASAN SPM 2026</h3>'
    html += f'<p><strong>No Rujukan: {no_surat}</strong> | Tarikh: {tarikh}</p></div>'
    html += '<div class="kandungan">'
    html += '<p><strong>Tuan/Puan,</strong></p>'
    html += '<p><strong>PELANTIKAN SEBAGAI PENYELIA KAWASAN PEPERIKSAAN SPM TAHUN 2026 - PENEMPATAN DI BILIK KEBAL</strong></p>'
    html += '<p>Dengan hormatnya saya merujuk kepada perkara di atas dan sukacita dimaklumkan bahawa tuan/puan telah dilantik sebagai <strong>Penyelia Kawasan SPM 2026</strong> dengan butiran seperti berikut:</p>'
    html += '<table class="info">'
    html += f'<tr><td>Nama Penyelia Kawasan</td><td>{nama}</td></tr>'
    html += f'<tr><td>No. Kad Pengenalan</td><td>{ic}</td></tr>'
    html += f'<tr><td>Sekolah Asal</td><td>{sek_asal} - {nama_sek_asal}</td></tr>'
    html += f'<tr><td>No. Telefon</td><td>{telefon}</td></tr>'
    html += f'<tr><td>Jawatan Lantikan</td><td><strong>PENYELIA KAWASAN</strong></td></tr>'
    html += f'<tr><td>Dilantik di Bilik Kebal</td><td><strong>{kod_bilik_kebal} - {nama_bilik_kebal}</strong><br><small>{alamat_bilik_kebal}</small></td></tr>'
    html += f'<tr><td>No Surat Lantikan</td><td>{no_surat}</td></tr>'
    html += f'<tr><td>PPD</td><td>{kod_ppd} - {ppd_name}</td></tr>'
    html += '</table>'

    html += '<div class="penting">'
    html += '<strong>BERTANGGUNGJAWAB ATAS PUSAT-PUSAT PEPERIKSAAN:</strong>'
    html += '<p>Penyelia Kawasan ini bertanggungjawab memantau dan menyelia pusat-pusat peperiksaan berikut di bawah Bilik Kebal yang berkenaan:</p>'
    html += '</div>'

    html += '<table class="pusat">'
    html += '<tr><th>Bil</th><th>Kod Pusat / Pusat Peperiksaan Di Bawah Jagaan</th></tr>'
    html += pusat_jagaan_table
    html += '</table>'

    html += f'<p><strong>Jumlah Pusat Jagaan: {len(pusat_jagaan_list) if isinstance(pusat_jagaan_list, list) else 1} pusat</strong></p>'

    html += '<p>3. <strong>Tugas dan Tanggungjawab Penyelia Kawasan:</strong></p>'
    html += '<ul>'
    html += '<li>Bertanggungjawab sepenuhnya ke atas keselamatan dan kelancaran pengurusan kertas soalan di Bilik Kebal yang ditetapkan;</li>'
    html += f'<li>Menyelia dan memantau {len(pusat_jagaan_list) if isinstance(pusat_jagaan_list, list) else 1} pusat peperiksaan di bawah jagaan Bilik Kebal {kod_bilik_kebal};</li>'
    html += '<li>Memastikan semua prosedur keselamatan dan tatacara peperiksaan SPM dipatuhi;</li>'
    html += '<li>Melaporkan sebarang isu atau masalah kepada Pegawai Pendidikan Daerah dengan segera;</li>'
    html += '<li>Hadir bertugas mengikut jadual yang ditetapkan oleh PPD.</li>'
    html += '</ul>'

    html += '<p>4. Tuan/puan dikehendaki hadir taklimat Penyelia Kawasan yang akan dimaklumkan kemudian oleh PPD.</p>'
    html += '<p>5. Kerjasama, komitmen dan integriti tuan/puan dalam menjayakan peperiksaan SPM 2026 amatlah dihargai.</p>'
    html += '<p>Sekian, terima kasih.</p>'

    html += '<div class="footer"><p><strong>MALAYSIA MADANI</strong><br><strong>BERKHIDMAT UNTUK NEGARA</strong></p>'
    html += '<div class="tandatangan"><div><p>Yang benar,</p><br><br><br>'
    html += f'<p>_________________________<br><strong>Pegawai Pendidikan Daerah<br>PPD {kod_ppd} - {ppd_name}</strong><br><small>Tarikh: {tarikh}</small></p></div>'
    html += '<div style="text-align:right;"><p>b.p Pengarah Pendidikan<br>Jabatan Pendidikan Negeri Selangor<br><br><small>Salinan: Pengetua {nama_sek_asal}<br>Sekolah Asal Penyelia Kawasan</small></p></div></div></div></div></div>'
    html += '</body></html>'
    return html

def generate_surat_kolektif_html(guru_list, kod_ppd, ppd_name, tarikh, prefix):

    # guru_list is list of dicts with NAMA, IC, etc
    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan Kolektif</title>'
    html += '<style>body{font-family:Arial,sans-serif;margin:20px;} .surat{border:1px solid #ccc;padding:20px;margin:10px 0;} h2{text-align:center;}</style></head><body>'
    html += f'<h2>SURAT LANTIKAN PETUGAS SPM 2026 - PPD {kod_ppd}</h2>'
    html += f'<p>Tarikh: {tarikh} | Jumlah: {len(guru_list)} guru</p><hr>'
    for g in guru_list:
        html += generate_surat_html(g["NAMA GURU"], g["IC"], g["JAWATAN"], g["SEKOLAH ASAL"], g["NAMA SEKOLAH ASAL"], g["PUSAT DITEMPATKAN"], g["NAMA PUSAT DITEMPATKAN"], g["NO SURAT"], kod_ppd, ppd_name, tarikh)
    html += '</body></html>'
    return html


def safe_count(table_name):
    """Count dengan fallback kalau RLS block count exact"""
    try:
        res = supa.table(table_name).select("*", count="exact").limit(1).execute()
        if res.count is not None and res.count > 0: return res.count
        if res.data and len(res.data) > 0: return len(res.data)
        return 0
    except: return 0

def get_sekolah(kod):
    for col in ["kod_sekolah", "kod_sekolah_tuan_rumah", "KOD_SEKOLAH"]:
        try:
            res = supa.table("sekolah_master").select("*").eq(col, kod.upper()).limit(1).execute()
            if res.data:
                row = res.data[0]
                return {
                    "kod_sekolah": row.get("kod_sekolah") or row.get("KOD_SEKOLAH") or kod,
                    "nama_sekolah": row.get("nama_sekolah") or row.get("NAMA_SEKOLAH") or f"SEKOLAH {kod}",
                    "kod_ppd": row.get("kod_ppd") or row.get("KOD_PPD") or "BH",
                    "ppd": row.get("ppd") or row.get("PPD") or "Petaling Perdana",
                    "_raw": row
                }
        except: continue
    return {"kod_sekolah": kod, "nama_sekolah": f"SEKOLAH {kod}", "kod_ppd": "BH", "ppd": "Petaling Perdana"}

@scope_cache(ttl=300, show_spinner=False)
def get_guru_df(kod_sekolah):
    try:
        res = None
        for col in ["kod_sekolah", "KOD_SEKOLAH", "kod_sekolah_tuan_rumah"]:
            try:
                r = supa.table("guru_master").select("*").eq(col, kod_sekolah.upper()).limit(2000).execute()
                if r.data: res=r; break
            except: continue

        if not res:
            res = supa.table("guru_master").select("*").eq("kod_sekolah", kod_sekolah.upper()).limit(2000).execute()

        rows = []
        sekolah_map_guru = {}
        try:
            res_sek = supa.table("sekolah_master").select("kod_sekolah,nama_sekolah").limit(2000).execute()
            for s in res_sek.data or []:
                k = (s.get("kod_sekolah") or s.get("KOD_SEKOLAH") or "").upper()
                n = s.get("nama_sekolah") or s.get("NAMA_SEKOLAH") or ""
                if k: sekolah_map_guru[k] = n
        except: pass

        for r in res.data or []:
            d = r.get("data") or {}
            if isinstance(d, str):
                try: d = json.loads(d)
                except: d = {}

            def _nk(x): return re.sub(r"[^A-Z0-9]", "", str(x).upper())
            _kosong_val = ("", "none", "null", "nan", "n/a", "-")
            _dn, _rn = {}, {}

            for _k, _v in d.items():
                if _v is not None and not isinstance(_v, (dict, list)) and str(_v).strip().lower() not in _kosong_val:
                    _dn.setdefault(_nk(_k), str(_v).strip())
            for _k, _v in r.items():
                if _v is not None and not isinstance(_v, (dict, list)) and str(_v).strip().lower() not in _kosong_val:
                    _rn.setdefault(_nk(_k), str(_v).strip())

            def get_val(*keys, default=""):
                for k in keys:
                    nk = _nk(k)
                    if nk in _dn: return _dn[nk]
                    if nk in _rn: return _rn[nk]
                return default

            ic_val = get_val("IC", "ic_guru", "IC_GURU", "ic", "no_ic", "NO_KP", "NO KP")
            nama_val = get_val("NAMA GURU", "nama_guru", "NAMA_GURU", "nama", "NAMA")
            jantina_val = get_val("JANTINA", "jantina", "JANTINA_GURU", "Jantina", "SEX")
            poskod_val = get_val("POSKOD_RUMAH", "poskod_rumah", "POSKOD", "poskod", "POSKOD RUMAH")
            alamat_val = get_val("ALAMAT_RUMAH", "alamat_rumah", "ALAMAT RUMAH", "alamat", "ALAMAT")
            telefon_val = get_val("TELEFON_GURU", "telefon_guru", "NO TELEFON GURU", "TELEFON", "no_telefon")
            email_val = get_val("EMAIL_GURU", "email_guru", "EMAIL GURU", "EMAIL", "email", "EMEL", "EMEL GURU", "E-MEL", "E-MAIL")
            pengalaman_val = get_val("PENGALAMAN_SPM", "pengalaman_spm", "PENGALAMAN", "pengalaman")
            jawatan_val = get_val("JAWATAN_CADANGAN", "jawatan_cadangan", "JAWATAN CADANGAN", "jawatan")
            kod_ppd_val = get_val("KOD_PPD", "kod_ppd", "kod_ppd_asal", "KOD_PPD_ASAL", "ppd", "PPD")
            kod_sek_val = get_val("KOD_SEKOLAH", "kod_sekolah", "KOD SEKOLAH", "kod_sekolah_asal", "KOD_SEKOLAH_ASAL", default=kod_sekolah)
            nama_sek_val = get_val("NAMA_SEKOLAH", "nama_sekolah", "NAMA SEKOLAH", "sekolah_asal", "NAMA_SEKOLAH_ASAL")
            no_pusat_asal_val = get_val("NO_PUSAT_ASAL", "no_pusat_asal", "NO PUSAT ASAL", "PUSAT ASAL", "pusat_asal", "KOD PUSAT ASAL", "NO_PUSAT", "KOD PUSAT")

            if not nama_sek_val or nama_sek_val == "" or nama_sek_val == kod_sek_val:
                nama_sek_val = sekolah_map_guru.get(kod_sek_val.upper(), "") or sekolah_map_guru.get(kod_sekolah.upper(), "") or kod_sek_val

            if not kod_ppd_val or kod_ppd_val == "":
                kod_ppd_val = kod_sekolah[:2] if len(kod_sekolah) >= 2 else "BA"

            if not jawatan_val or jawatan_val.strip() == "":
                jawatan_val = "Pengawas Peperiksaan"

            rows.append({
                "id": r.get("id"),
                "NAMA GURU": nama_val, "IC": ic_val, "JANTINA": jantina_val,
                "POSKOD_RUMAH": poskod_val, "ALAMAT_RUMAH": alamat_val,
                "TELEFON": telefon_val, "TELEFON_GURU": telefon_val,
                "EMAIL_GURU": email_val, "EMAIL": email_val,
                "JAWATAN CADANGAN": jawatan_val, "JAWATAN_CADANGAN": jawatan_val,
                "PENGALAMAN_SPM": pengalaman_val, "PENGALAMAN": pengalaman_val,
                "KOD_PPD": kod_ppd_val, "KOD_PPD_ASAL": kod_ppd_val,
                "KOD SEKOLAH": kod_sek_val, "KOD_SEKOLAH": kod_sek_val,
                "KOD_SEKOLAH_ASAL": kod_sek_val,
                "NAMA_SEKOLAH_ASAL": nama_sek_val, "NAMA_SEKOLAH": nama_sek_val,
                "NO_PUSAT_ASAL": no_pusat_asal_val, "ALAMAT": alamat_val,
                "data_full": d if isinstance(d, dict) else {}, "raw": r
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

@scope_cache(ttl=300, show_spinner=False)
def get_pusat_df():
    try:
        res = supa.table("pusat_master").select("*").limit(2000).execute()
        df = pd.DataFrame(res.data or [])
        if not df.empty:
            df_norm = df.copy()
            if "no_pusat" in df_norm.columns: df_norm["kod_pusat_std"] = df_norm["no_pusat"]
            elif "kod_pusat" in df_norm.columns: df_norm["kod_pusat_std"] = df_norm["kod_pusat"]
            elif "NO_PUSAT" in df_norm.columns: df_norm["kod_pusat_std"] = df_norm["NO_PUSAT"]
            else: df_norm["kod_pusat_std"] = df_norm.iloc[:, 1] if len(df_norm.columns) > 1 else " "

            if "nama_pusat" in df_norm.columns: df_norm["nama_pusat_std"] = df_norm["nama_pusat"]
            elif "NAMA_PUSAT" in df_norm.columns: df_norm["nama_pusat_std"] = df_norm["NAMA_PUSAT"]
            else: df_norm["nama_pusat_std"] = df_norm.get("nama_sekolah", " ")
            return df
    except Exception as e:
        st.error(f"pusat_master error: {e}")
    return pd.DataFrame()

@scope_cache(ttl=120, show_spinner=False)
def get_cadangan_df(kod_ppd=None, kod_sekolah=None):
    try:
        # Fetch with larger limit and without strict eq first to avoid missing data due to case issues
        try:
            # Always fetch all then filter locally for robustness
            res = supa.table("cadangan_sup").select("*").limit(10000).execute()
        except:
            res = supa.table("cadangan_sup").select("*").limit(5000).execute()

        df = pd.DataFrame(res.data or [])
        if df.empty:
            return df

        # Normalize - merge data json and top-level columns
        norm_rows = []
        for _, r in df.iterrows():
            row_dict = {}
            for k, v in r.items():
                if k != 'data':
                    row_dict[k] = v
                else:
                    if isinstance(v, dict):
                        row_dict.update(v)
                    elif isinstance(v, str):
                        try:
                            parsed = json.loads(v)
                            if isinstance(parsed, dict):
                                row_dict.update(parsed)
                        except:
                            pass
            # Normalize keys to upper for consistency but keep original too
            # Ensure critical fields
            # JAWATAN - normalize various possible keys
            jaw = row_dict.get('JAWATAN_CADANGAN') or row_dict.get('jawatan_cadangan') or row_dict.get('JAWATAN') or row_dict.get('jawatan') or row_dict.get('JAWATAN CADANGAN') or ''
            jaw = str(jaw).strip()
            # Clean jawatan: remove extra spaces, normalize case for comparison but keep original display
            jaw_clean = ' '.join(jaw.split())
            row_dict['JAWATAN_CADANGAN'] = jaw_clean
            row_dict['jawatan_cadangan'] = jaw_clean
            row_dict['JAWATAN_CADANGAN_NORM'] = jaw_clean.lower()

            # KOD PPD
            kppd = row_dict.get('KOD_PPD') or row_dict.get('kod_ppd') or row_dict.get('KOD_PPD_ASAL') or row_dict.get('kod_ppd_asal') or ''
            row_dict['KOD_PPD'] = str(kppd).strip().upper()

            # KOD SEKOLAH ASAL
            ksa = row_dict.get('KOD_SEKOLAH_ASAL') or row_dict.get('kod_sekolah_asal') or row_dict.get('KOD_SEKOLAH') or row_dict.get('kod_sekolah') or row_dict.get('kod_sekolah_tuan_rumah') or ''
            row_dict['KOD_SEKOLAH_ASAL'] = str(ksa).strip().upper()

            # NAMA
            ng = row_dict.get('NAMA_GURU') or row_dict.get('nama_guru') or row_dict.get('NAMA GURU') or ''
            row_dict['NAMA_GURU'] = str(ng).strip().upper()

            # NAMA SEKOLAH ASAL - V28 FIX
            nsa = row_dict.get('NAMA_SEKOLAH_ASAL') or row_dict.get('nama_sekolah_asal') or row_dict.get('NAMA_SEKOLAH') or row_dict.get('nama_sekolah') or row_dict.get('NAMA SEKOLAH ASAL') or ''
            row_dict['NAMA_SEKOLAH_ASAL'] = str(nsa).strip().upper()
            row_dict['nama_sekolah_asal'] = str(nsa).strip()

            # IC
            ic = row_dict.get('IC_GURU') or row_dict.get('ic_guru') or row_dict.get('IC') or row_dict.get('ic') or ''
            ic = str(ic).strip()
            # Normalize IC - remove spaces
            ic = ic.replace(' ', '')
            row_dict['IC_GURU'] = ic

            # ALAMAT, TELEFON, EMAIL, POSKOD - ensure exists
            for key_lower, key_upper in [('alamat_rumah','ALAMAT_RUMAH'), ('telefon_guru','TELEFON_GURU'), ('email_guru','EMAIL_GURU'), ('poskod_rumah','POSKOD_RUMAH'), ('no_pusat_asal','NO_PUSAT_ASAL'), ('pengalaman_spm','PENGALAMAN_SPM')]:
                val = row_dict.get(key_upper) or row_dict.get(key_lower) or ''
                row_dict[key_upper] = str(val).strip()
                row_dict[key_lower] = str(val).strip()

            # Lajur `status` (top-level) ialah SUMBER SEBENAR - ia dikemas kini oleh Hantar / Jana / Lulus.
            # STATUS dalam JSON `data` hanya nilai semasa insert ("DICADANGKAN") dan tak pernah dikemas kini,
            # jadi ia tak boleh menimpa lajur `status` (punca paparan kekal "belum dihantar").
            _top = r.get('status')
            if _top is not None and not (isinstance(_top, float) and pd.isna(_top)) and str(_top).strip():
                row_dict['STATUS'] = str(_top).strip()
                row_dict['status'] = str(_top).strip()
            elif 'STATUS' not in row_dict or not row_dict['STATUS']:
                row_dict['STATUS'] = row_dict.get('status') or 'DICADANGKAN'

            # No Surat: lajur `no_surat` (top-level) ialah sumber sebenar. Nilai kosong dalam JSON `data`
            # tak boleh menimpanya (punca guru kekal "belum lulus" walaupun surat dah dijana).
            def _ns_ok(v):
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    return ""
                t = str(v).strip()
                return "" if t.lower() in ("nan", "none", "null") else t
            _ns_final = _ns_ok(r.get('no_surat')) or _ns_ok(r.get('NO_SURAT')) \
                or _ns_ok(row_dict.get('no_surat')) or _ns_ok(row_dict.get('NO_SURAT')) \
                or _ns_ok(row_dict.get('surat_no')) or _ns_ok(row_dict.get('SURAT_NO')) \
                or _ns_ok(row_dict.get('no_surat_lantikan'))
            row_dict['no_surat'] = _ns_final
            row_dict['NO_SURAT'] = _ns_final

            norm_rows.append(row_dict)

        df_norm = pd.DataFrame(norm_rows)
        if df_norm.empty:
            return df_norm

        # V25 FIX: Deduplicate and keep HANTAR status prioritized over DICADANGKAN
        if 'IC_GURU' in df_norm.columns:
            # Create priority for status: LULUS=3, HANTAR=2, DICADANGKAN=1
            def status_priority(s):
                s = str(s).upper()
                if 'LULUS' in s:
                    return 5
                if any(x in s for x in ('DILANTIK', 'DIJANA', 'DITEMPATKAN', 'SURAT')):
                    return 4
                if 'HANTAR' in s or 'TERPILIH' in s or 'SIMPANAN' in s:
                    return 3
                return 1
            try:
                df_norm['status_prio'] = df_norm['STATUS'].apply(status_priority)
            except:
                try:
                    df_norm['status_prio'] = df_norm['status'].apply(status_priority)
                except:
                    df_norm['status_prio'] = 1

            # Add sort key: id descending, status_prio descending
            sort_cols = ['status_prio']
            if 'id' in df_norm.columns:
                try:
                    df_norm['id_num'] = pd.to_numeric(df_norm['id'], errors='coerce')
                    sort_cols.append('id_num')
                except:
                    pass
            if 'created_at' in df_norm.columns:
                sort_cols.append('created_at')

            df_norm = df_norm.sort_values(by=sort_cols, ascending=False)
            df_norm = df_norm.drop_duplicates(subset=['IC_GURU', 'KOD_SEKOLAH_ASAL'], keep='first')
            # Clean helper columns
            for col in ['id_num', 'status_prio']:
                if col in df_norm.columns:
                    df_norm = df_norm.drop(columns=[col])

        # Filter by PPD if requested - STRICT FILTER (FIX untuk isu Sepang nampak Klang)
        if kod_ppd:
            kod_ppd_u = kod_ppd.strip().upper()
            try:
                # Step 1: Get list of sekolah kod for this PPD from sekolah_master
                kod_list = []
                try:
                    res_sek = supa.table("sekolah_master").select("kod_sekolah").eq("kod_ppd", kod_ppd_u).limit(2000).execute()
                    kod_list = [str(s.get('kod_sekolah','')).upper().strip() for s in (res_sek.data or []) if str(s.get('kod_sekolah','')).strip()]
                except:
                    kod_list = []

                # Step 2: Strict filter - only allow if KOD_PPD exact match OR KOD_SEKOLAH_ASAL in kod_list
                # NOT include empty KOD_PPD unless sekolah is in list
                if kod_list:
                    # Exact match for KOD_PPD (not contains) + sekolah in list
                    mask_ppd_exact = df_norm['KOD_PPD'].astype(str).str.upper().str.strip() == kod_ppd_u
                    mask_sek_in_list = df_norm['KOD_SEKOLAH_ASAL'].astype(str).str.upper().str.strip().isin(kod_list)
                    # Strict: only keep if either PPD matches exactly OR sekolah is in this PPD's list
                    df_norm = df_norm[mask_ppd_exact | mask_sek_in_list].copy()
                else:
                    # Fallback if sekolah_master empty - filter exact PPD only, no empty allowed
                    mask_ppd_exact = df_norm['KOD_PPD'].astype(str).str.upper().str.strip() == kod_ppd_u
                    df_norm = df_norm[mask_ppd_exact].copy()
            except Exception as e:
                # On error, try exact match only
                try:
                    kod_ppd_u = kod_ppd.strip().upper()
                    df_norm = df_norm[df_norm['KOD_PPD'].astype(str).str.upper().str.strip() == kod_ppd_u].copy()
                except:
                    pass

        if kod_sekolah:
            kod_s_u = kod_sekolah.strip().upper()
            try:
                df_norm = df_norm[df_norm['KOD_SEKOLAH_ASAL'].astype(str).str.upper() == kod_s_u]
            except:
                pass

        return df_norm
    except Exception as e:
        return pd.DataFrame()

def flash(level, msg):
    st.session_state.setdefault("_flash", []).append((level, msg))

def show_flash():
    for level, msg in st.session_state.pop("_flash", []):
        getattr(st, level)(msg)

def _id_py(x):
    if hasattr(x, "item"): x = x.item()
    if isinstance(x, float) and x.is_integer(): return int(x)
    return x

def hantar_ke_ppd(ids, kod_ppd, df_sasaran=None):
    """FIX: Hanya update STATUS, jangan sentuh nama_guru"""
    berjaya, gagal = 0, []
    ic_list = []
    if df_sasaran is not None and not df_sasaran.empty:
        try:
            if 'IC_GURU' in df_sasaran.columns:
                ic_list = df_sasaran['IC_GURU'].astype(str).str.strip().tolist()
        except:
            pass
    for i in range(0, len(ids), 100):
        kelompok = ids[i:i+100]
        payloads_to_try = [
            {"status": "HANTAR KE PPD", "status": "HANTAR KE PPD"},
            {"status": "HANTAR KE PPD"},
            {"status": "HANTAR KE PPD"},
        ]
        success = False
        last_err = ""
        for payload in payloads_to_try:
            try:
                supa.table("cadangan_sup").update(payload).in_("id", kelompok).execute()
                success = True
                break
            except Exception as e:
                last_err = str(e)
                continue
        if success:
            berjaya += len(kelompok)
        else:
            gagal.append(last_err)
    if ic_list:
        for ic_val in ic_list:
            if not ic_val or ic_val.lower() in ["nan","none",""]:
                continue
            try:
                supa.table("cadangan_sup").update({"status": "HANTAR KE PPD"}).eq("ic_guru", ic_val).execute()
            except:
                pass
    return berjaya, gagal

def simpan_penempatan_ppd(items):
    """Simpan hasil janaan ke cadangan_sup (lajur kod_pusat + status DIJANA PPD), berkelompok ikut pusat.
    items: [{"id":..., "ic":..., "pusat":...}]. Pulang (bil_berjaya, senarai_gagal)."""
    berjaya, gagal = 0, []
    ikut_pusat = {}
    for it in items:
        ikut_pusat.setdefault(str(it["pusat"]), []).append(it)
    for pusat, senarai in ikut_pusat.items():
        ids = [_id_py(i["id"]) for i in senarai if str(i.get("id") or "").strip() not in ("", "nan", "None")]
        for k in range(0, len(ids), 100):
            kelompok = ids[k:k + 100]
            try:
                supa.table("cadangan_sup").update({"kod_pusat": pusat, "status": "DIJANA PPD"}).in_("id", kelompok).execute()
                berjaya += len(kelompok)
            except Exception as e:
                gagal.append(f"{pusat}: {e}")
        for i in senarai:
            if str(i.get("id") or "").strip() in ("", "nan", "None") and i.get("ic"):
                try:
                    supa.table("cadangan_sup").update({"kod_pusat": pusat, "status": "DIJANA PPD"}).eq("ic_guru", i["ic"]).execute()
                    berjaya += 1
                except Exception as e:
                    gagal.append(f"{i.get('ic')}: {e}")
    return berjaya, gagal


def to_excel(df):
    output = BytesIO()
    try:
        import openpyxl
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()
    except ImportError: pass
    except Exception: pass

    try:
        output.write(df.to_csv(index=False).encode('utf-8-sig'))
        return output.getvalue()
    except:
        return b""


def clean_nan(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan","none","null","nat",""):
        return ""
    return s

def get_nama_sekolah_full(kod_sek, fallback=""):
    try:
        ks = str(kod_sek).upper().strip()
        if not ks:
            return fallback
        try:
            res = supa.table("sekolah_master").select("nama_sekolah, kod_sekolah").eq("kod_sekolah", ks).limit(1).execute()
            if res.data:
                nm = res.data[0].get("nama_sekolah") or ""
                if nm and str(nm).lower() not in ("nan","none",""):
                    return str(nm).strip()
        except:
            pass
        if fallback and str(fallback).upper().strip() != ks:
            if str(fallback).lower() not in ("nan","none",""):
                return str(fallback).strip()
        return ks
    except:
        return fallback or str(kod_sek)

def create_simple_pdf_bytes(pages_text_list, title="Surat Lantikan"):
    try:
        import io
        def esc_pdf(s):
            s = str(s)
            s = s.replace('\\','\\\\').replace('(','\\(').replace(')', '\\)')
            return s
        content_streams = []
        for page_lines in pages_text_list:
            stream = "BT\n/F1 10 Tf\n40 800 Td\n"
            for line in page_lines:
                line = str(line)[:120]
                if not line.strip():
                    stream += "0 -14 Td\n"
                    continue
                safe = esc_pdf(line)
                stream += f"({safe}) Tj\n0 -14 Td\n"
            stream += "ET\n"
            content_streams.append(stream)
        pdf_parts = []
        pdf_parts.append(b"%PDF-1.4\n")
        obj_offsets = []
        obj_id = 1
        obj_offsets.append(len(b"".join(pdf_parts)))
        pdf_parts.append(f"{obj_id} 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n".encode())
        obj_id+=1
        obj_offsets.append(len(b"".join(pdf_parts)))
        kids = " ".join([f"{3 + i*2} 0 R" for i in range(len(content_streams))])
        pdf_parts.append(f"{obj_id} 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(content_streams)} >>\nendobj\n".encode())
        obj_id+=1
        for i in range(len(content_streams)):
            obj_offsets.append(len(b"".join(pdf_parts)))
            content_obj_id = obj_id+1
            font_obj_id = 2 + len(content_streams)*2 + 1
            pdf_parts.append(f"{obj_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {content_obj_id} 0 R /Resources << /Font << /F1 {font_obj_id} 0 R >> >> >>\nendobj\n".encode())
            obj_id+=1
            obj_offsets.append(len(b"".join(pdf_parts)))
            stream_bytes = content_streams[i].encode('utf-8', errors='ignore')
            pdf_parts.append(f"{obj_id} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode())
            pdf_parts.append(stream_bytes)
            pdf_parts.append(b"\nendstream\nendobj\n")
            obj_id+=1
        obj_offsets.append(len(b"".join(pdf_parts)))
        font_obj_id = obj_id
        pdf_parts.append(f"{font_obj_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n".encode())
        xref_offset = len(b"".join(pdf_parts))
        pdf_parts.append(f"xref\n0 {font_obj_id+1}\n".encode())
        pdf_parts.append(b"0000000000 65535 f \n")
        for off in obj_offsets:
            pdf_parts.append(f"{off:010d} 00000 n \n".encode())
        pdf_parts.append(f"trailer\n<< /Size {font_obj_id+1} /Root 1 0 R >>\n".encode())
        pdf_parts.append(f"startxref\n{xref_offset}\n%%EOF".encode())
        return b"".join(pdf_parts)
    except Exception as e:
        return None

def create_zip_of_individual_pdfs(surat_list, kod_ppd, ppd_name):
    import io, zipfile
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, s in enumerate(surat_list, start=1):
                nama = str(s.get('nama','') or s.get('NAMA GURU','')).strip()
                ic = str(s.get('ic','') or s.get('IC','')).strip()
                jawatan = str(s.get('jawatan') or s.get('JAWATAN') or '').strip()
                sek_asal = str(s.get('sekolah_asal') or s.get('SEKOLAH ASAL') or '').strip()
                pusat = str(s.get('pusat') or s.get('PUSAT') or '').strip()
                no_surat = str(s.get('no_surat') or s.get('NO SURAT') or s.get('NO SURAT BARU') or '').strip()
                nama_pusat = str(s.get('nama_pusat') or s.get('NAMA PUSAT') or '').strip()
                nama_sek_asal = str(s.get('nama_sekolah_asal') or s.get('NAMA SEKOLAH ASAL') or '').strip()
                def clean_z(v):
                    v = str(v).strip()
                    return "" if v.lower() in ("nan","none","null","") else v
                nama = clean_z(nama) or f"GURU_{idx}"
                no_surat = clean_z(no_surat) or f"JPN_{idx:04d}"
                try:
                    pdf_bytes = generate_surat_pdf_bytes(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, __import__("datetime").date.today().strftime('%d %B %Y'), no_surat)
                except:
                    pdf_bytes = None
                if pdf_bytes:
                    safe_nama = "".join(c if c.isalnum() or c in ("_","-") else "_" for c in nama)[:30]
                    safe_no = no_surat.replace("/","_").replace("\\","_")
                    file_name = f"{idx:02d}_{safe_nama}_{safe_no}.pdf"
                    zip_file.writestr(file_name, pdf_bytes)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    except Exception as e:
        return None

def generate_surat_html_FIXED(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh):
    nama = clean_nan(nama) or "Nama Guru"
    ic = clean_nan(ic)
    jawatan = clean_nan(jawatan) or "Petugas Peperiksaan"
    sek_asal = clean_nan(sek_asal)
    nama_sek_asal = clean_nan(nama_sek_asal)
    pusat = clean_nan(pusat)
    nama_pusat = clean_nan(nama_pusat)
    if not nama_pusat or nama_pusat.upper() == pusat.upper():
        try:
            _pmap = build_pusat_map_from_master()
            if pusat and str(pusat).upper().strip() in _pmap and _pmap[str(pusat).upper().strip()]:
                nama_pusat = _pmap[str(pusat).upper().strip()]
        except:
            pass
    no_surat = clean_nan(no_surat) or "JPN.SPP.HHJH/0001"
    kod_ppd = clean_nan(kod_ppd) or "BA"
    ppd_name = clean_nan(ppd_name) or kod_ppd
    if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper():
        display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
    else:
        try:
            full_nama = get_nama_sekolah_full(sek_asal, nama_sek_asal)
            display_sek_asal = f"{sek_asal} - {full_nama}" if full_nama and full_nama.upper() != sek_asal.upper() else sek_asal
        except:
            display_sek_asal = sek_asal
    display_pusat = f"{pusat} - {nama_pusat}" if nama_pusat and nama_pusat.upper() != pusat.upper() else pusat
    html = '<html><head><meta charset="UTF-8"><title>Surat Lantikan SPM 2026</title>'
    html += '<style>body{font-family:Times New Roman,serif;margin:40px;color:#000;}.surat{border:2px solid #000;padding:30px;margin-bottom:30px;page-break-after:always;background:white;}.header{text-align:center;border-bottom:3px double #000;padding-bottom:15px;margin-bottom:20px;}.kandungan{line-height:1.6;}table.info{width:100%;border-collapse:collapse;margin:15px 0;}table.info td{padding:5px 10px;}table.info td:first-child{width:180px;font-weight:bold;}.tandatangan{margin-top:60px;display:flex;justify-content:space-between;}</style></head><body>'
    html += '<div class="surat"><div class="header">'
    html += '<h2>JABATAN PENDIDIKAN NEGERI SELANGOR</h2>'
    html += f'<h3>PEJABAT PENDIDIKAN DAERAH {kod_ppd} - {ppd_name}</h3>'
    html += f'<p>No Surat: {no_surat}</p></div>'
    html += '<div class="kandungan">'
    html += f'<p>Tarikh: {tarikh}</p><p><strong>Tuan/Puan,</strong></p><p><strong>PELANTIKAN SEBAGAI {jawatan.upper()} PEPERIKSAAN SPM TAHUN 2026</strong></p>'
    html += '<p>Dengan hormatnya saya merujuk kepada perkara di atas.</p><p>2. Sukacita dimaklumkan bahawa tuan/puan telah dilantik sebagai petugas peperiksaan SPM 2026 seperti butiran berikut:</p><table class="info">'
    html += f'<tr><td>Nama</td><td>: {nama}</td></tr><tr><td>No. IC</td><td>: {ic}</td></tr><tr><td>Jawatan</td><td>: {jawatan}</td></tr><tr><td>Sekolah Asal</td><td>: {display_sek_asal}</td></tr><tr><td>Pusat Ditugaskan</td><td>: {display_pusat}</td></tr><tr><td>No Surat Lantikan</td><td>: {no_surat}</td></tr></table>'
    html += '<p>3. Tuan/puan dikehendaki hadir bertugas di pusat peperiksaan yang telah ditetapkan mengikut jadual yang akan dimaklumkan kemudian.</p><p>4. Kerjasama dan komitmen tuan/puan dalam menjayakan peperiksaan SPM 2026 amatlah dihargai dan didahului dengan ucapan terima kasih.</p><p>Sekian.</p>'
    html += '<div class="footer"><p><strong>MALAYSIA MADANI</strong><br><strong>BERKHIDMAT UNTUK NEGARA</strong></p><div class="tandatangan"><div><p>Yang benar,</p><br><br><br>'
    html += f'<p>_________________________<br><strong>Pegawai Pendidikan Daerah<br>PPD {kod_ppd} - {ppd_name}</strong></p></div><div style="text-align:right;"><p>b.p Pengarah Pendidikan<br>Jabatan Pendidikan Negeri Selangor</p></div></div></div></div></div></body></html>'
    return html





def generate_surat_pdf_bytes_FIXED(nama, ic, jawatan, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, no_rujukan="", bilik_kebal="", kod_bilik_kebal=""):
    try:
        nama = clean_nan(nama) or "Nama Guru"
        ic = clean_nan(ic)
        jawatan = clean_nan(jawatan) or "Pengawas Peperiksaan"
        sek_asal = clean_nan(sek_asal)
        nama_sek_asal = clean_nan(nama_sek_asal) or get_nama_sekolah_full(sek_asal, "")
        pusat = clean_nan(pusat)
        nama_pusat = clean_nan(nama_pusat) or get_nama_sekolah_full(pusat, "")
        no_surat = clean_nan(no_surat) or f"JPNS.SPP 600-7/17/5 Jld.2 (01)"
        kod_ppd = clean_nan(kod_ppd) or "BA"
        ppd_name = clean_nan(ppd_name) or kod_ppd
        tarikh = clean_nan(tarikh) or datetime.date.today().strftime("%d %B %Y")
        _bk_nama_raw, _bk_kod_raw = clean_nan(bilik_kebal), clean_nan(kod_bilik_kebal)
        if _bk_nama_raw and _bk_kod_raw and not _bk_nama_raw.upper().startswith(_bk_kod_raw.upper()):
            bilik_kebal = f"{_bk_kod_raw} \u2013 {_bk_nama_raw}"          # contoh: CB12 – SMK TELOK PANGLIMA GARANG
        else:
            bilik_kebal = _bk_nama_raw or _bk_kod_raw or ""

        if nama_sek_asal and nama_sek_asal.upper() != sek_asal.upper() and sek_asal not in nama_sek_asal:
            display_sek_asal = f"{sek_asal} - {nama_sek_asal}"
        else:
            display_sek_asal = nama_sek_asal if nama_sek_asal else sek_asal
        if nama_pusat and nama_pusat.upper() != pusat.upper() and pusat not in nama_pusat:
            display_pusat = f"{pusat} - {nama_pusat}"
        else:
            display_pusat = nama_pusat if nama_pusat else pusat

        # No pusat untuk display - ambil dari pusat
        no_pusat_display = pusat.split("-")[0].strip() if "-" in pusat else pusat
        if len(no_pusat_display) < 3:
            no_pusat_display = pusat

        # ===== V37: TEMPLAT JPN DIUTAMAKAN - kalau JPN dah cipta templat jawatan ini, PDF dijana dari templat itu =====
        _h37 = render_jpn_template_html(jawatan, nama, ic, sek_asal, nama_sek_asal, pusat, nama_pusat, no_surat, kod_ppd, ppd_name, tarikh, bilik_kebal)
        if _h37:
            _pdf37 = html_to_pdf_bytes(_h37)
            if _pdf37:
                return _pdf37
        # (jika templat tiada / enjin PDF tiada -> guna susun atur lama di bawah)
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        import io, os
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=16*mm, leftMargin=17.5*mm, topMargin=8*mm, bottomMargin=19*mm)
        styles = getSampleStyleSheet()

        style_header_mid = ParagraphStyle('HeaderMid', parent=styles['Normal'], fontSize=10.5, leading=13.5, alignment=0, fontName='Times-Bold')
        style_header_right = ParagraphStyle('HeaderRight', parent=styles['Normal'], fontSize=10, leading=13, alignment=2, fontName='Times-Roman')
        style_normal = ParagraphStyle('NormalJPN', parent=styles['Normal'], fontSize=10.5, leading=13, spaceAfter=3, alignment=4, fontName='Helvetica')
        style_normal_left = ParagraphStyle('NormalLeft', parent=styles['Normal'], fontSize=10.5, leading=13, spaceAfter=3, alignment=0, fontName='Helvetica')
        style_bold = ParagraphStyle('BoldJPN', parent=styles['Normal'], fontSize=10.5, leading=13, spaceAfter=4, alignment=0, fontName='Helvetica-Bold')
        style_tajuk = ParagraphStyle('TajukJPN', parent=styles['Normal'], fontSize=10.5, leading=13, spaceAfter=6, alignment=0, fontName='Helvetica-Bold')
        style_small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=10.5, leading=13, alignment=0, fontName='Helvetica')
        style_num = ParagraphStyle('NumItem', parent=style_small, leftIndent=11*mm)

        story = []

        # ===== HEADER - IKUT GAMBAR =====
        logo_path = find_asset(LOGO_NAMES)
        for cand in ([] if logo_path else ["/mnt/data/jata_cropped.png", "/mnt/data/65b0dade-7a33-4312-b19b-9d5b24dd57ce.jpg", "jata_negara_hd.png","./jata_negara_hd.png","jata_negara.png","./jata_negara.png","/mnt/data/jata_negara_hd.png"]):
            if os.path.exists(cand):
                logo_path = cand
                break

        middle_html = """<b>KEMENTERIAN PENDIDIKAN<br/>Jabatan Pendidikan Negeri Selangor<br/>Jalan Jambu Bol 4/3E, Seksyen 4<br/>40604 Shah Alam, Selangor</b>"""
        right_html = """Tel &nbsp;: &nbsp;03 \u2013 5518 6500<br/>Faks &nbsp;: &nbsp;03 \u2013 5510 2133<br/>Laman Web &nbsp;: jpnselangor.moe.gov.my"""

        if logo_path:
            try:
                logo_img = RLImage(logo_path, width=30*mm, height=21*mm, kind='proportional')
                header_data = [[logo_img, Paragraph(middle_html, style_header_mid), Paragraph(right_html, style_header_right)]]
                t = Table(header_data, colWidths=[34*mm, 78*mm, 64*mm])
                t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.8, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 2), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
                story.append(t)
            except:
                header_data = [[Paragraph("", style_header_mid), Paragraph(middle_html, style_header_mid), Paragraph(right_html, style_header_right)]]
                t = Table(header_data, colWidths=[34*mm, 78*mm, 64*mm])
                t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.8, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
                story.append(t)
        else:
            header_data = [[Paragraph("", style_header_mid), Paragraph(middle_html, style_header_mid), Paragraph(right_html, style_header_right)]]
            t = Table(header_data, colWidths=[34*mm, 78*mm, 64*mm])
            t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 0.8, colors.black), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
            story.append(t)

        story.append(Spacer(1,4))

        # ===== RUJ KAMI & TARIKH - KANAN, TABLE KEMAS =====
        style_ruj_label = ParagraphStyle('RujLabel', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica')
        style_ruj_value = ParagraphStyle('RujValue', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica')
        style_ruj_colon = ParagraphStyle('RujColon', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica')

        ruj_inner_data = [
            [Paragraph("Ruj. Kami", style_ruj_label), Paragraph(":", style_ruj_colon), Paragraph(no_surat, style_ruj_value)],
            [Paragraph("Tarikh", style_ruj_label), Paragraph(":", style_ruj_colon), Paragraph(tarikh, style_ruj_value)]
        ]
        t_ruj_inner = Table(ruj_inner_data, colWidths=[22*mm, 4*mm, 62*mm])
        t_ruj_inner.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 1), ('RIGHTPADDING', (0,0), (-1,-1), 1), ('TOPPADDING', (0,0), (-1,-1), 1), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        wrapper_data = [[Paragraph("", style_ruj_label), t_ruj_inner]]
        t_wrapper = Table(wrapper_data, colWidths=[80*mm, 88*mm])
        t_wrapper.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
        story.append(t_wrapper)
        story.append(Spacer(1,4))

        # ===== NAMA & MELALUI =====
        story.append(Paragraph(f"<b>{nama.upper()}</b>", style_bold))
        story.append(Spacer(1,4))
        style_blok = ParagraphStyle('BlokPenerima', parent=style_normal_left, spaceAfter=0)
        story.append(Paragraph("Melalui :", style_normal_left))
        story.append(Spacer(1,2))
        story.append(Paragraph("<b>PENGETUA/ GURU BESAR</b>", style_blok))
        story.append(Paragraph(f"<b>{(nama_sek_asal or sek_asal).upper()}</b>", style_blok))     # nama sekolah sahaja (tanpa kod)
        story.append(Paragraph(f"<b>{ppd_name.upper()}</b>", style_blok))
        story.append(Spacer(1,4))
        story.append(Paragraph("Tuan,", style_normal_left))
        story.append(Spacer(1,4))

        # ===== TAJUK - IKUT GAMBAR =====
        tajuk_jawatan = jawatan.upper()
        if "PENYELIA KAWASAN" in tajuk_jawatan:
            tajuk_full = f"SIJIL PELAJARAN MALAYSIA ULANGAN ( SPMU ) TAHUN 2026 :<br/>PELANTIKAN SEBAGAI PENYELIA KAWASAN BERTULIS ( TATAKIRA/PEMEGANG KUNCI )"
        else:
            from program_config import tajuk_surat as _tajuk_surat, cfg as _pcfg, adalah_spm as _adalah_spm
            _t1, _t2 = _tajuk_surat(tajuk_jawatan)
            tajuk_full = f"{_t1}<br/>{_t2}"

        story.append(Paragraph(f"<b>{tajuk_full}</b>", style_tajuk))
        story.append(Spacer(1,4))
        story.append(Paragraph("Dengan hormatnya perkara di atas dirujuk.", style_normal))
        story.append(Spacer(1,4))

        # ===== PARA 2 - IKUT GAMBAR 100% - FIX NO PUSAT & BILIK KEBAL =====
        # LOGIK BARU: No Pusat = No Pusat sebenar (BB017), Bilik Kebal kosong dulu kalau belum set di selenggara
        # Kalau Penyelia Kawasan, bilik_kebal datang dari selenggara bilik kebal -> kod_bilik_kebal
        # No Pusat datang dari kod_pusat (pusat jagaan)

        # Tentukan jenis jawatan
        is_penyelia_kawasan = "PENYELIA KAWASAN" in jawatan.upper()

        if is_penyelia_kawasan:
            para2_text = f"2. &nbsp;&nbsp;&nbsp;&nbsp;Sukacita dimaklumkan bahawa, tuan dilantik sebagai <b>{jawatan}</b> bagi peperiksaan di atas dari tempoh <b>14 Julai hingga 16 Julai 2026</b>. Pelantikan ini merupakan sebahagian daripada tugas rasmi. Maklumat pusat peperiksaan di bawah pengawasan tuan adalah seperti berikut:"
        else:
            para2_text = f"2. &nbsp;&nbsp;&nbsp;&nbsp;Sukacita dimaklumkan tuan dilantik sebagai <b>{jawatan.title()}</b> bagi {_pcfg()["ujian_kata"]} di atas. Berikut adalah pusat {_pcfg()["ujian_kata"]} di bawah pengawasan tuan:"

        story.append(Paragraph(para2_text, style_normal))
        story.append(Spacer(1,4))

        # 2.1, 2.2, 2.3 - TABLE KEMAS - FIX: No Pusat betul, Bilik Kebal ikut selenggara
        style_sub_label = ParagraphStyle('SubLabel', parent=styles['Normal'], fontSize=10.5, leading=13, alignment=0, leftIndent=15*mm, fontName='Helvetica')
        style_sub_value = ParagraphStyle('SubValue', parent=styles['Normal'], fontSize=10.5, leading=13, alignment=0, fontName='Helvetica-Bold')
        style_sub_value_empty = ParagraphStyle('SubValueEmpty', parent=styles['Normal'], fontSize=10, leading=13, alignment=0, fontName='Helvetica', textColor=colors.HexColor('#1565c0'))

        # LOGIK: No Pusat = kod pusat sebenar, BUKAN bilik kebal
        # Kalau bilik_kebal kosong, paparkan - atau kosong untuk isi kemudian
        if not bilik_kebal or bilik_kebal.strip() == "" or bilik_kebal.lower() in ("nan","none","null","-"):
            bilik_kebal_display = ""  # Kosongkan dulu seperti request
            bilik_kebal_para = Paragraph(f": <i>(Akan dikemaskini melalui Selenggara Bilik Kebal)</i>", style_sub_value_empty)
        else:
            bilik_kebal_display = bilik_kebal.upper()
            bilik_kebal_para = Paragraph(f": {bilik_kebal_display}", style_sub_value)

        # No Pusat - pastikan bukan bilik kebal code (CB, BK)
        # Jika no_pusat_display mengandungi CB/BK dan kita ada pusat sebenar, guna pusat sebenar
        if no_pusat_display.upper().startswith(("CB","BK")) and pusat:
            # no_pusat_display ni sebenarnya bilik kebal, tukar guna pusat sebenar
            no_pusat_final = pusat.split(",")[0].strip() if "," in pusat else pusat
        else:
            no_pusat_final = no_pusat_display

        _nama_pusat_only = (nama_pusat or display_pusat).upper()
        if not bilik_kebal_display:
            _bk_cell = Paragraph("<i>(Akan dikemaskini melalui Selenggara Bilik Kebal)</i>", style_sub_value_empty)
        else:
            _bk_cell = Paragraph(bilik_kebal_display, style_sub_value)
        sub_data = [
            [Paragraph("2.1", style_num), Paragraph("No. Pusat", style_small), Paragraph(":", style_small), Paragraph(no_pusat_final, style_sub_value)],
            [Paragraph("2.2", style_num), Paragraph("Nama Pusat", style_small), Paragraph(":", style_small), Paragraph(_nama_pusat_only, style_sub_value)],
            [Paragraph("2.3", style_num), Paragraph("Bilik Kebal", style_small), Paragraph(":", style_small), _bk_cell],
        ]
        t_sub = Table(sub_data, colWidths=[20*mm, 30*mm, 4*mm, 100*mm])
        t_sub.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        story.append(t_sub)
        story.append(Spacer(1,4))

        # ===== PARA 3 - ELAUN =====
        story.append(Paragraph("3. &nbsp;&nbsp;&nbsp;&nbsp;Tuan akan dibayar dengan kadar elaun berikut:", style_normal))
        story.append(Spacer(1,4))

        elaun_data = [
            [Paragraph("3.1", style_num), Paragraph("Elaun Ikhtisas", style_small), Paragraph(":", style_small), Paragraph(f"<b>{_pcfg()['elaun_ikhtisas']}</b>", style_small)],
            [Paragraph("3.2", style_num), Paragraph("Elaun Perjalanan", style_small), Paragraph(":", style_small),
             Paragraph("<b>Tuan layak membuat tuntutan perjalanan menggunakan kenderaan sendiri/ awam berdasarkan kepada Arahan Perbendaharaan yang sedang berkuatkuasa.</b>", style_small)],
        ]
        t_elaun = Table(elaun_data, colWidths=[20*mm, 32*mm, 4*mm, 100*mm])
        t_elaun.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        story.append(t_elaun)
        story.append(Spacer(1,4))

        # ===== PARA 4 =====
        para4 = """4. &nbsp;&nbsp;&nbsp;&nbsp;Pelantikan ini adalah sebahagian daripada tugas rasmi. Sehubungan dengan itu, tuan dikehendaki melaksanakan tugasan seperti yang tersenarai di <b>Lampiran A</b>. Tuan boleh dilantik oleh Ketua Pengawas sebagai <b>Pengawas Pengiring</b> mengikut keperluan ke bilik kebal. Pelantikan tuan adalah <b>Sulit</b> dan tertakluk kepada <b>Akta Rahsia Rasmi 1972</b> dan lain-lain peraturan keselamatan yang sedang berkuatkuasa."""
        if not _adalah_spm():          # UBBM/UBBI: tiada Pengawas Pengiring
            para4 = re.sub(r"\s*Tuan boleh dilantik oleh Ketua Pengawas sebagai <b>Pengawas Pengiring</b> mengikut keperluan ke bilik kebal\.", "", para4)
        story.append(Paragraph(para4, style_normal))
        story.append(Spacer(1,4))

        # ===== PARA 5 =====
        para5 = "5. &nbsp;&nbsp;&nbsp;&nbsp;Semoga tuan dapat melaksanakan tugas ini dengan penuh dedikasi dan berintegriti dalam menyempurnakan amanah yang dipertanggungjawabkan."
        story.append(Paragraph(para5, style_normal))
        story.append(Spacer(1,4))
        # ===== PENUTUP + TANDATANGAN (satu blok, tak terpisah antara muka surat) =====
        sig_path = find_asset(SIGN_NAMES)
        _base = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
        for _name in ([] if sig_path else ["tandatangan_pengarah_hd.png", "tandatangan_pengarah.png", "tandatangan_pengarah.jpg", "tandatangan.png"]):
            for _dir in [_base, ".", "/mnt/data", os.path.join(_base, "assets")]:
                _p = os.path.join(_dir, _name)
                if os.path.exists(_p):
                    sig_path = _p
                    break
            if sig_path:
                break

        penutup = [
            Paragraph("Sekian, terima kasih.", style_normal_left),
            Spacer(1, 5),
            Paragraph("\u201cMALAYSIA MADANI\u201d", style_bold),
            Paragraph("\u201cBERKHIDMAT UNTUK NEGARA\u201d", style_bold),
            Spacer(1, 5),
            Paragraph("Saya yang menjalankan amanah,", style_normal_left),
        ]
        sig_flow = None
        if sig_path:
            try:
                sig_flow = RLImage(sig_path, width=40*mm, height=17*mm, kind='proportional')
                sig_flow.hAlign = 'LEFT'
            except Exception:
                sig_flow = None
        penutup.append(sig_flow if sig_flow is not None else Spacer(1, 26))
        penutup.append(Paragraph("<b>(DATIN WAN NOR ASHIKIN BINTI ABU KASSIM)<br/>Pengarah Pendidikan,<br/>Jabatan Pendidikan Selangor.</b>", style_normal_left))
        story.append(KeepTogether(penutup))

        def _kaki_surat(canvas, _doc):
            canvas.saveState()
            _W = A4[0]
            _x0, _x1 = 17.5*mm, _W - 16*mm
            canvas.setFillColor(colors.black)
            canvas.rect(_x0, 8*mm, _x1 - _x0, 7*mm, stroke=0, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 8.5)
            canvas.drawCentredString((_x0 + _x1) / 2, 10.4*mm, "JABATAN PENDIDIKAN NEGERI SELANGOR SENTIASA BERKUALITI DAN TERUS UNGGUL")
            canvas.restoreState()
        doc.build(story, onFirstPage=_kaki_surat, onLaterPages=_kaki_surat)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        _log.debug(f"PDF surat error: {e}"); _surat_err("PDF surat (ReportLab)", e)
        return None




def generate_surat_kolektif_pdf_bytes_JPN(surat_list, kod_ppd, ppd_name, title_prefix="SURAT LANTIKAN"):
    if len(surat_list) > MAX_PDF_KOLEKTIF:
        st.warning(f"PDF dihadkan {MAX_PDF_KOLEKTIF} surat (ada {len(surat_list)}).")
        surat_list = surat_list[:MAX_PDF_KOLEKTIF]
    # RINGAN-START
    """Jana PDF kolektif guna template JPN - untuk PPD download pukal"""
    # ===== V37: gabung PDF individu (templat JPN) menjadi satu PDF kolektif =====
    try:
        from pypdf import PdfWriter, PdfReader
        import io as _io
        _w = PdfWriter()
        _n = 0
        for _s in surat_list:
            _pdf = generate_surat_pdf_bytes_FIXED(
                _s.get("nama",""), _s.get("ic",""), _s.get("jawatan",""),
                _s.get("sekolah_asal",""), _s.get("nama_sekolah_asal","") or _s.get("sekolah_asal",""),
                _s.get("pusat",""), _s.get("nama_pusat","") or _s.get("pusat",""),
                _s.get("no_surat",""), kod_ppd, ppd_name,
                datetime.date.today().strftime("%d %B %Y"),
                bilik_kebal=_s.get("bilik_kebal","") or _s.get("kod_bilik_kebal","")
            )
            if _pdf:
                for _pg in PdfReader(_io.BytesIO(_pdf)).pages:
                    _w.add_page(_pg)
                _n += 1
        if _n > 0:
            _out = _io.BytesIO()
            _w.write(_out)
            return _out.getvalue()
    except Exception as _e:
        _log.debug(f"Gabung PDF kolektif gagal, guna kaedah lama: {_e}"); _surat_err("PDF kolektif (pypdf) - guna susun atur ringkas", _e)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        import io
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=10*mm, bottomMargin=10*mm)
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('TitleKolektif', parent=styles['Heading1'], fontSize=12, alignment=1, spaceAfter=6)
        style_normal = ParagraphStyle('NormalKolektif', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=3)
        story = []
        story.append(Paragraph(f"{title_prefix} - PPD {kod_ppd} {ppd_name} - {len(surat_list)} Surat - JPN SELARAS", style_title))
        story.append(Spacer(1,8))
        for idx, s in enumerate(surat_list, 1):
            try:
                # Guna function JPN baru
                pdf_one = generate_surat_pdf_bytes_FIXED(
                    s.get("nama",""), s.get("ic",""), s.get("jawatan",""),
                    s.get("sekolah_asal",""), s.get("nama_sekolah_asal","") or s.get("sekolah_asal",""),
                    s.get("pusat",""), s.get("nama_pusat","") or s.get("pusat",""),
                    s.get("no_surat",""), kod_ppd, ppd_name,
                    datetime.date.today().strftime("%d %B %Y")
                )
                # Kita tak embed pdf_one, kita buat text representation kolektif - buat isi ringkas
                # Tapi untuk kolektif kita buat paragraph per surat guna template JPN HTML rendering
                jpn_html = render_jpn_template_html(
                    s.get("jawatan",""), s.get("nama",""), s.get("ic",""),
                    s.get("sekolah_asal",""), s.get("nama_sekolah_asal",""),
                    s.get("pusat",""), s.get("nama_pusat",""),
                    s.get("no_surat",""), kod_ppd, ppd_name,
                    datetime.date.today().strftime("%d %B %Y")
                )
                if jpn_html:
                    # bersihkan sikit
                    import re
                    clean = re.sub(r'<style.*?</style>', '', jpn_html, flags=re.DOTALL|re.IGNORECASE)
                    clean = re.sub(r'<head.*?</head>', '', clean, flags=re.DOTALL|re.IGNORECASE)
                    story.append(Paragraph(f"<b>{idx}. {s.get('nama','')} - {s.get('no_surat','')} - {s.get('sekolah_asal','')}</b>", style_normal))
                    story.append(Paragraph(clean[:8000], style_normal))
                else:
                    story.append(Paragraph(f"<b>{idx}. {s.get('nama','')} - {s.get('jawatan','')} - {s.get('pusat','')} - {s.get('no_surat','')}</b><br/>Sekolah Asal: {s.get('sekolah_asal','')} - Pusat: {s.get('pusat','')}", style_normal))
                story.append(Spacer(1,6))
                if idx % 3 == 0:
                    story.append(PageBreak())
            except Exception as e:
                story.append(Paragraph(f"Error surat {idx}: {e}", style_normal))
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        _log.debug(f"Kolektif JPN error: {e}"); _surat_err("PDF kolektif", e)
        return None

def create_zip_pukal_dari_JPN(surat_list, kod_ppd, ppd_name):
    """VERSI RINGAN: Limit 200 file per ZIP untuk 300 user"""
    try:
        import zipfile, io
        if len(surat_list) > MAX_ZIP_FILES:
            st.warning(f"ZIP dihadkan {MAX_ZIP_FILES} file (ada {len(surat_list)}).")
            surat_list = surat_list[:MAX_ZIP_FILES]
        zip_buffer = io.BytesIO()
        _zip_ok = 0
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, s in enumerate(surat_list, 1):
                try:
                    pdf_bytes = generate_surat_pdf_bytes_FIXED(
                        s.get("nama",""), s.get("ic",""), s.get("jawatan",""),
                        s.get("sekolah_asal",""), s.get("nama_sekolah_asal","") or s.get("sekolah_asal",""),
                        s.get("pusat",""), s.get("nama_pusat","") or s.get("pusat",""),
                        s.get("no_surat",""), kod_ppd, ppd_name,
                        datetime.date.today().strftime("%d %B %Y")
                    )
                    if pdf_bytes:
                        safe_nama = "".join(c if c.isalnum() or c in ("_","-") else "_" for c in str(s.get("nama",""))[:25])
                        safe_no = str(s.get("no_surat","")).replace("/","_").replace("\\","_").replace(" ","_")[:30]
                        safe_sek = str(s.get("sekolah_asal","")).replace("/","_")[:10]
                        # Format: 01_NAMA_SEKOLAH_NOSURAT.pdf - senang SUP cari
                        file_name = f"{idx:03d}_{safe_nama}_{safe_sek}_{safe_no}.pdf"
                        zip_file.writestr(file_name, pdf_bytes)
                        _zip_ok += 1
                except Exception as e:
                    _surat_err("ZIP surat individu", e)
                    continue
        if _zip_ok == 0:
            _surat_err("ZIP surat individu", "tiada satu pun PDF berjaya dijana - ZIP tidak dihasilkan")
            return None
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    except Exception as e:
        _log.debug(f"ZIP JPN error: {e}")
        return None

def hantar_surat_ke_sekolah_asal_bulk(surat_list, kod_ppd):
    """NEW: Bila PPD jana surat, auto update status supaya surat sampai ke sekolah asal petugas"""
    try:
        # Kita update cadangan_sup dengan status SURAT_SAMPAI_SEKOLAH_ASAL + tambah log
        berjaya = 0
        for s in surat_list:
            try:
                no_surat = s.get("no_surat","")
                ic = s.get("ic","")
                sek_asal = s.get("sekolah_asal","")
                pusat = s.get("pusat","")
                if not ic:
                    continue
                # Update cadangan_sup
                payload = {
                    "status": "SURAT_SAMPAI_SEKOLAH_ASAL",
                    "no_surat": no_surat,
                    "kod_pusat": pusat,
                    "tarikh_jana_surat": str(datetime.date.today()),
                    "sekolah_asal_hantar": sek_asal
                }
                try:
                    supa.table("cadangan_sup").update(payload).eq("ic_guru", ic).eq("kod_ppd", kod_ppd.lower() if kod_ppd else "bh").execute()
                    berjaya += 1
                except:
                    try:
                        supa.table("cadangan_sup").update(payload).eq("ic_guru", ic).execute()
                        berjaya += 1
                    except:
                        pass
            except:
                continue
        # Cuba simpan ke table log khas jika ada (surat_hantar_sekolah_asal) - optional
        try:
            log_data = []
            for s in surat_list:
                log_data.append({
                    "kod_ppd": kod_ppd,
                    "ic_guru": s.get("ic",""),
                    "nama_guru": s.get("nama",""),
                    "kod_sekolah_asal": s.get("sekolah_asal",""),
                    "kod_pusat": s.get("pusat",""),
                    "no_surat": s.get("no_surat",""),
                    "jawatan": s.get("jawatan",""),
                    "tarikh_hantar": str(datetime.date.today()),
                    "status": "SAMPAI_KE_SEKOLAH_ASAL"
                })
            # batch insert kalau table wujud
            try:
                supa.table("surat_hantar_sekolah_asal").insert(log_data).execute()
            except:
                pass
        except:
            pass
        return berjaya
    except Exception as e:
        _log.debug(f"hantar sekolah asal error: {e}")
        return 0

# Monkey-patch
try:
    generate_surat_html = generate_surat_html_FIXED
    generate_surat_pdf_bytes = generate_surat_pdf_bytes_FIXED
    generate_surat_pdf_bytes_FIXED_OLD = generate_surat_pdf_bytes_FIXED
    # keep original names also
    globals()['generate_surat_html'] = generate_surat_html_FIXED
    globals()['generate_surat_pdf_bytes'] = generate_surat_pdf_bytes_FIXED
    # new bulk funcs
    globals()['generate_surat_kolektif_pdf_bytes_JPN'] = generate_surat_kolektif_pdf_bytes_JPN
    globals()['create_zip_pukal_dari_JPN'] = create_zip_pukal_dari_JPN
    globals()['hantar_surat_ke_sekolah_asal_bulk'] = hantar_surat_ke_sekolah_asal_bulk
except:
    pass



def get_template_guru(kod_sekolah_contoh="BFT0003", nama_sekolah_contoh="SAM NURUL IMAN", kod_ppd_contoh="BH"):
    """Template FINAL ringkas - hanya wajib, pengalaman & jawatan boleh kosong"""
    template = {
        "kod_ppd": [kod_ppd_contoh.lower()],
        "kod_sekolah": [kod_sekolah_contoh.upper()],
        "nama_guru": ["CONTOH: ALI BIN ABU"],
        "ic_guru": ["900101-01-1234"],
        "jantina": ["LELAKI"],
        "poskod_rumah": ["40000"],
        "alamat_rumah": ["NO 1, JALAN CONTOH, KLANG"],
        "telefon_guru": ["012-3456789"],
        "no_pusat_asal": ["BA142"],
        "kod_sekolah_asal": [kod_sekolah_contoh.upper()],
        "nama_sekolah_asal": [nama_sekolah_contoh],
        "kod_ppd_asal": [kod_ppd_contoh],
        "jawatan_cadangan": [""],
        "pengalaman_spm": [""],
        "email_guru": [""],
    }
    return pd.DataFrame(template)

def get_template_guru_friendly():
    template_mudah = {
        "NAMA GURU": ["CONTOH: ALI BIN ABU"],
        "IC GURU": ["900101-01-1234"],
        "JANTINA": ["L/LELAKI/PEREMPUAN"],
        "KOD PPD": ["BH"],
        "KOD SEKOLAH": ["BFT0003"],
        "POSKOD RUMAH": ["40000"],
        "ALAMAT RUMAH": ["NO 1, JALAN CONTOH, KLANG"],
        "TELEFON GURU": ["012-3456789"],
        "NO PUSAT ASAL": ["BA142"],
        "KOD SEKOLAH ASAL": ["BFT0003"],
        "NAMA SEKOLAH ASAL": ["SAM NURUL IMAN"],
        "KOD PPD ASAL": ["BH"],
        "JAWATAN CADANGAN": ["(Kosongkan)"],
        "PENGALAMAN SPM": ["(Kosongkan)"],
    }
    return pd.DataFrame(template_mudah)

def normalize_guru_import(df_upload):
    HEADER_MAP = {
        "NAMA GURU": "nama_guru", "NAMA_GURU": "nama_guru", "nama_guru": "nama_guru", "NAMA": "nama_guru",
        "IC GURU": "ic_guru", "IC_GURU": "ic_guru", "ic_guru": "ic_guru", "IC": "ic_guru",
        "KOD PPD": "kod_ppd", "KOD_PPD": "kod_ppd", "kod_ppd": "kod_ppd",
        "KOD SEKOLAH": "kod_sekolah", "KOD_SEKOLAH": "kod_sekolah", "kod_sekolah": "kod_sekolah",
        "KOD SEKOLAH ASAL": "kod_sekolah_asal", "KOD_SEKOLAH_ASAL": "kod_sekolah_asal", "kod_sekolah_asal": "kod_sekolah_asal",
        "JANTINA": "jantina", "jantina": "jantina",
        "POSKOD RUMAH": "poskod_rumah", "POSKOD_RUMAH": "poskod_rumah", "poskod_rumah": "poskod_rumah",
        "ALAMAT RUMAH": "alamat_rumah", "ALAMAT_RUMAH": "alamat_rumah", "alamat_rumah": "alamat_rumah",
        "TELEFON GURU": "telefon_guru", "TELEFON_GURU": "telefon_guru", "telefon_guru": "telefon_guru",
        "EMAIL GURU": "email_guru", "EMAIL_GURU": "email_guru", "email_guru": "email_guru",
        "JAWATAN CADANGAN": "jawatan_cadangan", "JAWATAN_CADANGAN": "jawatan_cadangan", "jawatan_cadangan": "jawatan_cadangan",
        "PENGALAMAN SPM": "pengalaman_spm", "PENGALAMAN_SPM": "pengalaman_spm", "pengalaman_spm": "pengalaman_spm",
        "NO PUSAT ASAL": "no_pusat_asal", "NO_PUSAT_ASAL": "no_pusat_asal", "no_pusat_asal": "no_pusat_asal",
        "NAMA SEKOLAH ASAL": "nama_sekolah_asal", "NAMA_SEKOLAH_ASAL": "nama_sekolah_asal", "nama_sekolah_asal": "nama_sekolah_asal",
        "KOD PPD ASAL": "kod_ppd_asal", "KOD_PPD_ASAL": "kod_ppd_asal", "kod_ppd_asal": "kod_ppd_asal",
    }
    normalized_cols = {}
    for col in df_upload.columns:
        col_str = str(col).strip()
        if col_str in HEADER_MAP:
            normalized_cols[col] = HEADER_MAP[col_str]
        elif col_str.upper() in HEADER_MAP:
            normalized_cols[col] = HEADER_MAP[col_str.upper()]
        elif col_str.lower() in HEADER_MAP:
            normalized_cols[col] = HEADER_MAP[col_str.lower()]
        else:
            for k,v in HEADER_MAP.items():
                if k.lower() == col_str.lower():
                    normalized_cols[col] = v
                    break
            else:
                normalized_cols[col] = None
    return normalized_cols

# ================= REFRESH COMPONENT =================
def add_refresh_button():
    """v39: butang refresh kini berada dalam header (ui_theme.shell_header). Dikekalkan untuk keserasian."""
    if st.button("REFRESH - Baca Data Baru", use_container_width=True, type="primary", key=f"refresh_legacy_{st.session_state.get('role')}"):
        st.cache_data.clear()
        st.rerun()

# ================= SESSION INIT =================
# ================= LOGIN PAGE =================


# ===== FIX: BUILD PUSAT MAP ROBUST - IKUT NO PUSAT COLUMN REFER PUSAT_MASTER =====
def build_pusat_map_from_master():
    """Map NO_PUSAT/KOD_PUSAT -> NAMA_PUSAT dari pusat_master"""
    pmap = {}
    try:
        df_p = get_pusat_df()
        for _, pr in df_p.iterrows():
            d = pr.get("data") if isinstance(pr.get("data"), dict) else {}
            if isinstance(d, str):
                try:
                    import json as _js
                    d = _js.loads(d)
                except:
                    d = {}
            # Ambil semua kemungkinan key untuk NO PUSAT
            no_p = str(pr.get("no_pusat") or pr.get("kod_pusat") or pr.get("NO_PUSAT") or pr.get("KOD_PUSAT") or d.get("NO_PUSAT") or d.get("NO PUSAT") or d.get("KOD_PUSAT") or d.get("KOD PUSAT") or "").upper().strip()
            nama_p = str(pr.get("nama_pusat") or pr.get("NAMA_PUSAT") or d.get("NAMA_PUSAT") or d.get("NAMA PUSAT") or "").strip()
            if no_p:
                pmap[no_p] = nama_p
                # juga map tanpa prefix? simpan kedua-dua
                # contoh BA140 tetap BA140
        # Fallback: cuba direct dari supabase pusat_master jika get_pusat_df kosong
        if not pmap:
            try:
                _supa = supa
                res = _supa.table("pusat_master").select("*").limit(1000).execute()
                for r in (res.data or []):
                    no_p = str(r.get("no_pusat") or r.get("kod_pusat") or r.get("NO_PUSAT") or "").upper().strip()
                    nama_p = str(r.get("nama_pusat") or r.get("NAMA_PUSAT") or "").strip()
                    if no_p:
                        pmap[no_p] = nama_p
            except:
                pass
    except Exception as _e:
        pass
    return pmap


# ================= LOGIN POPUP BARU - IKUT HTML (SUP/PPD/JPN POPUP) =================
FLY_SUP = {
    'dashboard': [('utama', '🏠 Utama'), ('pusat', '📍 Senarai Pusat'), ('guru', '👥 Guru Terkini')],
    'senarai':   [('filter', '🔍 Senarai & Filter'), ('edit', '✏️ Edit Data Guru')],
    'cadangan':  [('pilih', '👥 Pilih & Cadang'), ('senarai', '📋 Senarai Cadangan')],
    'surat':     [('jadual', '📑 Jadual Jawatan'), ('individu', '📄 Surat Individu')],
}
FLY_PPD = {
    'dashboard':  [('ringkasan', '📊 Ringkasan'), ('status', '📍 Status Pusat'), ('berwarna', '🎨 Paparan Warna'), ('sekolah', '🏫 Sekolah & Export')],
    'pusat':      [('senarai', '📋 Senarai Pusat'), ('poskod', '📮 Poskod Pusat')],
    'zon':        [('tetap', '⚙️ Tetapan Zon'), ('tempat', '🚀 Jana Penempatan Zon'), ('semak', '📋 Semakan Zon')],
    'cadangan':   [('sekolah', '🏫 Ikut Sekolah'), ('nama', '📝 Senarai Nama Cadangan'), ('simpanan', '📦 Senarai Simpanan')],
    'jana':       [('auto', '🌍 Jana Auto Poskod'), ('jawatan', '👑 Ikut Jawatan')],
    'hasil':      [('ringkasan', '📋 Ringkasan Pusat'), ('sekolah', '🏫 Ikut Sekolah Asal'), ('guru', '👥 Semua Guru')],
    'semakan':    [('semak', '🔍 Semakan Lantikan'), ('kosong', '➕ Isi Kekosongan')],
    'kelulusan':  [('keseluruhan', '✅ Lulus Keseluruhan'), ('pusat', '🏫 Lulus Ikut Pusat')],
    'selenggara': [('form', '➕ Tambah Bilik Kebal'), ('senarai', '📋 Senarai Bilik Kebal'), ('import', '📤 Import Excel'), ('penyelia', '🔐 Tempatkan Penyelia'), ('surat', '📄 Jana Surat Penyelia')],
    'jana_surat': [('keseluruhan', '📄 Semua Surat'), ('pusat', '🏫 Ikut Pusat'), ('sekolah', '🏫 Ikut Sekolah Asal')],
}
FLY_JPN = {
    'dashboard': [('ringkasan', '📊 Ringkasan'), ('ppd', '🏢 Breakdown PPD')],
    'sekolah':   [('senarai', '🏫 Senarai Sekolah'), ('import', '📤 Import Sekolah'), ('auto', '⚡ Auto Generate')],
    'pusat':     [('senarai', '📋 Senarai Pusat'), ('fix', '🔧 Fix Jumlah Calon'), ('tambah', '➕ Tambah Pusat'), ('import', '📤 Import Pusat'), ('kosong', '🗑️ Kosongkan Pusat')],
    'guru':      [('import', '📤 Import Master 60K'), ('data', '📊 Data Sedia Ada')],
    'admin':     [('status', '🩺 Status Sistem'), ('table', '🛠️ Buat Table')],
}

import os as _os
_ASSET_DIR = _os.path.dirname(_os.path.abspath(__file__))
LOGO_NAMES = ["jata_cropped.png", "jata_negara_hd.png", "jata_negara.png"]
SIGN_NAMES = ["tandatangan_pengarah_hd.png", "tandatangan_pengarah.png", "tandatangan_pengarah.jpg", "tandatangan.png"]

def find_asset(names):
    """Cari imej: (1) yang dimuat naik ke Supabase, (2) fail di folder projek, ./, /mnt/data dan assets/."""
    kind = "logo" if names is LOGO_NAMES else ("tandatangan" if names is SIGN_NAMES else None)
    if kind:
        _p = aset_file(kind)
        if _p:
            return _p
    for n in names:
        for d in (_ASSET_DIR, ".", "/mnt/data", _os.path.join(_ASSET_DIR, "assets"), "assets"):
            p = _os.path.join(d, n)
            if _os.path.exists(p):
                return p
    return None

def surat_aset_amaran():
    """Papar amaran jika logo / tandatangan surat tiada dalam repo (surat akan keluar tanpa logo/sign)."""
    miss = []
    if not find_asset(LOGO_NAMES):
        miss.append("logo Jata Negara (jata_negara_hd.png)")
    if not find_asset(SIGN_NAMES):
        miss.append("tandatangan Pengarah (tandatangan_pengarah_hd.png)")
    if miss:
        st.warning("⚠️ Fail imej surat tidak dijumpai dalam repo: " + " dan ".join(miss) +
                   ". Letakkan fail ini di folder yang sama dengan spm_core.py (atau dalam folder assets/), kemudian deploy semula. "
                   "Tanpa fail ini, surat PDF keluar tanpa logo dan tandatangan.")


# ======================================================================= v40: ASET SURAT & DIAGNOSTIK
ASET_KEYS = {"logo": "__ASET_LOGO__", "tandatangan": "__ASET_TANDATANGAN__"}


def _surat_err(ctx, e):
    """Simpan ralat terakhir penjanaan surat (dipaparkan dalam panel Semakan Sistem Surat)."""
    try:
        st.session_state["_surat_err"] = f"{ctx}: {type(e).__name__}: {str(e)[:300]}" if isinstance(e, Exception) else f"{ctx}: {e}"
    except Exception:
        pass


@st.cache_data(ttl=300, show_spinner=False)
def aset_data_uri(kind):
    """Imej logo/tandatangan yang dimuat naik JPN (disimpan dalam surat_templates_jpn). Pulang data URI atau ''."""
    try:
        res = get_supabase().table("surat_templates_jpn").select("template_html").eq("jawatan", ASET_KEYS[kind]).limit(1).execute()
        v = ((res.data or [{}])[0].get("template_html")) or ""
        return v if str(v).startswith("data:image") else ""
    except Exception:
        return ""


def aset_bytes(kind):
    import base64
    uri = aset_data_uri(kind)
    if not uri:
        return None
    try:
        return base64.b64decode(uri.split(",", 1)[1])
    except Exception:
        return None


def aset_file(kind):
    """Tulis imej dari Supabase ke fail sementara supaya boleh dibaca oleh ReportLab / xhtml2pdf."""
    import hashlib, tempfile
    b = aset_bytes(kind)
    if not b:
        return None
    p = _os.path.join(tempfile.gettempdir(), f"spm_aset_{kind}_{hashlib.md5(b).hexdigest()[:10]}.png")
    if not _os.path.exists(p):
        with open(p, "wb") as f:
            f.write(b)
    return p


def aset_save(kind, raw_bytes):
    """Kecilkan (maks 900px) dan simpan sebagai PNG dalam surat_templates_jpn. Pulang (ok, mesej)."""
    import base64, io
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
        im.thumbnail((900, 900))
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        if len(data) > 600_000:
            im.thumbnail((500, 500))
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            data = buf.getvalue()
        uri = "data:image/png;base64," + base64.b64encode(data).decode()
    except Exception as e:
        return False, f"Fail imej tidak sah: {e}"
    try:
        get_supabase().table("surat_templates_jpn").delete().eq("jawatan", ASET_KEYS[kind]).execute()
        get_supabase().table("surat_templates_jpn").insert({"jawatan": ASET_KEYS[kind], "template_html": uri}).execute()
        aset_data_uri.clear()
        return True, ""
    except Exception as e:
        return False, f"Gagal simpan ke Supabase: {str(e)[:200]}"


def aset_delete(kind):
    try:
        get_supabase().table("surat_templates_jpn").delete().eq("jawatan", ASET_KEYS[kind]).execute()
        aset_data_uri.clear()
        return True
    except Exception:
        return False


def _img_uri(kind):
    """Data URI logo/tandatangan: Supabase dahulu, kemudian fail repo. '' jika tiada."""
    import base64, mimetypes
    uri = aset_data_uri(kind)
    if uri:
        return uri
    p = find_asset(LOGO_NAMES if kind == "logo" else SIGN_NAMES)
    if p:
        try:
            with open(p, "rb") as f:
                return f"data:{mimetypes.guess_type(p)[0] or 'image/png'};base64," + base64.b64encode(f.read()).decode()
        except Exception:
            return ""
    return ""


def _perbaiki_img_src(html):
    """Pastikan <img src="..."> dalam templat JPN boleh dibaca: fail relatif tiada -> guna imej Supabase/repo (data URI)."""
    import re as _re2, base64, mimetypes

    def fix(m):
        q, src = m.group(1), m.group(2)
        if src.lower().startswith(("data:", "http://", "https://")):
            return m.group(0)
        base = _os.path.basename(src)
        low = base.lower()
        p = src if _os.path.exists(src) else find_asset([base])
        if p:
            try:
                with open(p, "rb") as f:
                    return f"src={q}data:{mimetypes.guess_type(p)[0] or 'image/png'};base64,{base64.b64encode(f.read()).decode()}{q}"
            except Exception:
                return m.group(0)
        kind = "logo" if any(x in low for x in ("jata", "logo", "lambang")) else ("tandatangan" if any(x in low for x in ("tanda", "sign", "ttd")) else None)
        uri = _img_uri(kind) if kind else ""
        return f"src={q}{uri}{q}" if uri else m.group(0)
    return _re2.sub(r'src\s*=\s*(["\'])([^"\']+)\1', fix, html, flags=_re2.I)


def _on_db_write(table):
    """Selepas sebarang tulisan ke jadual: kosongkan cache bacaan jadual itu supaya paparan (cth Hasil Janaan) terus kemas kini."""
    try:
        if table == "cadangan_sup":
            get_cadangan_df.clear()
        elif table == "pusat_master":
            get_pusat_df.clear()
        elif table == "guru_master":
            get_guru_df.clear()
    except Exception:
        pass


supa.on_write = _on_db_write


def render_footer():
    st.markdown("<div class='app-footer'>Sistem Pelantikan Petugas SPM Selangor 2026 · Jabatan Pendidikan Negeri Selangor</div>", unsafe_allow_html=True)

def apply_global_ui():
    """Panggil SETIAP rerun (CSS mesti dipaparkan semula)."""
    try:
        hide_fork_github()
    except Exception:
        pass
    apply_pretty_theme()
    _apply_jpn_kad_css()
    for _h in _CSS_QUEUE:
        st.markdown(_h, unsafe_allow_html=True)
