# -*- coding: utf-8 -*-
"""
auth_db.py - Kata laluan JPN / PPD / SUP disimpan dalam Supabase (di-hash), bukan dalam kod.

Jadual `kata_laluan` (lihat kata_laluan.sql): peranan ('JPN'|'PPD'|'SUP'), kod ('JPN' | kod PPD cth BG | kod sekolah cth BGS001), hash.
  - Kata laluan TIDAK disimpan sebagai teks biasa: PBKDF2-HMAC-SHA256 (200,000 pusingan) + garam rawak.
  - Jadual hendaklah dilindungi RLS (tiada polisi). Aplikasi (di pelayan Streamlit) membacanya dengan SUPABASE_SERVICE_KEY
    dalam Secrets - kunci ini tidak pernah sampai ke pelayar atau GitHub.
  - Akaun yang ada baris dalam jadual: HANYA kata laluan pangkalan data diterima (kata laluan lama dalam kod / 'a' tidak lagi berfungsi).
  - Akaun tanpa baris: kaedah lama (dalam kod) kekal, kecuali AUTH_DB_ONLY = true dalam Secrets.
  - 5 percubaan salah -> dikunci 5 minit (setiap sesi).
"""
import base64
import hashlib
import hmac
import os
import secrets as _py_secrets
import time
import pandas as pd
import streamlit as st
import spm_core as core

TABLE = "kata_laluan"
ITER = 200_000
MAX_GAGAL = 5
KUNCI_SAAT = 300
PERANAN = ("JPN", "PPD", "SUP")
SQL = """create table if not exists kata_laluan (
  id bigserial primary key,
  peranan text not null check (peranan in ('JPN','PPD','SUP')),
  kod text not null,                    -- 'JPN', kod PPD (cth BG) atau kod sekolah (cth BGS001)
  hash text not null,                   -- pbkdf2_sha256$pusingan$garam$hash
  dikemas timestamptz default now(),
  unique (peranan, kod)
);
-- Lindungi jadual: kunci anon TIDAK boleh baca/tulis. Aplikasi guna SUPABASE_SERVICE_KEY (Secrets).
alter table kata_laluan enable row level security;"""


# ------------------------------------------------------------------ hash
def _b64(b):
    return base64.b64encode(b).decode()


def hash_password(pw, salt=None, iters=ITER):
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(pw).encode("utf-8"), salt, iters)
    return f"pbkdf2_sha256${iters}${_b64(salt)}${_b64(dk)}"


def verify_hash(pw, stored):
    try:
        algo, it, salt, dk = str(stored).split("$")
        if algo != "pbkdf2_sha256":
            return False
        calc = hashlib.pbkdf2_hmac("sha256", str(pw).encode("utf-8"), base64.b64decode(salt), int(it))
        return hmac.compare_digest(calc, base64.b64decode(dk))
    except Exception:
        return False


def kata_laluan_rawak(n=8):
    abjad = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"        # tanpa huruf mengelirukan (0 O 1 l I)
    return "".join(_py_secrets.choice(abjad) for _ in range(n))


# ------------------------------------------------------------------ capaian pangkalan data
@st.cache_resource(show_spinner=False)
def _klien_servis(key):
    from supabase import create_client
    return create_client(core.SUPABASE_URL, key)


def _db():
    """Klien untuk jadual kata laluan: kunci servis (Secrets) jika ada, jika tidak klien biasa."""
    key = str(core._secret("SUPABASE_SERVICE_KEY", "")).strip()
    return _klien_servis(key) if key else core._RAW


def guna_kunci_servis():
    return bool(str(core._secret("SUPABASE_SERVICE_KEY", "")).strip())


def jadual_ada():
    try:
        _db().table(TABLE).select("kod").limit(1).execute()
        return True
    except Exception:
        return False


def ambil(peranan, kod):
    """Baris kata laluan atau None. Pulang (baris|None, jadual_ok)."""
    try:
        res = _db().table(TABLE).select("hash").eq("peranan", peranan).eq("kod", str(kod).upper().strip()).limit(1).execute()
        return ((res.data or [None])[0], True)
    except Exception:
        return None, False


def tetapkan(peranan, kod, pw):
    """Simpan (ganti) kata laluan. Pulang (ok, mesej)."""
    kod = str(kod).upper().strip()
    if len(str(pw)) < 8:
        return False, "Kata laluan sekurang-kurangnya 8 aksara."
    try:
        h = hash_password(pw)
        db = _db()
        db.table(TABLE).delete().eq("peranan", peranan).eq("kod", kod).execute()
        db.table(TABLE).insert({"peranan": peranan, "kod": kod, "hash": h}).execute()
        return True, ""
    except Exception as e:
        return False, f"Gagal simpan: {str(e)[:160]}"


def tetapkan_pukal(peranan, pasangan):
    """pasangan = [(kod, pw)]. Pulang (bil_ok, ralat)."""
    ok, err = 0, []
    try:
        db = _db()
        kods = [str(k).upper().strip() for k, _ in pasangan]
        for i in range(0, len(kods), 100):
            db.table(TABLE).delete().eq("peranan", peranan).in_("kod", kods[i:i + 100]).execute()
        rows = [{"peranan": peranan, "kod": str(k).upper().strip(), "hash": hash_password(p)} for k, p in pasangan]
        for i in range(0, len(rows), 100):
            db.table(TABLE).insert(rows[i:i + 100]).execute()
            ok += len(rows[i:i + 100])
    except Exception as e:
        err.append(str(e)[:160])
    return ok, err


def padam(peranan, kod):
    try:
        _db().table(TABLE).delete().eq("peranan", peranan).eq("kod", str(kod).upper().strip()).execute()
        return True
    except Exception:
        return False


def bilangan():
    out = {p: 0 for p in PERANAN}
    try:
        res = _db().table(TABLE).select("peranan").limit(5000).execute()
        for r in res.data or []:
            out[r.get("peranan")] = out.get(r.get("peranan"), 0) + 1
    except Exception:
        pass
    return out


# ------------------------------------------------------------------ log masuk
def _db_sahaja():
    return str(core._secret("AUTH_DB_ONLY", "")).strip().lower() in ("1", "true", "yes")


def baki_kunci():
    return max(0, int(st.session_state.get("_auth_kunci", 0) - time.time()))


def verify_login(peranan, kod, pw, fallback_ok):
    """Semak log masuk. fallback_ok = hasil semakan kaedah lama (dalam kod) - dipakai HANYA jika akaun tiada baris dalam DB.
    Pulang (ok, sebab) - sebab: 'db' | 'lama' | 'salah' | 'kunci' | 'tiada_db'."""
    if baki_kunci() > 0:
        return False, "kunci"
    pw = str(pw or "")
    row, jadual_ok = ambil(peranan, kod)
    if row:
        ok, sebab = verify_hash(pw, row.get("hash")), "db"
    elif _db_sahaja() and jadual_ok:
        ok, sebab = False, "tiada_db"
    else:
        ok, sebab = bool(fallback_ok), "lama"
    if ok:
        st.session_state["_auth_gagal"] = 0
        return True, sebab
    n = int(st.session_state.get("_auth_gagal", 0)) + 1
    st.session_state["_auth_gagal"] = n
    if n >= MAX_GAGAL:
        st.session_state["_auth_kunci"] = time.time() + KUNCI_SAAT
        st.session_state["_auth_gagal"] = 0
    return False, "salah"


def mesej_gagal(sebab, nama="Kata laluan"):
    if sebab == "kunci":
        return f"Terlalu banyak percubaan salah. Cuba lagi dalam {max(1, baki_kunci() // 60 + 1)} minit."
    if sebab == "tiada_db":
        return "Akaun ini belum ditetapkan kata laluannya. Hubungi JPN/PPD."
    return f"{nama} salah."


# ------------------------------------------------------------------ UI JPN: urus kata laluan
def render_urus_kata_laluan():
    import ppd_cadangan as pc
    from spm_core import KOD_DAERAH, PPD_MAP
    pc._banner("🔑 Urus Kata Laluan (JPN / PPD / SUP)",
               "Kata laluan disimpan di Supabase dalam bentuk hash (tidak boleh dibaca semula). Akaun yang ditetapkan di sini tidak lagi menerima kata laluan lama dalam kod.")
    pc._flash()
    ada = jadual_ada()
    if not ada:
        st.error("Jadual `kata_laluan` belum wujud (atau kunci Supabase tiada akses). Jalankan SQL di bawah sekali di Supabase > SQL Editor.")
        st.code(SQL, language="sql")
        return
    if not guna_kunci_servis():
        st.warning("⚠️ `SUPABASE_SERVICE_KEY` belum ditetapkan dalam Secrets. Tanpa kunci servis, jadual hanya selamat jika RLS dimatikan - "
                   "iaitu sesiapa yang ada kunci anon boleh membaca hash. Disyorkan: tetapkan kunci servis dan biarkan RLS dihidupkan.")
    cn = bilangan()
    a, b, c = st.columns(3)
    a.metric("JPN", cn.get("JPN", 0))
    b.metric("PPD (10)", cn.get("PPD", 0))
    c.metric("SUP (sekolah)", cn.get("SUP", 0))

    st.markdown("#### 1. Tetapkan satu kata laluan")
    per = st.radio("Peranan", list(PERANAN), horizontal=True, key="auth_per")
    kod = "JPN"
    if per == "PPD":
        kod = st.selectbox("Daerah PPD", list(KOD_DAERAH), key="auth_ppd", format_func=lambda k: f"{k} - {PPD_MAP.get(k, '')}")
    elif per == "SUP":
        dae = st.selectbox("Daerah", list(KOD_DAERAH), key="auth_dae", format_func=lambda k: f"{k} - {PPD_MAP.get(k, '')}")
        sek = _sekolah_daerah(dae)
        kod = st.selectbox("Sekolah", [s["kod"] for s in sek], key="auth_sek", format_func=lambda k: f"{k} - " + next((s["nama"] for s in sek if s["kod"] == k), ""))
    ada_row, _ = ambil(per, kod) if kod else (None, True)
    st.caption("Status: " + ("✅ sudah ada kata laluan dalam pangkalan data" if ada_row else "⚪ belum ada (guna kaedah lama dalam kod)"))
    pw = st.text_input("Kata laluan baharu (min 8 aksara)", type="password", key="auth_pw")
    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("💾 Simpan", type="primary", key="auth_simpan", disabled=not kod, use_container_width=True):
        ok, msg = tetapkan(per, kod, pw)
        if ok:
            st.session_state["cad_flash"] = f"✅ Kata laluan {per} {kod} disimpan."
            st.rerun()
        else:
            st.error(msg)
    if c2.button("🎲 Jana rawak", key="auth_rawak", disabled=not kod, use_container_width=True):
        baru = kata_laluan_rawak()
        ok, msg = tetapkan(per, kod, baru)
        if ok:
            st.success(f"Kata laluan baharu {per} {kod}: **{baru}** (catat sekarang - tidak akan dipaparkan lagi)")
        else:
            st.error(msg)
    if c3.button("🗑️ Padam dari DB", key="auth_padam", disabled=not (kod and ada_row), use_container_width=True):
        padam(per, kod)
        st.session_state["cad_flash"] = f"Kata laluan {per} {kod} dipadam dari pangkalan data (kembali ke kaedah lama)."
        st.rerun()

    st.markdown("#### 2. Jana kata laluan pukal (rawak)")
    skop = st.radio("Untuk", ["PPD", "SUP"], horizontal=True, key="auth_pukal_per", format_func=lambda k: "Semua PPD (10 daerah)" if k == "PPD" else "Semua sekolah (SUP) dalam satu daerah")
    dae2 = None
    if skop == "SUP":
        dae2 = st.selectbox("Daerah", list(KOD_DAERAH), key="auth_pukal_dae", format_func=lambda k: f"{k} - {PPD_MAP.get(k, '')}")
    if st.button("🎲 Jana & simpan kata laluan pukal", key="auth_pukal_btn", use_container_width=True):
        if skop == "PPD":
            sen = [(k, PPD_MAP.get(k, "")) for k in KOD_DAERAH]
        else:
            sen = [(s["kod"], s["nama"]) for s in _sekolah_daerah(dae2)]
        pasang = [(k, kata_laluan_rawak()) for k, _ in sen]
        ok, err = tetapkan_pukal(skop, pasang)
        if err:
            st.error("Gagal: " + " | ".join(err))
        else:
            nama = dict(sen)
            st.session_state["_auth_pukal_hasil"] = pd.DataFrame([{"PERANAN": skop, "KOD": k, "NAMA": nama.get(k, ""), "KATA LALUAN": p} for k, p in pasang])
            st.success(f"✅ {ok} kata laluan dijana dan disimpan (hash).")
    hasil = st.session_state.get("_auth_pukal_hasil")
    if hasil is not None and len(hasil):
        st.warning("Kata laluan di bawah dipaparkan SEKALI SAHAJA. Muat turun dan edarkan dengan selamat; ia tidak boleh dibaca semula dari pangkalan data.")
        st.dataframe(hasil, use_container_width=True, hide_index=True)
        st.download_button("📥 Muat turun CSV", hasil.to_csv(index=False).encode("utf-8-sig"), file_name="kata_laluan_baharu.csv", mime="text/csv", key="auth_csv")
        if st.button("Sembunyikan jadual", key="auth_sembunyi"):
            st.session_state.pop("_auth_pukal_hasil", None)
            st.rerun()


def _sekolah_daerah(dae):
    out = []
    try:
        res = core.supa.table("sekolah_master").select("kod_sekolah,nama_sekolah,kod_ppd").ilike("kod_ppd", dae).limit(2000).execute()
        for r in res.data or []:
            k = str(r.get("kod_sekolah") or "").upper().strip()
            if k:
                out.append({"kod": k, "nama": str(r.get("nama_sekolah") or "").upper().strip()})
    except Exception:
        pass
    return sorted(out, key=lambda x: x["nama"])
