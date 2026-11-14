# -*- coding: utf-8 -*-
"""
ppd_zon.py - Menu PPD "Penempatan Zon" (zon bilik kebal).

Peraturan:
  1. PPD tetapkan sekolah-sekolah di bawah setiap bilik kebal (= zon).
  2. Hanya guru dari sekolah dalam zon boleh ditempatkan; hanya di pusat yang bertapak di sekolah dalam zon yang sama.
  3. Guru TIDAK boleh ditempatkan di sekolah asalnya sendiri.
  4. Pusingan: calon diagih bergilir antara sekolah asal (round-robin) dan dihantar ke pusat zon yang paling kurang diisi.
  5. Peraturan sedia ada dikekalkan: ikut keperluan petugas pusat, 1 KP + 1 TKP setiap pusat, maksimum 3 guru sekolah yang sama setiap pusat.

Zon disimpan dalam jadual Supabase `zon_bilik_kebal` (lihat ZON_SQL). Jika jadual belum wujud, zon disimpan sementara dalam sesi.
Penempatan disimpan seperti Jana sedia ada: cadangan_sup.kod_pusat = no pusat, status = "DILANTIK PPD".
"""
import json
import re
import pandas as pd
import streamlit as st
import spm_core as core
from spm_core import get_cadangan_df, get_pusat_df, supa
import ppd_cadangan as pc
from ui_theme import esc

ZON_TABLE = "zon_bilik_kebal"
MAX_SEK_SAMA = 3
ZON_SQL = """create table if not exists zon_bilik_kebal (
  id bigserial primary key,
  kod_ppd text not null,
  kod_bilik_kebal text not null,
  kod_sekolah text not null unique,   -- satu sekolah hanya dalam satu zon
  created_at timestamptz default now()
);
alter table zon_bilik_kebal disable row level security;"""


# ------------------------------------------------------------------ jawatan
def _perlu_manual(d, jk, core):
    """PERLU manual yang diedit PPD di Dashboard (data["PERLU_PPD"]); jika tiada guna KELAS + 9."""
    try:
        ov = d.get("PERLU_PPD") if isinstance(d, dict) else None
        if ov is not None and int(float(str(ov))) >= 0:
            return int(float(str(ov)))
    except Exception:
        pass
    return core.kira_petugas_dari_kelas(jk)


def kelas_jawatan(j):
    """KP / TKP / PENGAWAS (jawatan auto). Jawatan khas & penyelia = None (kekal penempatan manual)."""
    j = str(j or "").upper()
    if any(x in j for x in ("HOSPITAL", "PENGIRING", "JURU", "PENGEMAS", "PENYELIA", "SELENGGARA", "KHAS")):
        return None
    if "TIMBALAN" in j and "KETUA" in j:
        return "TKP"
    if "KETUA PENGAWAS" in j:
        return "KP"
    if j.startswith("PENGAWAS"):
        return "PENGAWAS"
    return None


def _dist(pk_a, pk_b):
    try:
        a = int(re.sub(r"\D", "", str(pk_a))[:5] or 0)
        b = int(re.sub(r"\D", "", str(pk_b))[:5] or 0)
        return 99999 if a == 0 or b == 0 else abs(a - b)
    except Exception:
        return 99999


# ------------------------------------------------------------------ penyimpanan zon
def _fb():
    return st.session_state.setdefault("zon_fb", {})


def zon_db_ok():
    try:
        supa.table(ZON_TABLE).select("kod_sekolah").limit(1).execute()
        return True
    except Exception:
        return False


def zon_load(db_ok):
    """{kod_bilik_kebal: [kod_sekolah, ...]}"""
    if db_ok:
        try:
            res = supa.table(ZON_TABLE).select("kod_bilik_kebal,kod_sekolah").limit(5000).execute()
            out = {}
            for r in res.data or []:
                bk = str(r.get("kod_bilik_kebal") or "").upper().strip()
                ks = str(r.get("kod_sekolah") or "").upper().strip()
                if bk and ks:
                    out.setdefault(bk, []).append(ks)
            return out
        except Exception:
            pass
    return {k: list(v) for k, v in _fb().items()}


def zon_save(kod_ppd, bk, schools, db_ok):
    schools = sorted({str(s).upper().strip() for s in schools if s})
    if db_ok:
        try:
            supa.table(ZON_TABLE).delete().eq("kod_ppd", kod_ppd).eq("kod_bilik_kebal", bk).execute()
            if schools:
                supa.table(ZON_TABLE).insert([{"kod_ppd": kod_ppd, "kod_bilik_kebal": bk, "kod_sekolah": s} for s in schools]).execute()
            return True, ""
        except Exception as e:
            return False, str(e)[:200]
    _fb()[bk] = schools
    return True, "sesi"


# ------------------------------------------------------------------ data
@st.cache_data(ttl=300, show_spinner=False)
def load_bilik_kebal(kod_ppd):
    out = []
    try:
        res = supa.table("bilik_kebal_master").select("*").limit(2000).execute()
        for r in res.data or []:
            k = str(r.get("kod_bilik_kebal") or r.get("KOD_BILIK_KEBAL") or "").upper().strip()
            if k:
                out.append({"kod": k, "nama": str(r.get("nama_bilik_kebal") or r.get("NAMA_BILIK_KEBAL") or "").strip()})
    except Exception:
        pass
    return sorted(out, key=lambda x: x["kod"])


@st.cache_data(ttl=600, show_spinner=False)
def sekolah_poskod(kod_ppd):
    out = {}
    try:
        res = supa.table("sekolah_master").select("*").limit(2000).execute()
        for r in res.data or []:
            d = r.get("data") or {}
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except Exception:
                    d = {}
            k = str(r.get("kod_sekolah") or "").upper().strip()
            pk = str(r.get("poskod") or (d.get("POSKOD") if isinstance(d, dict) else "") or "").strip()
            if k:
                out[k] = pk
    except Exception:
        pass
    return out


def load_pusat(kod_ppd):
    """{no_pusat: {NO, NAMA, KOD_TUAN, KELAS, CALON, PETUGAS, POSKOD}} - pusat daerah ini."""
    out = {}
    df = get_pusat_df()
    if df is None or df.empty:
        return out
    spk = sekolah_poskod(kod_ppd)
    for _, r in df.iterrows():
        d = r.get("data")
        if isinstance(d, str):
            try:
                d = json.loads(d)
            except Exception:
                d = {}
        if not isinstance(d, dict):
            d = {}
        no = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or d.get("NO PUSAT") or "").upper().strip()
        if not no or not no.startswith(str(kod_ppd).upper()):
            continue
        tuan = str(r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or d.get("KOD_SEKOLAH") or d.get("KOD SEKOLAH") or "").upper().strip()
        try:
            jc = int(float(str(r.get("jumlah_calon") or d.get("JUMLAH_CALON") or 0)))
        except Exception:
            jc = 0
        try:
            jk = int(float(str(r.get("jumlah_kelas") or d.get("JUMLAH_KELAS") or 0)))
        except Exception:
            jk = 0
        if jk == 0:
            jk = core.kira_kelas_dari_calon(jc)
        pk = str(r.get("poskod") or d.get("POSKOD") or d.get("POSKOD_PUSAT") or "").strip() or spk.get(tuan, "")
        out[no] = {"NO": no, "NAMA": str(r.get("nama_pusat") or d.get("NAMA_PUSAT") or "").strip(), "KOD_TUAN": tuan,
                   "KELAS": jk, "CALON": jc, "PETUGAS": _perlu_manual(d, jk, core), "POSKOD": pk}
    return out


def load_calon(kod_ppd, inc_unrev=False):
    """Pulang (layak, placed): layak = senarai dict calon belum ditempatkan; placed = {no_pusat: {total, KP, TKP, asal}}."""
    df = pc.normalize(get_cadangan_df(kod_ppd=kod_ppd))
    layak, placed = [], {}
    for _, r in df.iterrows():
        kelas = kelas_jawatan(r["JAWATAN"])
        if r["KOD_PUSAT"]:
            p = placed.setdefault(r["KOD_PUSAT"], {"total": 0, "KP": 0, "TKP": 0, "asal": {}})
            p["total"] += 1
            if kelas in ("KP", "TKP"):
                p[kelas] += 1
            p["asal"][r["KOD_SEK"]] = p["asal"].get(r["KOD_SEK"], 0) + 1
            continue
        if kelas is None:
            continue
        if r["STAGE"] == "TERPILIH" or (inc_unrev and r["STAGE"] == "BARU"):
            layak.append({"id": r["id"], "IC": r["IC"], "NAMA": r["NAMA"], "KOD_SEK": r["KOD_SEK"], "NAMA_SEK": r["NAMA_SEK"],
                          "JAWATAN": r["JAWATAN"], "KELAS": kelas, "POSKOD": r["POSKOD"]})
    return layak, placed


# ------------------------------------------------------------------ enjin penempatan zon (fungsi tulen - boleh diuji)
def jana_zon(calon, pusat, zone, placed=None, kaedah="seimbang", nama_sek=None):
    """
    calon : [{id, IC, NAMA, KOD_SEK, JAWATAN, KELAS, POSKOD}]
    pusat : {no: {NAMA, KOD_TUAN, PETUGAS, POSKOD}}  - sudah ditapis: hanya pusat bertapak di sekolah dalam zon
    zone  : set kod sekolah dalam zon
    placed: {no: {total, KP, TKP, asal:{kod: n}}} - sudah ditempatkan sebelum ini (tidak diubah)
    Pulang (assignments, tidak_ditempatkan, state)

    Kaedah: setiap calon diberi pusat yang layak mengikut keutamaan (seimbang / terdekat). Jika tiada ruang terus,
    guru yang sudah ditempatkan dalam larian ini dialih ke pusat lain (laluan penambahan - seperti padanan bipartit)
    supaya sebanyak mungkin guru ditempatkan, tanpa melanggar sebarang peraturan.
    """
    nama_sek = nama_sek or {}
    state = {no: {"total": 0, "KP": 0, "TKP": 0, "asal": {}} for no in pusat}
    for no, p in (placed or {}).items():
        if no in state:
            state[no] = {"total": p.get("total", 0), "KP": p.get("KP", 0), "TKP": p.get("TKP", 0), "asal": dict(p.get("asal", {}))}
    occ = {no: [] for no in pusat}          # calon yang ditempatkan dalam larian ini (boleh dialih)
    where = {}                              # id calon -> no pusat
    order, unplaced = [], []

    def can_add(no, c):
        p, s = pusat[no], state[no]
        if p["KOD_TUAN"] == c["KOD_SEK"]:                    # peraturan: bukan di sekolah asal
            return False
        if s["total"] >= p["PETUGAS"]:
            return False
        if s["asal"].get(c["KOD_SEK"], 0) >= MAX_SEK_SAMA:
            return False
        if c["KELAS"] in ("KP", "TKP") and s[c["KELAS"]] >= 1:
            return False
        return True

    def put(c, no):
        s = state[no]
        s["total"] += 1
        if c["KELAS"] in ("KP", "TKP"):
            s[c["KELAS"]] += 1
        s["asal"][c["KOD_SEK"]] = s["asal"].get(c["KOD_SEK"], 0) + 1
        occ[no].append(c)
        where[c["id"]] = no

    def take(c, no):
        s = state[no]
        s["total"] -= 1
        if c["KELAS"] in ("KP", "TKP"):
            s[c["KELAS"]] -= 1
        s["asal"][c["KOD_SEK"]] -= 1
        occ[no].remove(c)
        del where[c["id"]]

    def keutamaan(c):
        out = []
        for no, p in pusat.items():
            if p["KOD_TUAN"] == c["KOD_SEK"]:
                continue
            fill = state[no]["total"] / max(1, p["PETUGAS"])
            d = _dist(c["POSKOD"], p["POSKOD"])
            out.append(((fill, d, no) if kaedah == "seimbang" else (d, fill, no), no))
        return [no for _, no in sorted(out)]

    def augment(c, seen):
        senarai = keutamaan(c)
        for no in senarai:                                   # 1. ruang terus (bukan pusat yang sedang dikosongkan oleh panggilan induk)
            if no not in seen and can_add(no, c):
                put(c, no)
                return True
        for no in senarai:                                   # 2. alih guru lain untuk beri ruang
            if no in seen:
                continue
            seen.add(no)
            for o in list(occ[no]):
                take(o, no)
                if can_add(no, c) and augment(o, seen):
                    put(c, no)
                    return True
                if o["id"] not in where:
                    put(o, no)                               # pulihkan jika gagal
        return False

    def round_robin(items):
        by = {}
        for c in sorted(items, key=lambda c: (c["KOD_SEK"], c["NAMA"])):
            by.setdefault(c["KOD_SEK"], []).append(c)
        queues = [by[k] for k in sorted(by)]
        while any(queues):
            for q in queues:
                if q:
                    yield q.pop(0)

    for kelas in ("KP", "TKP", "PENGAWAS"):
        for c in round_robin([x for x in calon if x["KELAS"] == kelas and x["KOD_SEK"] in zone]):
            order.append(c)
            if not augment(c, set()):
                lain = [n for n, p in pusat.items() if p["KOD_TUAN"] != c["KOD_SEK"]]
                unplaced.append({**c, "SEBAB": ("Tiada pusat lain dalam zon (hanya sekolah sendiri)" if not lain
                                                else "Semua pusat zon penuh / had guru sekolah sama / KP-TKP sudah ada")})
    for c in calon:                                           # calon yang sekolah asalnya bukan dalam zon
        if c["KOD_SEK"] not in zone:
            unplaced.append({**c, "SEBAB": "Sekolah asal bukan dalam zon"})
    assignments = []
    for c in order:
        no = where.get(c["id"])
        if no is None:
            continue
        p = pusat[no]
        assignments.append({"id": c["id"], "IC_GURU": c["IC"], "NAMA_GURU": c["NAMA"], "KOD_SEKOLAH_ASAL": c["KOD_SEK"],
                            "NAMA_SEKOLAH_ASAL": c.get("NAMA_SEK") or nama_sek.get(c["KOD_SEK"], ""), "JAWATAN_CADANGAN": c["JAWATAN"],
                            "NO_PUSAT_TUGAS": no, "NAMA_PUSAT_TUGAS": p["NAMA"], "SEKOLAH_DITEMPATKAN": p["KOD_TUAN"],
                            "NAMA_SEKOLAH_DITEMPATKAN": nama_sek.get(p["KOD_TUAN"], "")})
    return assignments, unplaced, state


def validate(assignments, zone, pusat):
    """Semakan akhir sebelum simpan. Pulang senarai pelanggaran peraturan."""
    bad = []
    for a in assignments:
        p = pusat.get(a["NO_PUSAT_TUGAS"])
        if p is None:
            bad.append((a["NAMA_GURU"], "Pusat di luar zon"))
        elif p["KOD_TUAN"] == a["KOD_SEKOLAH_ASAL"]:
            bad.append((a["NAMA_GURU"], "Ditempatkan di sekolah asal"))
        elif a["KOD_SEKOLAH_ASAL"] not in zone:
            bad.append((a["NAMA_GURU"], "Sekolah asal bukan dalam zon"))
    return bad


def simpan_penempatan(assignments):
    by = {}
    for a in assignments:
        by.setdefault(a["NO_PUSAT_TUGAS"], []).append(a["id"])
    ok, err = 0, []
    for no, ids in by.items():
        for i in range(0, len(ids), 100):
            b = [pc._pyid(x) for x in ids[i:i + 100]]
            try:
                supa.table("cadangan_sup").update({"kod_pusat": no, "status": "DILANTIK PPD"}).in_("id", b).execute()
                ok += len(b)
            except Exception as e:
                err.append(str(e)[:150])
    try:
        get_cadangan_df.clear()
    except Exception:
        pass
    return ok, err


# ------------------------------------------------------------------ UI
def _pilih_bilik_kebal(kod_ppd):
    bks = load_bilik_kebal(kod_ppd)
    if not bks:
        st.info("Belum ada bilik kebal untuk PPD ini. Daftar dahulu di **Selenggara Bilik Kebal > Tambah Bilik Kebal**.")
        return None, {}
    nama = {b["kod"]: b["nama"] for b in bks}
    bk = st.selectbox("🔐 Pilih Bilik Kebal", [b["kod"] for b in bks], format_func=lambda k: f"{k} - {nama.get(k, '')}", key="zon_bk")
    return bk, nama


def render_penempatan_zon(kod_ppd, fly_cur=None):
    pc._banner(f"🗺️ Penempatan Zon Bilik Kebal - PPD {kod_ppd}",
               "Pilih bilik kebal → tetapkan sekolah di bawahnya (zon) → jana penempatan. Guru hanya bertugas dalam zon dan tidak di sekolah asal.")
    pc._flash()
    db_ok = zon_db_ok()
    if not db_ok:
        st.warning("⚠️ Jadual `zon_bilik_kebal` belum wujud di Supabase. Zon disimpan **sementara dalam sesi ini sahaja** "
                   "(hilang bila sesi tamat). Untuk simpanan kekal, jalankan SQL di bawah sekali di Supabase > SQL Editor.")
        with st.expander("📋 SQL untuk mencipta jadual zon_bilik_kebal"):
            st.code(ZON_SQL, language="sql")
    if fly_cur == "tempat":
        import program_config
        if not program_config.adalah_spm():
            import ppd_program
            ppd_program.render_jana_program(kod_ppd, "zon")
            return
        _view_jana(kod_ppd, db_ok)
    elif fly_cur == "semak":
        _view_semak(kod_ppd, db_ok)
    else:
        _view_tetap(kod_ppd, db_ok)


def _view_tetap(kod_ppd, db_ok):
    bk, nama_bk = _pilih_bilik_kebal(kod_ppd)
    if not bk:
        return
    smap = pc.sekolah_map(kod_ppd)
    zon = zon_load(db_ok)
    di_zon_lain = {s for k, v in zon.items() if k != bk for s in v}
    mine = [s for s in zon.get(bk, []) if s in smap or s]
    opts = sorted([s for s in smap if s not in di_zon_lain] + [s for s in mine if s not in smap])
    pusat = load_pusat(kod_ppd)
    layak, placed = load_calon(kod_ppd)
    st.markdown(f"#### Sekolah di bawah bilik kebal **{bk}**")
    if di_zon_lain:
        st.caption(f"ℹ️ {len(di_zon_lain)} sekolah sudah berada dalam zon bilik kebal lain dan tidak dipaparkan.")
    key = f"zon_ms_{bk}"
    if key not in st.session_state:
        st.session_state[key] = [s for s in mine if s in opts]
    pilih = st.multiselect("Pilih sekolah dalam zon ini (boleh taip untuk cari)", opts, key=key,
                           format_func=lambda k: f"{smap.get(k, '')} ({k})".strip())
    rows = []
    for ks in pilih:
        host = [p for p in pusat.values() if p["KOD_TUAN"] == ks]
        rows.append({"KOD SEKOLAH": ks, "NAMA SEKOLAH": smap.get(ks, ""),
                     "PUSAT DI SEKOLAH": ", ".join(p["NO"] for p in host) or "-",
                     "PETUGAS DIPERLUKAN": sum(p["PETUGAS"] for p in host),
                     "CALON TERPILIH": sum(1 for c in layak if c["KOD_SEK"] == ks)})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        no_host = [r["KOD SEKOLAH"] for r in rows if r["PUSAT DI SEKOLAH"] == "-"]
        if no_host:
            st.caption(f"ℹ️ {len(no_host)} sekolah tiada pusat bertapak - gurunya boleh ditempatkan di pusat sekolah lain dalam zon, tetapi sekolah itu tidak menerima petugas.")
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button(f"💾 Simpan Zon {bk} ({len(pilih)} sekolah)", type="primary", key="zon_simpan", disabled=not pilih, use_container_width=True):
        ok, msg = zon_save(kod_ppd, bk, pilih, db_ok)
        if ok:
            st.session_state["cad_flash"] = f"✅ Zon {bk} disimpan: {len(pilih)} sekolah" + (" (sementara dalam sesi)" if msg == "sesi" else "")
            st.rerun()
        else:
            st.error(f"Gagal simpan zon: {msg}. Mungkin ada sekolah yang sudah berada dalam zon lain.")
    if c2.button("🗑️ Kosongkan Zon", key="zon_kosong", disabled=not zon.get(bk), use_container_width=True):
        zon_save(kod_ppd, bk, [], db_ok)
        st.session_state.pop(key, None)
        st.session_state["cad_flash"] = f"Zon {bk} dikosongkan."
        st.rerun()
    st.markdown('<div class="cn-guide"><b>Peraturan zon:</b> guru hanya boleh ditempatkan dalam zon bilik kebal yang sama, '
                'hanya di pusat yang bertapak di sekolah dalam zon itu, dan <b>tidak di sekolah asalnya sendiri</b>.</div>', unsafe_allow_html=True)


def _view_jana(kod_ppd, db_ok):
    bk, nama_bk = _pilih_bilik_kebal(kod_ppd)
    if not bk:
        return
    zon = zon_load(db_ok)
    zone = set(zon.get(bk, []))
    if not zone:
        st.warning(f"Zon {bk} belum ditetapkan. Pergi ke **Tetapan Zon** dan pilih sekolah di bawah bilik kebal ini dahulu.")
        return
    smap = pc.sekolah_map(kod_ppd)
    pusat_all = load_pusat(kod_ppd)
    pusat = {no: p for no, p in pusat_all.items() if p["KOD_TUAN"] in zone}
    inc = st.checkbox("Termasuk cadangan yang belum disemak PPD", key="zon_inc")
    layak_all, placed = load_calon(kod_ppd, inc)
    layak = [c for c in layak_all if c["KOD_SEK"] in zone]
    perlu = sum(p["PETUGAS"] for p in pusat.values())
    sudah = sum(placed.get(no, {}).get("total", 0) for no in pusat)
    a, b, c, d = st.columns(4)
    a.metric("🏫 Sekolah dalam zon", len(zone))
    b.metric("📍 Pusat dalam zon", len(pusat))
    c.metric("📋 Baki petugas diperlukan", max(0, perlu - sudah))
    d.metric("👨‍🏫 Calon layak (belum ditempatkan)", len(layak))
    if not pusat:
        st.warning("Tiada pusat bertapak di sekolah dalam zon ini, jadi tiada tempat untuk penempatan.")
        return
    kaedah = st.radio("Kaedah agihan", ["seimbang", "terdekat"], horizontal=True, key="zon_kaedah",
                      format_func=lambda k: "🔄 Seimbang (pusingan antara sekolah, isi pusat paling kurang dahulu)" if k == "seimbang" else "📮 Terdekat (ikut poskod)")
    rkey = f"zon_res_{bk}"
    if st.button(f"🚀 Jana Penempatan Zon {bk}", type="primary", key="zon_jana", use_container_width=True, disabled=not layak):
        asg, unp, state = jana_zon(layak, pusat, zone, placed, kaedah, smap)
        st.session_state[rkey] = {"asg": asg, "unp": unp, "state": state}
    res = st.session_state.get(rkey)
    if not res:
        return
    asg, unp, state = res["asg"], res["unp"], res["state"]
    st.success(f"✅ {len(asg)} guru ditempatkan dalam zon {bk}" + (f"  •  ⚠️ {len(unp)} tidak dapat ditempatkan" if unp else ""))
    bad = validate(asg, zone, pusat)
    if bad:
        st.error("❌ Pelanggaran peraturan zon dikesan - simpanan disekat: " + "; ".join(f"{n}: {m}" for n, m in bad[:5]))
    if asg:
        st.dataframe(pd.DataFrame(asg).drop(columns=["id"]), use_container_width=True, hide_index=True)
    ring = [{"NO PUSAT": no, "NAMA PUSAT": p["NAMA"], "SEKOLAH TUAN RUMAH": f"{p['KOD_TUAN']} {smap.get(p['KOD_TUAN'], '')}".strip(),
             "DIPERLUKAN": p["PETUGAS"], "DIISI": state[no]["total"], "BAKI": max(0, p["PETUGAS"] - state[no]["total"])} for no, p in pusat.items()]
    with st.expander("📍 Ringkasan isian pusat dalam zon", expanded=True):
        st.dataframe(pd.DataFrame(ring), use_container_width=True, hide_index=True)
    if unp:
        with st.expander(f"⚠️ {len(unp)} guru tidak dapat ditempatkan"):
            st.dataframe(pd.DataFrame([{"NAMA": u["NAMA"], "SEKOLAH ASAL": u["KOD_SEK"], "JAWATAN": u["JAWATAN"], "SEBAB": u["SEBAB"]} for u in unp]),
                         use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    if c1.button(f"💾 Simpan Penempatan ({len(asg)})", type="primary", key="zon_simpan_asg", disabled=bool(bad) or not asg, use_container_width=True):
        ok, err = simpan_penempatan(asg)
        if err:
            st.error("Sebahagian gagal disimpan: " + " | ".join(err[:2]))
        else:
            st.session_state.pop(rkey, None)
            st.session_state["cad_flash"] = f"✅ {ok} guru ditempatkan dalam zon {bk} (status DILANTIK PPD)."
            st.rerun()
    if c2.button("🗑️ Buang keputusan", key="zon_buang", use_container_width=True):
        st.session_state.pop(rkey, None)
        st.rerun()


def _view_semak(kod_ppd, db_ok):
    zon = zon_load(db_ok)
    bks = {b["kod"]: b["nama"] for b in load_bilik_kebal(kod_ppd)}
    smap = pc.sekolah_map(kod_ppd)
    pusat = load_pusat(kod_ppd)
    layak, placed = load_calon(kod_ppd)
    if not zon:
        st.info("Belum ada zon ditetapkan. Gunakan **Tetapan Zon**.")
        return
    rows = []
    for bk in sorted(zon):
        zs = set(zon[bk])
        pz = [p for p in pusat.values() if p["KOD_TUAN"] in zs]
        rows.append({"BILIK KEBAL": bk, "NAMA": bks.get(bk, ""), "SEKOLAH": len(zs), "PUSAT": len(pz),
                     "PETUGAS DIPERLUKAN": sum(p["PETUGAS"] for p in pz),
                     "SUDAH DITEMPATKAN": sum(placed.get(p["NO"], {}).get("total", 0) for p in pz),
                     "CALON BELUM DITEMPATKAN": sum(1 for c in layak if c["KOD_SEK"] in zs)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    di_zon = {s for v in zon.values() for s in v}
    tanpa = sorted(set(smap) - di_zon)
    st.metric("Sekolah belum dalam mana-mana zon", len(tanpa))
    if tanpa:
        with st.expander("Senarai sekolah tanpa zon"):
            st.dataframe(pd.DataFrame([{"KOD": k, "NAMA": smap.get(k, "")} for k in tanpa]), use_container_width=True, hide_index=True)
