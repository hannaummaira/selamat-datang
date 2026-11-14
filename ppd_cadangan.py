# -*- coding: utf-8 -*-
"""
ppd_cadangan.py - Aliran semakan cadangan SUP oleh PPD.

  Cadangan SUP > Senarai Nama Cadangan : popup  Jawatan -> Sekolah -> Senarai nama (tick = dijana)
                                         Hantar: tick -> status "TERPILIH PPD", tidak tick -> "SIMPANAN PPD"
  Cadangan SUP > Senarai Simpanan      : pilih sekolah, tick untuk pindah semula ke Jana
  Jana Keseluruhan                     : hanya calon TERPILIH PPD (+ yang sudah diproses) masuk pool;
                                         PPD boleh tapis siapa dilantik / tidak dilantik.

Hanya lajur `status` dalam cadangan_sup digunakan (tiada perubahan skema pangkalan data).
"""
import json
import pandas as pd
import streamlit as st
import spm_core as core
from spm_core import get_cadangan_df, supa
from ui_theme import esc

ST_TERPILIH = "TERPILIH PPD"
ST_SIMPANAN = "SIMPANAN PPD"
_LOCK = ("DILANTIK", "DITEMPATKAN", "SURAT", "LULUS", "DIJANA")     # sudah diproses - jangan diusik
ORDER_JAWATAN = ["KETUA PENGAWAS", "TIMBALAN KETUA PENGAWAS", "PENYELIA KAWASAN", "PENGAWAS PEPERIKSAAN",
                 "SELENGGARA BILIK KEBAL", "JURU TULIS", "JURU BACA"]


# ------------------------------------------------------------------ pembantu data
def _pick(r, *keys):
    for k in keys:
        try:
            v = r.get(k)
        except Exception:
            v = None
        if v is not None and str(v).strip().lower() not in ("", "nan", "none", "null", "nat"):
            return str(v).strip()
    return ""


def stage_of(status):
    s = str(status or "").upper()
    if "SIMPANAN" in s:
        return "SIMPANAN"
    if "TERPILIH" in s:
        return "TERPILIH"
    if any(x in s for x in _LOCK):
        return "LOCKED"
    return "BARU"                      # DICADANGKAN / HANTAR KE PPD - belum disemak PPD


def normalize(df):
    cols = ["id", "NAMA", "IC", "KOD_SEK", "NAMA_SEK", "JAWATAN", "STATUS", "POSKOD", "STAGE", "KOD_PUSAT"]
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    for _, r in df.iterrows():
        rid = r.get("id")
        if rid is None or str(rid).strip().lower() in ("", "nan", "none"):
            continue                                           # tanpa id tak boleh dikemas kini
        kod = _pick(r, "KOD_SEKOLAH_ASAL", "kod_sekolah_asal", "KOD_SEKOLAH", "kod_sekolah").upper()
        if not kod:
            continue
        status = _pick(r, "STATUS", "status").upper()
        rows.append({"id": rid, "NAMA": _pick(r, "NAMA_GURU", "nama_guru"), "IC": _pick(r, "IC_GURU", "ic_guru"),
                     "KOD_SEK": kod, "NAMA_SEK": _pick(r, "NAMA_SEKOLAH_ASAL", "nama_sekolah_asal"),
                     "JAWATAN": (_pick(r, "JAWATAN_CADANGAN", "jawatan_cadangan", "JAWATAN") or "TIADA JAWATAN").upper(),
                     "STATUS": status, "POSKOD": _pick(r, "POSKOD_RUMAH", "poskod_rumah"), "STAGE": stage_of(status),
                     "KOD_PUSAT": "" if _pick(r, "KOD_PUSAT", "kod_pusat") in ("-",) else _pick(r, "KOD_PUSAT", "kod_pusat").upper()})
    return pd.DataFrame(rows, columns=cols)


@st.cache_data(ttl=600, show_spinner=False)
def sekolah_map(kod_ppd):
    """{kod_sekolah: nama_sekolah} - sudah ditapis ikut daerah oleh scoped_db."""
    out = {}
    try:
        res = supa.table("sekolah_master").select("kod_sekolah,nama_sekolah").limit(2000).execute()
        for s in res.data or []:
            k = str(s.get("kod_sekolah") or "").upper().strip()
            if k:
                out[k] = str(s.get("nama_sekolah") or "").upper().strip()
    except Exception:
        pass
    return out


def _nama_sek(kod, row_nama, smap):
    return smap.get(kod) or row_nama or kod


def _pyid(x):
    try:
        return int(float(str(x)))
    except Exception:
        return str(x)


def ppd_set_status(ids, status):
    """Kemas kini status mengikut id (kelompok 100). Pulang (bilangan_ok, senarai_ralat)."""
    ok, err = 0, []
    ids = [_pyid(i) for i in ids if i is not None]
    for i in range(0, len(ids), 100):
        b = ids[i:i + 100]
        try:
            supa.table("cadangan_sup").update({"status": status}).in_("id", b).execute()
            ok += len(b)
        except Exception as e:
            err.append(str(e)[:150])
    try:
        get_cadangan_df.clear()
    except Exception:
        pass
    return ok, err


def _jaw_sorted(vals):
    from program_config import urutan_jawatan, adalah_spm
    vals = list(vals)
    order = ORDER_JAWATAN if adalah_spm() else urutan_jawatan()
    return sorted(vals, key=lambda x: (order.index(str(x).upper()) if str(x).upper() in order else 99, x))


def _banner(title, sub):
    st.markdown(f"""<div class="sup-box"><div class="sup-card-h"><span class="t">{title}</span></div>
    <div style="padding:8px 14px;font-size:12px;color:#5f6f85">{sub}</div></div>""", unsafe_allow_html=True)


def _flash():
    msg = st.session_state.pop("cad_flash", None)
    if msg:
        st.success(msg)


def _container(height=None):
    try:
        return st.container(height=height) if height else st.container()
    except TypeError:
        return st.container()


def _counts_strip(df):
    c = df["STAGE"].value_counts().to_dict() if not df.empty else {}
    a, b, c2, d = st.columns(4)
    a.metric("✅ Terpilih (dijana)", c.get("TERPILIH", 0))
    b.metric("📦 Simpanan", c.get("SIMPANAN", 0))
    c2.metric("🆕 Belum disemak", c.get("BARU", 0))
    d.metric("📌 Sudah diproses", c.get("LOCKED", 0))


# ------------------------------------------------------------------ SENARAI NAMA CADANGAN (replika: pilih sekolah -> tick -> hantar)
PER_PAGE = 10

CN_CSS = """<style>
.cn-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:8px 0}
.cn-card{background:#fff;border:1px solid #c5d6e8;border-radius:8px;padding:10px 12px}
.cn-card .l{font-size:10px;font-weight:700;letter-spacing:.1em;color:#5f6f85}
.cn-card .v{font-size:15px;font-weight:800;color:#0d47a1;margin-top:2px;line-height:1.2}
.cn-card .s{font-size:10px;color:#5f6f85;margin-top:3px}
.cn-legend{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:11px;color:#5f6f85;margin:6px 0}
.cn-head{background:#e3f2fd;border:1px solid #c5d6e8;border-radius:6px 6px 0 0;padding:7px 4px;font-size:10px;font-weight:700;letter-spacing:.08em;color:#0d47a1}
.cn-b{display:inline-flex;align-items:center;gap:6px;padding:2px 9px;border-radius:999px;font-size:10px;font-weight:700;border:1px solid}
.cn-b.ok{background:#dcfce7;border-color:#86efac;color:#166534}
.cn-b.sim{background:#fef3c7;border-color:#fde68a;color:#92400e}
.cn-b.jw{background:#e3f2fd;border-color:#90caf9;color:#0d47a1;border-radius:4px}
.cn-b i{width:6px;height:6px;border-radius:50%;display:inline-block;background:currentColor}
.cn-nm{font-weight:700;color:#13233f;font-size:13px}
.cn-ic{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:#475569}
.cn-sm{font-size:11px;color:#334155}
.cn-bar{background:#fff;border:1px solid #c5d6e8;border-radius:8px;padding:10px 14px;margin:10px 0 6px;display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.cn-bar .k{font-size:10px;font-weight:700;letter-spacing:.08em;color:#5f6f85}
.cn-bar .n{font-size:20px;font-weight:800;margin-left:6px}
.cn-bar .ok{color:#166534}.cn-bar .sim{color:#92400e}
.cn-guide{background:#f0f7ff;border:1px solid #bbdefb;border-radius:8px;padding:8px 12px;font-size:11px;color:#334155;margin-top:8px}
@media(max-width:900px){.cn-cards{grid-template-columns:repeat(2,1fr)}}
</style>"""

JAW_ALL = "Semua"


def _cols(spec):
    try:
        return st.columns(spec, vertical_alignment="center")
    except TypeError:
        return st.columns(spec)


def _sel_state():
    return st.session_state.setdefault("cn_sel", {})


def _ck_key(school, rid):
    return f"cn_ck_{school}_{rid}"


def _toggle(school, rid):
    sel = _sel_state().setdefault(school, set())
    if st.session_state.get(_ck_key(school, rid)):
        sel.add(rid)
    else:
        sel.discard(rid)


def _set_many(school, ids, value):
    sel = _sel_state().setdefault(school, set())
    for rid in ids:
        if value:
            sel.add(rid)
        else:
            sel.discard(rid)
        st.session_state[_ck_key(school, rid)] = bool(value)


def _reset_filters():
    st.session_state["cn_q"] = ""
    st.session_state["cn_jw"] = JAW_ALL
    st.session_state["cn_page"] = 1


def _forget_school(school):
    _sel_state().pop(school, None)
    for k in [k for k in list(st.session_state.keys()) if str(k).startswith(f"cn_ck_{school}_")]:
        try:
            del st.session_state[k]
        except Exception:
            pass


def _badge(kind, text):
    return f'<span class="cn-b {kind}"><i></i>{text}</span>'


@st.dialog("Sahkan Tindakan")
def dlg_confirm(school, nama_sek, mode, yes, no):
    """yes / no = senarai (id, nama, no_pusat)."""
    if mode == "terpilih":
        st.markdown(f"### Hantar {len(yes)} sebagai TERPILIH PPD?")
        st.write(f"{len(yes)} guru yang ditick akan masuk **Jana Keseluruhan** (TERPILIH PPD). "
                 f"Baki {len(no)} guru yang tidak ditick akan masuk **Senarai Simpanan** secara automatik.")
        show = yes
    else:
        st.markdown(f"### Simpan {len(no)} sebagai SIMPANAN PPD?")
        st.write(f"{len(no)} guru yang tidak ditick akan masuk **Senarai Simpanan**. Guru yang ditick tidak diubah.")
        show = no
    st.caption("SENARAI TERPILIH" if mode == "terpilih" else "SENARAI SIMPANAN")
    for rid, nama, pusat in show[:8]:
        st.markdown(f"- **{nama}** · {pusat or '-'}")
    if len(show) > 8:
        st.caption(f"+ {len(show) - 8} lagi...")
    c1, c2 = st.columns(2)
    if c1.button("Batal", key="cf_batal", use_container_width=True):
        st.rerun()
    if c2.button("Ya, Hantar Sekarang" if mode == "terpilih" else "Ya, Simpan", type="primary", key="cf_ya", use_container_width=True):
        msg, err = commit_pilihan(mode, [r[0] for r in yes], [r[0] for r in no], nama_sek)
        if err:
            st.error("Sebahagian gagal dikemas kini: " + " | ".join(err[:2]))
        else:
            _forget_school(school)
            st.session_state["cad_flash"] = msg
            st.rerun()


def commit_pilihan(mode, yes_ids, no_ids, nama_sek=""):
    """mode 'terpilih': tick -> TERPILIH PPD, tidak tick -> SIMPANAN PPD (automatik).
       mode 'simpanan': hanya yang tidak tick -> SIMPANAN PPD."""
    ok1, e1 = ppd_set_status(yes_ids, ST_TERPILIH) if (mode == "terpilih" and yes_ids) else (0, [])
    ok2, e2 = ppd_set_status(no_ids, ST_SIMPANAN) if no_ids else (0, [])
    if mode == "terpilih":
        msg = f"✅ {nama_sek}: {ok1} guru TERPILIH PPD (masuk Jana Keseluruhan), {ok2} guru masuk SENARAI SIMPANAN."
    else:
        msg = f"✅ {nama_sek}: {ok2} guru disimpan sebagai SIMPANAN PPD."
    return msg, e1 + e2


def render_senarai_nama(kod_ppd):
    st.markdown(CN_CSS, unsafe_allow_html=True)
    _banner(f"📝 Senarai Nama Cadangan - PPD {kod_ppd}",
            "Pilih sekolah → tick guru yang dipilih → Hantar. Guru yang tidak ditick masuk Senarai Simpanan secara automatik.")
    _flash()
    df = normalize(get_cadangan_df(kod_ppd=kod_ppd))
    if df.empty:
        st.warning(f"Belum ada cadangan SUP untuk PPD {kod_ppd}")
        return
    smap = sekolah_map(kod_ppd)

    # ---------- 1. pilih sekolah
    labels = {}
    for kod, g in df.groupby("KOD_SEK"):
        work = g[g["STAGE"] != "LOCKED"]
        if work.empty:
            continue
        c = work["STAGE"].value_counts().to_dict()
        labels[kod] = (f"{_nama_sek(kod, g['NAMA_SEK'].iloc[0], smap)} ({kod}) — {len(work)} nama  "
                       f"✅{c.get('TERPILIH', 0)}  📦{c.get('SIMPANAN', 0)}  🆕{c.get('BARU', 0)}")
    if not labels:
        st.info("Semua cadangan sudah diproses (dilantik/ditempatkan).")
        return
    order = sorted(labels, key=lambda k: labels[k])
    school = st.selectbox("🏫 Pilih Sekolah", [""] + order, format_func=lambda k: labels.get(k, "— Pilih sekolah —"), key="cn_sek")
    if not school:
        _counts_strip(df)
        st.info("Pilih sekolah di atas untuk melihat senarai guru yang dicadangkan.")
        return

    rows = df[(df["KOD_SEK"] == school) & (df["STAGE"] != "LOCKED")].reset_index(drop=True)
    nama_sek = _nama_sek(school, rows["NAMA_SEK"].iloc[0] if not rows.empty else "", smap)
    try:
        import ui_theme as _ui
        pusat = ", ".join(_ui.sup_no_pusat_list(school)) or "-"
    except Exception:
        pusat = "-"
    all_ids = rows["id"].tolist()
    sel = _sel_state()
    if school not in sel:                                     # lalai: yang sudah TERPILIH ditick, selebihnya tidak
        sel[school] = set(rows.loc[rows["STAGE"] == "TERPILIH", "id"].tolist())
    chosen = sel[school] & set(all_ids)
    g_n, e_n, total = len(chosen), len(all_ids) - len(chosen), len(all_ids)

    # ---------- 2. kad ringkasan
    c = rows["STAGE"].value_counts().to_dict()
    jw_now = st.session_state.get("cn_jw", JAW_ALL)
    st.markdown(f"""<div class="cn-cards">
      <div class="cn-card"><div class="l">JAWATAN SEMASA</div><div class="v">{esc(jw_now if jw_now != JAW_ALL else 'Semua Jawatan')}</div><div class="s">{rows['JAWATAN'].nunique()} jawatan dicadangkan</div></div>
      <div class="cn-card"><div class="l">SEKOLAH RUJUKAN</div><div class="v">{esc(nama_sek)}</div><div class="s">{esc(school)} • No Pusat: {esc(pusat)}</div></div>
      <div class="cn-card"><div class="l">NISBAH TERPILIH</div><div class="v">{g_n} <span style="font-size:12px;color:#5f6f85;font-weight:600">/ {total} dipilih</span></div><div class="s">{e_n} Simpanan PPD (automatik jika tidak ditick)</div></div>
      <div class="cn-card"><div class="l">STATUS SEMASA (PANGKALAN DATA)</div><div class="v" style="font-size:13px">✅ {c.get('TERPILIH', 0)} &nbsp; 📦 {c.get('SIMPANAN', 0)} &nbsp; 🆕 {c.get('BARU', 0)}</div><div class="s">Terpilih • Simpanan • Belum disemak</div></div>
    </div>""", unsafe_allow_html=True)

    # ---------- 3. carian + tapisan jawatan
    f1, f2, f3 = _cols([3, 2, 1])
    q = f1.text_input("Cari", key="cn_q", placeholder="Cari nama guru, IC...", label_visibility="collapsed").upper().strip()
    jaw_opts = [JAW_ALL] + _jaw_sorted(rows["JAWATAN"].unique())
    jw = f2.selectbox("Jawatan", jaw_opts, key="cn_jw", label_visibility="collapsed")
    f3.button("Reset", key="cn_reset", on_click=_reset_filters, use_container_width=True)
    view = rows
    if q:
        view = view[view["NAMA"].str.upper().str.contains(q, regex=False) | view["IC"].str.contains(q, regex=False)]
    if jw and jw != JAW_ALL:
        view = view[view["JAWATAN"] == jw]
    view = view.reset_index(drop=True)
    view_ids = view["id"].tolist()

    sig = (school, q, jw)
    if st.session_state.get("cn_sig") != sig:
        st.session_state["cn_sig"] = sig
        st.session_state["cn_page"] = 1

    st.markdown(f'<div class="cn-legend"><b>LEGENDA:</b> {_badge("ok", "TERPILIH PPD")} {_badge("sim", "SIMPANAN PPD")} '
                f'<span>Tick = akan dihantar sebagai TERPILIH PPD • Tidak tick = SIMPANAN PPD (automatik)</span></div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 3])
    b1.button("☑ Tanda semua", key="cn_all", on_click=_set_many, args=(school, view_ids, True), use_container_width=True, disabled=not view_ids)
    b2.button("☐ Kosongkan", key="cn_none", on_click=_set_many, args=(school, view_ids, False), use_container_width=True, disabled=not view_ids)
    b3.caption(f"{len(view)} rekod dipaparkan • tindakan Hantar/Simpan melibatkan semua {total} nama sekolah ini")

    # ---------- 4. jadual (tick = TERPILIH, tidak tick = SIMPANAN - status berubah serta-merta)
    SPEC = [0.5, 0.5, 2.9, 1.7, 1.2, 2.0, 2.0, 1.6]
    hc = _cols(SPEC)
    for col, h in zip(hc, ["", "BIL", "NAMA GURU", "IC", "NO PUSAT", "SEKOLAH ASAL", "JAWATAN DICADANG", "STATUS"]):
        col.markdown(f'<div class="cn-head">{h}</div>', unsafe_allow_html=True)
    pages = max(1, -(-len(view) // PER_PAGE))
    page = min(max(1, st.session_state.get("cn_page", 1)), pages)
    chunk = view.iloc[(page - 1) * PER_PAGE: page * PER_PAGE]
    if chunk.empty:
        st.info("Tiada rekod dijumpai. Cuba tukar carian atau tapisan jawatan.")
    for i, (_, r) in enumerate(chunk.iterrows()):
        rid = r["id"]
        on = rid in sel[school]
        cc = _cols(SPEC)
        cc[0].checkbox("pilih", value=on, key=_ck_key(school, rid), on_change=_toggle, args=(school, rid), label_visibility="collapsed")
        cc[1].markdown(f'<span class="cn-sm">{(page - 1) * PER_PAGE + i + 1:02d}</span>', unsafe_allow_html=True)
        cc[2].markdown(f'<div class="cn-nm">{esc(r["NAMA"])}</div>', unsafe_allow_html=True)
        cc[3].markdown(f'<span class="cn-ic">{esc(r["IC"])}</span>', unsafe_allow_html=True)
        cc[4].markdown(f'<span class="cn-sm">{esc(pusat)}</span>', unsafe_allow_html=True)
        cc[5].markdown(f'<span class="cn-sm">{esc(nama_sek)}</span>', unsafe_allow_html=True)
        cc[6].markdown(_badge("jw", esc(r["JAWATAN"])), unsafe_allow_html=True)
        cc[7].markdown(_badge("ok", "TERPILIH PPD") if on else _badge("sim", "SIMPANAN PPD"), unsafe_allow_html=True)
    if pages > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        if p1.button("◀ Sebelum", disabled=page <= 1, key="cn_prev", use_container_width=True):
            st.session_state["cn_page"] = page - 1
            st.rerun()
        p2.markdown(f"<div style='text-align:center;padding-top:6px;color:#5f6f85;font-size:12px'>Menunjukkan {(page-1)*PER_PAGE+1}-{min(page*PER_PAGE, len(view))} dari {len(view)} • Halaman {page} / {pages}</div>", unsafe_allow_html=True)
        if p3.button("Seterus ▶", disabled=page >= pages, key="cn_next", use_container_width=True):
            st.session_state["cn_page"] = page + 1
            st.rerun()

    st.markdown('<div class="cn-guide"><b>Panduan:</b> tick kotak untuk memilih guru sebagai <b>TERPILIH PPD</b>. '
                'Guru yang tidak ditick akan disimpan secara automatik sebagai <b>SIMPANAN PPD</b> apabila butang Hantar ditekan. '
                'Semak IC dan No Pusat sebelum hantar.</div>', unsafe_allow_html=True)

    # ---------- 5. dua butang di bawah
    st.markdown(f'<div class="cn-bar"><span class="k">TERPILIH<span class="n ok">{g_n}</span></span>'
                f'<span class="k">SIMPANAN<span class="n sim">{e_n}</span></span>'
                f'<span class="k" style="font-weight:500">{esc(nama_sek)} • {total} nama</span></div>', unsafe_allow_html=True)
    yes = [(r["id"], r["NAMA"], pusat) for _, r in rows.iterrows() if r["id"] in sel[school]]
    no = [(r["id"], r["NAMA"], pusat) for _, r in rows.iterrows() if r["id"] not in sel[school]]
    x1, x2 = st.columns(2)
    if x1.button(f"Simpan sebagai SIMPANAN PPD ({e_n})", key="cn_btn_sim", disabled=e_n == 0, use_container_width=True):
        dlg_confirm(school, nama_sek, "simpanan", yes, no)
    if x2.button(f"Hantar - TERPILIH PPD ({g_n})", key="cn_btn_hantar", type="primary", disabled=g_n == 0, use_container_width=True):
        dlg_confirm(school, nama_sek, "terpilih", yes, no)


# ------------------------------------------------------------------ SENARAI SIMPANAN
def render_senarai_simpanan(kod_ppd):
    _banner(f"📦 Senarai Simpanan - PPD {kod_ppd}", "Nama yang tidak ditanda semasa Hantar. Tick dan pindahkan semula ke Jana Keseluruhan bila perlu.")
    _flash()
    df = normalize(get_cadangan_df(kod_ppd=kod_ppd))
    sim = df[df["STAGE"] == "SIMPANAN"] if not df.empty else df
    if sim.empty:
        st.info("Senarai simpanan kosong. Nama yang tidak ditanda di 'Senarai Nama Cadangan' akan masuk ke sini.")
        return
    smap = sekolah_map(kod_ppd)
    a, b, c = st.columns(3)
    a.metric("📦 Jumlah Simpanan", len(sim))
    b.metric("🏫 Sekolah", sim["KOD_SEK"].nunique())
    c.metric("👔 Jawatan", sim["JAWATAN"].nunique())
    opts = {"SEMUA": f"Semua Sekolah ({len(sim)})"}
    for kod, g in sim.groupby("KOD_SEK"):
        opts[kod] = f"{_nama_sek(kod, g['NAMA_SEK'].iloc[0], smap)} ({kod}) - {len(g)}"
    pilih = st.selectbox("🏫 Pilihan Sekolah", list(opts.keys()), format_func=lambda k: opts.get(k, k), key="simp_sek")
    jaw = st.multiselect("Jawatan (kosong = semua)", _jaw_sorted(sim["JAWATAN"].unique()), key="simp_jaw")
    view = sim.copy()
    if pilih != "SEMUA":
        view = view[view["KOD_SEK"] == pilih]
    if jaw:
        view = view[view["JAWATAN"].isin(jaw)]
    view = view.reset_index(drop=True)
    if view.empty:
        st.info("Tiada nama untuk tapisan ini.")
        return
    tbl = view[["id", "NAMA", "IC", "KOD_SEK", "JAWATAN", "POSKOD"]].copy()
    tbl.insert(0, "PINDAH", False)
    edited = st.data_editor(
        tbl, hide_index=True, use_container_width=True, key=f"simp_ed_{pilih}_{'-'.join(jaw)}",
        disabled=["id", "NAMA", "IC", "KOD_SEK", "JAWATAN", "POSKOD"],
        column_config={"PINDAH": st.column_config.CheckboxColumn("Pindah ke Jana"), "id": None})
    if not isinstance(edited, pd.DataFrame):
        edited = tbl
    ids = edited.loc[edited["PINDAH"] == True, "id"].tolist()          # noqa: E712
    if st.button(f"➡️ Pindahkan ke Jana Keseluruhan ({len(ids)})", type="primary", disabled=not ids, key="simp_pindah"):
        ok, err = ppd_set_status(ids, ST_TERPILIH)
        if err:
            st.error("Gagal: " + " | ".join(err[:2]))
        else:
            st.session_state["cad_flash"] = f"✅ {ok} nama dipindahkan ke Jana Keseluruhan (TERPILIH)."
            st.rerun()


# ------------------------------------------------------------------ JANA KESELURUHAN: pool + tapis lantik / tidak
def jana_pool_panel(kod_ppd, df_raw):
    """Pulang df cadangan yang layak dijana. Dipanggil dalam menu Jana Keseluruhan."""
    if df_raw is None or df_raw.empty:
        return df_raw
    stages = df_raw.apply(lambda r: stage_of(_pick(r, "STATUS", "status")), axis=1)
    cnt = stages.value_counts().to_dict()
    _flash()
    a, b, c, d = st.columns(4)
    a.metric("✅ Terpilih (dijana)", cnt.get("TERPILIH", 0))
    b.metric("📦 Simpanan (tidak dijana)", cnt.get("SIMPANAN", 0))
    c.metric("🆕 Belum disemak PPD", cnt.get("BARU", 0))
    d.metric("📌 Sudah diproses", cnt.get("LOCKED", 0))
    inc = st.checkbox("Termasuk cadangan yang belum disemak PPD (cara lama)", key="jana_inc_unrev",
                      help="Biasanya biarkan kosong. Hanya calon yang ditanda di Cadangan SUP > Senarai Nama Cadangan akan dijana.")
    keep = stages.isin(["TERPILIH", "LOCKED"]) | ((stages == "BARU") if inc else False)
    pool = df_raw[keep]
    with st.expander("🎯 Tapis: siapa dilantik / tidak dilantik", expanded=False):
        _tapis_editor(df_raw, inc)
    if pool.empty:
        st.info("Tiada calon untuk dijana. Pergi ke **Cadangan SUP > Senarai Nama Cadangan** dan tanda calon, atau pindahkan dari **Senarai Simpanan**.")
    return pool


def _tapis_editor(df_raw, inc):
    nd = normalize(df_raw)
    nd = nd[(nd["STAGE"] == "TERPILIH") | ((nd["STAGE"] == "BARU") if inc else False)]
    if nd.empty:
        st.caption("Tiada calon terpilih untuk ditapis.")
        return
    smap = sekolah_map(st.session_state.get("kod", ""))
    c1, c2 = st.columns(2)
    sek = c1.multiselect("Sekolah (kosong = semua)", sorted(nd["KOD_SEK"].unique()),
                         format_func=lambda k: f"{_nama_sek(k, '', smap)} ({k})", key="jp_sek")
    jaw = c2.multiselect("Jawatan (kosong = semua)", _jaw_sorted(nd["JAWATAN"].unique()), key="jp_jaw")
    v = nd
    if sek:
        v = v[v["KOD_SEK"].isin(sek)]
    if jaw:
        v = v[v["JAWATAN"].isin(jaw)]
    v = v.reset_index(drop=True)
    if v.empty:
        st.caption("Tiada nama untuk tapisan ini.")
        return
    tbl = v[["id", "NAMA", "IC", "KOD_SEK", "JAWATAN", "STATUS"]].copy()
    tbl.insert(0, "LANTIK", True)
    edited = st.data_editor(
        tbl, hide_index=True, use_container_width=True, key=f"jp_ed_{'-'.join(sek)}_{'-'.join(jaw)}_{inc}",
        disabled=["id", "NAMA", "IC", "KOD_SEK", "JAWATAN", "STATUS"],
        column_config={"LANTIK": st.column_config.CheckboxColumn("Lantik", help="Tick = dilantik (dijana). Tidak tick = tidak dilantik (masuk simpanan)."), "id": None})
    if not isinstance(edited, pd.DataFrame):
        edited = tbl
    yes = edited.loc[edited["LANTIK"] == True, "id"].tolist()          # noqa: E712
    no = edited.loc[edited["LANTIK"] != True, "id"].tolist()           # noqa: E712
    if st.button(f"💾 Simpan Pilihan ({len(yes)} dilantik • {len(no)} tidak dilantik)", type="primary", key="jp_simpan"):
        ok1, e1 = ppd_set_status(yes, ST_TERPILIH) if yes else (0, [])
        ok2, e2 = ppd_set_status(no, ST_SIMPANAN) if no else (0, [])
        if e1 or e2:
            st.error("Sebahagian gagal: " + " | ".join((e1 + e2)[:2]))
        else:
            st.session_state["cad_flash"] = f"✅ {ok1} dilantik (kekal dalam Jana), {ok2} tidak dilantik (dialih ke Senarai Simpanan)."
            st.rerun()


# ------------------------------------------------------------------ HASIL JANAAN: pusat tugas & sekolah ditempatkan
def hasil_lookup(df_pusat_raw, kod_ppd):
    """Peta pusat untuk jadual Hasil Janaan.
       pusat[no_pusat] = {nama, kod_sek, nama_sek}  (nama pusat tugas + sekolah tuan rumah/ditempatkan)
       asal[kod_sekolah] = [no_pusat, ...]          (pusat asal sesebuah sekolah)"""
    smap = sekolah_map(kod_ppd)
    pusat, asal = {}, {}
    if df_pusat_raw is not None and not df_pusat_raw.empty:
        for _, r in df_pusat_raw.iterrows():
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
            nama = str(r.get("nama_pusat") or d.get("NAMA_PUSAT") or d.get("NAMA PUSAT") or "").strip()
            ks = str(r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or d.get("KOD_SEKOLAH") or d.get("KOD SEKOLAH") or "").upper().strip()
            pusat[no] = {"nama": nama, "kod_sek": ks, "nama_sek": smap.get(ks) or (nama if ks else "")}
            if ks:
                asal.setdefault(ks, [])
                if no not in asal[ks]:
                    asal[ks].append(no)
    return {"pusat": pusat, "asal": asal, "smap": smap}


def hasil_row(r, pusat_no, lk):
    """Satu baris jadual hasil janaan - lengkap dengan nama pusat tugas dan sekolah ditempatkan."""
    kod_asal = _pick(r, "KOD_SEKOLAH_ASAL", "kod_sekolah_asal").upper()
    nama_asal = _pick(r, "NAMA_SEKOLAH_ASAL", "nama_sekolah_asal") or lk["smap"].get(kod_asal, "")
    no = str(pusat_no or "").upper().strip()
    info = lk["pusat"].get(no, {})
    return {
        "NAMA": _pick(r, "NAMA_GURU", "nama_guru"),
        "NO IC": _pick(r, "IC_GURU", "ic_guru"),
        "JAWATAN": _pick(r, "JAWATAN_CADANGAN", "jawatan_cadangan", "JAWATAN"),
        "SEKOLAH ASAL": kod_asal,
        "NAMA SEKOLAH ASAL": nama_asal,
        "NO PUSAT ASAL": ", ".join(lk["asal"].get(kod_asal, [])) or "-",
        "PUSAT TUGAS": no,
        "NAMA PUSAT TUGAS": info.get("nama", ""),
        "SEKOLAH DITEMPATKAN": info.get("kod_sek", ""),
        "NAMA SEKOLAH DITEMPATKAN": info.get("nama_sek", ""),
        "JANTINA": _pick(r, "JANTINA", "jantina"),
        "TELEFON": _pick(r, "TELEFON_GURU", "telefon_guru"),
    }

def batal_semua_penempatan_ppd(kod_ppd):
    """PPD batal semua penempatan - clear kod_pusat + reset TERPILIH PPD. Scoped ikut PPD."""
    try:
        from spm_core import supa, get_cadangan_df
        res = supa.table("cadangan_sup").select("id,kod_pusat").limit(10000).execute()
        rows = [r for r in (res.data or []) if str(r.get("kod_pusat") or "").strip() not in ("", "None", "null")]
        if not rows:
            return 0, "Tiada penempatan untuk dibatalkan"
        ids = [r["id"] for r in rows if r.get("id") is not None]
        ok, last_err = 0, ""
        for i in range(0, len(ids), 100):
            batch = ids[i:i+100]
            try:
                supa.table("cadangan_sup").update({"kod_pusat": None, "status": "TERPILIH PPD"}).in_("id", batch).execute()
                ok += len(batch)
            except Exception as e:
                last_err = str(e)[:400]
                try:
                    supa.table("cadangan_sup").update({"status": "TERPILIH PPD"}).in_("id", batch).execute()
                    supa.table("cadangan_sup").update({"kod_pusat": ""}).in_("id", batch).execute()
                    ok += len(batch)
                    last_err = ""
                except Exception as e2:
                    last_err = str(e2)[:400]
        try:
            get_cadangan_df.clear()
        except:
            pass
        return ok, last_err
    except Exception as e:
        return 0, str(e)[:400]

def batal_semua_cadangan_ppd(kod_ppd, mode="reset"):
    """PPD batal semua cadangan. mode=reset -> status=HANTAR KE PPD (BELUM HANTAR KE SEKOLAH), mode=delete -> padam."""
    try:
        from spm_core import supa, get_cadangan_df
        res = supa.table("cadangan_sup").select("id").limit(10000).execute()
        rows = res.data or []
        if not rows:
            return 0, "Tiada cadangan"
        ids = [r["id"] for r in rows if r.get("id") is not None]
        if not ids:
            return 0, "Tiada ID"
        ok, last_err = 0, ""
        for i in range(0, len(ids), 100):
            batch = ids[i:i+100]
            try:
                if mode == "delete":
                    supa.table("cadangan_sup").delete().in_("id", batch).execute()
                else:
                    # SAFE: hanya kod_pusat + status - tiada tarikh_jana_surat / no_surat supaya tak error PGRST204
                    # Status HANTAR KE PPD = bermakna BELUM HANTAR KE SEKOLAH / belum dijana surat
                    payload = {"kod_pusat": None, "status": "HANTAR KE PPD"}
                    try:
                        supa.table("cadangan_sup").update(payload).in_("id", batch).execute()
                    except Exception as e:
                        # Fallback jika kod_pusat NULL tak dibenarkan
                        if "kod_pusat" in str(e).lower() or "null" in str(e).lower():
                            supa.table("cadangan_sup").update({"status": "HANTAR KE PPD"}).in_("id", batch).execute()
                            try:
                                supa.table("cadangan_sup").update({"kod_pusat": ""}).in_("id", batch).execute()
                            except:
                                pass
                        else:
                            raise
                ok += len(batch)
            except Exception as e:
                last_err = str(e)[:500]
        try:
            get_cadangan_df.clear()
        except:
            pass
        return ok, last_err
    except Exception as e:
        return 0, str(e)[:500]


# ------------------------------------------------------------------ HASIL JANAAN: status Cukup ikut kuota pusat
def jenis_jawatan(jawatan):
    """Peranan kuota ikut program aktif (SPM: KP/TKP/PENGAWAS/LAIN - tidak sensitif huruf besar-kecil)."""
    from program_config import role_of
    return role_of(jawatan)


def status_kuota_pusat(kp, tkp, peng, kuota_total):
    """Status satu pusat. kuota_total = keperluan pusat (kelas+9) = 1 KP + 1 TKP + (kuota_total-2) pengawas.
    'Cukup' HANYA jika 1 KP, 1 TKP dan pengawas penuh mengikut kuota. Pulang (status, catatan)."""
    try:
        kuota_total = int(kuota_total)
    except Exception:
        kuota_total = 0
    kp, tkp, peng = int(kp), int(tkp), int(peng)
    if kuota_total <= 0:
        return "❓ Tiada kuota", "Isi jumlah calon / kelas pusat di menu Pusat di PPD"
    need_p = max(0, kuota_total - 2)
    if kp + tkp + peng == 0:
        return "❌ Belum Ada", f"Perlu 1 KP, 1 TKP, {need_p} Pengawas"
    kurang, lebih = [], []
    if kp < 1:
        kurang.append("1 KP")
    if tkp < 1:
        kurang.append("1 TKP")
    if peng < need_p:
        kurang.append(f"{need_p - peng} Pengawas")
    if kp > 1:
        lebih.append(f"{kp - 1} KP")
    if tkp > 1:
        lebih.append(f"{tkp - 1} TKP")
    if peng > need_p:
        lebih.append(f"{peng - need_p} Pengawas")
    if kurang:
        return "⚠️ Kurang", "Kurang: " + ", ".join(kurang) + ((" | Lebih: " + ", ".join(lebih)) if lebih else "")
    if lebih:
        return "🔺 Lebih", "Lebih: " + ", ".join(lebih)
    return "✅ Cukup", "Kuota penuh (1 KP, 1 TKP, %d Pengawas)" % need_p
