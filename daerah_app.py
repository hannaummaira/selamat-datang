# -*- coding: utf-8 -*-
"""
daerah_app.py - Aplikasi SATU DAERAH (SUP + PPD).
Contoh: app_BG.py -> PPD Gombak: hanya membaca data Gombak dari Supabase.
  - SUP  : baca guru_master (sekolah sendiri), tulis cadangan_sup
  - PPD  : baca cadangan_sup (daerah sendiri)
"""
import streamlit as st
import pandas as pd
import spm_core as core
import ui_theme as ui
import auth_db
from program_config import cfg
from spm_core import KOD_DAERAH, PPD_MAP
from ui_theme import esc

PER_PAGE = 30


def master_ok():
    """Kata laluan induk ('a', a-j) dibenarkan kecuali DISABLE_MASTER_PASSWORD = true dalam secrets."""
    return str(core._secret("DISABLE_MASTER_PASSWORD", "")).strip().lower() not in ("1", "true", "yes")


# ------------------------------------------------------------------ data landing
@st.cache_data(ttl=3600, show_spinner=False)
def _id_offset(kod_ppd):
    """Kata laluan SUP = ID berjalan merentas daerah (sama seperti sistem asal).
    Offset = jumlah sekolah daerah-daerah sebelum daerah ini. Hanya KIRAAN (bukan data) dibaca."""
    off = 0
    for k in KOD_DAERAH:
        if k == kod_ppd:
            break
        try:
            r = (core._RAW.table("sekolah_master").select("kod_sekolah", count="exact")
                 .ilike("kod_ppd", k).not_.is_("kod_sekolah", "null").not_.is_("nama_sekolah", "null").limit(1).execute())
            off += int(r.count or 0)
        except Exception:
            pass
    return off


@st.cache_data(ttl=300, show_spinner=False)
def load_sekolah_daerah(kod_ppd):
    res = core.supa.table("sekolah_master").select("*").limit(2000).execute()      # sudah ditapis ikut daerah
    rows = []
    for r in res.data or []:
        kod = str(r.get("kod_sekolah") or r.get("KOD_SEKOLAH") or "").upper().strip()
        nama = str(r.get("nama_sekolah") or r.get("NAMA_SEKOLAH") or "").upper().strip()
        if kod and nama:
            rows.append({"KOD_SEKOLAH": kod, "NAMA_SEKOLAH": nama})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.drop_duplicates("KOD_SEKOLAH").sort_values("NAMA_SEKOLAH", kind="stable").reset_index(drop=True)
    df["ID"] = df.index + 1 + _id_offset(kod_ppd)
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_sekolah_selesai(kod_ppd):
    """Sekolah yang cadangannya sudah dihantar ke PPD (baca cadangan_sup daerah ini sahaja)."""
    done = set()
    try:
        res = core.supa.table("cadangan_sup").select("kod_sekolah,status").limit(10000).execute()
        for r in res.data or []:
            s = str(r.get("status") or "").upper()
            if any(x in s for x in ("HANTAR", "LULUS", "SAH", "JANA", "TEMPAT")):
                ks = str(r.get("kod_sekolah") or "").upper().strip()
                if ks:
                    done.add(ks)
    except Exception:
        pass
    return done


# ------------------------------------------------------------------ dialog log masuk
@st.dialog("🔑 Log Masuk SUP")
def dlg_sup(kod, nama, sid, kod_ppd):
    st.write(f"**{kod}** - {nama}")
    st.caption(f"ID: {sid}")
    pwd = st.text_input("Kata laluan", type="password", key="pwd_sup_dlg")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Masuk", type="primary", use_container_width=True, key="btn_sup_masuk"):
            valid = [str(sid), f"12345{sid}", "12345"] + (["a"] if master_ok() else [])
            legacy = pwd.strip() in valid or (master_ok() and pwd.strip().lower() == "a")
            lulus, sebab = auth_db.verify_login("SUP", kod, pwd.strip(), legacy)
            if lulus:
                info = core.get_sekolah(kod)
                info.update({"kod_sekolah": kod, "nama_sekolah": nama, "kod_ppd": kod_ppd})
                st.session_state.update({"role": "SUP", "kod": kod, "info": info, "sup_id": sid})
                st.rerun()
            else:
                st.error(auth_db.mesej_gagal(sebab))
    with c2:
        if st.button("Batal", use_container_width=True, key="btn_sup_batal"):
            st.rerun()


@st.dialog("🏢 Log Masuk PPD")
def dlg_ppd(kod_ppd):
    ppd_id = KOD_DAERAH.index(kod_ppd) + 1 if kod_ppd in KOD_DAERAH else 1
    st.write(f"**PPD {kod_ppd} - {PPD_MAP.get(kod_ppd, '')}**")
    pwd = st.text_input("Kata laluan PPD", type="password", key="pwd_ppd_dlg")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Masuk PPD", type="primary", use_container_width=True, key="btn_ppd_masuk"):
            valid = [str(ppd_id), f"12345{ppd_id}", kod_ppd.lower()]
            if master_ok():
                valid += [chr(96 + ppd_id), "a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
            legacy = pwd.strip().lower() in [v.lower() for v in valid]
            lulus, sebab = auth_db.verify_login("PPD", kod_ppd, pwd.strip(), legacy)
            if lulus:
                st.session_state.update({"role": "PPD", "kod": kod_ppd, "ppd_id": ppd_id})
                st.rerun()
            else:
                st.error(auth_db.mesej_gagal(sebab, f"Kata laluan PPD {kod_ppd}"))
    with c2:
        if st.button("Batal", use_container_width=True, key="btn_ppd_batal"):
            st.rerun()


# ------------------------------------------------------------------ halaman pilih sekolah (contoh SUP Gombak)
def render_landing(kod_ppd):
    nama_ppd = PPD_MAP.get(kod_ppd, kod_ppd)
    df = load_sekolah_daerah(kod_ppd)
    selesai = load_sekolah_selesai(kod_ppd)
    total = len(df)
    n_ok = int(df["KOD_SEKOLAH"].isin(selesai).sum()) if total else 0
    n_belum = total - n_ok

    if st.session_state.get("portal"):
        if st.button("⬅ Pilih Daerah / JPN Lain", key="back_home"):
            st.session_state.clear()
            st.rerun()
    st.markdown(f"""
    <div class="land-top">
      <div style="display:flex;align-items:center"><span class="logo">PPD</span>
        <div><div class="n">PPD {esc(nama_ppd.upper())}</div><div class="s">KEMENTERIAN PENDIDIKAN MALAYSIA</div></div></div>
      <div class="r">Pelantikan Petugas {esc(cfg()['singkatan'])} Selangor 2026 &nbsp;•&nbsp; JPN Selangor</div>
    </div>
    <div class="land-head">
      <div style="max-width:640px">
        <span class="land-chip"><i></i>Selamat Datang ke PPD {esc(nama_ppd)}</span>
        <div class="land-h1">Pilih Sekolah Anda - <span>SUP</span></div>
        <div class="land-p">PPD {esc(nama_ppd)} {esc(kod_ppd)} - {total} Sekolah • Sila pilih sekolah untuk log masuk sebagai SUP</div>
      </div>
      <div class="land-stats">
        <div class="land-stat"><div class="l">Jumlah</div><div class="v">{total}</div><div class="s">sekolah</div></div>
        <div class="land-stat ok"><div class="l">Selesai</div><div class="v">{n_ok}</div><div class="s">cadangan dihantar</div></div>
        <div class="land-stat warn"><div class="l">Belum</div><div class="v">{n_belum}</div><div class="s">perlu tindakan</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3, 3.2, 1.4], gap="small")
    q = c1.text_input("Cari sekolah", key="land_q", placeholder="Cari nama sekolah atau kod...", label_visibility="collapsed")
    flt = c2.radio("Tapisan", ["Semua", "Belum Lengkap", "Selesai"], horizontal=True, key="land_f", label_visibility="collapsed")
    if c3.button("🏢 Log Masuk PPD", type="primary", use_container_width=True, key="land_ppd"):
        dlg_ppd(kod_ppd)

    if total == 0:
        st.warning(f"Tiada sekolah dijumpai untuk daerah {kod_ppd}. Semak jadual sekolah_master (lajur kod_ppd).")
        return
    view = df
    if q:
        qq = q.upper().strip()
        view = view[view["KOD_SEKOLAH"].str.contains(qq, regex=False) | view["NAMA_SEKOLAH"].str.contains(qq, regex=False)]
    if flt == "Selesai":
        view = view[view["KOD_SEKOLAH"].isin(selesai)]
    elif flt == "Belum Lengkap":
        view = view[~view["KOD_SEKOLAH"].isin(selesai)]

    sig = (q, flt)
    if st.session_state.get("land_sig") != sig:
        st.session_state["land_sig"] = sig
        st.session_state["land_page"] = 1
    pages = max(1, -(-len(view) // PER_PAGE))
    page = min(max(1, st.session_state.get("land_page", 1)), pages)
    st.caption(f"Menunjukkan {len(view)} sekolah" + (f' untuk carian "{q}"' if q else "") + (f" • tapisan {flt}" if flt != "Semua" else "") + f" • halaman {page}/{pages}")

    chunk = view.iloc[(page - 1) * PER_PAGE: page * PER_PAGE]
    cols = st.columns(3, gap="small")
    for i, (_, r) in enumerate(chunk.iterrows()):
        kod, nama, sid = r["KOD_SEKOLAH"], r["NAMA_SEKOLAH"], int(r["ID"])
        ok = kod in selesai
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"""
                <div class="sch-card">
                  <div class="sch-row">
                    <div style="display:flex;align-items:center"><span class="sch-ico">🏫</span>
                      <div><div class="sch-code">{esc(kod)}</div><div class="sch-sub">PPD {esc(nama_ppd)} • {esc(kod_ppd)}</div></div></div>
                    <span class="badge {'ok' if ok else 'warn'}"><i></i>{'Selesai' if ok else 'Belum Lengkap'}</span>
                  </div>
                  <div class="sch-name">{esc(nama)}</div>
                  <div class="sch-meta">📍 Daerah {esc(nama_ppd)} &nbsp;•&nbsp; 👤 ID SUP: {sid}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("Masuk sebagai SUP →", key=f"sup_{kod}", use_container_width=True, type="primary"):
                    dlg_sup(kod, nama, sid, kod_ppd)

    if pages > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        if p1.button("◀ Sebelum", disabled=page <= 1, key="pg_prev", use_container_width=True):
            st.session_state["land_page"] = page - 1
            st.rerun()
        p2.markdown(f"<div style='text-align:center;padding-top:6px;color:#5f708c;font-size:12px'>Halaman {page} / {pages}</div>", unsafe_allow_html=True)
        if p3.button("Seterusnya ▶", disabled=page >= pages, key="pg_next", use_container_width=True):
            st.session_state["land_page"] = page + 1
            st.rerun()
    st.markdown(f'<div class="sup-note" style="margin-top:14px"><b>Maklumat Log Masuk SUP</b><span>Setiap kad dikaitkan dengan kod sekolah. Aplikasi ini hanya membaca data daerah {esc(nama_ppd)} ({esc(kod_ppd)}). Status "Selesai" bermaksud cadangan sekolah telah dihantar ke PPD.</span></div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ runner
def run_daerah(kod_ppd, chrome=True):
    kod_ppd = kod_ppd.upper()
    core.set_scope(kod_ppd)
    if chrome:
        core.apply_global_ui()
        ui.apply_theme()
    role = st.session_state.get("role")
    if role == "PPD" and st.session_state.get("kod") != kod_ppd:
        st.session_state.clear()
        role = None
    if role == "JPN":                       # JPN tidak boleh masuk melalui app daerah
        st.session_state.clear()
        role = None
    if role == "SUP":
        import role_sup
        role_sup.render_sup()
    elif role == "PPD":
        import role_ppd
        role_ppd.render_ppd()
    else:
        render_landing(kod_ppd)
    if chrome:
        core.render_footer()
