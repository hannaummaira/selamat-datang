# -*- coding: utf-8 -*-
"""
surat_tools.py - Alat surat untuk SUP / PPD / JPN.

  surat_panel(role, ...)      : Semakan Sistem Surat + Padam Surat Janaan (letak di atas menu surat)
  surat_diagnostik(role)      : enjin PDF, templat JPN, logo/tandatangan, ralat terakhir, uji jana 1 surat
  surat_aset_panel()          : (JPN) muat naik logo & tandatangan terus ke Supabase (tiada fail repo diperlukan)
  render_padam_surat(...)     : padam no surat + status surat supaya surat boleh dijana semula (untuk ujian perubahan)
"""
import datetime
import importlib
import pandas as pd
import streamlit as st
import spm_core as core
import ppd_cadangan as pc
from spm_core import supa, get_cadangan_df, PPD_MAP, KOD_DAERAH


# ------------------------------------------------------------------ semakan sistem surat
def _lib(name):
    try:
        m = importlib.import_module(name)
        return True, getattr(m, "__version__", "")
    except Exception as e:
        return False, str(e)[:80]


def uji_surat(jawatan="PENGAWAS PEPERIKSAAN"):
    """Jana 1 surat contoh. Pulang (pdf_bytes|None, mod) - mod: 'Templat JPN' / 'Susun atur asas (ReportLab)' / 'Gagal'."""
    args = ("NAMA GURU CONTOH", "800101015555", jawatan, "BA0001", "SEKOLAH ASAL CONTOH", "BA142", "SEKOLAH PUSAT CONTOH",
            "JPNS.SPP 600-7/17/5 Jld.2 (01)", "BA", "Klang", datetime.date.today().strftime("%d %B %Y"))
    try:
        html = core.render_jpn_template_html(jawatan, *[args[0], args[1], args[3], args[4], args[5], args[6], args[7], args[8], args[9], args[10]])
    except Exception:
        html = None
    if html:
        pdf = core.html_to_pdf_bytes(html)
        if pdf:
            return pdf, "Templat JPN"
    pdf = core.generate_surat_pdf_bytes_FIXED(*args)
    return (pdf, "Susun atur asas (ReportLab)") if pdf else (None, "Gagal")


def surat_diagnostik(role="PPD"):
    logo = core.find_asset(core.LOGO_NAMES)
    sign = core.find_asset(core.SIGN_NAMES)
    logo_src = "Supabase" if core.aset_bytes("logo") else ("fail repo" if logo else "")
    sign_src = "Supabase" if core.aset_bytes("tandatangan") else ("fail repo" if sign else "")
    libs = {n: _lib(n) for n in ("xhtml2pdf", "reportlab", "pypdf", "PIL")}
    try:
        templates = core.get_jpn_templates_one() or {}
    except Exception:
        templates = {}
    good_t = {k for k, v in templates.items() if v and len(v) > 30}
    masalah = []
    if not libs["xhtml2pdf"][0]:
        masalah.append("xhtml2pdf tiada: templat JPN TIDAK boleh digunakan, surat guna susun atur asas.")
    if not libs["pypdf"][0]:
        masalah.append("pypdf tiada: PDF kolektif guna susun atur ringkas (bukan format surat sebenar).")
    if not good_t:
        masalah.append("Tiada templat JPN dalam Supabase (surat_templates_jpn): surat guna susun atur asas. JPN perlu cipta templat di menu Template Surat.")
    if not logo_src:
        masalah.append("Logo belum ada. JPN boleh muat naik di menu Template Surat > Logo & Tandatangan.")
    if not sign_src:
        masalah.append("Tandatangan belum ada. JPN boleh muat naik di menu Template Surat > Logo & Tandatangan.")
    err = st.session_state.get("_surat_err")
    with st.expander(("⚠️ " if masalah or err else "✅ ") + "Semakan Sistem Surat", expanded=bool(masalah) and role != "SUP"):
        rows = [
            {"SEMAKAN": "Enjin templat JPN (xhtml2pdf)", "STATUS": "✅ ada" if libs["xhtml2pdf"][0] else "❌ tiada"},
            {"SEMAKAN": "Enjin susun atur asas (ReportLab)", "STATUS": "✅ ada" if libs["reportlab"][0] else "❌ tiada"},
            {"SEMAKAN": "Gabung PDF kolektif (pypdf)", "STATUS": "✅ ada" if libs["pypdf"][0] else "❌ tiada"},
            {"SEMAKAN": "Templat JPN dalam Supabase", "STATUS": f"✅ {len(good_t)} jawatan" if good_t else "⚠️ tiada"},
            {"SEMAKAN": "Logo Jata Negara", "STATUS": f"✅ {logo_src}" if logo_src else "❌ tiada"},
            {"SEMAKAN": "Tandatangan Pengarah", "STATUS": f"✅ {sign_src}" if sign_src else "❌ tiada"},
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        for m in masalah:
            st.warning(m)
        if good_t:
            st.caption("Templat tersedia untuk: " + ", ".join(sorted(good_t)))
        if err:
            st.error(f"Ralat terakhir: {err}")
        if st.button("🧪 Uji jana 1 surat contoh", key=f"uji_surat_{role}"):
            pdf, mod = uji_surat()
            st.session_state["_uji_surat"] = (pdf, mod)
        res = st.session_state.get("_uji_surat")
        if res:
            pdf, mod = res
            if pdf:
                st.success(f"✅ Surat contoh berjaya dijana guna: {mod}")
                st.download_button("📥 Muat turun surat contoh (PDF)", data=pdf, file_name="surat_contoh.pdf", mime="application/pdf", key=f"dl_uji_{role}")
            else:
                st.error("❌ Surat contoh gagal dijana. Lihat 'Ralat terakhir' di atas.")


# ------------------------------------------------------------------ muat naik logo & tandatangan (JPN)
def surat_aset_panel():
    logo_ok = bool(core.find_asset(core.LOGO_NAMES))
    sign_ok = bool(core.find_asset(core.SIGN_NAMES))
    with st.expander("🖼️ Logo & Tandatangan Surat", expanded=not (logo_ok and sign_ok)):
        st.caption("Imej disimpan dalam Supabase (jadual surat_templates_jpn) dan digunakan oleh semua surat. Tiada fail repo diperlukan. "
                   "Dalam templat HTML, guna {{LOGO}} dan {{TANDATANGAN}} (atau <img src=\"jata_negara_hd.png\"> - akan diganti automatik).")
        c1, c2 = st.columns(2)
        for col, kind, label, names in ((c1, "logo", "Logo Jata Negara", core.LOGO_NAMES), (c2, "tandatangan", "Tandatangan Pengarah", core.SIGN_NAMES)):
            with col:
                st.markdown(f"**{label}**")
                cur = core.aset_bytes(kind)
                fil = core.find_asset(names)
                if cur:
                    st.image(cur, width=130)
                    st.caption("✅ Disimpan dalam sistem (Supabase)")
                elif fil:
                    st.image(fil, width=130)
                    st.caption("ℹ️ Daripada fail repo")
                else:
                    st.warning("Belum ada imej")
                up = st.file_uploader(f"Muat naik {label} (PNG/JPG)", type=["png", "jpg", "jpeg"], key=f"aset_up_{kind}")
                if up is not None and st.button(f"💾 Simpan {label}", key=f"aset_sv_{kind}", type="primary"):
                    ok, msg = core.aset_save(kind, up.getvalue())
                    if ok:
                        st.session_state["cad_flash"] = f"✅ {label} disimpan."
                        st.rerun()
                    else:
                        st.error(msg)
                if cur and st.button(f"🗑️ Buang {label}", key=f"aset_rm_{kind}"):
                    core.aset_delete(kind)
                    st.rerun()


# ------------------------------------------------------------------ padam surat janaan
def _padam_dibenarkan():
    return str(core._secret("DISABLE_PADAM_SURAT", "")).strip().lower() not in ("1", "true", "yes")


def _surat_rows(df):
    rows = []
    if df is None or df.empty:
        return rows
    for _, r in df.iterrows():
        rid = r.get("id")
        if rid is None or str(rid).strip().lower() in ("", "nan", "none"):
            continue
        ns = pc._pick(r, "no_surat", "NO_SURAT")
        stt = pc._pick(r, "STATUS", "status").upper()
        ada = (ns != "") or ("SURAT" in stt)
        if not ada:
            continue
        rows.append({"id": rid, "ic": pc._pick(r, "IC_GURU", "ic_guru"), "nama": pc._pick(r, "NAMA_GURU", "nama_guru"),
                     "asal": pc._pick(r, "KOD_SEKOLAH_ASAL", "kod_sekolah_asal", "KOD_SEKOLAH", "kod_sekolah").upper(),
                     "pusat": pc._pick(r, "KOD_PUSAT", "kod_pusat").upper(), "no_surat": ns, "status": stt,
                     "kod_ppd": pc._pick(r, "KOD_PPD", "kod_ppd").upper()})
    return rows


def _status_balik(r):
    """Status selepas surat dipadam: penempatan kekal."""
    if "PK" in r["status"].split() or "PENYELIA" in r["status"]:
        return "DITEMPATKAN BILIK KEBAL"
    return "DILANTIK PPD" if r["pusat"] else "TERPILIH PPD"


def padam_surat(rows):
    """Kosongkan no_surat & status surat. Pusat tugas (kod_pusat) TIDAK dipadam. Pulang (bilangan_ok, ralat)."""
    groups = {}
    for r in rows:
        groups.setdefault(_status_balik(r), []).append(r["id"])
    ok, err = 0, []
    for stt, ids in groups.items():
        ids = [pc._pyid(x) for x in ids]
        for i in range(0, len(ids), 100):
            b = ids[i:i + 100]
            last = ""
            for payload in ({"status": stt, "no_surat": None, "tarikh_jana_surat": None, "sekolah_asal_hantar": None},
                            {"status": stt, "no_surat": None}):
                try:
                    supa.table("cadangan_sup").update(payload).in_("id", b).execute()
                    ok += len(b)
                    break
                except Exception as e:
                    last = str(e)[:140]
            else:
                err.append(last)
    try:                                              # jadual log (pilihan)
        ics = [r["ic"] for r in rows if r["ic"]]
        for i in range(0, len(ics), 100):
            supa.table("surat_hantar_sekolah_asal").delete().in_("ic_guru", ics[i:i + 100]).execute()
    except Exception:
        pass
    for k in [k for k in list(st.session_state.keys()) if str(k).startswith(("pdf_", "zip_", "surat_list_", "_uji_surat"))]:
        try:
            del st.session_state[k]
        except Exception:
            pass
    try:
        get_cadangan_df.clear()
    except Exception:
        pass
    return ok, err


def render_padam_surat(role, kod_ppd=None, kod_sekolah=None):
    if not _padam_dibenarkan():
        return
    with st.expander("🗑️ Padam Surat Janaan (untuk ujian perubahan)"):
        st.caption("Memadam no surat dan status surat supaya surat boleh dijana semula. Penempatan pusat tugas TIDAK dipadam.")
        if role == "SUP":
            df = get_cadangan_df(kod_sekolah=kod_sekolah)
            tajuk = f"sekolah {kod_sekolah}"
        elif role == "PPD":
            df = get_cadangan_df(kod_ppd=kod_ppd)
            tajuk = f"PPD {kod_ppd}"
        else:
            dae = st.selectbox("Daerah", ["SEMUA"] + list(KOD_DAERAH), key="padam_dae",
                               format_func=lambda k: "Semua daerah" if k == "SEMUA" else f"{k} - {PPD_MAP.get(k, '')}")
            df = get_cadangan_df(kod_ppd=None if dae == "SEMUA" else dae)
            tajuk = "semua daerah" if dae == "SEMUA" else f"PPD {dae}"
        rows = _surat_rows(df)
        st.metric(f"Surat janaan ({tajuk})", len(rows))
        if not rows:
            st.info("Tiada surat janaan untuk dipadam.")
            return
        sel = rows
        if role != "SUP":
            skop = st.radio("Skop padam", ["semua", "pusat", "sekolah"], horizontal=True, key=f"padam_skop_{role}",
                            format_func=lambda k: {"semua": "Semua surat", "pusat": "Ikut pusat tugas", "sekolah": "Ikut sekolah asal"}[k])
            if skop in ("pusat", "sekolah"):
                key = "pusat" if skop == "pusat" else "asal"
                vals = sorted({r[key] for r in rows if r[key]})
                pilih = st.selectbox("Pilih", vals, key=f"padam_pilih_{role}_{skop}",
                                     format_func=lambda v: f"{v} ({sum(1 for r in rows if r[key] == v)} surat)")
                sel = [r for r in rows if r[key] == pilih]
        st.dataframe(pd.DataFrame([{"NAMA": r["nama"], "IC": r["ic"], "SEKOLAH ASAL": r["asal"], "PUSAT": r["pusat"],
                                    "NO SURAT": r["no_surat"], "STATUS": r["status"]} for r in sel[:20]]), use_container_width=True, hide_index=True)
        if len(sel) > 20:
            st.caption(f"... dan {len(sel) - 20} lagi")
        yakin = st.checkbox(f"Saya faham: {len(sel)} surat akan dipadam (no surat & status dikosongkan).", key=f"padam_yakin_{role}")
        if st.button(f"🗑️ Padam {len(sel)} Surat Janaan", type="primary", disabled=not yakin or not sel, key=f"padam_btn_{role}", use_container_width=True):
            ok, err = padam_surat(sel)
            if err:
                st.error("Sebahagian gagal dipadam: " + " | ".join(err[:2]))
            else:
                st.session_state["cad_flash"] = f"✅ {ok} surat janaan dipadam. Surat boleh dijana semula."
                st.rerun()


# ------------------------------------------------------------------ panel gabungan
def surat_panel(role, kod_ppd=None, kod_sekolah=None):
    pc._flash()
    surat_diagnostik(role)
    render_padam_surat(role, kod_ppd=kod_ppd, kod_sekolah=kod_sekolah)
