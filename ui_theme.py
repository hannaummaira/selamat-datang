# -*- coding: utf-8 -*-
"""
ui_theme.py - Susun atur & gaya seragam ikut contoh (Dashboard SUP / Dashboard PPD / Pilih Sekolah SUP).
Digunakan oleh role_sup.py, role_ppd.py, role_jpn.py dan daerah_app.py / jpn_app.py.
"""
import datetime
import html as _html
import json
import streamlit as st
import spm_core as core
from spm_core import PPD_MAP, SCOPE, get_pusat_df

MY_TZ = datetime.timezone(datetime.timedelta(hours=8))


def now_my():
    return datetime.datetime.now(MY_TZ).strftime("%d/%m %H:%M:%S")


def esc(x):
    return _html.escape(str(x if x is not None else ""))


def kc(key):
    """Container ber-key (Streamlit >= 1.39); jatuh ke container biasa pada versi lama."""
    try:
        return st.container(key=key)
    except TypeError:
        return st.container()


THEME_CSS = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display:none!important}
.stApp {background:#e3f2fd!important}
.block-container {max-width:1600px!important;padding-top:.6rem!important;padding-bottom:1rem!important}

/* ---------- kotak & header (contoh Dashboard SUP / PPD) ---------- */
.sup-box {background:#fff;border:1px solid #c5d6e8;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow:hidden;margin-bottom:8px}
.sup-id {font-size:11px;font-weight:700;line-height:1.35;letter-spacing:.03em;color:#0d47a1;text-transform:uppercase}
.sup-pusat {margin-top:8px;background:#e8f0fe;border:1px solid #90caf9;border-radius:4px;padding:8px}
.sup-pusat .l {font-size:10px;font-weight:600;letter-spacing:.1em;color:#0d47a1}
.sup-pusat .v {font-size:13px;font-weight:800;color:#0d47a1;margin-top:2px}
.sup-last {font-size:10px;color:#5f6f85;margin-top:6px}
.sup-red {font-size:9px;line-height:11px;color:#d32f2f;font-weight:500;margin:2px 0 8px}
.sup-banner {background:#0d47a1;color:#fff;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}
.sup-banner .t {font-size:13px;font-weight:700;letter-spacing:.03em}
.sup-pill {display:inline-flex;align-items:center;gap:6px;background:#42a5f5;color:#fff;font-size:10px;font-weight:700;padding:4px 10px;border-radius:999px;letter-spacing:.1em;margin-left:12px}
.sup-pill i {width:6px;height:6px;background:#fff;border-radius:50%;display:inline-block}
.sup-right {font-size:11px;opacity:.8}
.sup-info {background:#fff;padding:8px 16px;display:flex;flex-wrap:wrap;gap:4px 16px;font-size:11px;border-bottom:1px solid #c5d6e8;align-items:center}
.sup-info b {color:#5f6f85;font-weight:700}
.sup-info .sep {color:#90a4b8}
.sup-online {margin-left:auto;display:inline-flex;align-items:center;gap:6px;font-size:10px;font-weight:500;color:#2e7d32;background:#e8f5e9;border:1px solid #a5d6a7;padding:2px 8px;border-radius:999px}
.sup-online i {width:8px;height:8px;background:#43a047;border-radius:50%;display:inline-block}
.sup-note {background:#fff;border:1px solid #c5d6e8;border-radius:4px;padding:10px;font-size:10px;line-height:1.4;margin-top:12px}
.sup-note b {color:#0d47a1;display:block;margin-bottom:4px}
.sup-note span {color:#5f6f85}
.sup-sub-h {background:#0d47a1;color:#fff;font-size:11px;font-weight:700;letter-spacing:.1em;padding:6px 8px;border-radius:4px 4px 0 0}
.sup-card-h {background:#e3f2fd;border-bottom:1px solid #c5d6e8;padding:8px 12px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px}
.sup-card-h .t {font-size:12px;font-weight:800;letter-spacing:.03em;color:#0d47a1}
.sup-chip {font-size:10px;background:#fff;border:1px solid #90caf9;padding:4px 8px;border-radius:4px;font-weight:700;color:#0d47a1}
.sup-tiles {padding:12px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.sup-tile {background:#fff;border:1px solid #c5d6e8;border-radius:4px;padding:12px;text-align:center}
.sup-tile.hl {background:#e3f2fd;border-color:#90caf9}
.sup-tile .l {font-size:11px;font-weight:700;letter-spacing:.1em;color:#5f6f85}
.sup-tile.hl .l {color:#0d47a1}
.sup-tile .n {font-size:28px;font-weight:800;color:#0d47a1;line-height:1;margin-top:4px}
.sup-tile .s {font-size:10px;color:#5f6f85;margin-top:4px}
.sup-tile.hl .s {color:#1565c0;font-weight:500}

/* ---------- kad metrik Streamlit => kad statistik contoh ---------- */
[data-testid="stMetric"] {background:#fff;border:1px solid #c5d6e8;border-radius:4px;padding:10px 12px!important}
[data-testid="stMetricLabel"] p {font-size:11px!important;font-weight:700!important;color:#5f6f85!important;text-transform:none}
[data-testid="stMetricValue"] {font-size:22px!important;font-weight:800!important;color:#0d47a1!important}

/* ---------- menu kiri: biru pekat, aktif = garis kuning ---------- */
.st-key-shellmenu, .st-key-shellsub {gap:4px!important}
.st-key-shellmenu [class*="st-key-flymenu_"] button {width:100%;justify-content:flex-start!important;text-align:left!important;background:#0d47a1!important;color:#fff!important;border:none!important;border-left:3px solid transparent!important;border-radius:0 4px 4px 0!important;padding:8px 12px!important;min-height:0!important;box-shadow:none!important;transform:none!important}
.st-key-shellmenu [class*="st-key-flymenu_"] button * {color:#fff!important;font-size:12px!important;font-weight:600!important;text-align:left!important}
.st-key-shellmenu [class*="st-key-flymenu_"] button:hover {background:#0a367e!important}
.st-key-shellmenu [class*="st-key-flymenu_"] button[kind="primary"],
.st-key-shellmenu [class*="st-key-flymenu_"] [data-testid="stBaseButton-primary"] {border-left:3px solid #ffca28!important;box-shadow:0 2px 8px rgba(13,71,161,.3)!important;background:#0d47a1!important}
.st-key-shellsub {background:#fff;border:1px solid #c5d6e8;border-top:0;border-radius:0 0 4px 4px}
.st-key-shellsub [class*="st-key-flysub_"] button {width:100%;justify-content:flex-start!important;text-align:left!important;background:#1565c0!important;border:none!important;border-radius:0!important;border-bottom:1px solid #0d47a1!important;border-left:3px solid transparent!important;padding:9px 12px!important;min-height:0!important;box-shadow:none!important;transform:none!important}
.st-key-shellsub [class*="st-key-flysub_"] button * {color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-size:12px!important;font-weight:600!important;text-align:left!important}
.st-key-shellsub [class*="st-key-flysub_"] button:hover {background:#0d47a1!important}
.st-key-shellsub [class*="st-key-flysub_"] button[kind="primary"],
.st-key-shellsub [class*="st-key-flysub_"] [data-testid="stBaseButton-primary"] {background:#0a2a66!important;border-left:3px solid #ffca28!important;box-shadow:none!important}
.st-key-shellsub [class*="st-key-flysub_"] button[kind="primary"] *,
.st-key-shellsub [class*="st-key-flysub_"] [data-testid="stBaseButton-primary"] * {color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;font-weight:800!important}
.st-key-suprefresh .stButton>button {width:100%;background:#0d47a1!important;border:none!important;border-radius:4px!important;box-shadow:0 2px 0 #082c62!important;padding:10px 0!important;min-height:0!important}
.st-key-suprefresh .stButton>button * {color:#fff!important;font-size:12px!important;font-weight:800!important;letter-spacing:.03em}

/* ---------- halaman pilih sekolah (contoh SUP Gombak) ---------- */
.land-top {background:#0d47a1;color:#fff;border-radius:6px;padding:10px 18px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
.land-top .logo {width:34px;height:34px;background:#fff;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;color:#0d47a1;font-weight:800;font-size:13px;margin-right:10px}
.land-top .n {font-weight:700;font-size:13px;letter-spacing:.02em}
.land-top .s {font-size:10px;opacity:.8;letter-spacing:.05em}
.land-top .r {font-size:11px;opacity:.9}
.land-head {background:#fff;border:1px solid #dbe3f0;border-radius:14px;padding:22px 24px;margin:12px 0;display:flex;flex-wrap:wrap;gap:18px;justify-content:space-between;align-items:flex-end}
.land-chip {display:inline-flex;align-items:center;gap:8px;padding:4px 12px;border-radius:999px;background:#e3eefe;border:1px solid #b7cdef;font-size:11px;font-weight:600;color:#0d47a1;letter-spacing:.04em;text-transform:uppercase}
.land-chip i {width:6px;height:6px;background:#0d47a1;border-radius:50%;display:inline-block}
.land-h1 {font-size:32px;font-weight:800;letter-spacing:-.02em;line-height:1.05;color:#0d47a1;margin:10px 0 4px}
.land-h1 span {color:#13233f}
.land-p {font-size:14px;color:#5f708c;font-weight:500}
.land-stats {display:grid;grid-template-columns:repeat(3,110px);gap:10px}
.land-stat {border-radius:14px;padding:12px;border:1px solid #dbe3f0;background:#f5f7fb}
.land-stat .l {font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#5f708c}
.land-stat .v {font-size:22px;font-weight:800;color:#13233f;line-height:1;margin-top:4px}
.land-stat .s {font-size:10px;color:#5f708c;margin-top:3px}
.land-stat.ok {background:#dcfce7;border-color:#bbf7d0}.land-stat.ok .l,.land-stat.ok .s{color:#15803d}.land-stat.ok .v{color:#166534}
.land-stat.warn {background:#fef3c7;border-color:#fde68a}.land-stat.warn .l,.land-stat.warn .s{color:#b45309}.land-stat.warn .v{color:#92400e}
.sch-card {padding:2px 2px 0}
.sch-row {display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.sch-ico {width:38px;height:38px;border-radius:10px;background:#e3eefe;display:inline-flex;align-items:center;justify-content:center;font-size:18px;margin-right:10px}
.sch-code {font-size:11px;font-weight:800;color:#0d47a1;letter-spacing:.04em}
.sch-sub {font-size:10px;color:#5f708c}
.sch-name {font-size:15px;font-weight:700;color:#13233f;margin:10px 0 6px;line-height:1.25;min-height:38px}
.sch-meta {font-size:11px;color:#5f708c;margin-bottom:6px}
.badge {display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;border:1px solid}
.badge.ok {background:#dcfce7;border-color:#bbf7d0;color:#166534}
.badge.warn {background:#fef3c7;border-color:#fde68a;color:#92400e}
.badge i {width:6px;height:6px;border-radius:50%;display:inline-block}
.badge.ok i {background:#16a34a}.badge.warn i {background:#d97706}
@media (max-width:900px) {.sup-tiles {grid-template-columns:repeat(2,1fr)} .sup-right {display:none} .land-stats{grid-template-columns:repeat(3,1fr);width:100%}}
</style>
"""


# ======================================================================= KONTRAS TINGGI (tulisan & jadual lebih jelas)
KONTRAS_CSS = """
<style>
/* ---- teks asas: gelap pekat, saiz selesa ---- */
html, body, .stApp, [data-testid="stAppViewContainer"] {color:#0b1b33!important}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] span {color:#0b1b33!important;font-size:15px;line-height:1.5}
h1,h2,h3,h4,h5,h6 {color:#0a2a66!important;font-weight:800!important}
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, label {color:#0b1b33!important;font-weight:700!important;font-size:14px!important}
[data-testid="stCaptionContainer"] p, .stCaption, small {color:#1e293b!important;font-size:13px!important;font-weight:500!important;opacity:1!important}
[data-testid="stMetricLabel"] p {color:#1e293b!important;font-size:12px!important;font-weight:700!important}
[data-testid="stMetricValue"] {color:#0a2a66!important}
[data-baseweb="tab"] {font-weight:700!important;color:#0a2a66!important}
[data-testid="stExpander"] summary p {font-weight:700!important;color:#0a2a66!important}

/* ---- input & pilihan: sempadan jelas ---- */
input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] {color:#0b1b33!important;background:#ffffff!important;border-color:#475569!important}
[data-baseweb="select"] *, [data-baseweb="input"] * {color:#0b1b33!important}
input::placeholder, textarea::placeholder {color:#475569!important;opacity:1!important}
/* ---- BUTANG: latar biru pekat + tulisan PUTIH (menimpa warna teks markdown di dalam butang) ---- */
.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button,
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-primaryFormSubmit"],
button[data-testid="stBaseButton-secondaryFormSubmit"] {background:#0d47a1!important;background-image:none!important;border:2px solid #0a367e!important;color:#ffffff!important;font-weight:700!important}
.stButton > button *,
.stButton > button p,
.stButton > button span,
.stButton > button div,
.stDownloadButton > button *,
.stDownloadButton > button p,
.stDownloadButton > button span,
.stDownloadButton > button div,
[data-testid="stFormSubmitButton"] > button *,
[data-testid="stFormSubmitButton"] > button p,
[data-testid="stFormSubmitButton"] > button span,
[data-testid="stFormSubmitButton"] > button div,
button[data-testid="stBaseButton-primary"] *,
button[data-testid="stBaseButton-primary"] p,
button[data-testid="stBaseButton-primary"] span,
button[data-testid="stBaseButton-primary"] div,
button[data-testid="stBaseButton-secondary"] *,
button[data-testid="stBaseButton-secondary"] p,
button[data-testid="stBaseButton-secondary"] span,
button[data-testid="stBaseButton-secondary"] div,
button[data-testid="stBaseButton-primaryFormSubmit"] *,
button[data-testid="stBaseButton-primaryFormSubmit"] p,
button[data-testid="stBaseButton-primaryFormSubmit"] span,
button[data-testid="stBaseButton-primaryFormSubmit"] div,
button[data-testid="stBaseButton-secondaryFormSubmit"] *,
button[data-testid="stBaseButton-secondaryFormSubmit"] p,
button[data-testid="stBaseButton-secondaryFormSubmit"] span,
button[data-testid="stBaseButton-secondaryFormSubmit"] div {color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;fill:#ffffff!important}
.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
button[data-testid="stBaseButton-secondaryFormSubmit"]:hover {background:#0a367e!important;border-color:#082a66!important}
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {background:#0a2a66!important;border-color:#082050!important}
.stButton > button:disabled,
.stDownloadButton > button:disabled,
button[data-testid="stBaseButton-secondary"]:disabled,
button[data-testid="stBaseButton-primary"]:disabled {background:#64748b!important;border-color:#475569!important;opacity:1!important}

/* ---- jadual: bingkai tebal & bayang supaya jelas dari latar ---- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {border:2px solid #475569!important;border-radius:6px!important;box-shadow:0 2px 6px rgba(15,23,42,.18)!important;background:#ffffff!important}
[data-testid="stMarkdownContainer"] table, [data-testid="stTable"] table {border-collapse:collapse!important;width:100%!important;background:#fff!important;border:2px solid #475569!important}
[data-testid="stMarkdownContainer"] th, [data-testid="stTable"] th {background:#0d47a1!important;color:#ffffff!important;font-size:13px!important;font-weight:800!important;padding:8px 10px!important;border:1px solid #0a367e!important;text-align:left!important}
[data-testid="stMarkdownContainer"] td, [data-testid="stTable"] td {color:#0b1b33!important;font-size:14px!important;padding:7px 10px!important;border:1px solid #64748b!important}
[data-testid="stMarkdownContainer"] tbody tr:nth-child(even) td, [data-testid="stTable"] tbody tr:nth-child(even) td {background:#eaf2ff!important}

/* ---- komponen buatan sendiri (header, kad, menu, senarai nama): lebih gelap & lebih besar ---- */
.sup-id {font-size:12px!important;color:#0a2a66!important}
.sup-last {font-size:12px!important;color:#1e293b!important}
.sup-red {font-size:11px!important;line-height:14px!important;color:#b71c1c!important;font-weight:600!important}
.sup-info {font-size:12.5px!important}
.sup-info b {color:#1e293b!important}
.sup-note {font-size:12px!important;border:1.5px solid #90a4c4!important}
.sup-note span {color:#1e293b!important}
.sup-pusat .l {font-size:11px!important;color:#0a2a66!important}
.sup-right {font-size:12px!important;opacity:1!important}
.sup-sub-h {font-size:12px!important}
.sup-card-h .t {font-size:13px!important}
.sup-chip {font-size:11.5px!important;border-width:1.5px!important}
.sup-tile .l {font-size:12px!important;color:#1e293b!important}
.sup-tile .s {font-size:12px!important;color:#1e293b!important}
.sup-tile .n {color:#0a2a66!important}
.sup-box {border:1.5px solid #90a4c4!important}
.st-key-shellmenu [class*="st-key-flymenu_"] button * {font-size:13px!important}
.st-key-shellsub [class*="st-key-flysub_"] button * {font-size:13px!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important}
.cn-card {border:1.5px solid #90a4c4!important}
.cn-card .l {font-size:11px!important;color:#1e293b!important}
.cn-card .s {font-size:12px!important;color:#1e293b!important}
.cn-card .v {color:#0a2a66!important}
.cn-head {font-size:11.5px!important;color:#0a2a66!important;background:#cfe0f7!important}
.cn-nm {font-size:14px!important;color:#0b1b33!important}
.cn-ic {font-size:12.5px!important;color:#0b1b33!important}
.cn-sm {font-size:13px!important;color:#0b1b33!important}
.cn-legend {font-size:12.5px!important;color:#1e293b!important}
.cn-bar {border:1.5px solid #90a4c4!important}
.cn-bar .k {font-size:11.5px!important;color:#1e293b!important}
.cn-guide {font-size:12.5px!important;color:#0b1b33!important}
.cn-b {font-size:11.5px!important}
.cn-b.ok {color:#14532d!important}
.cn-b.sim {color:#78350f!important}
.land-p, .land-stat .l, .land-stat .s, .sch-sub, .sch-meta {color:#1e293b!important}
.land-p {font-size:15px!important}
.sch-name {font-size:16px!important;color:#0b1b33!important}
.sch-code {font-size:12px!important}
.badge {font-size:12px!important}
</style>
"""


def apply_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    st.markdown(KONTRAS_CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ header
def _refresh_block(role):
    with kc("suprefresh"):
        if st.button("REFRESH - Baca Data Baru", key=f"refresh_{role}", use_container_width=True):
            st.cache_data.clear()
            st.session_state["last_refresh"] = now_my()
            st.rerun()
    st.markdown('<div class="sup-red">Tekan selepas SUP buat pertukaran / cadangan</div>', unsafe_allow_html=True)


def shell_header(role, id_html, banner_title, pill, right_text, info_html):
    last = st.session_state.get("last_refresh") or now_my()
    st.session_state["last_refresh"] = last
    hl, hr = st.columns([1.25, 6.4], gap="small")
    with hl:
        st.markdown(f'<div class="sup-box" style="padding:12px">{id_html}<div class="sup-last">Last: {esc(last)}</div></div>', unsafe_allow_html=True)
        _refresh_block(role)
    with hr:
        st.markdown(f"""
        <div class="sup-box">
          <div class="sup-banner">
            <div style="display:flex;align-items:center;flex-wrap:wrap"><span class="t">{esc(banner_title)}</span><span class="sup-pill"><i></i>{esc(pill)}</span></div>
            <div class="sup-right">{esc(right_text)}</div>
          </div>
          <div class="sup-info">{info_html}<span class="sup-online"><i></i> Online</span></div>
        </div>""", unsafe_allow_html=True)


def _kv(k, v):
    return f'<span><b>{esc(k)}:</b> <b style="color:#1a2332">{esc(v)}</b></span>'


def sup_no_pusat_list(kod):
    """No pusat bagi sekolah ini (baca pusat_master - sudah ditapis ikut daerah)."""
    out = []
    try:
        df = get_pusat_df()
        kod = kod.upper().strip()
        for _, r in df.iterrows():
            d = r.get("data") if isinstance(r.get("data"), dict) else {}
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except Exception:
                    d = {}
            ks_tuan = str(r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or r.get("KOD_SEKOLAH") or d.get("KOD_SEKOLAH") or d.get("KOD SEKOLAH") or "").upper().strip()
            ks_biasa = str(r.get("kod_sekolah") or d.get("KOD_SEKOLAH") or "").upper().strip()
            if ks_tuan == kod or ks_biasa == kod:
                no_p = str(r.get("no_pusat") or r.get("kod_pusat") or r.get("NO_PUSAT") or d.get("NO_PUSAT") or d.get("NO PUSAT") or "").upper().strip()
                if no_p and no_p not in out:
                    out.append(no_p)
    except Exception:
        pass
    return out


def shell_header_sup(kod, info, no_pusat_list):
    nama = info.get("nama_sekolah", "")
    kppd = str(info.get("kod_ppd", "")).upper()
    nppd = PPD_MAP.get(kppd, "")
    pusat = ", ".join(no_pusat_list) if no_pusat_list else "-"
    id_html = (f'<div class="sup-id">SUP {esc(kod)}<br>{esc(nama)}<br>{esc(kppd)} - {esc(nppd)}</div>'
               f'<div class="sup-pusat"><div class="l">NO PUSAT SEKOLAH:</div><div class="v">{esc(pusat)}</div></div>')
    info_html = _kv("Kod Sekolah", kod) + '<span class="sep">|</span>' + _kv("PPD", f"{kppd} - {nppd}") + '<span class="sep">|</span>' + _kv("Nama", nama)
    shell_header("sup", id_html, f"Dashboard SUP - {kod} {nama}", "App Ringan - 1 Sekolah Sahaja",
                 "Sistem Pengurusan Pengawas Peperiksaan | JPN Selangor 2026", info_html)


def shell_header_ppd(kod_ppd):
    nppd = PPD_MAP.get(kod_ppd, "")
    id_html = f'<div class="sup-id">PPD {esc(kod_ppd)}<br>{esc(nppd)}<br>Pejabat Pendidikan Daerah</div>'
    info_html = _kv("Kod PPD", kod_ppd) + '<span class="sep">|</span>' + _kv("Daerah", nppd) + '<span class="sep">|</span>' + _kv("Sumber data", "cadangan_sup (daerah ini sahaja)")
    shell_header("ppd", id_html, f"Dashboard PPD - {kod_ppd} {nppd}", f"App Daerah - {nppd} Sahaja",
                 "Sistem Pengurusan Pengawas Peperiksaan | JPN Selangor 2026", info_html)


def shell_header_jpn():
    id_html = '<div class="sup-id">JPN SELANGOR<br>Pentadbir Sistem<br>Semua Daerah</div>'
    info_html = _kv("Peranan", "JPN") + '<span class="sep">|</span>' + _kv("Skop", "10 daerah PPD")
    shell_header("jpn", id_html, f"Dashboard JPN Selangor - Pelantikan {__import__('program_config').cfg()['singkatan']} 2026", "Pentadbir Negeri",
                 "Sistem Pengurusan Pengawas Peperiksaan | JPN Selangor 2026", info_html)


# ------------------------------------------------------------------ menu kiri | sub menu | kandungan
def shell_layout(skey, items, fly_map, dash_key, prefix):
    """Menu kiri + (sub menu jika ada) + ruang kandungan. Pulang (menu, sub_aktif, col_kandungan)."""
    keys = [k for k, _ in items]
    if st.session_state.get(skey) not in keys:
        st.session_state[skey] = keys[0]
    cur = st.session_state[skey]
    subs = fly_map.get(cur)
    cols = st.columns([1.25, 1.0, 5.4] if subs else [1.25, 6.4], gap="small")
    with cols[0]:
        with kc("shellmenu"):
            for k, label in items:
                if st.button(label, key=f"flymenu_{skey}_{k}", use_container_width=True,
                             type="primary" if k == cur else "secondary"):
                    if k != cur:
                        st.session_state[skey] = k
                        st.rerun()
        st.markdown('<div class="sup-note"><b>NOTA SISTEM</b><span>Paparan ini hanya membaca data skop anda sahaja, jadi lebih ringan dan laju.</span></div>', unsafe_allow_html=True)
    fly_cur = None
    if subs:
        sk = dash_key if (dash_key and cur == "dashboard") else f"{prefix}_{cur}"
        sk_keys = [k for k, _ in subs]
        if st.session_state.get(sk) not in sk_keys:
            st.session_state[sk] = sk_keys[0]
        fly_cur = st.session_state[sk]
        with cols[1]:
            st.markdown('<div class="sup-sub-h">SUB MENU</div>', unsafe_allow_html=True)
            with kc("shellsub"):
                for k, label in subs:
                    if st.button(label, key=f"flysub_{sk}_{k}", use_container_width=True,
                                 type="primary" if k == fly_cur else "secondary"):
                        if k != fly_cur:
                            st.session_state[sk] = k
                            st.rerun()
    return cur, fly_cur, cols[-1]
