# -*- coding: utf-8 -*-
"""
main_app.py - SATU URL untuk JPN + 10 daerah PPD (SUP & PPD).

Halaman utama: pilih JPN atau satu daerah.
  - JPN   : jpn_app.run_jpn()        -> skop semua daerah
  - Daerah: daerah_app.run_daerah()  -> skop daerah itu SAHAJA (SUP baca guru_master, PPD baca cadangan_sup)
Skop daerah disimpan PER SESI (st.session_state) dan semua cache data dikunci dengan skop,
jadi pengguna Klang dan Gombak boleh menggunakan URL yang sama serentak tanpa bercampur data.
"""
import streamlit as st
import spm_core as core
import ui_theme as ui
from spm_core import KOD_DAERAH, PPD_MAP
from ui_theme import esc
from program_config import nama_sistem


def _home():
    core.set_scope(None)
    st.markdown(f"""
    <div class="land-top">
      <div style="display:flex;align-items:center"><span class="logo">JPN</span>
        <div><div class="n">JABATAN PENDIDIKAN NEGERI SELANGOR</div><div class="s">KEMENTERIAN PENDIDIKAN MALAYSIA</div></div></div>
      <div class="r">{esc(nama_sistem())}</div>
    </div>
    <div class="land-head">
      <div style="max-width:700px">
        <span class="land-chip"><i></i>Portal Tunggal</span>
        <div class="land-h1">Pilih Portal <span>Anda</span></div>
        <div class="land-p">Pilih JPN Selangor atau Pejabat Pendidikan Daerah (PPD). Setiap daerah hanya memaparkan data daerahnya sendiri.</div>
      </div>
    </div>""", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("""<div class="sch-card"><div class="sch-row"><div style="display:flex;align-items:center"><span class="sch-ico">🏛️</span>
          <div><div class="sch-code">JPN SELANGOR</div><div class="sch-sub">Pentadbir Negeri</div></div></div>
          <span class="badge ok"><i></i>Semua Daerah</span></div>
          <div class="sch-meta" style="margin-top:8px">Pusat Master • Guru Master • Template Surat • Pantau 10 daerah</div></div>""", unsafe_allow_html=True)
        if st.button("Masuk sebagai JPN →", key="portal_JPN", type="primary", use_container_width=True):
            st.session_state["portal"] = "JPN"
            st.rerun()

    st.markdown("#### Pejabat Pendidikan Daerah (PPD)")
    cols = st.columns(3, gap="small")
    for i, kod in enumerate(KOD_DAERAH):
        nama = PPD_MAP.get(kod, kod)
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"""<div class="sch-card"><div class="sch-row"><div style="display:flex;align-items:center"><span class="sch-ico">🏫</span>
                  <div><div class="sch-code">PPD {esc(nama.upper())}</div><div class="sch-sub">Kod daerah {esc(kod)}</div></div></div></div>
                  <div class="sch-name">{esc(nama)}</div>
                  <div class="sch-meta">SUP (pilih sekolah) • PPD</div></div>""", unsafe_allow_html=True)
                if st.button("Masuk →", key=f"portal_{kod}", use_container_width=True, type="primary"):
                    st.session_state["portal"] = kod
                    st.rerun()


def _portal_from_state():
    """Tentukan portal semasa daripada sesi (juga selamat jika sesi sudah log masuk)."""
    role = st.session_state.get("role")
    if role == "JPN":
        return "JPN"
    if role == "PPD" and st.session_state.get("kod") in KOD_DAERAH:
        return st.session_state["kod"]
    if role == "SUP":
        kp = str((st.session_state.get("info") or {}).get("kod_ppd", "")).upper()
        if kp in KOD_DAERAH:
            return kp
    p = st.session_state.get("portal")
    return p if (p == "JPN" or p in KOD_DAERAH) else None


def run_app():
    core.apply_global_ui()
    ui.apply_theme()
    portal = _portal_from_state()
    if portal:
        st.session_state["portal"] = portal
    if portal == "JPN":
        import jpn_app
        jpn_app.run_jpn(chrome=False)
    elif portal:
        import daerah_app
        daerah_app.run_daerah(portal, chrome=False)
    else:
        _home()
    core.render_footer()
