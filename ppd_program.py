# -*- coding: utf-8 -*-
"""
ppd_program.py - Bahagian khusus program UBBM / UBBI (kuota ikut bilik ujian).

  keperluan_ub_sekolah()  : kotak keperluan petugas pada menu SUP (ganti kotak SPM)
  metrik_cadangan_ub()    : kiraan cadangan mengikut jawatan (SUP)
  jana_program()          : enjin penempatan umum mengikut kuota setiap jawatan di setiap pusat
  render_jana_program()   : Jana Keseluruhan (daerah) / Jana Penempatan Zon (UB) - PPD
  render_tetapan_program(): JPN > Tetapan Program (ubah kuota ikut bilik ujian)
Peraturan: guru TIDAK ditempatkan di sekolah asalnya; dalam mod zon hanya pusat & guru dalam zon; kuota setiap jawatan dipatuhi;
agihan bergilir antara sekolah asal; maksimum 3 guru sekolah sama setiap pusat.
"""
import pandas as pd
import streamlit as st
import spm_core as core
from spm_core import get_cadangan_df, supa
import program_config as PC
import ppd_cadangan as pc
import ppd_zon as pz
from ui_theme import esc

MAX_SEK_SAMA = 3


# ------------------------------------------------------------------ data pusat & calon
def pusat_ub(kod_ppd):
    """{no: {NO, NAMA, KOD_TUAN, KELAS, CALON, POSKOD, BILIK, KUOTA{role:n}}} untuk daerah ini."""
    out = {}
    for no, p in pz.load_pusat(kod_ppd).items():
        bilik = PC.bilik_ujian(p.get("KELAS", 0), p.get("CALON", 0))
        out[no] = dict(p, BILIK=bilik, KUOTA=PC.kuota_roles(bilik=p.get("KELAS", 0), calon=p.get("CALON", 0)))
    return out


def load_calon_ub(kod_ppd, inc_unrev=False):
    """(layak, placed): layak = calon TERPILIH belum ditempatkan; placed = {no: {total, roles{}, asal{}}}."""
    df = pc.normalize(get_cadangan_df(kod_ppd=kod_ppd))
    nama_role = {k for k, _n, _c in PC.roles()}
    layak, placed = [], {}
    for _, r in df.iterrows():
        role = PC.role_of(r["JAWATAN"])
        if r["KOD_PUSAT"]:
            if role in nama_role:
                p = placed.setdefault(r["KOD_PUSAT"], {"total": 0, "roles": {}, "asal": {}})
                p["total"] += 1
                p["roles"][role] = p["roles"].get(role, 0) + 1
                p["asal"][r["KOD_SEK"]] = p["asal"].get(r["KOD_SEK"], 0) + 1
            continue
        if role not in nama_role:
            continue
        if r["STAGE"] == "TERPILIH" or (inc_unrev and r["STAGE"] == "BARU"):
            layak.append({"id": r["id"], "IC": r["IC"], "NAMA": r["NAMA"], "KOD_SEK": r["KOD_SEK"], "NAMA_SEK": r["NAMA_SEK"],
                          "JAWATAN": r["JAWATAN"], "ROLE": role, "POSKOD": r["POSKOD"]})
    return layak, placed


# ------------------------------------------------------------------ enjin penempatan umum
def jana_program(calon, pusat, zone, placed=None, kaedah="seimbang", nama_sek=None, maks_sekolah=MAX_SEK_SAMA):
    """
    calon : [{id, IC, NAMA, KOD_SEK, JAWATAN, ROLE, POSKOD}]
    pusat : {no: {NAMA, KOD_TUAN, POSKOD, KUOTA{role:n}}}  (hanya pusat yang dibenarkan)
    zone  : set kod sekolah dibenarkan (None = semua dalam daerah)
    placed: {no: {total, roles{}, asal{}}} - sudah ditempatkan (tidak diubah)
    Pulang (assignments, tidak_ditempatkan, state)
    """
    nama_sek = nama_sek or {}
    state = {no: {"roles": {}, "total": 0, "asal": {}} for no in pusat}
    for no, p in (placed or {}).items():
        if no in state:
            state[no] = {"roles": dict(p.get("roles", {})), "total": p.get("total", 0), "asal": dict(p.get("asal", {}))}
    occ = {no: [] for no in pusat}
    where, order, unplaced = {}, [], []
    tertib = [k for k, _n, _c in PC.roles()]

    def can_add(no, c):
        p, s = pusat[no], state[no]
        if zone is not None and p["KOD_TUAN"] not in zone:          # pusat mesti dalam zon
            return False
        if p["KOD_TUAN"] == c["KOD_SEK"]:
            return False
        if s["roles"].get(c["ROLE"], 0) >= p["KUOTA"].get(c["ROLE"], 0):
            return False
        if s["asal"].get(c["KOD_SEK"], 0) >= maks_sekolah:
            return False
        return True

    def put(c, no):
        s = state[no]
        s["total"] += 1
        s["roles"][c["ROLE"]] = s["roles"].get(c["ROLE"], 0) + 1
        s["asal"][c["KOD_SEK"]] = s["asal"].get(c["KOD_SEK"], 0) + 1
        occ[no].append(c)
        where[c["id"]] = no

    def take(c, no):
        s = state[no]
        s["total"] -= 1
        s["roles"][c["ROLE"]] -= 1
        s["asal"][c["KOD_SEK"]] -= 1
        occ[no].remove(c)
        del where[c["id"]]

    def keutamaan(c):
        out = []
        for no, p in pusat.items():
            if p["KOD_TUAN"] == c["KOD_SEK"] or (zone is not None and p["KOD_TUAN"] not in zone):
                continue
            kt = max(1, sum(p["KUOTA"].values()))
            fill = state[no]["total"] / kt
            d = pz._dist(c["POSKOD"], p["POSKOD"])
            out.append(((fill, d, no) if kaedah == "seimbang" else (d, fill, no), no))
        return [no for _, no in sorted(out)]

    def augment(c, seen):
        senarai = keutamaan(c)
        for no in senarai:
            if no not in seen and can_add(no, c):
                put(c, no)
                return True
        for no in senarai:
            if no in seen:
                continue
            seen.add(no)
            for o in list(occ[no]):
                take(o, no)
                if can_add(no, c) and augment(o, seen):
                    put(c, no)
                    return True
                if o["id"] not in where:
                    put(o, no)
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

    for role in tertib:
        for c in round_robin([x for x in calon if x["ROLE"] == role and (zone is None or x["KOD_SEK"] in zone)]):
            order.append(c)
            if not augment(c, set()):
                lain = [n for n, p in pusat.items() if p["KOD_TUAN"] != c["KOD_SEK"] and p["KUOTA"].get(role, 0) > 0]
                unplaced.append({**c, "SEBAB": ("Tiada pusat lain yang memerlukan jawatan ini (hanya sekolah sendiri)" if not lain
                                                else "Kuota jawatan ini sudah penuh di semua pusat / had guru sekolah sama")})
    for c in calon:
        if zone is not None and c["KOD_SEK"] not in zone:
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
                            "NAMA_SEKOLAH_DITEMPATKAN": nama_sek.get(p["KOD_TUAN"], ""), "ROLE": c["ROLE"]})
    return assignments, unplaced, state


def validate_program(asg, zone, pusat, placed=None):
    """Semakan akhir: pusat sah (dalam zon), bukan sekolah asal, kuota jawatan tidak dilebihi."""
    bad, cnt = [], {}
    for a in asg:
        p = pusat.get(a["NO_PUSAT_TUGAS"])
        if p is None:
            bad.append((a["NAMA_GURU"], "Pusat tidak dibenarkan"))
            continue
        if zone is not None and p["KOD_TUAN"] not in zone:
            bad.append((a["NAMA_GURU"], "Pusat di luar zon"))
        if p["KOD_TUAN"] == a["KOD_SEKOLAH_ASAL"]:
            bad.append((a["NAMA_GURU"], "Ditempatkan di sekolah asal"))
        if zone is not None and a["KOD_SEKOLAH_ASAL"] not in zone:
            bad.append((a["NAMA_GURU"], "Sekolah asal bukan dalam zon"))
        k = (a["NO_PUSAT_TUGAS"], a["ROLE"])
        cnt[k] = cnt.get(k, 0) + 1
    for (no, role), n in cnt.items():
        sedia = (placed or {}).get(no, {}).get("roles", {}).get(role, 0)
        if n + sedia > pusat[no]["KUOTA"].get(role, 0):
            bad.append((no, f"Kuota {role} dilebihi"))
    return bad


# ------------------------------------------------------------------ SUP: keperluan & kiraan
def keperluan_ub_sekolah(kod_ppd, kod_sekolah):
    """Kotak keperluan petugas sekolah (pusat yang bertapak di sekolah ini). Pulang (jumlah_bilik, jumlah_kuota, kuota_gabungan)."""
    c = PC.cfg()
    try:
        semua = pusat_ub(kod_ppd)
    except Exception:
        semua = {}
    mine = [p for p in semua.values() if p["KOD_TUAN"] == str(kod_sekolah).upper().strip()]
    gab = {k: 0 for k, _n, _c in PC.roles()}
    if not mine:
        st.info(f"Tiada pusat {c['singkatan']} bertapak di {kod_sekolah}. Kuota ditentukan mengikut bilik ujian pusat; PPD akan mengagihkan guru anda.")
        return 0, 0, gab
    bilik = sum(p["BILIK"] for p in mine)
    for p in mine:
        for k, n in p["KUOTA"].items():
            gab[k] += n
    nama = {k: n for k, n, _c in PC.roles()}
    baris = "<br>".join(f"<b style='color:#0d47a1;'>{esc(nama[k])}:</b> {gab[k]} orang" for k in gab)
    perincian = "; ".join(f"{p['NO']} ({p['BILIK']} bilik ujian)" for p in mine)
    st.markdown(f"""
    <div style="background:#e3f2fd; padding:15px; border-radius:10px; border-left:5px solid #0d47a1; margin-bottom:20px;">
        <h4 style="margin:0; color:#0d47a1;">📢 KEPERLUAN PETUGAS {esc(c['singkatan'])} - {esc(kod_sekolah)}</h4>
        <p style="margin:5px 0;">Pusat: {len(mine)} | Bilik ujian: {bilik} &nbsp;•&nbsp; {esc(perincian)}</p>
        <p style="margin:5px 0; font-size:15px;">{baris}<br>
        <b style="color:#0d47a1;">OPTIONAL:</b> Penyelia Kawasan 1 orang<br>
        <b>Jumlah kuota pusat: {sum(gab.values())} orang</b> (ikut jadual bilik ujian {esc(c['singkatan'])})</p>
    </div>""", unsafe_allow_html=True)
    return bilik, sum(gab.values()), gab


def metrik_cadangan_ub(df_cad, kuota=None):
    """Kiraan cadangan mengikut jawatan program (ganti 4 kad SPM)."""
    kuota = kuota or {}
    cnt = {}
    if df_cad is not None and len(df_cad):
        col = next((c for c in df_cad.columns if str(c).upper() == "JAWATAN_CADANGAN"), None)
        if col:
            for j in df_cad[col]:
                r = PC.role_of(j)
                cnt[r] = cnt.get(r, 0) + 1
    paparan = [(k, n) for k, n, _c in PC.roles()] + [("PK", "Penyelia Kawasan")]
    cols = st.columns(len(paparan))
    for col, (k, nama) in zip(cols, paparan):
        need = kuota.get(k)
        n = cnt.get(k, 0)
        col.metric(nama, n, delta=(f"Perlu {need}" if need else None))


# ------------------------------------------------------------------ PPD: jana
def render_jana_program(kod_ppd, mod="daerah"):
    c = PC.cfg()
    judul = "Jana Penempatan Zon" if mod == "zon" else "Jana Keseluruhan"
    pc._banner(f"🚀 {judul} {c['singkatan']} - PPD {kod_ppd}",
               "Penempatan mengikut kuota setiap jawatan bagi setiap pusat (bilik ujian). Guru tidak ditempatkan di sekolah asal.")
    pc._flash()
    zone = None
    if mod == "zon":
        db_ok = pz.zon_db_ok()
        bk, _nama = pz._pilih_bilik_kebal(kod_ppd)
        if not bk:
            return
        zone = set(pz.zon_load(db_ok).get(bk, []))
        if not zone:
            st.warning(f"Zon {bk} belum ditetapkan. Pergi ke Tetapan Zon dan pilih sekolah di bawah bilik kebal ini dahulu.")
            return
    else:
        bk = "DAERAH"
    smap = pc.sekolah_map(kod_ppd)
    semua = pusat_ub(kod_ppd)
    pusat = {no: p for no, p in semua.items() if (zone is None or p["KOD_TUAN"] in zone) and sum(p["KUOTA"].values()) > 0}
    inc = st.checkbox("Termasuk cadangan yang belum disemak PPD", key=f"prg_inc_{bk}")
    layak_all, placed = load_calon_ub(kod_ppd, inc)
    layak = [x for x in layak_all if zone is None or x["KOD_SEK"] in zone]
    perlu = sum(sum(p["KUOTA"].values()) for p in pusat.values())
    sudah = sum(placed.get(no, {}).get("total", 0) for no in pusat)
    a, b, c3, d = st.columns(4)
    a.metric("📍 Pusat (ada kuota)", len(pusat))
    b.metric("📋 Jumlah kuota", perlu)
    c3.metric("✅ Sudah ditempatkan", sudah)
    d.metric("👨‍🏫 Calon layak", len(layak))
    tanpa_bilik = [no for no, p in semua.items() if sum(p["KUOTA"].values()) == 0 and (zone is None or p["KOD_TUAN"] in zone)]
    if tanpa_bilik:
        st.warning(f"{len(tanpa_bilik)} pusat tiada kuota kerana bilik ujian belum ditetapkan: {', '.join(tanpa_bilik[:8])}{' ...' if len(tanpa_bilik) > 8 else ''}. "
                   "Isi 'Bilik Ujian' di menu Pusat di PPD.")
    if not pusat:
        st.info("Tiada pusat yang boleh menerima penempatan.")
        return
    nama_role = {k: n for k, n, _c in PC.roles()}
    jadual = []
    for no, p in pusat.items():
        row = {"NO PUSAT": no, "NAMA PUSAT": p["NAMA"], "BILIK UJIAN": p["BILIK"]}
        for k, n in nama_role.items():
            row[f"{n} (ada/kuota)"] = f"{placed.get(no, {}).get('roles', {}).get(k, 0)}/{p['KUOTA'].get(k, 0)}"
        jadual.append(row)
    with st.expander("📍 Kuota & penempatan semasa setiap pusat", expanded=False):
        st.dataframe(pd.DataFrame(jadual), use_container_width=True, hide_index=True)
    kaedah = st.radio("Kaedah agihan", ["seimbang", "terdekat"], horizontal=True, key=f"prg_kaedah_{bk}",
                      format_func=lambda k: "🔄 Seimbang (pusingan antara sekolah, isi pusat paling kurang dahulu)" if k == "seimbang" else "📮 Terdekat (ikut poskod)")
    rkey = f"prg_res_{mod}_{bk}"
    if st.button(f"🚀 Jana Penempatan {c['singkatan']}", type="primary", key=f"prg_jana_{mod}", use_container_width=True, disabled=not layak):
        asg, unp, state = jana_program(layak, pusat, zone, placed, kaedah, smap)
        st.session_state[rkey] = {"asg": asg, "unp": unp, "state": state}
    res = st.session_state.get(rkey)
    if not res:
        return
    asg, unp, state = res["asg"], res["unp"], res["state"]
    st.success(f"✅ {len(asg)} guru ditempatkan" + (f"  •  ⚠️ {len(unp)} tidak dapat ditempatkan" if unp else ""))
    bad = validate_program(asg, zone, pusat, placed)
    if bad:
        st.error("❌ Pelanggaran peraturan dikesan - simpanan disekat: " + "; ".join(f"{n}: {m}" for n, m in bad[:5]))
    if asg:
        st.dataframe(pd.DataFrame(asg).drop(columns=["id", "ROLE"]), use_container_width=True, hide_index=True)
    ring = []
    for no, p in pusat.items():
        row = {"NO PUSAT": no, "SEKOLAH TUAN RUMAH": f"{p['KOD_TUAN']} {smap.get(p['KOD_TUAN'], '')}".strip()}
        for k, n in nama_role.items():
            row[n] = f"{state[no]['roles'].get(k, 0)}/{p['KUOTA'].get(k, 0)}"
        ring.append(row)
    with st.expander("📍 Ringkasan isian pusat selepas janaan", expanded=True):
        st.dataframe(pd.DataFrame(ring), use_container_width=True, hide_index=True)
    if unp:
        with st.expander(f"⚠️ {len(unp)} guru tidak dapat ditempatkan"):
            st.dataframe(pd.DataFrame([{"NAMA": u["NAMA"], "SEKOLAH ASAL": u["KOD_SEK"], "JAWATAN": u["JAWATAN"], "SEBAB": u["SEBAB"]} for u in unp]),
                         use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    if c1.button(f"💾 Simpan Penempatan ({len(asg)})", type="primary", key=f"prg_simpan_{mod}", disabled=bool(bad) or not asg, use_container_width=True):
        ok, err = pz.simpan_penempatan(asg)
        if err:
            st.error("Sebahagian gagal disimpan: " + " | ".join(err[:2]))
        else:
            st.session_state.pop(rkey, None)
            st.session_state["cad_flash"] = f"✅ {ok} guru ditempatkan (status DILANTIK PPD)."
            st.rerun()
    if c2.button("🗑️ Buang keputusan", key=f"prg_buang_{mod}", use_container_width=True):
        st.session_state.pop(rkey, None)
        st.rerun()


# ------------------------------------------------------------------ JPN: Tetapan Program
def render_tetapan_program():
    c = PC.cfg()
    pc._banner(f"⚙️ Tetapan Program - {c['singkatan']}", c["nama_sistem"])
    pc._flash()
    st.markdown("**Struktur jawatan:** " + " • ".join(c["jawatan_pilihan"]))
    if PC.adalah_spm():
        st.info("Program SPM: kuota dikira daripada keperluan pusat (kelas + 9) - 1 KP, 1 TKP dan pengawas. Tiada jadual bilik ujian. "
                "Tetapkan `PROGRAM` = UBBM atau UBBI dalam Secrets untuk program ujian bertutur.")
        return
    nama = [(k, n) for k, n, _c in PC.roles()]
    jadual = PC.tetapan()
    st.caption(f"Kuota petugas bagi satu pusat mengikut bilangan bilik ujian (maksimum {c['maks_bilik']} bilik). Bilangan bilik ujian ialah lajur 'Bilik Ujian' pusat.")
    df = pd.DataFrame([{"BILIK UJIAN": b, **{n: jadual[b].get(k, 0) for k, n in nama}} for b in sorted(jadual)])
    ed = st.data_editor(df, hide_index=True, use_container_width=True, disabled=["BILIK UJIAN"], key=f"tetapan_{c['kod']}",
                        column_config={n: st.column_config.NumberColumn(n, min_value=0, step=1) for _k, n in nama})
    if not isinstance(ed, pd.DataFrame):
        ed = df
    c1, c2 = st.columns(2)
    if c1.button("💾 Simpan Kuota", type="primary", key="tetapan_simpan", use_container_width=True):
        baru = {int(r["BILIK UJIAN"]): {k: int(r[n]) for k, n in nama} for _, r in ed.iterrows()}
        ok, msg = PC.simpan_tetapan(baru)
        if ok:
            st.session_state["cad_flash"] = "✅ Kuota disimpan."
            st.rerun()
        else:
            st.error(f"Gagal simpan: {msg}")
    if c2.button("↩️ Kembali ke nilai lalai", key="tetapan_lalai", use_container_width=True):
        PC.simpan_tetapan({b: dict(v) for b, v in PC.cfg()["kuota_lalai"].items()})
        st.session_state["cad_flash"] = "Kuota dikembalikan kepada nilai lalai."
        st.rerun()
