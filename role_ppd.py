# -*- coding: utf-8 -*-
"""Peranan PPD - bacaan dari cadangan_sup (satu daerah)."""
import spm_core as _core
import ui_theme as _ui
globals().update({k: v for k, v in vars(_core).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(_ui).items() if not k.startswith("__")})
from ppd_cadangan import render_senarai_nama, render_senarai_simpanan, jana_pool_panel, hasil_lookup, hasil_row, jenis_jawatan, normalize as norm_cadangan
from ppd_zon import render_penempatan_zon
from program_config import adalah_spm, kuota_roles, roles as program_roles, status_kuota as status_program, cfg as program_cfg
from ppd_program import render_jana_program
from surat_tools import surat_panel, surat_aset_panel, surat_diagnostik

def _int_atau_none(x):
    try:
        if x is None or (isinstance(x, float) and x != x): return None
        return int(float(str(x)))
    except Exception:
        return None


def perlu_pusat(d, jk):
    """Bil petugas diperlukan sesuatu pusat: nilai manual PPD (data["PERLU_PPD"]) jika ada, jika tidak KELAS + 9."""
    if not adalah_spm():                       # UBBM/UBBI: keperluan pusat = jumlah kuota mengikut bilik ujian
        return sum(kuota_roles(bilik=jk).values())
    ov = _int_atau_none(d.get("PERLU_PPD")) if isinstance(d, dict) else None
    return ov if (ov is not None and ov >= 0) else kira_petugas_dari_kelas(jk)


def selaras_edit_pusat(asal, baru):
    """Peraturan SATU-SATUNYA bagi edit CALON / KELAS / PERLU di Dashboard PPD.
    asal/baru = dict(calon, kelas, perlu). Pulang (calon, kelas, perlu, manual).
      - Ubah CALON sahaja  -> KELAS = CEIL(calon/20), PERLU = KELAS + 9
      - Ubah KELAS         -> PERLU = KELAS + 9
      - Ubah PERLU         -> PERLU manual (disimpan); jika sama dengan KELAS + 9 dianggap auto
    """
    calon, kelas, perlu = int(baru["calon"]), int(baru["kelas"]), int(baru["perlu"])
    c_ubah, k_ubah, p_ubah = calon != int(asal["calon"]), kelas != int(asal["kelas"]), perlu != int(asal["perlu"])
    if c_ubah and not k_ubah:
        kelas = kira_kelas_dari_calon(calon)
        k_ubah = True
    if p_ubah:
        return calon, kelas, perlu, perlu != kira_petugas_dari_kelas(kelas)
    if c_ubah or k_ubah:
        return calon, kelas, kira_petugas_dari_kelas(kelas), False
    return calon, kelas, perlu, perlu != kira_petugas_dari_kelas(kelas)


def simpan_kuota_pusat(no_pusat, calon, kelas, perlu, manual, data_lama):
    """Simpan CALON / KELAS / PERLU satu pusat ke pusat_master. Pulang (berjaya, mesej_ralat)."""
    data = dict(data_lama) if isinstance(data_lama, dict) else {}
    data.update({"JUMLAH_CALON": calon, "JUMLAH_KELAS": kelas, "CALON": calon, "KELAS": kelas})
    if manual:
        data["PERLU_PPD"] = perlu
    else:
        data.pop("PERLU_PPD", None)
    payloads = [{"jumlah_calon": calon, "jumlah_kelas": kelas, "calon": calon, "data": data},
                {"jumlah_calon": calon, "jumlah_kelas": kelas, "data": data},
                {"data": data}]
    ralat = ""
    for payload in payloads:
        for lajur in ("no_pusat", "kod_pusat"):
            try:
                res = supa.table("pusat_master").update(payload).eq(lajur, no_pusat).execute()
                if res.data:
                    return True, ""
            except Exception as e:
                ralat = str(e)
    return False, ralat or "tiada baris dikemas kini (semak no_pusat)"


def kuota_pusat_ppd(df_pusat_raw, kod_ppd):
    """Kuota setiap pusat dalam satu PPD - SUMBER TUNGGAL untuk Dashboard PPD dan Hasil Janaan.
    CALON (pusat_master / data), KELAS (data, jika 0 = CEIL(calon/20)), SEPATUTNYA = PERLU manual PPD jika ada, jika tidak KELAS + 9."""
    def _v(x):   # NaN / None dianggap kosong supaya "or" jatuh ke nilai seterusnya
        try:
            if x is None or (isinstance(x, float) and x != x): return ""
        except Exception:
            pass
        return x
    out = []
    if df_pusat_raw is None or df_pusat_raw.empty:
        return out
    for _, r in df_pusat_raw.iterrows():
        d = r.get("data")
        if isinstance(d, str):          # data disimpan sebagai teks JSON
            try: d = json.loads(d)
            except: d = {}
        if not isinstance(d, dict):
            d = {}
        no_pusat = str(_v(r.get("no_pusat")) or _v(r.get("kod_pusat")) or d.get("NO_PUSAT") or d.get("NO PUSAT") or "").upper().strip()
        if not no_pusat.startswith(kod_ppd.upper()):
            continue
        nama_pusat = str(_v(r.get("nama_pusat")) or d.get("NAMA_PUSAT") or d.get("NAMA PUSAT") or "").upper().strip()
        kod_tuan = str(_v(r.get("kod_sekolah_tuan_rumah")) or _v(r.get("kod_sekolah")) or d.get("KOD_SEKOLAH") or d.get("KOD_SEKOLAH_TUAN_RUMAH") or "").upper().strip()
        j_calon = _v(r.get("jumlah_calon")) or _v(r.get("calon")) or d.get("JUMLAH_CALON") or d.get("CALON") or 0
        j_kelas = _v(r.get("jumlah_kelas")) or d.get("JUMLAH_KELAS") or 0
        try: jc = int(float(str(j_calon) or 0))
        except: jc = 0
        try: jk = int(float(str(j_kelas) or 0))
        except: jk = 0
        if jk == 0:
            jk = kira_kelas_dari_calon(jc)
        out.append({"NO_PUSAT": no_pusat, "NAMA_PUSAT": nama_pusat, "KOD_TUAN_RUMAH": kod_tuan,
                    "CALON": jc, "KELAS": jk, "SEPATUTNYA": perlu_pusat(d, jk),
                    "PERLU_MANUAL": _int_atau_none(d.get("PERLU_PPD")) is not None})
    return out


def status_kuota(ditempatkan, perlu):
    """Status sama seperti Dashboard: 0 = Belum Ada, < perlu = Belum Cukup, >= perlu = Cukup."""
    if ditempatkan == 0:
        return "🔴 Belum Ada"
    if ditempatkan < perlu:
        return "🟡 Belum Cukup"
    return "🟢 Cukup"


def status_kuota_penuh(kp, tkp, peng, perlu, jumlah):
    """'Cukup' HANYA jika 1 KP, 1 TKP dan Pengawas penuh mengikut kuota (kuota pengawas = PERLU - 2).
    Pulang (status, catatan). Label sama seperti Dashboard supaya kiraan kad tidak berubah."""
    perlu = int(perlu or 0)
    if jumlah == 0:
        return "🔴 Belum Ada", (f"Perlu 1 KP, 1 TKP, {max(0, perlu - 2)} Pengawas" if perlu > 0 else "Kuota pusat belum ditetapkan")
    if perlu <= 0:
        return "🟡 Belum Cukup", "Kuota pusat belum ditetapkan (isi calon / kelas / perlu di Dashboard)"
    need_p = max(0, perlu - 2)
    kurang = []
    if kp < 1:
        kurang.append("1 KP")
    if tkp < 1:
        kurang.append("1 TKP")
    if peng < need_p:
        kurang.append(f"{need_p - peng} Pengawas")
    lebih = []
    if kp > 1:
        lebih.append(f"{kp - 1} KP")
    if tkp > 1:
        lebih.append(f"{tkp - 1} TKP")
    if peng > need_p:
        lebih.append(f"{peng - need_p} Pengawas")
    if kurang:
        return "🟡 Belum Cukup", "Kurang: " + ", ".join(kurang) + ((" | Lebih: " + ", ".join(lebih)) if lebih else "")
    return "🟢 Cukup", ("Kuota penuh" + ((" | Lebih: " + ", ".join(lebih)) if lebih else ""))


def render_ppd():
    kod_ppd = st.session_state.kod
    if SCOPE["ppd"] and kod_ppd != SCOPE["ppd"]:
        st.session_state.clear(); st.rerun()
    MENU_PPD = [('dashboard', '📊 Dashboard PPD'),
                ('sekolah', '🏫 Sekolah dalam PPD'),
                ('pusat', '🏫 Pusat di PPD'),
                ('cadangan', '📋 Cadangan SUP'),
                ('selenggara', '🔐 Selenggara Bilik Kebal'),
                ('jana', '🚀 Jana Keseluruhan'),
                ('manual', '📌 Penempatan Manual'),
                ('zon', '🗺️ Penempatan Zon'),
                ('hasil', '📋 Hasil Janaan'),
                ('kelulusan', '✅ Kelulusan'),
                ('semakan', '🔍 Semakan Lantikan'),
                ('jana_surat', '📄 Janaan Surat Lantikan'),
                ('batal', '🗑️ Batal Semua'),
                ('export', '📥 Export'),
                ('keluar', '🚪 Log Keluar')]
    shell_header_ppd(kod_ppd)
    menu, fly_cur, col_main = shell_layout("ppd_menu_sel", MENU_PPD, FLY_PPD, None, "fly_ppd")

    with col_main:
        if menu == "keluar":
            st.session_state.clear()
            st.rerun()

        elif menu == "dashboard":

            show_flash()
            try:
                # Load data
                df_pusat_raw = get_pusat_df()
                df_cad_all = get_cadangan_df(kod_ppd=kod_ppd)
                df_sekolah_raw = supa.table("sekolah_master").select("*").eq("kod_ppd", kod_ppd).limit(2000).execute()
                df_sekolah_list = pd.DataFrame(df_sekolah_raw.data or [])

                # Parse pusat - guna pembantu kongsi kuota_pusat_ppd() (sama dengan Hasil Janaan)
                pusat_list = kuota_pusat_ppd(df_pusat_raw, kod_ppd)
                for _p in pusat_list:
                    no_pusat = _p["NO_PUSAT"]
                    # Kira berapa petugas telah dicadangkan untuk pusat ini
                    dicadangkan = 0
                    if not df_cad_all.empty:
                        for _, c_row in df_cad_all.iterrows():
                            c_no_pusat = str(c_row.get("kod_pusat") or c_row.get("no_pusat_asal") or c_row.get("NO_PUSAT_ASAL") or c_row.get("KOD_PUSAT") or "").upper().strip()
                            c_data = c_row.get("data") or {}
                            if isinstance(c_data, str):
                                try: c_data = json.loads(c_data)
                                except: c_data = {}
                            c_no_pusat2 = str(c_data.get("NO_PUSAT_ASAL") or c_data.get("KOD_PUSAT") or "").upper().strip()
                            if c_no_pusat == no_pusat or c_no_pusat2 == no_pusat:
                                dicadangkan += 1
                    _p["DICADANGKAN"] = dicadangkan

                df_pusat_ppd = pd.DataFrame(pusat_list)

                if df_pusat_ppd.empty:
                    st.warning(f"⚠️ Tiada pusat dijumpai untuk PPD {kod_ppd} - {PPD_MAP.get(kod_ppd, '')}. Sila import pusat di JPN > Pusat Master")
                else:
                    if fly_cur == "ringkasan":
                        # Summary metrics
                        total_pusat = len(df_pusat_ppd)
                        total_calon = int(df_pusat_ppd["CALON"].sum())
                        total_kelas = int(df_pusat_ppd["KELAS"].sum())
                        total_sepatutnya = int(df_pusat_ppd["SEPATUTNYA"].sum())
                        total_dicadangkan = len(df_cad_all) if not df_cad_all.empty else 0
                        kekurangan = total_sepatutnya - total_dicadangkan

                        # Color logic for total
                        if total_dicadangkan == 0:
                            color_total = "#0d47a1"
                            bg_total = "#bbdefb"
                            icon_total = "🔴"
                        elif total_dicadangkan < total_sepatutnya:
                            color_total = "#0d47a1"
                            bg_total = "#e3f2fd"
                            icon_total = "🟡"
                        else:
                            color_total = "#0d47a1"
                            bg_total = "#ffffff"
                            icon_total = "🟢"

                        st.markdown(jpn_status_meter(total_pusat, total_calon, total_kelas, total_sepatutnya, total_dicadangkan, kod_ppd), unsafe_allow_html=True)

                        c1, c2, c3, c4, c5, c6 = st.columns(6)
                        c1.metric("🏫 Pusat", total_pusat)
                        c2.metric("👨‍🎓 Calon", total_calon)
                        c3.metric("🏫 Kelas", total_kelas)
                        c4.metric("📋 Perlu", total_sepatutnya)
                        c5.metric("✅ Dicadangkan", total_dicadangkan)
                        c6.metric("⚠️ Kurang", kekurangan if kekurangan > 0 else 0, delta=f"{'Cukup' if kekurangan <=0 else f'-{kekurangan}'}", delta_color="normal" if kekurangan <=0 else "inverse")

                    if fly_cur == "status":
                        st.markdown("---")
                        st.markdown("### 📍 Senarai Pusat Peperiksaan - Status Petugas (PPD Boleh Edit)")
                        st.caption("🔴 Merah = Belum Ada (0) | 🟡 Kuning = Belum Cukup (< sepatutnya) | 🟢 Hijau = Cukup / Lebih (>= sepatutnya) | ✏️ PPD boleh edit BIL CALON, KELAS, PERLU ikut keperluan")
                        st.info("💡 **Cara Edit:** Klik pada angka CALON / KELAS / PERLU dalam table di bawah, tukar ikut keperluan, kemudian tekan **💾 Simpan Perubahan**")

                    # Build editable table
                    # Prepare data for data_editor with BIL, editable columns
                    editable_rows = []
                    for idx, p in enumerate(df_pusat_ppd.sort_values("NO_PUSAT").iterrows()):
                        p_data = p[1]
                        no_p = p_data["NO_PUSAT"]
                        dic = p_data["DICADANGKAN"]
                        sep = p_data["SEPATUTNYA"]

                        if dic == 0:
                            status_icon = "🔴"
                            status_text = "Belum Ada"
                        elif dic < sep:
                            status_icon = "🟡"
                            status_text = f"Belum Cukup"
                        else:
                            status_icon = "🟢"
                            status_text = f"Cukup"

                        editable_rows.append({
                            "BIL": idx + 1,
                            "NO_PUSAT": no_p,
                            "NAMA_PUSAT": p_data["NAMA_PUSAT"][:35],
                            "KOD_TUAN": p_data["KOD_TUAN_RUMAH"],
                            "BIL_CALON": p_data["CALON"],
                            "KELAS": p_data["KELAS"],
                            "PERLU_K9": sep,
                            "DICADANGKAN": dic,
                            "STATUS": f"{status_icon} {status_text}",
                            "KEKURANGAN": max(0, sep - dic),
                            "MANUAL": bool(p_data.get("PERLU_MANUAL", False))
                        })

                    df_editable = pd.DataFrame(editable_rows)

                    if fly_cur == "status":
                        # Data editor - PPD boleh edit BIL_CALON, KELAS, PERLU_K9
                        st.markdown("#### ✏️ Edit Data Pusat (PPD)")
                        edited_df = st.data_editor(
                            df_editable.drop(columns=["MANUAL"]),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "BIL": st.column_config.NumberColumn("BIL", width="small", disabled=True),
                                "NO_PUSAT": st.column_config.TextColumn("NO PUSAT", width="medium", disabled=True),
                                "NAMA_PUSAT": st.column_config.TextColumn("NAMA PUSAT", width="large", disabled=True),
                                "KOD_TUAN": st.column_config.TextColumn("KOD TUAN RUMAH", width="medium", disabled=True),
                                "BIL_CALON": st.column_config.NumberColumn("BIL CALON", help="PPD boleh edit ikut keperluan sebenar", min_value=0, max_value=500, step=1, required=True),
                                "KELAS": st.column_config.NumberColumn("KELAS", help="Auto: CEIL(Calon/20), tapi PPD boleh edit", min_value=0, max_value=30, step=1, required=True),
                                "PERLU_K9": st.column_config.NumberColumn("PERLU (K+9)", help="PPD boleh edit ikut keperluan, formula asal Kelas+9", min_value=0, max_value=50, step=1, required=True),
                                "DICADANGKAN": st.column_config.NumberColumn("DICADANGKAN", disabled=True),
                                "STATUS": st.column_config.TextColumn("STATUS", disabled=True),
                                "KEKURANGAN": st.column_config.NumberColumn("KEKURANGAN", help="Auto kira: PERLU - DICADANGKAN", disabled=True)
                            },
                            key=f"ppd_edit_{kod_ppd}_{st.session_state.get(f'ppd_edit_ver_{kod_ppd}', 0)}",
                            num_rows="fixed"
                        )

                        # ===== Selaraskan edit (CALON -> KELAS -> PERLU) & pratonton jumlah keseluruhan =====
                        _asal = df_editable.set_index("NO_PUSAT")
                        _sync, _berubah = [], []
                        for _, _row in edited_df.iterrows():
                            _a = _asal.loc[_row["NO_PUSAT"]]
                            try:
                                _n = selaras_edit_pusat(
                                    {"calon": _a["BIL_CALON"], "kelas": _a["KELAS"], "perlu": _a["PERLU_K9"]},
                                    {"calon": _row["BIL_CALON"], "kelas": _row["KELAS"], "perlu": _row["PERLU_K9"]})
                            except Exception:
                                _n = (int(_a["BIL_CALON"]), int(_a["KELAS"]), int(_a["PERLU_K9"]), False)
                            _sync.append(_n)
                            if (_n[0], _n[1], _n[2]) != (int(_a["BIL_CALON"]), int(_a["KELAS"]), int(_a["PERLU_K9"])):
                                _berubah.append((_row["NO_PUSAT"], _a, _n))
                        _t_calon, _t_kelas, _t_perlu = sum(x[0] for x in _sync), sum(x[1] for x in _sync), sum(x[2] for x in _sync)
                        _o_calon, _o_kelas, _o_perlu = int(df_editable["BIL_CALON"].sum()), int(df_editable["KELAS"].sum()), int(df_editable["PERLU_K9"].sum())
                        _p1, _p2, _p3, _p4 = st.columns(4)
                        _p1.metric("📝 Pusat diedit", len(_berubah))
                        _p2.metric("👨‍🎓 Jumlah Calon", _t_calon, delta=_t_calon - _o_calon if _berubah else None)
                        _p3.metric("🏫 Jumlah Kelas", _t_kelas, delta=_t_kelas - _o_kelas if _berubah else None)
                        _p4.metric("📋 Jumlah Perlu (Keseluruhan)", _t_perlu, delta=_t_perlu - _o_perlu if _berubah else None)
                        if _berubah:
                            st.info("💡 Peraturan: ubah **CALON** → KELAS = CEIL(calon/20) & PERLU = KELAS+9 | ubah **KELAS** → PERLU = KELAS+9 | "
                                    "ubah **PERLU** → disimpan sebagai nilai manual. Jumlah di atas ialah **pratonton** - tekan **💾 Simpan** untuk menyimpan.")
                        _n_manual = int(df_pusat_ppd["PERLU_MANUAL"].sum()) if "PERLU_MANUAL" in df_pusat_ppd.columns else 0
                        if _n_manual:
                            st.caption(f"✏️ {_n_manual} pusat menggunakan PERLU manual (bukan KELAS+9). Guna 🔄 Reset Auto untuk kembali ke formula.")

                        col_save, col_reset, col_info = st.columns([1, 1, 2])
                        with col_save:
                            if st.button("💾 Simpan Perubahan Pusat", type="primary", use_container_width=True, key=f"save_pusat_{kod_ppd}", disabled=not _berubah):
                                _ok, _gagal = 0, []
                                _raw_map = {}
                                for _, _r in df_pusat_raw.iterrows():
                                    _d = _r.get("data")
                                    if isinstance(_d, str):
                                        try: _d = json.loads(_d)
                                        except Exception: _d = {}
                                    if not isinstance(_d, dict): _d = {}
                                    _k = str(_r.get("no_pusat") or _r.get("kod_pusat") or _d.get("NO_PUSAT") or "").upper().strip()
                                    _raw_map[_k] = _d
                                for _no, _a, _n in _berubah:
                                    _res, _err = simpan_kuota_pusat(_no, _n[0], _n[1], _n[2], _n[3], _raw_map.get(_no, {}))
                                    if _res: _ok += 1
                                    else: _gagal.append(f"{_no}: {_err}")
                                st.cache_data.clear()      # data pusat di-cache 120s - kosongkan supaya jumlah keseluruhan terus berubah
                                st.session_state[f"ppd_edit_ver_{kod_ppd}"] = st.session_state.get(f"ppd_edit_ver_{kod_ppd}", 0) + 1
                                if _ok:
                                    flash("success", f"✅ {_ok} pusat disimpan. Jumlah Perlu keseluruhan kini {_t_perlu}.")
                                for _g in _gagal:
                                    flash("error", f"Gagal simpan {_g}")
                                st.rerun()

                        with col_reset:
                            _sah_reset = st.checkbox("Sahkan reset semua pusat", key=f"sah_reset_pusat_{kod_ppd}")
                            if st.button("🔄 Reset Auto (Kira Semula)", use_container_width=True, key=f"reset_auto_{kod_ppd}", disabled=not _sah_reset):
                                _ok = 0
                                for _, _r in df_pusat_raw.iterrows():
                                    _d = _r.get("data")
                                    if isinstance(_d, str):
                                        try: _d = json.loads(_d)
                                        except Exception: _d = {}
                                    if not isinstance(_d, dict): _d = {}
                                    _k = str(_r.get("no_pusat") or _r.get("kod_pusat") or _d.get("NO_PUSAT") or "").upper().strip()
                                    if not _k.startswith(kod_ppd.upper()): continue
                                    _c = _int_atau_none(_r.get("jumlah_calon")) or _int_atau_none(_r.get("calon")) or _int_atau_none(_d.get("JUMLAH_CALON")) or 0
                                    _kl = kira_kelas_dari_calon(_c)
                                    _res, _err = simpan_kuota_pusat(_k, _c, _kl, kira_petugas_dari_kelas(_kl), False, _d)
                                    if _res: _ok += 1
                                st.cache_data.clear()
                                st.session_state[f"ppd_edit_ver_{kod_ppd}"] = st.session_state.get(f"ppd_edit_ver_{kod_ppd}", 0) + 1
                                flash("success", f"🔄 {_ok} pusat dikira semula: KELAS = CEIL(CALON/20), PERLU = KELAS+9.")
                                st.rerun()

                        with col_info:
                            st.caption(f"Total: {len(edited_df)} pusat | Boleh edit CALON, KELAS, PERLU")

                    if fly_cur == "berwarna":
                        st.markdown("---")

                        # Also show colored HTML table for quick view
                        st.markdown("#### 📊 Paparan Status Berwarna")
                        # Create HTML table with colors
                        html_table = """
                    <style>
                    .ppd-table {width:100%; border-collapse:collapse; font-size:13px; background:white;}
                    .ppd-table th {background:#0d47a1; color:white; padding:0 8px; height:40px; text-align:left; font-weight:700; position:sticky; top:0; z-index:2; white-space:nowrap;}
                    .ppd-scroll {max-height:480px; overflow-y:auto; overflow-x:auto; border:2px solid #90caf9; border-radius:6px; background:white;}
                    .ppd-table td {padding:0 8px; height:44px; border-bottom:1px solid #e0e0e0; background:white; color:#0d47a1; white-space:nowrap;}
                    .ppd-table tr:hover td {background:#f5f5f5 !important;}
                    .badge-merah {background:#0d47a1 !important; color:#ffffff !important; padding:4px 8px; border-radius:12px; font-weight:700; border:2px solid #0d47a1;}
                    .badge-kuning {background:#bbdefb !important; color:#0d47a1 !important; padding:4px 8px; border-radius:12px; font-weight:700; border:2px solid #0d47a1;}
                    .badge-hijau {background:#ffffff !important; color:#0d47a1 !important; padding:4px 8px; border-radius:12px; font-weight:700; border:2px solid #0d47a1;}
                    .edit-hint {background:#e3f2fd; border-left:4px solid #1976d2; padding:6px 10px; margin:4px 0; font-size:11px;}
                    </style>
                    <div class="edit-hint">✏️ <b>PPD boleh edit:</b> BIL CALON, KELAS, PERLU (K+9) ikut keperluan sebenar - klik angka dalam table atas untuk edit &nbsp;|&nbsp; 📜 Papar 10 baris - skrol ke bawah untuk lihat selebihnya</div>
                    <div class="ppd-scroll"><table class="ppd-table">
                    <tr><th>BIL</th><th>NO PUSAT</th><th>NAMA PUSAT</th><th>KOD TUAN</th><th>BIL CALON ✏️</th><th>KELAS ✏️</th><th>PERLU (K+9) ✏️</th><th>DICADANG</th><th>STATUS</th></tr>
                    """

                        for _, r in (edited_df if 'edited_df' in locals() else df_editable).iterrows():
                            dic = r["DICADANGKAN"]
                            sep = r["PERLU_K9"]
                            if dic == 0:
                                badge_class = "badge-merah"
                                badge_text = f"🔴 {dic}"
                                status_badge = f'<span class="{badge_class}">🔴 Belum Ada</span>'
                            elif dic < sep:
                                badge_class = "badge-kuning"
                                badge_text = f"🟡 {dic}"
                                status_badge = f'<span class="{badge_class}">🟡 Belum Cukup</span>'
                            else:
                                badge_class = "badge-hijau"
                                badge_text = f"🟢 {dic}"
                                status_badge = f'<span class="{badge_class}">🟢 Cukup</span>'

                            html_table += f"<tr><td><b>{r['BIL']}</b></td><td><b>{r['NO_PUSAT']}</b></td><td>{r['NAMA_PUSAT']}</td><td>{r['KOD_TUAN']}</td><td style='text-align:center; background:#e3f2fd; font-weight:700; border:1px dashed #0d47a1;'>{r['BIL_CALON']}</td><td style='text-align:center; background:#e3f2fd; font-weight:700; border:1px dashed #1976d2;'>{r['KELAS']}</td><td style='text-align:center; background:#bbdefb; font-weight:700; border:1px dashed #0d47a1;'>{r['PERLU_K9']}</td><td style='text-align:center;'><span class='{badge_class}'>{badge_text}</span></td><td>{status_badge}</td></tr>"

                        html_table += "</table></div>"

                        st.markdown(html_table, unsafe_allow_html=True)

                    if fly_cur == "sekolah":
                        st.markdown("---")

                        # Export
                        with st.expander("📊 Export Data", expanded=False):
                            st.dataframe(df_pusat_ppd.sort_values("NO_PUSAT"), use_container_width=True, hide_index=True)
                            st.download_button(f"📥 Export Dashboard PPD {kod_ppd} (Excel)", to_excel(df_pusat_ppd), file_name=f"Dashboard_PPD_{kod_ppd}_{datetime.date.today()}.xlsx", use_container_width=True)

                        # Senarai sekolah dalam PPD
                        st.markdown("---")
                        st.markdown(f"### 🏫 Senarai Sekolah dalam PPD {kod_ppd} ({len(df_sekolah_list)} sekolah)")
                        if not df_sekolah_list.empty:
                            # Kira cadangan per sekolah
                            sekolah_cad_count = {}
                            if not df_cad_all.empty:
                                for _, c_row in df_cad_all.iterrows():
                                    k_sek = str(c_row.get("kod_sekolah") or c_row.get("kod_sekolah_asal") or "").upper().strip()
                                    if k_sek:
                                        sekolah_cad_count[k_sek] = sekolah_cad_count.get(k_sek, 0) + 1

                            sekolah_rows = []
                            for _, s in df_sekolah_list.iterrows():
                                k_sek = str(s.get("kod_sekolah") or s.get("KOD_SEKOLAH") or "").upper().strip()
                                n_sek = str(s.get("nama_sekolah") or s.get("NAMA_SEKOLAH") or "").upper().strip()
                                cad = sekolah_cad_count.get(k_sek, 0)

                                if cad == 0:
                                    s_icon = "🔴"
                                    s_status = "Belum Cadang"
                                elif cad < 5:
                                    s_icon = "🟡"
                                    s_status = f"{cad} dicadang"
                                else:
                                    s_icon = "🟢"
                                    s_status = f"{cad} dicadang"

                                sekolah_rows.append({"Logo": "🏫", "KOD_SEKOLAH": k_sek, "NAMA_SEKOLAH": n_sek[:35], "DICADANGKAN": cad, "STATUS": f"{s_icon} {s_status}"})

                            df_sekolah_display = pd.DataFrame(sekolah_rows).sort_values("KOD_SEKOLAH")
                            st.dataframe(df_sekolah_display, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"Tiada sekolah dijumpai untuk PPD {kod_ppd}")

            except Exception as e:
                st.error(f"Error dashboard PPD: {e}")
                # Fallback simple
                try:
                    cnt_sekolah = supa.table("sekolah_master").select("kod_sekolah", count="exact").eq("kod_ppd", kod_ppd).execute()
                    cnt_cadang = supa.table("cadangan_sup").select("id", count="exact").eq("kod_ppd", kod_ppd).execute()
                    c1, c2 = st.columns(2)
                    c1.metric("Sekolah", cnt_sekolah.count)
                    c2.metric("Cadangan", cnt_cadang.count)
                except Exception as e2:
                    st.error(f"Fallback error: {e2}")

        elif menu == "sekolah":
            st.header(f"Senarai Sekolah PPD {kod_ppd}")
            try:
                res = supa.table("sekolah_master").select("*").eq("kod_ppd", kod_ppd).limit(2000).execute()
                df = pd.DataFrame(res.data or [])
                st.dataframe(df, use_container_width=True)
                st.download_button("Export Sekolah", to_excel(df), file_name=f"sekolah_{kod_ppd}.xlsx")
            except Exception as e:
                st.error(f"Error baca sekolah: {e}")

        elif menu == "pusat":
            st.header(f"Pusat di PPD {kod_ppd} - {PPD_MAP.get(kod_ppd, '')} - Total Calon & Poskod Pusat")
            st.caption("Filter BETUL ikut NO_PUSAT prefix BA=Klang sahaja | PPD boleh tambah/edit POSKOD PUSAT untuk jana ikut poskod terdekat")
            df_pusat_raw = get_pusat_df()
            if df_pusat_raw.empty:
                st.info("pusat_master kosong")
            else:
                rows = []
                for _, r in df_pusat_raw.iterrows():
                    d = r.get("data") if isinstance(r.get("data"), dict) else {}
                    if isinstance(d, str):
                        try: d = json.loads(d)
                        except: d = {}
                    no_pusat = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                    nama = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                    j_calon = r.get("jumlah_calon") or r.get("calon") or d.get("JUMLAH_CALON") or 0
                    j_kelas = r.get("jumlah_kelas") or r.get("bilik") or d.get("JUMLAH_KELAS") or 0
                    try: jc = int(float(str(j_calon) or 0))
                    except: jc = 0
                    try: jk = int(float(str(j_kelas) or 0))
                    except: jk = kira_kelas_dari_calon(jc)
                    if jk == 0: jk = kira_kelas_dari_calon(jc)
                    _pk9 = perlu_pusat(d, jk)     # ikut edit PPD (PERLU manual) jika ada
                    rows.append({"NO_PUSAT": no_pusat, "NAMA_PUSAT": nama, "JUMLAH_CALON": jc, "JUMLAH_KELAS": jk, "PETUGAS_K9": _pk9, "SEKOLAH_PERLU": _pk9 + 3})

                df_all = pd.DataFrame(rows)
                df_f = df_all[df_all["NO_PUSAT"].str.startswith(kod_ppd.upper())].copy() if not df_all.empty else df_all
                if df_f.empty:
                    st.warning(f"Tiada pusat dengan prefix {kod_ppd}")
                else:
                    if fly_cur == "senarai":
                        st.success(f"Jumpa {len(df_f)} pusat di PPD {kod_ppd} - {PPD_MAP.get(kod_ppd, '')}")
                        st.dataframe(df_f.sort_values("NO_PUSAT"), use_container_width=True, hide_index=True)
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Jumlah Pusat", len(df_f))
                        c2.metric("Total Calon", int(df_f["JUMLAH_CALON"].sum()))
                        c3.metric("Total Kelas", int(df_f["JUMLAH_KELAS"].sum()))
                        c4.metric("Total Perlu", int(df_f["SEKOLAH_PERLU"].sum()))
                        st.download_button(f"Export Pusat {kod_ppd}", to_excel(df_f), file_name=f"pusat_{kod_ppd}.xlsx", use_container_width=True)

                    if fly_cur == "poskod":
                        st.markdown("---")
                        st.markdown("### 📮 Tambah/Edit Poskod Pusat (Untuk Jana Poskod Terdekat)")
                        st.info("💡 Poskod Pusat diperlukan untuk sistem kira jarak poskod rumah guru vs pusat. Kalau kosong, sistem akan guna poskod sekolah tuan rumah sebagai fallback.")
                        with st.expander("✏️ Edit Poskod Pusat - Klik untuk buka", expanded=False):
                            # Build editable table for poskod
                            poskod_rows = []
                            for _, r in df_f.iterrows():
                                no_p = r["NO_PUSAT"]
                                # Try get existing poskod
                                existing_poskod = ""
                                try:
                                    df_raw = df_pusat_raw
                                    for _, pr in df_raw.iterrows():
                                        d = pr.get("data") if isinstance(pr.get("data"), dict) else {}
                                        if isinstance(d, str):
                                            try: d = json.loads(d)
                                            except: d = {}
                                        no_check = str(pr.get("no_pusat") or pr.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                                        if no_check == no_p:
                                            existing_poskod = str(pr.get("poskod") or d.get("POSKOD") or d.get("POSKOD_PUSAT") or "").strip()
                                            break
                                except:
                                    pass
                                poskod_rows.append({"NO_PUSAT": no_p, "NAMA_PUSAT": r["NAMA_PUSAT"][:30], "POSKOD_SEKARANG": existing_poskod, "POSKOD_BARU": existing_poskod})
                            df_poskod_edit = pd.DataFrame(poskod_rows)
                            edited_poskod = st.data_editor(
                                df_poskod_edit,
                                column_config={
                                    "NO_PUSAT": st.column_config.TextColumn("NO_PUSAT", disabled=True),
                                    "NAMA_PUSAT": st.column_config.TextColumn("NAMA PUSAT", disabled=True),
                                    "POSKOD_SEKARANG": st.column_config.TextColumn("Sekarang", disabled=True),
                                    "POSKOD_BARU": st.column_config.TextColumn("Poskod Baru (5 digit)", help="Contoh: 41000 untuk Klang"),
                                },
                                use_container_width=True,
                                hide_index=True,
                                key="edit_poskod_pusat"
                            )
                            if st.button("💾 Simpan Poskod Pusat", type="primary", use_container_width=True, key="simpan_poskod_pusat"):
                                try:
                                    berjaya_poskod = 0
                                    for _, row_edit in edited_poskod.iterrows():
                                        no_p = row_edit["NO_PUSAT"]
                                        pk_baru = str(row_edit["POSKOD_BARU"]).strip()
                                        if not pk_baru or pk_baru == row_edit["POSKOD_SEKARANG"]:
                                            continue
                                        # Update pusat_master
                                        try:
                                            # Get existing record
                                            res = supa.table("pusat_master").select("*").eq("no_pusat", no_p).limit(1).execute()
                                            if not res.data:
                                                res = supa.table("pusat_master").select("*").eq("kod_pusat", no_p).limit(1).execute()
                                            if res.data:
                                                rec = res.data[0]
                                                rec_id = rec.get("id")
                                                d = rec.get("data") or {}
                                                if isinstance(d, str):
                                                    try: d = json.loads(d)
                                                    except: d = {}
                                                d["POSKOD"] = pk_baru
                                                d["POSKOD_PUSAT"] = pk_baru
                                                # Try update with poskod column if exists, else only data
                                                try:
                                                    supa.table("pusat_master").update({"poskod": pk_baru, "data": d}).eq("id", rec_id).execute()
                                                except:
                                                    supa.table("pusat_master").update({"data": d}).eq("id", rec_id).execute()
                                                berjaya_poskod += 1
                                        except Exception as e:
                                            st.warning(f"{no_p}: {e}")
                                    st.success(f"✅ Berjaya kemaskini {berjaya_poskod} poskod pusat!")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error simpan poskod: {e}")



        elif menu == "jana" and not adalah_spm():
            render_jana_program(kod_ppd, "daerah")

        elif menu == "manual" and not adalah_spm():
            st.info("Penempatan Manual belum disesuaikan untuk program ini. Guna Jana Keseluruhan atau Penempatan Zon (mengikut kuota bilik ujian).")

        elif menu == "jana":
            st.markdown(f"""
            <div style="background: #0d47a1; padding:20px; border-radius:12px; color:white; border: 2px solid #002171; margin-bottom:20px;">
                <div style="display:flex; align-items:center; gap:15px;">
                    <div style="font-size:48px;">🚀</div>
                    <div>
                        <h2 style="margin:0; color:white; font-size:24px;">Jana Keseluruhan - PPD {kod_ppd} - {PPD_MAP.get(kod_ppd, '')}</h2>
                        <p style="margin:5px 0 0 0; color:#bbdefb; font-size:13px;">Pilih: Jana Keseluruhan (Auto Poskod Terdekat) atau Jana Mengikut Jawatan - Kekal Max 3</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            df_pusat_raw = get_pusat_df()
            df_cad_all = get_cadangan_df(kod_ppd=kod_ppd)
            df_cad_all = jana_pool_panel(kod_ppd, df_cad_all)   # hanya calon TERPILIH PPD (+ yang sudah diproses)

            if df_pusat_raw.empty:
                st.warning("⚠️ Tiada pusat_master")
                st.stop()
            if df_cad_all.empty:
                st.warning("⚠️ Belum ada calon untuk dijana. Lihat arahan di atas.")
                st.stop()

            # Parse pusat with poskod
            rows = []
            for _, r in df_pusat_raw.iterrows():
                d = r.get("data") if isinstance(r.get("data"), dict) else {}
                if isinstance(d, str):
                    try: d = json.loads(d)
                    except: d = {}
                no_pusat = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                if not no_pusat.startswith(kod_ppd.upper()): continue
                nama = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                kod_sek_tuan = str(r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or d.get("KOD_SEKOLAH") or "").upper().strip()
                j_calon = r.get("jumlah_calon") or d.get("JUMLAH_CALON") or 0
                j_kelas = r.get("jumlah_kelas") or d.get("JUMLAH_KELAS") or 0
                poskod_pusat = str(r.get("poskod") or d.get("POSKOD") or d.get("POSKOD_PUSAT") or "").strip()
                try: jc = int(float(str(j_calon) or 0))
                except: jc = 0
                try: jk = int(float(str(j_kelas) or 0))
                except: jk = kira_kelas_dari_calon(jc)
                if jk == 0: jk = kira_kelas_dari_calon(jc)
                rows.append({"NO_PUSAT": no_pusat, "NAMA_PUSAT": nama, "KOD_SEKOLAH_TUAN_RUMAH": kod_sek_tuan, "JUMLAH_CALON": jc, "JUMLAH_KELAS": jk, "PETUGAS": perlu_pusat(d, jk), "POSKOD_PUSAT": poskod_pusat})
            df_pusat_ppd = pd.DataFrame(rows)

            if df_pusat_ppd.empty:
                st.warning(f"Tiada pusat dengan prefix {kod_ppd}")
                st.stop()

            def get_poskod_guru(row):
                return str(row.get("POSKOD_RUMAH") or row.get("poskod_rumah") or "").strip()
            def get_poskod_pusat_val(no_pusat):
                r = df_pusat_ppd[df_pusat_ppd["NO_PUSAT"]==no_pusat]
                if not r.empty:
                    pk = str(r.iloc[0].get("POSKOD_PUSAT") or "").strip()
                    if pk and pk.lower() not in ("none","nan",""):
                        return pk
                try:
                    kod_tuan = str(r.iloc[0].get("KOD_SEKOLAH_TUAN_RUMAH") or "").strip() if not r.empty else ""
                    if kod_tuan:
                        res_sek = supa.table("sekolah_master").select("*").eq("kod_sekolah", kod_tuan).limit(1).execute()
                        if res_sek.data:
                            d = res_sek.data[0].get("data") or {}
                            if isinstance(d, str):
                                try: d = json.loads(d)
                                except: d = {}
                            pk = str(res_sek.data[0].get("poskod") or d.get("POSKOD") or "").strip()
                            if pk: return pk
                except: pass
                return ""
            def poskod_distance(pk_guru, pk_pusat):
                try:
                    g = int(re.sub(r"\D","", pk_guru)[:5] or 0)
                    p = int(re.sub(r"\D","", pk_pusat)[:5] or 0)
                    if g==0 or p==0: return 99999
                    return abs(g-p)
                except: return 99999

            # ===== SUB MENU UTAMA =====
            sub_jana = "🌍 Jana Keseluruhan (Auto Poskod Terdekat)" if fly_cur == "auto" else "👑 Jana Mengikut Jawatan"

            # ===== TAB 1: JANA KESELURUHAN AUTO POSKOD =====
            if "Jana Keseluruhan" in sub_jana:
                st.markdown("### 🌍 Jana Keseluruhan - Auto Poskod Terdekat")
                st.info("Baca POSKOD RUMAH guru vs POSKOD PUSAT, pusat paling dekat dulu. Kalau penuh, auto ke pusat kedua terdekat. Kekal Max 3 & elak sekolah sendiri. Penyelia Kawasan TIDAK termasuk di sini - lantik di Selenggara Bilik Kebal.")

                # FIX FINAL: Jana Keseluruhan Auto HANYA untuk 3 jawatan biasa sahaja - Khas langsung tak masuk
                # Hanya benarkan: Ketua Pengawas, Timbalan Ketua Pengawas, Pengawas Peperiksaan (exact)
                # Semua Khas (Juru Tulis, Juru Baca, Hospital, Pengiring, Pengemas, Penyelia) dikeluarkan terus - hanya di Penempatan Manual sahaja
                def is_auto_jawatan(r):
                    j = str(r.get("JAWATAN_CADANGAN") or r.get("jawatan_cadangan") or r.get("JAWATAN") or "").upper().strip()
                    # Hanya 3 ini sahaja yang boleh auto
                    if "KETUA PENGAWAS" in j and "TIMBALAN" not in j and "HOSPITAL" not in j:
                        return True
                    if "TIMBALAN KETUA PENGAWAS" in j or ("TIMBALAN" in j and "KETUA" in j and "HOSPITAL" not in j):
                        return True
                    if j == "PENGAWAS PEPERIKSAAN" or (j.startswith("PENGAWAS") and "HOSPITAL" not in j and "PENGIRING" not in j and "KHAS" not in j):
                        # Pengawas Peperiksaan biasa sahaja
                        if "HOSPITAL" in j or "PENGIRING" in j or "JURU" in j or "PENGEMAS" in j or "PENYELIA" in j or "SELENGGARA" in j:
                            return False
                        return True
                    # Semua lain (Juru Tulis, Juru Baca, Hospital, Pengiring, Pengemas, Penyelia, Selenggara) = False - tak masuk auto
                    return False

                df_cad_all_auto = df_cad_all[df_cad_all.apply(is_auto_jawatan, axis=1)].copy() if not df_cad_all.empty else df_cad_all.copy()
                # Info
                try:
                    khas_count = len(df_cad_all) - len(df_cad_all_auto)
                    if khas_count > 0:
                        st.info(f"ℹ️ Jana Keseluruhan Auto: {len(df_cad_all_auto)} petugas biasa (KP/TKP/Pengawas) akan dijana auto. {khas_count} Pengawas Khas (JT/JB/Hospital/Pengiring/Pengemas/Penyelia) TIDAK termasuk auto - sila guna Jana Ikut Jawatan atau Penempatan Manual")
                except:
                    pass

                cad_per_sekolah = {}
                for _, c in df_cad_all_auto.iterrows():
                    k_sek = str(c.get("KOD_SEKOLAH") or c.get("KOD_SEKOLAH_ASAL") or "").upper().strip()
                    if k_sek: cad_per_sekolah[k_sek] = cad_per_sekolah.get(k_sek, 0) + 1
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("📚 Sekolah Mencadang", len(cad_per_sekolah))
                c2.metric("👨‍🏫 Guru Dicadang", len(df_cad_all))
                c3.metric("🏫 Pusat", len(df_pusat_ppd))
                c4.metric("📋 Perlu Petugas", int(df_pusat_ppd["PETUGAS"].sum()))

                with st.expander(f"📋 Lihat {len(df_cad_all)} Cadangan Dari SUP", expanded=False):
                    cols = [c for c in ["NAMA_GURU","IC_GURU","JANTINA","POSKOD_RUMAH","JAWATAN_CADANGAN","KOD_SEKOLAH_ASAL","STATUS"] if c in df_cad_all.columns]
                    st.dataframe(df_cad_all[cols] if cols else df_cad_all, use_container_width=True, hide_index=True)

                col_jana_all, col_clear = st.columns([3,1])
                with col_jana_all:
                    btn_jana_all = st.button("🌍 JANA KESELURUHAN - Auto Poskod Terdekat (1 KP + 1 TKP + Pengawas)", type="primary", use_container_width=True, key="btn_jana_all_poskod_v3")
                with col_clear:
                    if st.button("🗑️ Clear", use_container_width=True, key="clear_jana_all_v3"):
                        if "jana_all_result" in st.session_state: del st.session_state["jana_all_result"]
                        st.rerun()

                if btn_jana_all or "jana_all_result" in st.session_state:
                    if btn_jana_all:
                        import random
                        assignments = []
                        df_pool_all = df_cad_all.copy()
                        def is_belum(row):
                            kp = str(row.get("kod_pusat") or row.get("KOD_PUSAT") or "").strip()
                            return kp == "" or kp.lower() in ("none","null","nan","nat","-")
                        df_pool = df_pool_all[df_pool_all.apply(is_belum, axis=1)].copy()
                        if df_pool.empty:
                            st.warning("Semua guru telah dilantik!")
                            st.stop()
                        pusat_info_map = {}
                        for _, p in df_pusat_ppd.iterrows():
                            pusat_info_map[p["NO_PUSAT"]] = {"KOD_TUAN": str(p.get("KOD_SEKOLAH_TUAN_RUMAH","") or "").upper().strip(), "NAMA": p.get("NAMA_PUSAT",""), "PETUGAS": int(p.get("PETUGAS",0)), "POSKOD": str(p.get("POSKOD_PUSAT") or "").strip()}
                        df_pool["POSKOD_GURU_NORM"] = df_pool.apply(lambda r: get_poskod_guru(r), axis=1)
                        df_pool_shuffled = df_pool.sample(frac=1, random_state=random.randint(1,100000)).reset_index(drop=True)
                        pusat_sekolah_count = {}
                        pusat_total = {no:0 for no in pusat_info_map.keys()}
                        pusat_kp = {no:0 for no in pusat_info_map.keys()}
                        pusat_tkp = {no:0 for no in pusat_info_map.keys()}
                        used_ic = set()
                        def cari_pusat_terdekat(guru_row):
                            poskod_guru = str(guru_row.get("POSKOD_GURU_NORM") or "")
                            kod_sek_guru = str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper().strip()
                            jarak_list = []
                            for no_pusat, info in pusat_info_map.items():
                                if info["KOD_TUAN"] and kod_sek_guru and info["KOD_TUAN"] == kod_sek_guru: continue
                                if pusat_sekolah_count.get((no_pusat, kod_sek_guru),0) >=3: continue
                                if pusat_total.get(no_pusat,0) >= info["PETUGAS"]: continue
                                jaw = str(guru_row.get("JAWATAN_CADANGAN") or "").upper()
                                if "KETUA PENGAWAS" in jaw and "TIMBALAN" not in jaw:
                                    if pusat_kp.get(no_pusat,0) >=1: continue
                                elif "TIMBALAN" in jaw:
                                    if pusat_tkp.get(no_pusat,0) >=1: continue
                                poskod_pusat_val = get_poskod_pusat_val(no_pusat) or info.get("POSKOD","")
                                jarak = poskod_distance(poskod_guru, poskod_pusat_val)
                                jarak_list.append((jarak, no_pusat))
                            jarak_list.sort(key=lambda x: x[0])
                            return [no for _, no in jarak_list]
                        # KP
                        for _, guru_row in df_pool_shuffled.iterrows():
                            ic = str(guru_row.get("IC_GURU") or "")
                            if ic in used_ic: continue
                            jaw = str(guru_row.get("JAWATAN_CADANGAN") or "").upper()
                            if "KETUA PENGAWAS" not in jaw or "TIMBALAN" in jaw: continue
                            cands = cari_pusat_terdekat(guru_row)
                            if not cands: continue
                            chosen = cands[0]
                            assignments.append({"IC_GURU": ic, "NAMA_GURU": guru_row.get("NAMA_GURU",""), "KOD_SEKOLAH_ASAL": str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper(), "JAWATAN_CADANGAN": guru_row.get("JAWATAN_CADANGAN",""), "POSKOD_RUMAH": guru_row.get("POSKOD_GURU_NORM",""), "NO_PUSAT_TUGAS": chosen, "NAMA_PUSAT_TUGAS": pusat_info_map[chosen]["NAMA"], "id": guru_row.get("id","")})
                            used_ic.add(ic)
                            pusat_sekolah_count[(chosen, str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper())] = pusat_sekolah_count.get((chosen, str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper()),0)+1
                            pusat_total[chosen] +=1
                            pusat_kp[chosen] +=1
                        # TKP
                        for _, guru_row in df_pool_shuffled.iterrows():
                            ic = str(guru_row.get("IC_GURU") or "")
                            if ic in used_ic: continue
                            if "TIMBALAN" not in str(guru_row.get("JAWATAN_CADANGAN") or "").upper(): continue
                            cands = cari_pusat_terdekat(guru_row)
                            if not cands: continue
                            chosen = cands[0]
                            assignments.append({"IC_GURU": ic, "NAMA_GURU": guru_row.get("NAMA_GURU",""), "KOD_SEKOLAH_ASAL": str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper(), "JAWATAN_CADANGAN": guru_row.get("JAWATAN_CADANGAN",""), "POSKOD_RUMAH": guru_row.get("POSKOD_GURU_NORM",""), "NO_PUSAT_TUGAS": chosen, "NAMA_PUSAT_TUGAS": pusat_info_map[chosen]["NAMA"], "id": guru_row.get("id","")})
                            used_ic.add(ic)
                            pusat_sekolah_count[(chosen, str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper())] = pusat_sekolah_count.get((chosen, str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper()),0)+1
                            pusat_total[chosen] +=1
                            pusat_tkp[chosen] +=1
                        # Pengawas - HANYA Pengawas Peperiksaan biasa sahaja - Khas (JT/JB/Hospital/Pengiring/Pengemas/Penyelia) langsung tak masuk auto, hanya Penempatan Manual
                        def is_pengawas_biasa_only(row):
                            j = str(row.get("JAWATAN_CADANGAN") or row.get("jawatan_cadangan") or "").upper().strip()
                            # Hanya Pengawas Peperiksaan exact sahaja
                            if "PENGAWAS PEPERIKSAAN" not in j:
                                return False
                            if any(k in j for k in ["PENYELIA", "JURU", "HOSPITAL", "PENGIRING", "PENGEMAS", "SELENGGARA", "BILIK KEBAL"]):
                                return False
                            return True
                        df_pool_biasa = [r for _, r in df_pool_shuffled.iterrows() if is_pengawas_biasa_only(r)]
                        for guru_row in df_pool_biasa:
                            ic = str(guru_row.get("IC_GURU") or "")
                            if ic in used_ic: continue
                            jaw = str(guru_row.get("JAWATAN_CADANGAN") or "").upper()
                            if "KETUA PENGAWAS" in jaw: continue
                            if "TIMBALAN" in jaw: continue
                            if "PENYELIA" in jaw: continue
                            cands = cari_pusat_terdekat(guru_row)
                            if not cands: continue
                            chosen = cands[0]
                            poskod_guru = str(guru_row.get("POSKOD_GURU_NORM") or "")
                            poskod_pusat_val = get_poskod_pusat_val(chosen) or pusat_info_map[chosen].get("POSKOD","")
                            jarak_val = poskod_distance(poskod_guru, poskod_pusat_val)
                            assignments.append({"IC_GURU": ic, "NAMA_GURU": guru_row.get("NAMA_GURU",""), "KOD_SEKOLAH_ASAL": str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper(), "JAWATAN_CADANGAN": guru_row.get("JAWATAN_CADANGAN",""), "POSKOD_RUMAH": poskod_guru, "POSKOD_PUSAT": poskod_pusat_val, "NO_PUSAT_TUGAS": chosen, "NAMA_PUSAT_TUGAS": pusat_info_map[chosen]["NAMA"], "JARAK": jarak_val, "id": guru_row.get("id","")})
                            used_ic.add(ic)
                            pusat_sekolah_count[(chosen, str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper())] = pusat_sekolah_count.get((chosen, str(guru_row.get("KOD_SEKOLAH_ASAL") or "").upper()),0)+1
                            pusat_total[chosen] +=1
                        st.session_state["jana_all_result"] = assignments
                        st.success(f"✅ Berjaya jana {len(assignments)} guru ikut poskod terdekat!")
                    else:
                        assignments = st.session_state.get("jana_all_result", [])

                    if st.session_state.get("jana_all_result"):
                        df_assign = pd.DataFrame(st.session_state["jana_all_result"])
                        st.dataframe(df_assign, use_container_width=True, hide_index=True)
                        if st.button("💾 Simpan Jana Keseluruhan ke DB", type="primary", use_container_width=True, key="simpan_jana_all_v3"):
                            try:
                                for a in assignments:
                                    if a.get("id"):
                                        supa.table("cadangan_sup").update({"kod_pusat": a.get("NO_PUSAT_TUGAS"), "status": "DILANTIK PPD"}).eq("id", a.get("id")).execute()
                                    else:
                                        supa.table("cadangan_sup").update({"kod_pusat": a.get("NO_PUSAT_TUGAS"), "status": "DILANTIK PPD"}).eq("ic_guru", a.get("IC_GURU")).execute()
                                st.success(f"✅ {len(assignments)} disimpan!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Gagal: {e}")
                        st.download_button("📥 Export", to_excel(df_assign), file_name=f"jana_poskod_{kod_ppd}.xlsx", use_container_width=True)

            # ===== TAB 2: JANA MENGIKUT JAWATAN - FIXED VISIBLE =====
            else:
                st.markdown("### 👑 Jana Mengikut Jawatan")
                st.info("Klik jawatan di bawah, sistem akan paparkan semua guru jawatan tersebut yang BELUM ditempatkan lagi. Kemudian pilih pusat & jana.")

                # Pilihan jawatan - BUTTON style - TANPA Penyelia Kawasan (sebab lantik di Selenggara Bilik Kebal)
                st.markdown("#### Pilih Jawatan (Klik untuk papar - Penyelia Kawasan tidak perlu di sini, lantik di Selenggara Bilik Kebal):")
                col_j1, col_j2, col_j3 = st.columns(3)
                with col_j1:
                    btn_kp = st.button("👑 Ketua Pengawas", use_container_width=True, key="btn_jawatan_kp_main", type="primary" if st.session_state.get("pilih_jawatan_jana_main")=="Ketua Pengawas" else "secondary")
                with col_j2:
                    btn_tkp = st.button("👑 Timbalan KP", use_container_width=True, key="btn_jawatan_tkp_main", type="primary" if st.session_state.get("pilih_jawatan_jana_main")=="Timbalan Ketua Pengawas" else "secondary")
                with col_j3:
                    btn_peng = st.button("👨‍🏫 Pengawas Peperiksaan", use_container_width=True, key="btn_jawatan_peng_main", type="primary" if st.session_state.get("pilih_jawatan_jana_main")=="Pengawas Peperiksaan" else "secondary")

                # Set session based on button click
                if btn_kp:
                    st.session_state["pilih_jawatan_jana_main"] = "Ketua Pengawas"
                if btn_tkp:
                    st.session_state["pilih_jawatan_jana_main"] = "Timbalan Ketua Pengawas"
                if btn_peng:
                    st.session_state["pilih_jawatan_jana_main"] = "Pengawas Peperiksaan"

                # Default
                if "pilih_jawatan_jana_main" not in st.session_state:
                    st.session_state["pilih_jawatan_jana_main"] = "Ketua Pengawas"

                pilih_jawatan_jana = st.session_state["pilih_jawatan_jana_main"]
                st.markdown(f"### 📋 {pilih_jawatan_jana} - Belum Ditempatkan")

                # Filter guru by jawatan & belum lantik
                def match_jawatan(row, target):
                    jaw = str(row.get("JAWATAN_CADANGAN") or row.get("jawatan_cadangan") or "").upper()
                    tgt = target.upper()
                    if "KETUA PENGAWAS" in tgt and "TIMBALAN" not in tgt:
                        return "KETUA PENGAWAS" in jaw and "TIMBALAN" not in jaw
                    elif "TIMBALAN" in tgt:
                        return "TIMBALAN" in jaw
                    elif "PENGAWAS PEPERIKSAAN" in tgt or tgt=="PENGAWAS PEPERIKSAAN":
                        return "PENGAWAS PEPERIKSAAN" in jaw or (jaw.strip()=="PENGAWAS")
                    elif "PENYELIA" in tgt:
                        return "PENYELIA" in jaw
                    else:
                        return tgt in jaw

                df_jawatan_all = df_cad_all[df_cad_all.apply(lambda r: match_jawatan(r, pilih_jawatan_jana), axis=1)].copy()
                df_belum_jawatan = df_jawatan_all[df_jawatan_all.apply(lambda r: str(r.get("kod_pusat") or r.get("KOD_PUSAT") or "").strip() in ("", "None", "none", "null", "nan", "nat"), axis=1)].copy()

                if df_belum_jawatan.empty:
                    st.warning(f"⚠️ Tiada {pilih_jawatan_jana} yang belum ditempatkan - semua sudah dilantik atau tiada cadangan jawatan ini.")
                    if not df_jawatan_all.empty:
                        st.info(f"Ada {len(df_jawatan_all)} {pilih_jawatan_jana} total, tapi semua sudah ada kod_pusat.")
                        st.dataframe(df_jawatan_all[["NAMA_GURU","IC_GURU","KOD_SEKOLAH_ASAL","kod_pusat","STATUS"]].head(20), use_container_width=True)
                else:
                    st.success(f"✅ Jumpa {len(df_belum_jawatan)} {pilih_jawatan_jana} yang BELUM ditempatkan lagi")

                    # Add poskod & jarak sorting - need to choose pusat first? Show without pusat first, then allow pilih pusat
                    # Show list of guru belum ditempatkan
                    display_belum = []
                    for _, r in df_belum_jawatan.iterrows():
                        display_belum.append({
                            "id": r.get("id",""),
                            "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                            "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                            "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                            "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                            "POSKOD RUMAH": r.get("POSKOD_RUMAH","") or r.get("poskod_rumah",""),
                            "TELEFON": r.get("TELEFON_GURU","") or r.get("telefon_guru",""),
                            "STATUS": r.get("STATUS","") or r.get("status","")
                        })
                    df_display_belum = pd.DataFrame(display_belum)
                    st.dataframe(df_display_belum, use_container_width=True, hide_index=True)

                    st.markdown("---")
                    st.markdown(f"#### 🎯 Pilih Pusat Untuk {pilih_jawatan_jana} Ini")

                    # Pilih pusat dropdown
                    pilihan_pusat_jawatan = st.selectbox(
                        f"Pilih Pusat Peperiksaan untuk {pilih_jawatan_jana}",
                        df_pusat_ppd["NO_PUSAT"].tolist(),
                        format_func=lambda x: f"{x} - {df_pusat_ppd[df_pusat_ppd['NO_PUSAT']==x]['NAMA_PUSAT'].values[0][:35] if not df_pusat_ppd[df_pusat_ppd['NO_PUSAT']==x].empty else x} (Perlu {df_pusat_ppd[df_pusat_ppd['NO_PUSAT']==x]['PETUGAS'].values[0] if not df_pusat_ppd[df_pusat_ppd['NO_PUSAT']==x].empty else '?'})",
                        key=f"pilih_pusat_jawatan_v3_{pilih_jawatan_jana}"
                    )

                    info_pusat = df_pusat_ppd[df_pusat_ppd["NO_PUSAT"]==pilihan_pusat_jawatan]
                    kod_tuan = str(info_pusat["KOD_SEKOLAH_TUAN_RUMAH"].values[0] if not info_pusat.empty else "").upper().strip()
                    poskod_pusat_val = get_poskod_pusat_val(pilihan_pusat_jawatan)

                    st.caption(f"Pusat {pilihan_pusat_jawatan} | Tuan Rumah: {kod_tuan or 'Tiada'} | Poskod Pusat: {poskod_pusat_val or 'Fallback poskod sekolah'} | Max 3 per sekolah | Elak sekolah sendiri")

                    # Count current in pusat
                    try:
                        res_curr = supa.table("cadangan_sup").select("*").eq("kod_pusat", pilihan_pusat_jawatan).limit(5000).execute()
                        df_curr = pd.DataFrame(res_curr.data or [])
                        sekolah_count_curr = {}
                        if not df_curr.empty:
                            for _, r in df_curr.iterrows():
                                ks = str(r.get("kod_sekolah_asal") or "").upper().strip()
                                sekolah_count_curr[ks] = sekolah_count_curr.get(ks, 0) + 1
                        st.info(f"ℹ️ Pusat {pilihan_pusat_jawatan} sudah ada {len(df_curr)} petugas ditempatkan. Sekolah count: {sekolah_count_curr}")
                    except:
                        df_curr = pd.DataFrame()
                        sekolah_count_curr = {}

                    # Filter eligible by max3 & sekolah sendiri & poskod terdekat
                    eligible_with_jarak = []
                    for _, r in df_belum_jawatan.iterrows():
                        ks = str(r.get("KOD_SEKOLAH_ASAL") or r.get("kod_sekolah_asal") or "").upper().strip()
                        if kod_tuan and ks == kod_tuan: continue
                        if sekolah_count_curr.get(ks,0) >=3: continue
                        pk_guru = str(r.get("POSKOD_RUMAH") or r.get("poskod_rumah") or "")
                        jarak = poskod_distance(pk_guru, poskod_pusat_val)
                        eligible_with_jarak.append((jarak, r))

                    eligible_with_jarak.sort(key=lambda x: x[0])

                    if not eligible_with_jarak:
                        st.warning("Tiada calon layak untuk pusat ini (semua sekolah sama atau max 3)")
                    else:
                        st.markdown(f"**{len(eligible_with_jarak)} calon {pilih_jawatan_jana} layak untuk {pilihan_pusat_jawatan} (disusun poskod terdekat):**")
                        display_eligible = []
                        for jarak, r in eligible_with_jarak:
                            display_eligible.append({
                                "JARAK": jarak if jarak!=99999 else "Tiada poskod",
                                "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                                "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                                "POSKOD RUMAH": r.get("POSKOD_RUMAH","") or r.get("poskod_rumah",""),
                                "POSKOD PUSAT": poskod_pusat_val,
                                "id": r.get("id","")
                            })
                        df_eligible_disp = pd.DataFrame(display_eligible)
                        st.dataframe(df_eligible_disp, use_container_width=True, hide_index=True)

                        pilih_guru_jawatan = st.multiselect(
                            f"Pilih {pilih_jawatan_jana} untuk lantik ke {pilihan_pusat_jawatan} (paling dekat di atas)",
                            df_eligible_disp["id"].tolist(),
                            format_func=lambda x: f"{df_eligible_disp[df_eligible_disp['id']==x]['NAMA GURU'].values[0]} - {df_eligible_disp[df_eligible_disp['id']==x]['SEKOLAH ASAL'].values[0]} - Poskod {df_eligible_disp[df_eligible_disp['id']==x]['POSKOD RUMAH'].values[0]} - Jarak {df_eligible_disp[df_eligible_disp['id']==x]['JARAK'].values[0]}" if not df_eligible_disp[df_eligible_disp['id']==x].empty else str(x),
                            key=f"multiselect_jawatan_v3_{pilih_jawatan_jana}_{pilihan_pusat_jawatan}"
                        )

                        col_lantik_j, col_export_j = st.columns([2,1])
                        with col_lantik_j:
                            if st.button(f"✅ Lantik {len(pilih_guru_jawatan)} {pilih_jawatan_jana} ke {pilihan_pusat_jawatan}", type="primary", use_container_width=True, key=f"btn_lantik_jawatan_v3_{pilih_jawatan_jana}_{pilihan_pusat_jawatan}", disabled=len(pilih_guru_jawatan)==0):
                                try:
                                    berjaya = 0
                                    for gid in pilih_guru_jawatan:
                                        supa.table("cadangan_sup").update({"kod_pusat": pilihan_pusat_jawatan, "status": "DILANTIK PPD"}).eq("id", gid).execute()
                                        berjaya+=1
                                    st.success(f"✅ {berjaya} {pilih_jawatan_jana} dilantik ke {pilihan_pusat_jawatan} (poskod terdekat)")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")
                        with col_export_j:
                            st.download_button(f"📥 Export {pilih_jawatan_jana}", to_excel(df_eligible_disp), file_name=f"{pilih_jawatan_jana.replace(' ','_')}_{pilihan_pusat_jawatan}.xlsx", use_container_width=True, key=f"exp_jawatan_v3_{pilih_jawatan_jana}")


        elif menu == "hasil":
            st.header(f"Hasil Janaan - PPD {kod_ppd}")

            # ===== BUTANG BATAL JANAAN - RESET SEMUA JADI 0 =====
            col_batal1, col_batal2 = st.columns([3, 1])
            with col_batal1:
                st.caption(f"PPD {kod_ppd} - Jika ada pelanggaran max 3 (contoh SAM NURUL IMAN 10 orang di BA021), batal dan jana semula")
            with col_batal2:
                if st.button("🗑️ Batal Janaan - Reset 0", type="primary", use_container_width=True, key="batal_janaan_all"):
                    st.session_state["confirm_batal"] = True

            if st.session_state.get("confirm_batal"):
                st.warning("⚠️ Anda pasti nak batal semua janaan? Semua penempatan akan jadi 0 dan perlu Jana Keseluruhan semula!")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ YA, Batal Semua Janaan", type="primary", use_container_width=True, key="confirm_yes_batal"):
                        try:
                            # Clear DB - set kod_pusat = None untuk PPD ini
                            st.info("Membatalkan semua janaan...")
                            # Update semua cadangan PPD ini
                            supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN"}).eq("kod_ppd", kod_ppd).execute()
                            # Clear session
                            if "jana_all_result" in st.session_state:
                                del st.session_state["jana_all_result"]
                            if "jana_pusat_result" in st.session_state:
                                del st.session_state["jana_pusat_result"]
                            if "jana_pusat_no" in st.session_state:
                                del st.session_state["jana_pusat_no"]
                            st.session_state["confirm_batal"] = False
                            st.success(f"✅ Berjaya batal semua janaan untuk PPD {kod_ppd}. Hasil janaan sekarang 0. Sila Jana Keseluruhan semula!")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal batal: {e}")
                            st.session_state["confirm_batal"] = False
                with col_no:
                    if st.button("❌ Tidak", use_container_width=True, key="confirm_no_batal"):
                        st.session_state["confirm_batal"] = False
                        st.rerun()

            st.markdown("---")
            df_pusat_raw = get_pusat_df()
            df_cad_all = get_cadangan_df(kod_ppd=kod_ppd)
            if df_pusat_raw.empty:
                st.warning("Tiada pusat_master")
                st.stop()
            pusat_list = []
            for _, r in df_pusat_raw.iterrows():
                d = r.get("data") if isinstance(r.get("data"), dict) else {}
                if isinstance(d, str):
                    try: d = json.loads(d)
                    except: d = {}
                no_pusat = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                if not no_pusat.startswith(kod_ppd.upper()): continue
                nama = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                pusat_list.append({"NO_PUSAT": no_pusat, "NAMA_PUSAT": nama})
            df_pusat_list = pd.DataFrame(pusat_list)
            if df_pusat_list.empty:
                st.warning(f"Tiada pusat untuk PPD {kod_ppd}")
                st.stop()
            if "pilih_pusat_hasil" not in st.session_state:          # elak mendarat di pusat kosong
                try:
                    _nz = norm_cadangan(df_cad_all)
                    _ada = set(_nz.loc[_nz["KOD_PUSAT"] != "", "KOD_PUSAT"]) if not _nz.empty else set()
                    _ada |= {str(_p.get("NO_PUSAT_TUGAS") or "").upper().strip() for _p in (st.session_state.get("jana_all_result") or []) if _p.get("NO_PUSAT_TUGAS")}
                    _pertama = next((x for x in df_pusat_list["NO_PUSAT"].tolist() if x in _ada), None)
                    if _pertama:
                        st.session_state["pilih_pusat_hasil"] = _pertama
                except Exception:
                    pass
            pilihan_pusat_hasil = st.selectbox("Pilih Pusat", df_pusat_list["NO_PUSAT"].tolist(), format_func=lambda x: f"{x} - {df_pusat_list[df_pusat_list['NO_PUSAT']==x]['NAMA_PUSAT'].values[0][:30] if not df_pusat_list[df_pusat_list['NO_PUSAT']==x].empty else x}", key="pilih_pusat_hasil")
            show_flash()
            def _bersih(v):
                s = "" if v is None else str(v).strip()
                return "" if s.lower() in ("", "nan", "none", "null", "nat") else s.upper()
            def _kunci(r):
                i = _bersih(r.get("id"))
                return f"ID:{i}" if i else "IC:" + re.sub(r"\D", "", str(r.get("IC_GURU") or r.get("ic_guru") or ""))
            tugas = {}
            if not df_cad_all.empty:
                for _, c in df_cad_all.iterrows():
                    k_c = _kunci(c)
                    p_db = _bersih(c.get("kod_pusat")) or _bersih(c.get("KOD_PUSAT"))
                    if p_db:
                        tugas[k_c] = {"pusat": p_db, "row": c}
            pending_rows = list(st.session_state.get("jana_all_result", []) or [])
            if st.session_state.get("jana_pusat_no"):
                pending_rows += list(st.session_state.get("jana_pusat_result", []) or [])
            for p in pending_rows:
                p_baru = _bersih(p.get("NO_PUSAT_TUGAS"))
                if not p_baru: continue
                k_p = _kunci(p)
                asal_row = pd.Series(p)
                tugas[k_p] = {"pusat": p_baru, "row": asal_row}
            hasil_pusat = []
            for v in tugas.values():
                if v["pusat"] == pilihan_pusat_hasil:
                    hasil_pusat.append(v["row"].copy())
            df_hasil = pd.DataFrame(hasil_pusat)

            # Semakan pelanggaran max 3 untuk pusat yang dipilih
            if not df_hasil.empty:
                sekolah_count_check = {}
                for _, r in df_hasil.iterrows():
                    kod = str(r.get("KOD_SEKOLAH_ASAL") or r.get("kod_sekolah_asal") or "").upper().strip()
                    if kod:
                        sekolah_count_check[kod] = sekolah_count_check.get(kod, 0) + 1
                pelanggaran = [(k, v) for k, v in sekolah_count_check.items() if v > 3]
                if pelanggaran:
                    st.error(f"❌ PELANGGARAN MAX 3 DI {pilihan_pusat_hasil}:")
                    for kod, cnt in pelanggaran:
                        st.error(f"   - {kod}: {cnt} orang (LANGGAR! Max 3 sahaja) - Contoh: SAM NURUL IMAN 10 orang di BA021")
                    st.warning("⚠️ Sila klik Batal Janaan di atas dan Jana Keseluruhan semula untuk betulkan!")
                else:
                    st.success(f"✅ Semakan Max 3 OK di {pilihan_pusat_hasil}: Tiada sekolah lebih 3 orang")

            st.markdown("---")
            if df_hasil.empty:
                st.warning(f"Belum Ada Hasil Janaan Di Pusat Yang Dipilih: {pilihan_pusat_hasil}")
                _kira = {}
                for _v in tugas.values():
                    _kira[_v["pusat"]] = _kira.get(_v["pusat"], 0) + 1
                _kira = {k: n for k, n in _kira.items() if k in set(df_pusat_list["NO_PUSAT"])}
                if _kira:
                    _susun = sorted(_kira)
                    st.info(f"Pusat ini belum menerima sesiapa. Janaan telah menempatkan guru di {len(_kira)} pusat lain: "
                            + ", ".join(f"{k} ({_kira[k]})" for k in _susun[:12]) + (" ..." if len(_susun) > 12 else ""))
                    st.button(f"➡️ Papar {_susun[0]}", key="hasil_ke_pusat_ada",
                              on_click=lambda _p=_susun[0]: st.session_state.update({"pilih_pusat_hasil": _p}))
                else:
                    st.info("Belum ada sebarang penempatan dalam pangkalan data. Sila Jana Keseluruhan dan tekan 'Simpan', atau guna Penempatan Manual / Zon.")
            else:
                pusat_nama_h = df_pusat_list[df_pusat_list["NO_PUSAT"] == pilihan_pusat_hasil]["NAMA_PUSAT"].values[0] if not df_pusat_list[df_pusat_list["NO_PUSAT"] == pilihan_pusat_hasil].empty else ""
                st.success(f"{pilihan_pusat_hasil} - {pusat_nama_h} | {len(df_hasil)} petugas: 1 Ketua, 1 Timbalan, {len(df_hasil)-2} Pengawas" if adalah_spm() else f"{pilihan_pusat_hasil} - {pusat_nama_h} | {len(df_hasil)} petugas")
                jawatan_groups = {}
                for _, r in df_hasil.iterrows():
                    jaw = str(r.get("JAWATAN_CADANGAN") or r.get("jawatan_cadangan") or r.get("JAWATAN") or "Pengawas Peperiksaan").strip()
                    if jaw not in jawatan_groups:
                        jawatan_groups[jaw] = []
                    jawatan_groups[jaw].append(r)
                order = ["Ketua Pengawas", "Timbalan Ketua Pengawas", "Pengawas Peperiksaan", "Juru Tulis", "Juru Baca", "Ketua Pengawas Hospital", "Pengawas Hospital", "Pengawas Pengiring", "Pengemas Bilik"]
                if not adalah_spm():
                    order = program_cfg()["jawatan_pilihan"]
                for jawatan in order:
                    if jawatan not in jawatan_groups: continue
                    guru_list = jawatan_groups[jawatan]
                    if "Ketua Pengawas" in jawatan and "Timbalan" not in jawatan:
                        label = "Ketua Pengawas - 1 orang"
                    elif "Timbalan" in jawatan:
                        label = "Timbalan Ketua Pengawas - 1 orang"
                    else:
                        label = f"Pengawas Peperiksaan - {len(guru_list)} orang" if adalah_spm() else f"{jawatan} - {len(guru_list)} orang"
                    st.subheader(label)
                    rows_j = []
                    for g in guru_list:
                        rows_j.append({"NAMA": g.get("NAMA_GURU", ""), "NO IC": g.get("IC_GURU", ""), "SEKOLAH ASAL": g.get("KOD_SEKOLAH_ASAL", ""), "NAMA SEKOLAH ASAL": str(g.get("NAMA_SEKOLAH_ASAL", ""))[:30], "JANTINA": g.get("JANTINA", "") or g.get("jantina", ""), "NO TELEFON": g.get("TELEFON_GURU", "") or g.get("telefon_guru", "")})
                    df_j = pd.DataFrame(rows_j)
                    st.dataframe(df_j, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("## 📊 Hasil Janaan Keseluruhan Untuk Setiap Sekolah")

            # [FLYOUT] st.tabs diganti sub menu flyout

            if fly_cur == "ringkasan":
                st.markdown("### 📋 Ringkasan Keseluruhan - Semua Pusat")
                st.caption("Data kuota sama dengan Dashboard PPD: PERLU = KELAS + 9 (KELAS = CEIL(calon/20)). "
                           "🔴 Belum Ada (0) | 🟡 Belum Cukup (< perlu) | 🟢 Cukup (>= perlu)")
                _kuota = {k["NO_PUSAT"]: k for k in kuota_pusat_ppd(df_pusat_raw, kod_ppd)}
                ringkas_all = []
                for _, pr in df_pusat_list.iterrows():
                    no_p = pr["NO_PUSAT"]
                    nama_p = pr["NAMA_PUSAT"]
                    guru_di_pusat = [v for v in tugas.values() if v["pusat"] == no_p]
                    def _jaw(v):
                        return str(v["row"].get("JAWATAN_CADANGAN") or v["row"].get("jawatan_cadangan") or v["row"].get("JAWATAN") or "")
                    _jn = [jenis_jawatan(_jaw(v)) for v in guru_di_pusat]
                    _cnt = {_k: _jn.count(_k) for _k, _n, _c in program_roles()}
                    k = _kuota.get(no_p, {})
                    perlu = int(k.get("SEPATUTNYA", 0))
                    jumlah = len(guru_di_pusat)
                    _q = kuota_roles(bilik=k.get("KELAS", 0), petugas=perlu)
                    _st, _ct = status_program(_cnt, _q, jumlah)
                    ringkas_all.append({"NO PUSAT": no_p, "NAMA PUSAT": str(nama_p)[:30],
                                        "CALON": int(k.get("CALON", 0)), "KELAS": int(k.get("KELAS", 0)),
                                        "PERLU": perlu, "DITEMPATKAN": jumlah,
                                        **{_c: _cnt[_k] for _k, _n, _c in program_roles()},
                                        "KEKURANGAN": max(0, perlu - jumlah),
                                        "STATUS": _st, "CATATAN": _ct})
                df_ringkas_all = pd.DataFrame(ringkas_all)
                if not df_ringkas_all.empty:
                    _tp, _tn = int(df_ringkas_all["PERLU"].sum()), int(df_ringkas_all["DITEMPATKAN"].sum())
                    m1, m2, m3, m4, m5, m6 = st.columns(6)
                    m1.metric("🏫 Pusat", len(df_ringkas_all))
                    m2.metric("📋 Perlu", _tp)
                    m3.metric("✅ Ditempatkan", _tn)
                    m4.metric("🟢 Cukup", int(df_ringkas_all["STATUS"].str.startswith("🟢").sum()))
                    m5.metric("🟡 Belum Cukup", int(df_ringkas_all["STATUS"].str.contains("Belum Cukup").sum()))
                    m6.metric("🔴 Belum Ada", int(df_ringkas_all["STATUS"].str.contains("Belum Ada").sum()))
                    st.caption("🟢 Cukup hanya jika setiap pusat ada 1 KP, 1 TKP dan Pengawas penuh mengikut kuota (PERLU - 2).")
                    st.dataframe(df_ringkas_all, use_container_width=True, hide_index=True)
                    st.download_button("📥 Export Ringkasan Semua Pusat", to_excel(df_ringkas_all), file_name=f"ringkasan_semua_pusat_{kod_ppd}.xlsx", use_container_width=True)
                else:
                    st.info("Belum ada hasil janaan keseluruhan")

            if fly_cur == "sekolah":
                _hl = hasil_lookup(df_pusat_raw, kod_ppd)
                st.markdown("### 🏫 Hasil Janaan Mengikut Sekolah Asal")
                st.caption("Setiap sekolah - berapa guru ditempatkan dan ke pusat mana")
                sekolah_groups = {}
                for v in tugas.values():
                    r = v["row"]
                    kod_sek = str(r.get("KOD_SEKOLAH_ASAL") or r.get("kod_sekolah_asal") or "TIADA KOD").upper().strip()
                    nama_sek = str(r.get("NAMA_SEKOLAH_ASAL") or r.get("nama_sekolah_asal") or kod_sek)[:35]
                    key = f"{kod_sek} - {nama_sek}"
                    if key not in sekolah_groups:
                        sekolah_groups[key] = []
                    sekolah_groups[key].append({"row": r, "pusat": v["pusat"]})

                if not sekolah_groups:
                    st.info("Belum ada hasil janaan")
                else:
                    # Summary per sekolah
                    summary_sekolah = []
                    for key, guru_list in sorted(sekolah_groups.items()):
                        kod = key.split(" - ")[0]
                        pusat_list = list(set([g["pusat"] for g in guru_list]))
                        summary_sekolah.append({"KOD SEKOLAH": kod, "NAMA SEKOLAH": key.split(" - ", 1)[1] if " - " in key else key, "NO PUSAT ASAL": ", ".join(_hl["asal"].get(kod, [])) or "-", "BIL GURU": len(guru_list), "PUSAT DITEMPATKAN": ", ".join(sorted(pusat_list)), "NAMA PUSAT TUGAS": " | ".join(sorted({_hl["pusat"].get(_p, {}).get("nama", "") for _p in pusat_list} - {""}))})
                    df_sum_sek = pd.DataFrame(summary_sekolah)
                    st.dataframe(df_sum_sek, use_container_width=True, hide_index=True)
                    st.markdown("---")
                    st.markdown("#### 🔍 Detail Setiap Sekolah")
                    pilih_sekolah = st.selectbox("Pilih Sekolah Untuk Lihat Detail", sorted(sekolah_groups.keys()), key="pilih_sekolah_hasil")
                    if pilih_sekolah:
                        detail = sekolah_groups[pilih_sekolah]
                        st.markdown(f"**{pilih_sekolah} - {len(detail)} guru ditempatkan:**")
                        rows_detail = []
                        for g in detail:
                            r = g["row"]
                            rows_detail.append(hasil_row(r, g["pusat"], _hl))
                        df_detail = pd.DataFrame(rows_detail)
                        st.dataframe(df_detail, use_container_width=True, hide_index=True)
                        st.download_button(f"📥 Export {pilih_sekolah}", to_excel(df_detail), file_name=f"hasil_{pilih_sekolah.split(' - ')[0]}_{kod_ppd}.xlsx", use_container_width=True, key=f"export_{pilih_sekolah}")

            if fly_cur == "guru":
                _hl = hasil_lookup(df_pusat_raw, kod_ppd)
                st.markdown("### 👥 Semua Guru Ditempatkan - Keseluruhan")
                all_guru_rows = []
                for v in tugas.values():
                    r = v["row"]
                    all_guru_rows.append(hasil_row(r, v["pusat"], _hl))
                df_all_guru = pd.DataFrame(all_guru_rows)
                if df_all_guru.empty:
                    st.info("Belum ada guru ditempatkan")
                else:
                    st.dataframe(df_all_guru, use_container_width=True, hide_index=True)
                    st.download_button("📥 Export Semua Guru Ditempatkan", to_excel(df_all_guru), file_name=f"semua_guru_ditempatkan_{kod_ppd}.xlsx", use_container_width=True)

        elif menu == "manual":
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
                <h2 style="margin:0; color:white;">📌 Penempatan Manual - PPD {kod_ppd}</h2>
                <p style="margin:5px 0 0 0; color:#e3f2fd;">Pilih pusat, klik kolum jawatan untuk pilih petugas secara manual - 1 Pusat = 1 KP + 1 TKP + Pengawas ikut keperluan</p>
            </div>
            ''', unsafe_allow_html=True)

            df_pusat_raw = get_pusat_df()
            df_cad_all = get_cadangan_df(kod_ppd=kod_ppd)

            if df_pusat_raw.empty:
                st.warning("Tiada pusat_master")
                st.stop()
            if df_cad_all.empty:
                st.warning(f"Belum ada cadangan SUP untuk PPD {kod_ppd}")
                st.stop()

            # ✅ INFO: Berapa guru telah dilantik vs belum
            total_cad = len(df_cad_all)
            def is_belum_info(row):
                kp = str(row.get("kod_pusat") or row.get("KOD_PUSAT") or "").strip()
                return kp == "" or kp.lower() in ("none", "null", "nan", "nat")
            belum_info = df_cad_all[df_cad_all.apply(is_belum_info, axis=1)]
            sudah_info = total_cad - len(belum_info)
            if sudah_info > 0:
                st.info(f"📊 Status PPD {kod_ppd}: {total_cad} cadangan | {sudah_info} telah dilantik (tidak akan dipapar di sini) | {len(belum_info)} belum dilantik (akan dipapar)")
            else:
                st.info(f"📊 Status PPD {kod_ppd}: {total_cad} cadangan | Semua belum dilantik")

            # Parse pusat list
            pusat_list_m = []
            for _, r in df_pusat_raw.iterrows():
                d = r.get("data") if isinstance(r.get("data"), dict) else {}
                if isinstance(d, str):
                    try: d = json.loads(d)
                    except: d = {}
                no_pusat = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                if not no_pusat.startswith(kod_ppd.upper()): continue
                nama = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                j_calon = r.get("jumlah_calon") or d.get("JUMLAH_CALON") or 0
                try: jc = int(float(str(j_calon) or 0))
                except: jc = 0
                jk = _int_atau_none(r.get("jumlah_kelas")) or _int_atau_none(d.get("JUMLAH_KELAS")) or kira_kelas_dari_calon(jc)   # ikut KELAS yang diedit PPD
                petugas_perlu = perlu_pusat(d, jk)                                                                                   # ikut PERLU yang diedit PPD
                kod_tuan = str(r.get("kod_sekolah_tuan_rumah") or d.get("KOD_SEKOLAH_TUAN_RUMAH") or "").upper().strip()
                pusat_list_m.append({"NO_PUSAT": no_pusat, "NAMA_PUSAT": nama, "CALON": jc, "KELAS": jk, "PERLU": petugas_perlu, "KOD_TUAN": kod_tuan})

            df_pusat_m = pd.DataFrame(pusat_list_m)
            if df_pusat_m.empty:
                st.warning(f"Tiada pusat untuk PPD {kod_ppd}")
                st.stop()

            # Pilih pusat
            st.markdown("### 📍 STEP 1: Pilih Pusat Daerah")
            col_pus1, col_pus2 = st.columns([2, 1])
            with col_pus1:
                pilih_pusat_manual = st.selectbox(
                    "Pilih Pusat",
                    df_pusat_m["NO_PUSAT"].tolist(),
                    format_func=lambda x: f"{x} - {df_pusat_m[df_pusat_m['NO_PUSAT']==x]['NAMA_PUSAT'].values[0][:30] if not df_pusat_m[df_pusat_m['NO_PUSAT']==x].empty else x}",
                    key="pilih_pusat_manual"
                )
            with col_pus2:
                info_pusat = df_pusat_m[df_pusat_m["NO_PUSAT"] == pilih_pusat_manual]
                if not info_pusat.empty:
                    perlu_m = int(info_pusat["PERLU"].values[0])
                    st.markdown(f'''
                    <div style="background:#e3f2fd; border:2px solid #1565c0; border-radius:8px; padding:10px; text-align:center;">
                        <div style="font-size:11px; color:#1565c0;">KEPERLUAN PUSAT</div>
                        <div style="font-size:20px; font-weight:800; color:#0d47a1;">{perlu_m} Petugas</div>
                        <div style="font-size:11px; color:#0d47a1;">1 KP + 1 TKP + {perlu_m-2} Pengawas</div>
                        <div style="font-size:10px; color:#1565c0; margin-top:4px;">{info_pusat['CALON'].values[0]} calon | {info_pusat['KELAS'].values[0]} kelas</div>
                    </div>
                    ''', unsafe_allow_html=True)

            st.markdown("---")

            # Load current placement for this pusat
            def _bersih_m(v):
                s = "" if v is None else str(v).strip()
                return "" if s.lower() in ("", "nan", "none", "null", "nat") else s.upper()

            def _kunci_m(r):
                i = _bersih_m(r.get("id"))
                return f"ID:{i}" if i else "IC:" + re.sub(r"\D", "", str(r.get("IC_GURU") or r.get("ic_guru") or ""))

            # Current tugas untuk pusat ini
            tugas_pusat_ini = {}
            if not df_cad_all.empty:
                for _, c in df_cad_all.iterrows():
                    p_db = _bersih_m(c.get("kod_pusat")) or _bersih_m(c.get("KOD_PUSAT"))
                    if p_db == pilih_pusat_manual:
                        tugas_pusat_ini[_kunci_m(c)] = c

            # Kira sekolah count untuk max 3 check
            sekolah_count_manual = {}
            for _, c in df_cad_all.iterrows():
                p_db = _bersih_m(c.get("kod_pusat")) or _bersih_m(c.get("KOD_PUSAT"))
                if p_db == pilih_pusat_manual:
                    kod = str(c.get("KOD_SEKOLAH_ASAL") or c.get("kod_sekolah_asal") or "").upper().strip()
                    if kod:
                        sekolah_count_manual[kod] = sekolah_count_manual.get(kod, 0) + 1

            # Paparan semasa
            st.markdown(f"### 🏫 Pusat {pilih_pusat_manual} - Penempatan Semasa")
            col_curr1, col_curr2, col_curr3, col_curr4, col_curr5, col_curr6 = st.columns(6)
            # FIX: 5 jawatan - Penyelia dari SUP, Selenggara dari PPD
            kp_curr_dict = {}
            tkp_curr_dict = {}
            penyelia_curr_dict = {}
            selenggara_curr_dict = {}
            peng_curr_dict = {}
            for k, c in tugas_pusat_ini.items():
                jaw = str(c.get("JAWATAN_CADANGAN") or c.get("jawatan_cadangan") or c.get("JAWATAN") or "").upper()
                if "KETUA PENGAWAS" in jaw and "TIMBALAN" not in jaw:
                    kp_curr_dict[k] = c
                elif "TIMBALAN" in jaw:
                    tkp_curr_dict[k] = c
                elif "PENYELIA KAWASAN" in jaw or ("PENYELIA" in jaw and "KAWASAN" in jaw):
                    penyelia_curr_dict[k] = c
                elif "SELENGGARA" in jaw or "BILIK KEBAL" in jaw:
                    selenggara_curr_dict[k] = c
                else:
                    peng_curr_dict[k] = c
            kp_curr = list(kp_curr_dict.values())
            tkp_curr = list(tkp_curr_dict.values())
            peng_curr = list(peng_curr_dict.values())

            with col_curr1:
                st.metric("Ketua Pengawas", f"{len(kp_curr)}/1", delta="OK" if len(kp_curr)==1 else "Perlu 1", delta_color="normal" if len(kp_curr)==1 else "inverse")
            with col_curr2:
                st.metric("Timbalan KP", f"{len(tkp_curr)}/1", delta="OK" if len(tkp_curr)==1 else "Perlu 1", delta_color="normal" if len(tkp_curr)==1 else "inverse")
            with col_curr3:
                st.metric("Penyelia Kawasan", f"{len(penyelia_curr_dict)}/1", delta="OK" if len(penyelia_curr_dict)>=1 else "Perlu 1", delta_color="normal" if len(penyelia_curr_dict)>=1 else "inverse")
            with col_curr4:
                st.metric("Selenggara BK", f"{len(selenggara_curr_dict)}/1", delta="OK" if len(selenggara_curr_dict)>=1 else "Perlu 1", delta_color="normal" if len(selenggara_curr_dict)>=1 else "inverse")
            with col_curr5:
                perlu_p = int(info_pusat["PERLU"].values[0]) if not info_pusat.empty else 0
                st.metric("Pengawas", f"{len(peng_curr)}/{max(perlu_p-4,0)}", delta=f"Perlu {max(perlu_p-4,0)}")
            with col_curr6:
                st.metric("Jumlah", f"{len(tugas_pusat_ini)}/{perlu_p}", delta="Cukup" if len(tugas_pusat_ini)>=perlu_p else f"Kurang {perlu_p-len(tugas_pusat_ini)}")

            # Check pelanggaran max 3
            pelanggaran_m = [(k, v) for k, v in sekolah_count_manual.items() if v > 3]
            if pelanggaran_m:
                st.error(f"❌ Pelanggaran Max 3 di {pilih_pusat_manual}:")
                for kod, cnt in pelanggaran_m:
                    st.error(f"  - {kod}: {cnt} orang (Max 3 sahaja!)")
            else:
                st.success(f"✅ Max 3 OK di {pilih_pusat_manual} - Tiada sekolah lebih 3 orang")

            st.markdown("---")

            # 3 Kolum Penempatan Manual
            st.markdown("### 📌 STEP 2: Penempatan Manual - Klik Kolum Untuk Pilih")

            col_kp, col_tkp, col_peng, col_jt, col_jb, col_pb = st.columns(6)

            # ===== KOLUM KETUA PENGAWAS =====
            with col_kp:
                st.markdown('<div style="background:#bbdefb; border:2px solid #0d47a1; border-radius:8px; padding:8px; text-align:center; margin-bottom:6px;"><div style="font-size:20px;">👑</div><div style="font-weight:700; color:#0d47a1; font-size:12px;">KETUA PENGAWAS</div></div>', unsafe_allow_html=True)

                if kp_curr:
                    st.markdown("**Semasa:**")
                    for c in kp_curr:
                        st.markdown(f'''
                        <div style="background:#bbdefb; border:1px solid #0d47a1; border-radius:6px; padding:8px; margin:4px 0;">
                            <div style="font-weight:700; font-size:12px;">{c.get("NAMA_GURU", "")}</div>
                            <div style="font-size:10px;">{c.get("KOD_SEKOLAH_ASAL", "")} | {c.get("IC_GURU", "")}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    if st.button("🗑️ Buang KP", key="buang_kp", use_container_width=True):
                        for k in list(kp_curr_dict.keys()):
                            try:
                                c = tugas_pusat_ini.get(k)
                                if c is not None:
                                    supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN"}).eq("id", c.get("id")).execute()
                            except Exception as e:
                                st.error(str(e))
                        st.success("KP dibuang")
                        st.rerun()
                else:
                    st.info("Belum ada KP")

                st.markdown("**Pilih KP:**")
                # ✅ FIX: Hanya guru BELUM dilantik - keluarkan yang sudah ada kod_pusat atau status LULUS/SURAT
                kod_tuan_m = info_pusat["KOD_TUAN"].values[0] if not info_pusat.empty else ""
                df_kp_calon_all = df_cad_all.copy()
                def is_belum_kp(row):
                    kp = str(row.get("kod_pusat") or row.get("KOD_PUSAT") or "").strip()
                    stt = str(row.get("status") or row.get("STATUS") or "").upper()
                    ns = str(row.get("no_surat") or "").strip()
                    # Sudah dilantik jika ada kod_pusat ATAU status LULUS/DILANTIK ATAU ada no_surat sah
                    if kp != "" and kp.lower() not in ("none","null","nan","nat","-"):
                        return False
                    if "LULUS" in stt or "DILANTIK" in stt or "SURAT" in stt:
                        if ns and ns.lower() not in ("none","null","nan",""):
                            return False
                    return True
                df_kp_calon = df_kp_calon_all[df_kp_calon_all.apply(is_belum_kp, axis=1)].copy()
                # Hanya KP (bukan Timbalan)
                df_kp_calon = df_kp_calon[df_kp_calon["JAWATAN_CADANGAN"].astype(str).str.contains("Ketua Pengawas", case=False, na=False) & ~df_kp_calon["JAWATAN_CADANGAN"].astype(str).str.contains("Timbalan", case=False, na=False)]
                # Elak sekolah sendiri
                if kod_tuan_m:
                    df_kp_calon = df_kp_calon[~df_kp_calon["KOD_SEKOLAH_ASAL"].astype(str).str.upper().str.strip().eq(kod_tuan_m)]
                # Elak yang sudah ada pusat lain? Biar boleh pilih, tapi warning
                # Check max 3
                def check_kp_max3(row):
                    kod = str(row.get("KOD_SEKOLAH_ASAL", "")).upper().strip()
                    return sekolah_count_manual.get(kod, 0) < 3 if kod else True
                df_kp_calon["MAX3_OK"] = df_kp_calon.apply(check_kp_max3, axis=1)

                # Show only yang layak max 3
                df_kp_layak = df_kp_calon[df_kp_calon["MAX3_OK"] == True]

                if df_kp_layak.empty:
                    # Check if empty because all already appointed
                    if len(df_kp_calon_all) > 0 and len(df_kp_calon) == 0:
                        st.warning("⚠️ Semua KP telah dilantik")
                    else:
                        st.warning("Tiada KP layak")
                    if not df_kp_calon.empty:
                        st.dataframe(df_kp_calon[["NAMA_GURU", "KOD_SEKOLAH_ASAL", "IC_GURU"]].head(10), use_container_width=True, hide_index=True)
                else:
                    st.caption(f"{len(df_kp_layak)} calon KP belum dilantik & layak (max 3 OK) - tidak akan muncul lagi jika telah dilantik")
                    pilih_kp = st.selectbox(
                        "Klik untuk pilih Ketua Pengawas",
                        df_kp_layak["id"].tolist() if "id" in df_kp_layak.columns else [],
                        format_func=lambda x: f"{df_kp_layak[df_kp_layak['id']==x]['NAMA_GURU'].values[0]} - {df_kp_layak[df_kp_layak['id']==x]['KOD_SEKOLAH_ASAL'].values[0]} | {df_kp_layak[df_kp_layak['id']==x]['NAMA_SEKOLAH_ASAL'].values[0][:20]}" if not df_kp_layak[df_kp_layak['id']==x].empty else str(x),
                        key="pilih_kp_manual"
                    )
                    if st.button("✅ Lantik Sebagai KP", type="primary", use_container_width=True, key="lantik_kp"):
                        if pilih_kp:
                            try:
                                # Jika sudah ada KP, buang dulu
                                for k in list(kp_curr_dict.keys()):
                                    c = tugas_pusat_ini.get(k)
                                    if c is not None:
                                        supa.table("cadangan_sup").update({"kod_pusat": None}).eq("id", c.get("id")).execute()
                                supa.table("cadangan_sup").update({"kod_pusat": pilih_pusat_manual, "status": "DILANTIK PPD"}).eq("id", pilih_kp).execute()
                                st.success(f"KP dilantik ke {pilih_pusat_manual}")
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))

            # ===== KOLUM TIMBALAN KETUA PENGAWAS =====
            with col_tkp:
                st.markdown('<div style="background:#e3f2fd; border:2px solid #0d47a1; border-radius:8px; padding:8px; text-align:center; margin-bottom:6px;"><div style="font-size:20px;">🎖️</div><div style="font-weight:700; color:#0d47a1; font-size:12px;">TIMBALAN KP</div></div>', unsafe_allow_html=True)

                if tkp_curr:
                    st.markdown("**Semasa:**")
                    for c in tkp_curr:
                        st.markdown(f'''
                        <div style="background:#e3f2fd; border:1px solid #0d47a1; border-radius:6px; padding:8px; margin:4px 0;">
                            <div style="font-weight:700; font-size:12px;">{c.get("NAMA_GURU", "")}</div>
                            <div style="font-size:10px;">{c.get("KOD_SEKOLAH_ASAL", "")} | {c.get("IC_GURU", "")}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    if st.button("🗑️ Buang TKP", key="buang_tkp", use_container_width=True):
                        for k in list(tkp_curr_dict.keys()):
                            try:
                                c = tugas_pusat_ini.get(k)
                                if c is not None:
                                    supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN"}).eq("id", c.get("id")).execute()
                            except Exception as e:
                                st.error(str(e))
                        st.success("TKP dibuang")
                        st.rerun()
                else:
                    st.info("Belum ada TKP")

                st.markdown("**Pilih TKP:**")
                # ✅ FIX: Hanya guru BELUM dilantik - keluarkan yang sudah dilantik
                df_tkp_calon_all = df_cad_all.copy()
                def is_belum_tkp(row):
                    kp = str(row.get("kod_pusat") or row.get("KOD_PUSAT") or "").strip()
                    stt = str(row.get("status") or row.get("STATUS") or "").upper()
                    ns = str(row.get("no_surat") or "").strip()
                    if kp != "" and kp.lower() not in ("none","null","nan","nat","-"):
                        return False
                    if "LULUS" in stt or "DILANTIK" in stt or "SURAT" in stt:
                        if ns and ns.lower() not in ("none","null","nan",""):
                            return False
                    return True
                df_tkp_calon = df_tkp_calon_all[df_tkp_calon_all.apply(is_belum_tkp, axis=1)].copy()
                df_tkp_calon = df_tkp_calon[df_tkp_calon["JAWATAN_CADANGAN"].astype(str).str.contains("Timbalan", case=False, na=False)]
                if kod_tuan_m:
                    df_tkp_calon = df_tkp_calon[~df_tkp_calon["KOD_SEKOLAH_ASAL"].astype(str).str.upper().str.strip().eq(kod_tuan_m)]
                def check_tkp_max3(row):
                    kod = str(row.get("KOD_SEKOLAH_ASAL", "")).upper().strip()
                    return sekolah_count_manual.get(kod, 0) < 3 if kod else True
                df_tkp_calon["MAX3_OK"] = df_tkp_calon.apply(check_tkp_max3, axis=1)
                df_tkp_layak = df_tkp_calon[df_tkp_calon["MAX3_OK"] == True]

                if df_tkp_layak.empty:
                    st.warning("Tiada TKP layak")
                else:
                    st.caption(f"{len(df_tkp_layak)} calon TKP layak - keseluruhan daerah {kod_ppd}")
                    pilih_tkp = st.selectbox(
                        "Klik untuk pilih Timbalan KP",
                        df_tkp_layak["id"].tolist() if "id" in df_tkp_layak.columns else [],
                        format_func=lambda x: f"{df_tkp_layak[df_tkp_layak['id']==x]['NAMA_GURU'].values[0]} - {df_tkp_layak[df_tkp_layak['id']==x]['KOD_SEKOLAH_ASAL'].values[0]}" if not df_tkp_layak[df_tkp_layak['id']==x].empty else str(x),
                        key="pilih_tkp_manual"
                    )
                    if st.button("✅ Lantik Sebagai TKP", type="primary", use_container_width=True, key="lantik_tkp"):
                        if pilih_tkp:
                            try:
                                for k in list(tkp_curr_dict.keys()):
                                    c = tugas_pusat_ini.get(k)
                                    if c is not None:
                                        supa.table("cadangan_sup").update({"kod_pusat": None}).eq("id", c.get("id")).execute()
                                supa.table("cadangan_sup").update({"kod_pusat": pilih_pusat_manual, "status": "DILANTIK PPD"}).eq("id", pilih_tkp).execute()
                                st.success(f"TKP dilantik ke {pilih_pusat_manual}")
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))

            # ===== KOLUM PENGAWAS =====
            with col_peng:
                perlu_p = int(info_pusat["PERLU"].values[0]) if not info_pusat.empty else 10
                perlu_pengawas = max(0, perlu_p - 1 - 1)
                st.markdown(f'<div style="background:#ffffff; border:2px solid #0d47a1; border-radius:8px; padding:8px; text-align:center; margin-bottom:6px;"><div style="font-size:20px;">👨‍🏫</div><div style="font-weight:700; color:#0d47a1; font-size:12px;">PENGAWAS ({perlu_pengawas})</div></div>', unsafe_allow_html=True)

                if peng_curr:
                    st.markdown(f"**Semasa: {len(peng_curr)}/{perlu_pengawas}**")
                    for c in peng_curr[:5]:
                        st.markdown(f'''
                        <div style="background:#ffffff; border:1px solid #0d47a1; border-radius:6px; padding:6px; margin:3px 0; font-size:11px;">
                            <b>{c.get("NAMA_GURU", "")[:20]}</b> - {c.get("KOD_SEKOLAH_ASAL", "")}
                        </div>
                        ''', unsafe_allow_html=True)
                    if len(peng_curr) > 5:
                        st.caption(f"... dan {len(peng_curr)-5} lagi")
                    if st.button("🗑️ Buang Semua Pengawas", key="buang_peng", use_container_width=True):
                        for k in list(peng_curr_dict.keys()):
                            try:
                                c = tugas_pusat_ini.get(k)
                                if c is not None:
                                    supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN"}).eq("id", c.get("id")).execute()
                            except Exception as e:
                                st.error(str(e))
                        st.success("Pengawas dibuang")
                        st.rerun()
                else:
                    st.info(f"Belum ada Pengawas ({perlu_pengawas} perlu)")

                st.markdown("**Pilih Pengawas Baru:**")
                # FIX: Filter hanya belum dilantik untuk Pengawas juga
                def is_belum_peng_manual(r):
                    kp = str(r.get("kod_pusat") or r.get("KOD_PUSAT") or "").strip()
                    stt = str(r.get("status") or r.get("STATUS") or "").upper()
                    ns = str(r.get("no_surat") or "").strip()
                    if kp != "" and kp.lower() not in ("none","null","nan","nat","-"):
                        return False
                    if "LULUS" in stt and ns and ns.lower() not in ("none","null","nan",""):
                        return False
                    return True
                # Apply to df_cad_all for Pengawas list
                try:
                    df_cad_all_filtered_peng = df_cad_all[df_cad_all.apply(is_belum_peng_manual, axis=1)].copy()
                except:
                    df_cad_all_filtered_peng = df_cad_all.copy()
                # ✅ QUERY BARU: Hanya guru BELUM dilantik
                df_peng_calon_all = df_cad_all.copy()
                def is_belum_peng(row):
                    kp = str(row.get("kod_pusat") or row.get("KOD_PUSAT") or "").strip()
                    return kp == "" or kp.lower() in ("none", "null", "nan", "nat")
                df_peng_calon = df_peng_calon_all[df_peng_calon_all.apply(is_belum_peng, axis=1)].copy()
                # Pengawas sahaja (bukan KP/TKP)
                df_peng_calon = df_peng_calon[~df_peng_calon["JAWATAN_CADANGAN"].astype(str).str.contains("Ketua Pengawas|Timbalan|Penyelia|Selenggara|Bilik Kebal", case=False, na=False, regex=True)]
                if kod_tuan_m:
                    df_peng_calon = df_peng_calon[~df_peng_calon["KOD_SEKOLAH_ASAL"].astype(str).str.upper().str.strip().eq(kod_tuan_m)]
                def check_peng_max3(row):
                    kod = str(row.get("KOD_SEKOLAH_ASAL", "")).upper().strip()
                    return sekolah_count_manual.get(kod, 0) < 3 if kod else True
                df_peng_calon["MAX3_OK"] = df_peng_calon.apply(check_peng_max3, axis=1)
                df_peng_layak = df_peng_calon[df_peng_calon["MAX3_OK"] == True]

                # Yang belum ditempatkan - df sudah filter belum dilantik, jadi semua belum
                df_peng_belum = df_peng_layak.copy()

                st.caption(f"{len(df_peng_belum)} calon | Perlu {perlu_pengawas}")

                if df_peng_belum.empty:
                    st.warning("Tiada calon Pengawas layak yang belum ditempatkan")
                    st.dataframe(df_peng_layak[["NAMA_GURU", "KOD_SEKOLAH_ASAL", "JAWATAN_CADANGAN"]].head(10), use_container_width=True, hide_index=True)
                else:
                    # Multi select
                    pilih_peng_list = st.multiselect(
                        f"Pilih Pengawas (perlu {perlu_pengawas}, max 3 per sekolah)",
                        df_peng_belum["id"].tolist() if "id" in df_peng_belum.columns else [],
                        format_func=lambda x: f"{df_peng_belum[df_peng_belum['id']==x]['NAMA_GURU'].values[0]} - {df_peng_belum[df_peng_belum['id']==x]['KOD_SEKOLAH_ASAL'].values[0]} - {df_peng_belum[df_peng_belum['id']==x]['JAWATAN_CADANGAN'].values[0]}" if not df_peng_belum[df_peng_belum['id']==x].empty else str(x),
                        key="pilih_peng_manual"
                    )
                    # Check kalau pilih lebih dari perlu atau langgar max 3
                    if pilih_peng_list:
                        # Kira sekolah count kalau tambah yang dipilih
                        temp_count = sekolah_count_manual.copy()
                        valid = True
                        for pid in pilih_peng_list:
                            row = df_peng_belum[df_peng_belum["id"]==pid]
                            if not row.empty:
                                kod = str(row["KOD_SEKOLAH_ASAL"].values[0]).upper().strip()
                                if temp_count.get(kod, 0) >= 3:
                                    st.error(f"❌ {kod} sudah 3 orang di {pilih_pusat_manual} - tidak boleh tambah lagi!")
                                    valid = False
                                temp_count[kod] = temp_count.get(kod, 0) + 1
                        if len(pilih_peng_list) > perlu_pengawas:
                            st.warning(f"⚠️ Anda pilih {len(pilih_peng_list)} tapi pusat perlu {perlu_pengawas} sahaja")

                        if st.button(f"✅ Lantik {len(pilih_peng_list)} Sebagai Pengawas", type="primary", use_container_width=True, key="lantik_peng", disabled=not valid):
                            try:
                                berjaya = 0
                                for pid in pilih_peng_list:
                                    supa.table("cadangan_sup").update({"kod_pusat": pilih_pusat_manual, "status": "DILANTIK PPD"}).eq("id", pid).execute()
                                    berjaya += 1
                                st.success(f"✅ {berjaya} Pengawas dilantik ke {pilih_pusat_manual}")
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))


            # ===== KOLUM JURU TULIS (Pengawas Khas - Tak Termasuk Kiraan Biasa) =====
            with col_jt:
                st.markdown('<div style="background:#e3f2fd; border:2px solid #0d47a1; border-radius:8px; padding:8px; text-align:center; margin-bottom:6px;"><div style="font-size:20px;">✍️</div><div style="font-weight:700; color:#0d47a1; font-size:12px;">JURU TULIS</div></div>', unsafe_allow_html=True)
                jt_curr = [c for k,c in tugas_pusat_ini.items() if "JURU TULIS" in str(c.get("JAWATAN_CADANGAN") or "").upper()]
                if jt_curr:
                    st.markdown(f"**Semasa: {len(jt_curr)} (Khas)**")
                    for c in jt_curr[:3]:
                        st.markdown(f'<div style="background:#e3f2fd; border-radius:6px; padding:6px; margin:3px 0; font-size:11px;"><b>{c.get("NAMA_GURU","")[:18]}</b> - {c.get("KOD_SEKOLAH_ASAL","")}</div>', unsafe_allow_html=True)
                    if st.button("🗑️ Buang Juru Tulis", key="buang_jt", use_container_width=True):
                        for c in jt_curr:
                            supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN"}).eq("id", c.get("id")).execute()
                        st.success("Juru Tulis dibuang"); st.rerun()
                else:
                    st.info("Belum ada Juru Tulis")
                st.markdown("**Pilih Juru Tulis:**")
                try:
                    df_jt_calon_all = df_cad_all[df_cad_all.apply(is_belum_peng_manual, axis=1)].copy()
                except:
                    try:
                        df_jt_calon_all = df_cad_all[df_cad_all.apply(is_belum_peng, axis=1)].copy()
                    except:
                        df_jt_calon_all = df_cad_all.copy()
                df_jt_calon = df_jt_calon_all[df_jt_calon_all["JAWATAN_CADANGAN"].astype(str).str.contains("Juru Tulis", case=False, na=False)]
                if kod_tuan_m:
                    df_jt_calon = df_jt_calon[~df_jt_calon["KOD_SEKOLAH_ASAL"].astype(str).str.upper().str.strip().eq(kod_tuan_m)]
                df_jt_calon["MAX3_OK"] = df_jt_calon.apply(lambda r: sekolah_count_manual.get(str(r.get("KOD_SEKOLAH_ASAL","")).upper().strip(),0) < 3, axis=1)
                df_jt_layak = df_jt_calon[df_jt_calon["MAX3_OK"]==True]
                st.caption(f"{len(df_jt_layak)} calon")
                if not df_jt_layak.empty:
                    pilih_jt = st.multiselect("Pilih Juru Tulis", df_jt_layak["id"].tolist(), format_func=lambda x: f"{df_jt_layak[df_jt_layak['id']==x]['NAMA_GURU'].values[0]} - {df_jt_layak[df_jt_layak['id']==x]['KOD_SEKOLAH_ASAL'].values[0]}" if not df_jt_layak[df_jt_layak['id']==x].empty else str(x), key="pilih_jt_manual")
                    if pilih_jt and st.button(f"✅ Lantik {len(pilih_jt)} Juru Tulis", type="primary", use_container_width=True, key="lantik_jt"):
                        for pid in pilih_jt:
                            supa.table("cadangan_sup").update({"kod_pusat": pilih_pusat_manual, "status": "DILANTIK PPD"}).eq("id", pid).execute()
                        st.success(f"✅ {len(pilih_jt)} Juru Tulis dilantik (Khas)"); st.balloons(); st.rerun()

            # ===== KOLUM JURU BACA (Pengawas Khas) =====
            with col_jb:
                st.markdown('<div style="background:#e3f2fd; border:2px solid #0d47a1; border-radius:8px; padding:8px; text-align:center; margin-bottom:6px;"><div style="font-size:20px;">📖</div><div style="font-weight:700; color:#0d47a1; font-size:12px;">JURU BACA</div></div>', unsafe_allow_html=True)
                jb_curr = [c for k,c in tugas_pusat_ini.items() if "JURU BACA" in str(c.get("JAWATAN_CADANGAN") or "").upper()]
                if jb_curr:
                    st.markdown(f"**Semasa: {len(jb_curr)} (Khas)**")
                    for c in jb_curr[:3]:
                        st.markdown(f'<div style="background:#e3f2fd; border-radius:6px; padding:6px; margin:3px 0; font-size:11px;"><b>{c.get("NAMA_GURU","")[:18]}</b> - {c.get("KOD_SEKOLAH_ASAL","")}</div>', unsafe_allow_html=True)
                    if st.button("🗑️ Buang Juru Baca", key="buang_jb", use_container_width=True):
                        for c in jb_curr:
                            supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN"}).eq("id", c.get("id")).execute()
                        st.success("Juru Baca dibuang"); st.rerun()
                else:
                    st.info("Belum ada Juru Baca")
                st.markdown("**Pilih Juru Baca:**")
                try:
                    df_jb_calon_all = df_cad_all[df_cad_all.apply(is_belum_peng_manual, axis=1)].copy()
                except:
                    try:
                        df_jb_calon_all = df_cad_all[df_cad_all.apply(is_belum_peng, axis=1)].copy()
                    except:
                        df_jb_calon_all = df_cad_all.copy()
                df_jb_calon = df_jb_calon_all[df_jb_calon_all["JAWATAN_CADANGAN"].astype(str).str.contains("Juru Baca", case=False, na=False)]
                if kod_tuan_m:
                    df_jb_calon = df_jb_calon[~df_jb_calon["KOD_SEKOLAH_ASAL"].astype(str).str.upper().str.strip().eq(kod_tuan_m)]
                df_jb_calon["MAX3_OK"] = df_jb_calon.apply(lambda r: sekolah_count_manual.get(str(r.get("KOD_SEKOLAH_ASAL","")).upper().strip(),0) < 3, axis=1)
                df_jb_layak = df_jb_calon[df_jb_calon["MAX3_OK"]==True]
                st.caption(f"{len(df_jb_layak)} calon")
                if not df_jb_layak.empty:
                    pilih_jb = st.multiselect("Pilih Juru Baca", df_jb_layak["id"].tolist(), format_func=lambda x: f"{df_jb_layak[df_jb_layak['id']==x]['NAMA_GURU'].values[0]} - {df_jb_layak[df_jb_layak['id']==x]['KOD_SEKOLAH_ASAL'].values[0]}" if not df_jb_layak[df_jb_layak['id']==x].empty else str(x), key="pilih_jb_manual")
                    if pilih_jb and st.button(f"✅ Lantik {len(pilih_jb)} Juru Baca", type="primary", use_container_width=True, key="lantik_jb"):
                        for pid in pilih_jb:
                            supa.table("cadangan_sup").update({"kod_pusat": pilih_pusat_manual, "status": "DILANTIK PPD"}).eq("id", pid).execute()
                        st.success(f"✅ {len(pilih_jb)} Juru Baca dilantik (Khas)"); st.balloons(); st.rerun()

            # ===== KOLUM PENGEMAS BILIK (Pengawas Khas) =====
            with col_pb:
                st.markdown('<div style="background:#e3f2fd; border:2px solid #0d47a1; border-radius:8px; padding:8px; text-align:center; margin-bottom:6px;"><div style="font-size:20px;">🧹</div><div style="font-weight:700; color:#0d47a1; font-size:12px;">PENGEMAS BILIK</div></div>', unsafe_allow_html=True)
                pb_curr = [c for k,c in tugas_pusat_ini.items() if "PENGEMAS BILIK" in str(c.get("JAWATAN_CADANGAN") or "").upper()]
                if pb_curr:
                    st.markdown(f"**Semasa: {len(pb_curr)} (Khas)**")
                    for c in pb_curr[:3]:
                        st.markdown(f'<div style="background:#e3f2fd; border-radius:6px; padding:6px; margin:3px 0; font-size:11px;"><b>{c.get("NAMA_GURU","")[:18]}</b> - {c.get("KOD_SEKOLAH_ASAL","")}</div>', unsafe_allow_html=True)
                    if st.button("🗑️ Buang Pengemas Bilik", key="buang_pb", use_container_width=True):
                        for c in pb_curr:
                            supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN"}).eq("id", c.get("id")).execute()
                        st.success("Pengemas Bilik dibuang"); st.rerun()
                else:
                    st.info("Belum ada Pengemas Bilik")
                st.markdown("**Pilih Pengemas Bilik:**")
                try:
                    df_pb_calon_all = df_cad_all[df_cad_all.apply(is_belum_peng_manual, axis=1)].copy()
                except:
                    try:
                        df_pb_calon_all = df_cad_all[df_cad_all.apply(is_belum_peng, axis=1)].copy()
                    except:
                        df_pb_calon_all = df_cad_all.copy()
                df_pb_calon = df_pb_calon_all[df_pb_calon_all["JAWATAN_CADANGAN"].astype(str).str.contains("Pengemas Bilik", case=False, na=False)]
                if kod_tuan_m:
                    df_pb_calon = df_pb_calon[~df_pb_calon["KOD_SEKOLAH_ASAL"].astype(str).str.upper().str.strip().eq(kod_tuan_m)]
                df_pb_calon["MAX3_OK"] = df_pb_calon.apply(lambda r: sekolah_count_manual.get(str(r.get("KOD_SEKOLAH_ASAL","")).upper().strip(),0) < 3, axis=1)
                df_pb_layak = df_pb_calon[df_pb_calon["MAX3_OK"]==True]
                st.caption(f"{len(df_pb_layak)} calon")
                if not df_pb_layak.empty:
                    pilih_pb = st.multiselect("Pilih Pengemas Bilik", df_pb_layak["id"].tolist(), format_func=lambda x: f"{df_pb_layak[df_pb_layak['id']==x]['NAMA_GURU'].values[0]} - {df_pb_layak[df_pb_layak['id']==x]['KOD_SEKOLAH_ASAL'].values[0]}" if not df_pb_layak[df_pb_layak['id']==x].empty else str(x), key="pilih_pb_manual")
                    if pilih_pb and st.button(f"✅ Lantik {len(pilih_pb)} Pengemas Bilik", type="primary", use_container_width=True, key="lantik_pb"):
                        for pid in pilih_pb:
                            supa.table("cadangan_sup").update({"kod_pusat": pilih_pusat_manual, "status": "DILANTIK PPD"}).eq("id", pid).execute()
                        st.success(f"✅ {len(pilih_pb)} Pengemas Bilik dilantik (Khas)"); st.balloons(); st.rerun()

            # ===== END 3 KOLUM TAMBAHAN =====


            st.markdown("---")
            st.markdown("### 📊 Ringkasan Penempatan Manual - Kumulatif (Tidak Hilang Bila Pilih Sekolah Kedua)")
            st.info("💡 Ringkasan ini kumulatif - bila PPD lantik Sekolah Kedua, lantikan Pertama masih kekal di bawah. Column ikut jawatan: KP, TKP, Pengawas.")

            # ===== RINGKASAN KUMULATIF - SEMUA PUSAT YANG TELAH DILANTIK MANUAL =====
            try:
                # Ambil semua yang sudah ada kod_pusat dan status DILANTIK PPD untuk PPD ini
                res_all_lantik = supa.table("cadangan_sup").select("*").eq("kod_ppd", kod_ppd).not_.is_("kod_pusat", "null").limit(5000).execute()
                df_all_lantik = __import__("pandas").DataFrame(res_all_lantik.data or [])
                # Filter hanya yang status DILANTIK / LULUS
                if not df_all_lantik.empty:
                    df_all_lantik = df_all_lantik[df_all_lantik.apply(lambda r: str(r.get("status") or "").upper() not in ("", "DICADANGKAN", "HANTAR KE PPD"), axis=1)]
            except:
                df_all_lantik = __import__("pandas").DataFrame()

            # Tambah juga yang baru di session ini (kalau belum save DB pun, tunjuk)
            # Gabungkan
            if not df_all_lantik.empty:
                # Build rows dengan column ikut jawatan
                all_rows_kum = []
                for _, c in df_all_lantik.iterrows():
                    jaw = str(c.get("jawatan_cadangan") or c.get("JAWATAN_CADANGAN") or "")
                    # Tentukan column jawatan
                    if "Ketua Pengawas" in jaw and "Timbalan" not in jaw:
                        jaw_col = "KETUA PENGAWAS"
                    elif "Timbalan" in jaw:
                        jaw_col = "TIMBALAN KP"
                    elif "Pengawas" in jaw:
                        jaw_col = "PENGAWAS PEPERIKSAAN"
                    elif "Penyelia" in jaw:
                        jaw_col = "PENYELIA KAWASAN"
                    else:
                        jaw_col = jaw.upper()

                    all_rows_kum.append({
                        "BIL": len(all_rows_kum)+1,
                        "NAMA GURU": c.get("nama_guru","") or c.get("NAMA_GURU",""),
                        "IC": c.get("ic_guru","") or c.get("IC_GURU",""),
                        "JAWATAN": jaw,
                        "KOLUM JAWATAN": jaw_col,
                        "SEKOLAH ASAL": c.get("kod_sekolah_asal","") or c.get("KOD_SEKOLAH_ASAL",""),
                        "NAMA SEKOLAH ASAL": str(c.get("nama_sekolah_asal","") or c.get("NAMA_SEKOLAH_ASAL",""))[:25],
                        "PUSAT TUGAS": c.get("kod_pusat","") or c.get("KOD_PUSAT",""),
                        "STATUS": c.get("status","")
                    })

                df_summary_kum = __import__("pandas").DataFrame(all_rows_kum)

                if df_summary_kum.empty:
                    st.info("Belum ada penempatan manual - Sila lantik di atas")
                else:
                    # Papar ikut tab jawatan
                    tab_kp, tab_tkp, tab_peng, tab_semua = st.tabs(["👑 Ketua Pengawas", "🎖️ Timbalan KP", "👨‍🏫 Pengawas", "📋 Semua (Kumulatif)"])

                    with tab_kp:
                        df_kp = df_summary_kum[df_summary_kum["KOLUM JAWATAN"]=="KETUA PENGAWAS"].copy()
                        st.markdown(f"**{len(df_kp)} Ketua Pengawas telah dilantik (kumulatif, tidak hilang bila pilih sekolah kedua):**")
                        if df_kp.empty:
                            st.info("Belum ada Ketua Pengawas dilantik")
                        else:
                            st.dataframe(df_kp[["BIL","NAMA GURU","IC","SEKOLAH ASAL","NAMA SEKOLAH ASAL","PUSAT TUGAS"]], use_container_width=True, hide_index=True)

                    with tab_tkp:
                        df_tkp = df_summary_kum[df_summary_kum["KOLUM JAWATAN"]=="TIMBALAN KP"].copy()
                        st.markdown(f"**{len(df_tkp)} Timbalan KP telah dilantik (kumulatif):**")
                        if df_tkp.empty:
                            st.info("Belum ada Timbalan KP")
                        else:
                            st.dataframe(df_tkp[["BIL","NAMA GURU","IC","SEKOLAH ASAL","NAMA SEKOLAH ASAL","PUSAT TUGAS"]], use_container_width=True, hide_index=True)

                    with tab_peng:
                        df_peng = df_summary_kum[df_summary_kum["KOLUM JAWATAN"]=="PENGAWAS PEPERIKSAAN"].copy()
                        st.markdown(f"**{len(df_peng)} Pengawas telah dilantik (kumulatif):**")
                        if df_peng.empty:
                            st.info("Belum ada Pengawas")
                        else:
                            st.dataframe(df_peng[["BIL","NAMA GURU","IC","SEKOLAH ASAL","NAMA SEKOLAH ASAL","PUSAT TUGAS"]], use_container_width=True, hide_index=True)

                    with tab_semua:
                        st.markdown(f"**📋 Ringkasan Kumulatif Keseluruhan: {len(df_summary_kum)} guru telah dilantik manual - Lantikan pertama kekal bila tambah lantikan kedua:**")
                        st.dataframe(df_summary_kum, use_container_width=True, hide_index=True)
                        # Export kumulatif
                        try:
                            import io
                            output = io.BytesIO()
                            with __import__("pandas").ExcelWriter(output, engine='openpyxl') as writer:
                                df_summary_kum.to_excel(writer, index=False, sheet_name='Kumulatif Semua')
                                if not df_kp.empty:
                                    df_kp.to_excel(writer, index=False, sheet_name='Ketua Pengawas')
                                if not df_tkp.empty:
                                    df_tkp.to_excel(writer, index=False, sheet_name='Timbalan KP')
                                if not df_peng.empty:
                                    df_peng.to_excel(writer, index=False, sheet_name='Pengawas')
                            st.download_button("📥 Export Excel Kumulatif (4 Sheet Ikut Jawatan)", data=output.getvalue(), file_name=f"ringkasan_manual_kumulatif_{kod_ppd}_{__import__('datetime').date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="export_kum_manual_excel")
                        except Exception as e:
                            st.caption(f"Export error: {e}")
                            st.download_button("📥 Export CSV Kumulatif", df_summary_kum.to_csv(index=False).encode('utf-8'), file_name=f"ringkasan_manual_kumulatif_{kod_ppd}.csv", mime="text/csv", use_container_width=True, key="export_kum_csv")

                    # Info tambahan: papar lantikan untuk pusat semasa juga (supaya nampak konteks)
                    st.markdown("---")
                    st.markdown(f"#### 📍 Lantikan Untuk Pusat Semasa: {pilih_pusat_manual}")
                    if tugas_pusat_ini:
                        all_rows_curr = []
                        for c in tugas_pusat_ini.values():
                            all_rows_curr.append({"NAMA": c.get("NAMA_GURU", ""), "IC": c.get("IC_GURU", ""), "JAWATAN": c.get("JAWATAN_CADANGAN", ""), "SEKOLAH ASAL": c.get("KOD_SEKOLAH_ASAL", ""), "PUSAT": pilih_pusat_manual})
                        df_curr_sum = __import__("pandas").DataFrame(all_rows_curr)
                        st.dataframe(df_curr_sum, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"Belum ada penempatan di {pilih_pusat_manual} - ini paparan pusat semasa sahaja, ringkasan kumulatif di atas kekal")
            else:
                st.info(f"Belum ada penempatan manual di PPD {kod_ppd} - Sila lantik KP, TKP, Pengawas di atas. Ringkasan kumulatif akan muncul di sini dan tidak hilang bila pilih sekolah kedua.")

        elif menu == "zon":
            render_penempatan_zon(kod_ppd, fly_cur)

        elif menu == "cadangan" and fly_cur == "nama":
            render_senarai_nama(kod_ppd)

        elif menu == "cadangan" and fly_cur == "simpanan":
            render_senarai_simpanan(kod_ppd)

        elif menu == "cadangan":
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #1565c0 0%, #1e88e5 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
                <h2 style="margin:0; color:white;">📋 Cadangan SUP - PPD {kod_ppd} - {PPD_MAP.get(kod_ppd, '')}</h2>
                <p style="margin:5px 0 0 0; color:#bbdefb;">Pilih sekolah dalam daerah untuk lihat senarai cadangan dari sekolah berkenaan</p>
            </div>
            ''', unsafe_allow_html=True)

            df_cad_all = get_cadangan_df(kod_ppd=kod_ppd)
            if df_cad_all.empty:
                st.warning(f"Belum ada cadangan SUP untuk PPD {kod_ppd}")
                st.stop()

            # ===== FILTER IKUT JAWATAN (MESTI AWAL) + CLEAN NAN =====
            # Clean NAN rows from df_cad_all - remove rows where KOD_SEKOLAH_ASAL is NAN/nan/None/empty
            def is_valid_sekolah(row):
                kod = str(row.get("KOD_SEKOLAH_ASAL") or row.get("kod_sekolah_asal") or row.get("KOD_SEKOLAH") or row.get("kod_sekolah") or "").strip()
                if kod.lower() in ("", "nan", "none", "null", "nat", "-"):
                    return False
                return True

            # Filter out NAN sekolah for display, but keep count for info
            df_cad_valid = df_cad_all[df_cad_all.apply(is_valid_sekolah, axis=1)].copy()
            df_cad_invalid = df_cad_all[~df_cad_all.apply(is_valid_sekolah, axis=1)].copy()
            if not df_cad_invalid.empty:
                st.warning(f"⚠️ Ada {len(df_cad_invalid)} cadangan dengan KOD SEKOLAH kosong/NAN - akan disembunyikan dari senarai sekolah. Sila betulkan di SUP.")

            jawatan_list_all = []
            for _, r in df_cad_valid.iterrows():
                j = str(r.get("JAWATAN_CADANGAN") or r.get("jawatan_cadangan") or r.get("JAWATAN") or "").strip()
                if j and j.lower() not in ("", "nan", "none") and j not in jawatan_list_all:
                    jawatan_list_all.append(j)
            order_jawatan = ["Ketua Pengawas", "Timbalan Ketua Pengawas", "Penyelia Kawasan", "Pengawas Peperiksaan", "Selenggara Bilik Kebal", "Juru Tulis", "Juru Baca", "Ketua Pengawas Hospital", "Pengawas Hospital", "Pengawas Pengiring", "Pengemas Bilik"]
            jawatan_sorted = sorted(jawatan_list_all, key=lambda x: (order_jawatan.index(x) if x in order_jawatan else 99, x))

            # Default filter from session
            filter_jawatan = st.session_state.get("filter_jawatan_cad", [])
            if filter_jawatan is None:
                filter_jawatan = []

            # Init df_cad_filtered as valid first
            df_cad_filtered = df_cad_valid.copy()
            if filter_jawatan:
                df_cad_filtered = df_cad_valid[df_cad_valid.apply(lambda r: str(r.get("JAWATAN_CADANGAN") or r.get("jawatan_cadangan") or r.get("JAWATAN") or "").strip() in filter_jawatan, axis=1)].copy()

            # Get sekolah list in PPD
            try:
                res_sek = supa.table("sekolah_master").select("*").eq("kod_ppd", kod_ppd).limit(2000).execute()
                df_sek_list = pd.DataFrame(res_sek.data or [])
            except:
                df_sek_list = pd.DataFrame()

            # Build sekolah groups dari cadangan (ikut filter) - SKIP NAN + STRICT PPD CHECK
            # Safety: get sekolah list for this PPD again to ensure no cross-PPD leak
            kod_list_ppd_check = []
            try:
                res_sek_check = supa.table("sekolah_master").select("kod_sekolah").eq("kod_ppd", kod_ppd.upper()).limit(2000).execute()
                kod_list_ppd_check = [str(s.get('kod_sekolah','')).upper().strip() for s in (res_sek_check.data or [])]
            except:
                kod_list_ppd_check = []

            sekolah_groups = {}
            for _, r in df_cad_filtered.iterrows():
                # Extra strict check: if sekolah code not in PPD list and KOD_PPD != requested PPD, skip
                kppd_row = str(r.get("KOD_PPD") or "").upper().strip()
                ksek_row = str(r.get("KOD_SEKOLAH_ASAL") or "").upper().strip()
                if kod_list_ppd_check:
                    if ksek_row not in kod_list_ppd_check and kppd_row != kod_ppd.upper():
                        continue
                else:
                    # If no list, check KOD_PPD exact
                    if kppd_row and kppd_row != kod_ppd.upper():
                        continue
                kod_sek_raw = r.get("KOD_SEKOLAH_ASAL") or r.get("kod_sekolah_asal") or r.get("KOD_SEKOLAH") or r.get("kod_sekolah") or ""
                kod_sek = str(kod_sek_raw).strip().upper()
                if kod_sek.lower() in ("", "nan", "none", "null", "nat", "-", "tiada kod"):
                    continue
                nama_sek_raw = r.get("NAMA_SEKOLAH_ASAL") or r.get("nama_sekolah_asal") or r.get("NAMA_SEKOLAH") or kod_sek
                nama_sek = str(nama_sek_raw).strip()
                if nama_sek.lower() in ("", "nan", "none", "null"):
                    nama_sek = kod_sek
                nama_sek = nama_sek[:50]
                key = f"{kod_sek} - {nama_sek}"
                if key not in sekolah_groups:
                    sekolah_groups[key] = []
                sekolah_groups[key].append(r)

            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏫 Sekolah Mencadang", len(sekolah_groups))
            with col2:
                st.metric("👥 Jumlah Cadangan", len(df_cad_all))
            with col3:
                # Belum vs sudah lantik
                def is_belum(row):
                    kp = str(row.get("kod_pusat") or row.get("KOD_PUSAT") or "").strip()
                    return kp == "" or kp.lower() in ("none", "null", "nan", "nat")
                belum = df_cad_all[df_cad_all.apply(is_belum, axis=1)]
                st.metric("✅ Belum Dilantik", len(belum), delta=f"{len(df_cad_all)-len(belum)} telah dilantik")

            st.markdown("### 🔍 Filter Ikut Jawatan")
            st.caption("Filter untuk tengok siapa Penyelia Kawasan, Ketua Pengawas, Timbalan, Pengawas Peperiksaan - senang PPD semak")

            # V20: SIMPLE - no widget key manipulation at all, use direct variable
            if "filter_jawatan_cad" not in st.session_state:
                st.session_state["filter_jawatan_cad"] = []

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                # V21 FIX DefaultNotInOptionsError: pastikan default ada dalam options
                # Jika Penyelia Kawasan tidak ada dalam jawatan_sorted (data kosong), tambah manual
                safe_default = [x for x in st.session_state["filter_jawatan_cad"] if x in jawatan_sorted]
                # Jika user pilih Penyelia Kawasan tapi jawatan_sorted kosong, tetap tunjuk semua option yang mungkin
                if not jawatan_sorted:
                    jawatan_sorted = ["Ketua Pengawas", "Timbalan Ketua Pengawas", "Penyelia Kawasan", "Pengawas Peperiksaan", "Juru Tulis", "Juru Baca", "Ketua Pengawas Hospital", "Pengawas Hospital", "Pengawas Pengiring", "Pengemas Bilik"]
                    safe_default = st.session_state["filter_jawatan_cad"]
                # Jika safe_default kosong tapi session ada value yang bukan dalam options, guna empty supaya tak error
                # Tapi untuk kes Penyelia Kawasan, kita benarkan jika memang dalam senarai tetap
                if st.session_state["filter_jawatan_cad"] and not safe_default:
                    # Kalau filter ada tapi takde dalam options, jangan error - guna filter tu sebagai options tambahan
                    for v in st.session_state["filter_jawatan_cad"]:
                        if v not in jawatan_sorted:
                            jawatan_sorted.append(v)
                    safe_default = st.session_state["filter_jawatan_cad"]

                filter_jawatan_ui = st.multiselect("Filter Jawatan", jawatan_sorted, default=safe_default, placeholder="Pilih jawatan - kosong = semua")
            with col_f2:
                if filter_jawatan_ui:
                    st.metric(f"Filter: {len(filter_jawatan_ui)} jawatan", f"{len(df_cad_valid[df_cad_valid.apply(lambda r: str(r.get('JAWATAN_CADANGAN') or r.get('jawatan_cadangan') or r.get('JAWATAN') or '').strip() in filter_jawatan_ui, axis=1)]) if filter_jawatan_ui else len(df_cad_all)} guru")
                else:
                    st.metric("Semua Jawatan", f"{len(df_cad_all)} guru")
            with col_f3:
                if st.button("🔐 Hanya Penyelia Kawasan", use_container_width=True, key="btn_filter_pk"):
                    st.session_state["filter_jawatan_cad"] = ["Penyelia Kawasan"]
                    st.rerun()
            with col_f4:
                if st.button("🔄 Clear Filter", use_container_width=True, key="btn_clear_filter"):
                    st.session_state["filter_jawatan_cad"] = []
                    st.rerun()

            # V22 ROBUST: filter using normalized lowercase contains
            def match_jawatan(row_jawatan, filter_list):
                if not filter_list:
                    return True
                rj = str(row_jawatan).strip().lower()
                rj = ' '.join(rj.split())
                for f in filter_list:
                    f_low = str(f).strip().lower()
                    f_low = ' '.join(f_low.split())
                    # Exact or contains
                    if f_low == rj or f_low in rj or rj in f_low:
                        return True
                    # Special for Penyelia Kawasan - check both words
                    if 'penyelia' in f_low and 'penyelia' in rj:
                        return True
                return False

            # Determine active filter list
            active_filter = filter_jawatan_ui if filter_jawatan_ui else st.session_state.get("filter_jawatan_cad", [])

            if active_filter:
                df_cad_filtered = df_cad_valid[df_cad_valid['JAWATAN_CADANGAN'].apply(lambda x: match_jawatan(x, active_filter))].copy()
                # Save for next run default
                if active_filter != st.session_state["filter_jawatan_cad"]:
                    st.session_state["filter_jawatan_cad"] = active_filter
                filter_jawatan_ui = active_filter
            else:
                df_cad_filtered = df_cad_valid.copy()

            if active_filter and len(df_cad_filtered) == 0:
                st.info("Tiada guru yang sepadan dengan penapis jawatan yang dipilih.")

            if st.session_state.get("filter_jawatan_cad"):
                st.success(f"✅ Filter aktif: {', '.join(st.session_state.get('filter_jawatan_cad', []))} - Jumpa {len(df_cad_filtered)} guru")

            # Show breakdown by jawatan
            st.markdown("#### 📊 Pecahan Ikut Jawatan")
            jawatan_counts = {}
            for _, r in df_cad_filtered.iterrows():
                j = str(r.get("JAWATAN_CADANGAN") or r.get("jawatan_cadangan") or "TIADA").strip()
                jawatan_counts[j] = jawatan_counts.get(j, 0) + 1

            if jawatan_counts:
                cols_j = st.columns(len(jawatan_counts))
                for idx, (j, cnt) in enumerate(sorted(jawatan_counts.items(), key=lambda x: (order_jawatan.index(x[0]) if x[0] in order_jawatan else 99, x[0]))):
                    with cols_j[idx % len(cols_j)]:
                        icon = "👑" if "Ketua Pengawas" in j and "Timbalan" not in j else "🎖️" if "Timbalan" in j else "🔐" if "Penyelia" in j else "👨‍🏫" if "Pengawas" in j else "🔧"
                        st.metric(f"{icon} {j}", cnt)

            st.markdown("---")

            # Ringkasan ikut sekolah
            st.markdown("### 📋 Ringkasan Cadangan Mengikut Sekolah (Ikut Filter Jawatan)")
            summary_rows = []
            for key, guru_list in sorted(sekolah_groups.items()):
                kod = key.split(" - ")[0]
                nama = key.split(" - ", 1)[1] if " - " in key else key
                # Kira belum vs sudah
                def _is_sudah_lantik(g):
                    kp = str(g.get("kod_pusat") or g.get("KOD_PUSAT") or g.get("kod_pusat_tugas") or "").strip()
                    status = str(g.get("status") or g.get("STATUS") or "").upper().strip()
                    if kp == "" or kp.lower() in ("none","null","nan","nat",""):
                        return False
                    # Jika kod_pusat == no_pusat_asal dan status HANTAR KE PPD, itu BUKAN sudah lantik (bug lama)
                    no_asal = str(g.get("no_pusat_asal") or g.get("NO_PUSAT_ASAL") or "").upper().strip()
                    if kp.upper() == no_asal and "HANTAR KE PPD" in status:
                        return False
                    # Sudah lantik jika ada kod_pusat dan status LULUS/DILANTIK/SURAT
                    if any(x in status for x in ["LULUS","DILANTIK","DITEMPATKAN","SURAT","SAH"]):
                        return True
                    # Jika kod_pusat ada tapi status masih HANTAR/DICADANGKAN, masih belum lantik
                    if "HANTAR KE PPD" in status or "DICADANGKAN" in status:
                        return False
                    # Default: kalau ada kod_pusat dan bukan HANTAR/DICADANGKAN, anggap sudah
                    return kp != ""
                belum_cnt = sum(1 for g in guru_list if not _is_sudah_lantik(g))
                sudah_cnt = len(guru_list) - belum_cnt
                summary_rows.append({
                    "KOD SEKOLAH": kod,
                    "NAMA SEKOLAH": nama[:35],
                    "JUMLAH CADANGAN": len(guru_list),
                    "BELUM LANTIK": belum_cnt,
                    "SUDAH LANTIK": sudah_cnt,
                    "status": "✅ Lengkap" if belum_cnt == 0 else f"⏳ {belum_cnt} belum"
                })
            df_summary = pd.DataFrame(summary_rows)
            st.dataframe(df_summary, use_container_width=True, hide_index=True)
            st.download_button("📥 Export Ringkasan Cadangan Ikut Sekolah", to_excel(df_summary), file_name=f"ringkasan_cadangan_{kod_ppd}.xlsx", use_container_width=True)

            st.markdown("---")
            st.markdown("### 🔍 Detail Cadangan Ikut Sekolah - Pilih Sekolah (Ikut Filter Jawatan)")
            if filter_jawatan:
                st.info(f"📋 Menunjukkan guru dengan jawatan: {', '.join(filter_jawatan)} sahaja. Clear filter untuk lihat semua.")

            # Pilih sekolah dropdown
            pilih_sek_cad = st.selectbox(
                "Pilih Sekolah Dalam Daerah Untuk Lihat Senarai Cadangan",
                sorted(sekolah_groups.keys()),
                format_func=lambda x: f"{x} ({len(sekolah_groups[x])} cadangan)",
                key="pilih_sekolah_cadangan"
            )

            if pilih_sek_cad:
                guru_list = sekolah_groups[pilih_sek_cad]
                st.markdown(f"#### 🏫 {pilih_sek_cad} - {len(guru_list)} cadangan")

                # Filter tabs: Semua, Belum Lantik, Sudah Lantik
                tab_all, tab_belum, tab_sudah = st.tabs(["📋 Semua", "⏳ Belum Dilantik", "✅ Sudah Dilantik"])

                def make_df_from_list(g_list):
                    rows = []
                    for g in g_list:
                        rows.append({
                            "NAMA GURU": g.get("NAMA_GURU", "") or g.get("nama_guru", ""),
                            "NO IC": g.get("IC_GURU", "") or g.get("ic_guru", ""),
                            "JAWATAN": g.get("JAWATAN_CADANGAN", "") or g.get("jawatan_cadangan", ""),
                            "JANTINA": g.get("JANTINA", "") or g.get("jantina", ""),
                            "TELEFON": g.get("TELEFON_GURU", "") or g.get("telefon_guru", ""),
                            "KOD PUSAT": g.get("kod_pusat", "") or g.get("KOD_PUSAT", "") or "- Belum -",
                            "STATUS": g.get("status", "") or g.get("STATUS", ""),
                            "SEKOLAH": g.get("KOD_SEKOLAH_ASAL", "") or g.get("kod_sekolah_asal", "")
                        })
                    return pd.DataFrame(rows)

                with tab_all:
                    # Additional filter inside school view by jawatan
                    if filter_jawatan:
                        guru_list_filtered_j = [g for g in guru_list if str(g.get("JAWATAN_CADANGAN") or g.get("jawatan_cadangan") or "").strip() in filter_jawatan]
                    else:
                        guru_list_filtered_j = guru_list

                    df_all_guru = make_df_from_list(guru_list_filtered_j)
                    if filter_jawatan:
                        st.caption(f"Filter aktif: {', '.join(filter_jawatan)} - {len(guru_list_filtered_j)} guru dalam sekolah ini")
                    st.dataframe(df_all_guru, use_container_width=True, hide_index=True)
                    st.download_button(f"📥 Export {pilih_sek_cad.split(' - ')[0]} - Semua", to_excel(df_all_guru), file_name=f"cadangan_{pilih_sek_cad.split(' - ')[0]}_semua.xlsx", use_container_width=True, key="exp_all")

                    # Show jawatan breakdown for this school
                    if guru_list_filtered_j:
                        j_count_school = {}
                        for g in guru_list_filtered_j:
                            jj = str(g.get("JAWATAN_CADANGAN") or g.get("jawatan_cadangan") or "TIADA").strip()
                            j_count_school[jj] = j_count_school.get(jj, 0) + 1
                        cols_js = st.columns(len(j_count_school))
                        for idx, (jj, cnt) in enumerate(j_count_school.items()):
                            with cols_js[idx]:
                                st.metric(jj, cnt)

                with tab_belum:
                    def _check_sudah(g):
                        kp = str(g.get("kod_pusat") or g.get("KOD_PUSAT") or "").strip()
                        stt = str(g.get("status") or g.get("STATUS") or "").upper()
                        no_asal = str(g.get("no_pusat_asal") or g.get("NO_PUSAT_ASAL") or "").upper().strip()
                        if kp == "" or kp.lower() in ("none","null","nan","nat",""):
                            return False
                        if kp.upper() == no_asal and "HANTAR KE PPD" in stt:
                            return False
                        if "HANTAR KE PPD" in stt or "DICADANGKAN" in stt:
                            return False
                        if any(x in stt for x in ["LULUS","DILANTIK","DITEMPATKAN","SURAT"]):
                            return True
                        return kp != ""
                    belum_list = [g for g in guru_list if not _check_sudah(g)]
                    st.markdown(f"**{len(belum_list)} guru belum dilantik dari {pilih_sek_cad}**")
                    if belum_list:
                        df_belum_guru = make_df_from_list(belum_list)
                        st.dataframe(df_belum_guru, use_container_width=True, hide_index=True)
                        st.download_button(f"📥 Export Belum Lantik", to_excel(df_belum_guru), file_name=f"cadangan_{pilih_sek_cad.split(' - ')[0]}_belum.xlsx", use_container_width=True, key="exp_belum")
                    else:
                        st.success("✅ Semua guru dari sekolah ini telah dilantik!")

                with tab_sudah:
                    sudah_list = [g for g in guru_list if _check_sudah(g)]
                    st.markdown(f"**{len(sudah_list)} guru sudah dilantik dari {pilih_sek_cad}**")
                    if sudah_list:
                        df_sudah_guru = make_df_from_list(sudah_list)
                        st.dataframe(df_sudah_guru, use_container_width=True, hide_index=True)
                        st.download_button(f"📥 Export Sudah Lantik", to_excel(df_sudah_guru), file_name=f"cadangan_{pilih_sek_cad.split(' - ')[0]}_sudah.xlsx", use_container_width=True, key="exp_sudah")
                    else:
                        st.info("Belum ada guru dilantik dari sekolah ini")


        elif menu == "semakan":
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
                <h2 style="margin:0; color:white;">🔍 Semakan Lantikan Ikut Pusat - PPD {kod_ppd}</h2>
                <p style="margin:5px 0 0 0; color:#e3f2fd;">Pilih pusat, akan keluar 4 table ikut jawatan: Penyelia Kawasan, Ketua Pengawas, Timbalan, Pengawas. PPD boleh batalkan lantikan & guru masuk semula ke cadangan untuk pilih pusat lain. Boleh isi kekosongan dengan guru lain.</p>
            </div>
            """, unsafe_allow_html=True)

            df_pusat_raw = get_pusat_df()
            df_cad_all = get_cadangan_df(kod_ppd=kod_ppd)

            if df_pusat_raw.empty:
                st.warning("Tiada pusat_master")
                st.stop()
            if df_cad_all.empty:
                st.warning("Belum ada cadangan")
                st.stop()

            # Parse pusat list
            pusat_list = []
            for _, r in df_pusat_raw.iterrows():
                d = r.get("data") if isinstance(r.get("data"), dict) else {}
                if isinstance(d, str):
                    try: d = json.loads(d)
                    except: d = {}
                no_pusat = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                if not no_pusat.startswith(kod_ppd.upper()): continue
                nama = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                pusat_list.append({"NO_PUSAT": no_pusat, "NAMA_PUSAT": nama})
            df_pusat_list = __import__("pandas").DataFrame(pusat_list)

            if df_pusat_list.empty:
                st.warning(f"Tiada pusat untuk PPD {kod_ppd}")
                st.stop()

            # Pilih pusat
            pilihan_pusat_semak = st.selectbox(
                "📍 Pilih Pusat Untuk Semakan Lantikan",
                df_pusat_list["NO_PUSAT"].tolist(),
                format_func=lambda x: f"{x} - {df_pusat_list[df_pusat_list['NO_PUSAT']==x]['NAMA_PUSAT'].values[0][:35] if not df_pusat_list[df_pusat_list['NO_PUSAT']==x].empty else x}",
                key="pilih_pusat_semakan"
            )

            st.markdown(f"### 🔍 Semakan Lantikan - Pusat {pilihan_pusat_semak}")

            # Get lantikan for this pusat
            try:
                res_lantik = supa.table("cadangan_sup").select("*").eq("kod_pusat", pilihan_pusat_semak).limit(5000).execute()
                df_lantik_pusat = __import__("pandas").DataFrame(res_lantik.data or [])
            except Exception as e:
                st.error(f"Error baca lantikan: {e}")
                df_lantik_pusat = __import__("pandas").DataFrame()

            if fly_cur == "semak":
                if df_lantik_pusat.empty:
                    st.warning(f"Belum ada lantikan di pusat {pilihan_pusat_semak}")
                    # Still allow to add guru
                    df_lantik_pusat = __import__("pandas").DataFrame()
                else:
                    st.success(f"Ada {len(df_lantik_pusat)} lantikan di {pilihan_pusat_semak}")

                # Helper to get jawatan groups
                def get_jawatan_group(df, keyword, exclude_keywords=[]):
                    if df.empty:
                        return __import__("pandas").DataFrame()
                    def match(row):
                        jaw = str(row.get("jawatan_cadangan") or row.get("JAWATAN_CADANGAN") or "").upper()
                        if keyword.upper() not in jaw:
                            return False
                        for ex in exclude_keywords:
                            if ex.upper() in jaw:
                                # Special handling for Ketua vs Timbalan
                                if keyword.upper()=="KETUA PENGAWAS" and "TIMBALAN" in jaw:
                                    return False
                                if keyword.upper()=="PENYELIA" and ex.upper() not in jaw:
                                    continue
                        # For Ketua Pengawas, exclude Timbalan
                        if keyword.upper()=="KETUA PENGAWAS" and "TIMBALAN" in jaw:
                            return False
                        # For Pengawas Peperiksaan, exclude Ketua, Timbalan, Penyelia
                        if keyword.upper()=="PENGAWAS" and any(k in jaw for k in ["KETUA","TIMBALAN","PENYELIA","SELENGGARA"]):
                            return False
                        return True
                    return df[df.apply(match, axis=1)].copy()

                # Split into 4 groups
                # Penyelia Kawasan
                df_penyelia = df_lantik_pusat[df_lantik_pusat.apply(lambda r: "PENYELIA" in str(r.get("jawatan_cadangan") or "").upper(), axis=1)].copy() if not df_lantik_pusat.empty else __import__("pandas").DataFrame()
                # Ketua Pengawas
                df_kp = df_lantik_pusat[df_lantik_pusat.apply(lambda r: "KETUA PENGAWAS" in str(r.get("jawatan_cadangan") or "").upper() and "TIMBALAN" not in str(r.get("jawatan_cadangan") or "").upper(), axis=1)].copy() if not df_lantik_pusat.empty else __import__("pandas").DataFrame()
                # Timbalan
                df_tkp = df_lantik_pusat[df_lantik_pusat.apply(lambda r: "TIMBALAN" in str(r.get("jawatan_cadangan") or "").upper(), axis=1)].copy() if not df_lantik_pusat.empty else __import__("pandas").DataFrame()
                # Pengawas
                df_peng = df_lantik_pusat[df_lantik_pusat.apply(lambda r: "PENGAWAS" in str(r.get("jawatan_cadangan") or "").upper() and "KETUA" not in str(r.get("jawatan_cadangan") or "").upper() and "TIMBALAN" not in str(r.get("jawatan_cadangan") or "").upper() and "PENYELIA" not in str(r.get("jawatan_cadangan") or "").upper(), axis=1)].copy() if not df_lantik_pusat.empty else __import__("pandas").DataFrame()

                # Function to display table with batal action
                def display_jawatan_table(df_jawatan, tajuk, icon, color, jawatan_name):
                    st.markdown(f"""
                <div style="background: {color}; padding:12px; border-radius:8px; color:white; margin:15px 0 10px 0;">
                    <h3 style="margin:0; color:white;">{icon} {tajuk} - {len(df_jawatan)} orang di {pilihan_pusat_semak}</h3>
                </div>
                """, unsafe_allow_html=True)

                    if df_jawatan.empty:
                        st.info(f"Belum ada {tajuk} di pusat ini")
                        return

                    # Build display rows
                    rows = []
                    for _, r in df_jawatan.iterrows():
                        rows.append({
                            "id": r.get("id",""),
                            "NAMA GURU": r.get("nama_guru","") or r.get("NAMA_GURU",""),
                            "IC": r.get("ic_guru","") or r.get("IC_GURU",""),
                            "JAWATAN": r.get("jawatan_cadangan","") or r.get("JAWATAN_CADANGAN",""),
                            "SEKOLAH ASAL": r.get("kod_sekolah_asal","") or r.get("KOD_SEKOLAH_ASAL",""),
                            "NAMA SEKOLAH ASAL": str(r.get("nama_sekolah_asal","") or r.get("NAMA_SEKOLAH_ASAL",""))[:25],
                            "POSKOD RUMAH": r.get("poskod_rumah","") or r.get("POSKOD_RUMAH",""),
                            "TELEFON": r.get("telefon_guru","") or r.get("TELEFON_GURU",""),
                            "STATUS": r.get("status","") or r.get("STATUS","")
                        })
                    df_disp = __import__("pandas").DataFrame(rows)
                    st.dataframe(df_disp, use_container_width=True, hide_index=True)

                    # Batalkan lantikan section
                    with st.expander(f"❌ Batalkan Lantikan {tajuk} di {pilihan_pusat_semak}", expanded=False):
                        st.warning(f"Jika PPD rasa guru ini tidak sesuai di {pilihan_pusat_semak}, boleh batalkan. Guru akan masuk semula ke bahagian cadangan SUP untuk dipilih di pusat lain.")
                        batal_ids = st.multiselect(
                            f"Pilih {tajuk} untuk batalkan lantikan di {pilihan_pusat_semak}",
                            df_disp["id"].tolist(),
                            format_func=lambda x: f"{df_disp[df_disp['id']==x]['NAMA GURU'].values[0]} - {df_disp[df_disp['id']==x]['SEKOLAH ASAL'].values[0]} - {df_disp[df_disp['id']==x]['IC'].values[0]}" if not df_disp[df_disp['id']==x].empty else str(x),
                            key=f"batal_{jawatan_name}_{pilihan_pusat_semak}"
                        )
                        if batal_ids:
                            st.error(f"Anda akan batalkan {len(batal_ids)} {tajuk} dari {pilihan_pusat_semak}. Guru akan kembali ke cadangan SUP (kod_pusat = NULL, status = HANTAR KE PPD).")
                            if st.button(f"❌ Confirm Batalkan {len(batal_ids)} {tajuk} dari {pilihan_pusat_semak}", type="primary", use_container_width=True, key=f"btn_batal_{jawatan_name}_{pilihan_pusat_semak}"):
                                try:
                                    berjaya = 0
                                    for gid in batal_ids:
                                        # Batalkan: set kod_pusat None, status HANTAR KE PPD supaya masuk semula ke cadangan
                                        supa.table("cadangan_sup").update({"kod_pusat": None, "status": "HANTAR KE PPD", "status": "HANTAR KE PPD"}).eq("id", gid).execute()
                                        berjaya+=1
                                    st.success(f"✅ Berjaya batalkan {berjaya} {tajuk} dari {pilihan_pusat_semak}. Guru masuk semula ke cadangan SUP untuk dipilih di pusat lain.")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Gagal batal: {e}")

                # Display 4 tables
                display_jawatan_table(df_penyelia, "Penyelia Kawasan", "🔐", "linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)", "penyelia")
                display_jawatan_table(df_kp, "Ketua Pengawas", "👑", "linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)", "kp")
                display_jawatan_table(df_tkp, "Timbalan Ketua Pengawas", "🎖️", "linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)", "tkp")
                display_jawatan_table(df_peng, "Pengawas Peperiksaan", "👨‍🏫", "linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)", "pengawas")

            if fly_cur == "kosong":
                st.markdown("---")
                st.markdown(f"### ➕ Isi Kekosongan di {pilihan_pusat_semak} - Pilih Guru Lain")
                st.info(f"Selepas batalkan lantikan di atas, PPD boleh pilih guru lain dari cadangan SUP untuk isi kekosongan di {pilihan_pusat_semak}. Guru yang dibatalkan tadi sudah masuk semula ke pool cadangan.")

                # Get guru yang belum dilantik (pool untuk isi kekosongan)
                try:
                    df_belum_pool = df_cad_all[df_cad_all.apply(lambda r: str(r.get("kod_pusat") or r.get("KOD_PUSAT") or "").strip() in ("", "None", "none", "null", "nan", "nat"), axis=1)].copy()
                except:
                    df_belum_pool = __import__("pandas").DataFrame()

                if df_belum_pool.empty:
                    st.warning("Tiada guru dalam pool cadangan yang belum dilantik - semua sudah dilantik. Batalkan dulu lantikan di atas untuk kembalikan guru ke pool.")
                else:
                    st.markdown(f"**{len(df_belum_pool)} guru dalam pool belum dilantik - boleh pilih untuk isi kekosongan di {pilihan_pusat_semak}:**")

                    # Filter by jawatan for easier selection
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        filter_jawatan_semak = st.selectbox(
                            "Filter Ikut Jawatan Untuk Isi Kekosongan",
                            ["Semua Jawatan", "Ketua Pengawas", "Timbalan Ketua Pengawas", "Pengawas Peperiksaan", "Penyelia Kawasan", "Juru Tulis", "Juru Baca", "Ketua Pengawas Hospital", "Pengawas Hospital", "Pengawas Pengiring", "Pengemas Bilik"],
                            key=f"filter_jawatan_semak_{pilihan_pusat_semak}"
                        )
                    with col_f2:
                        # Info pusat tuan rumah for max3 check
                        info_pusat_semak = df_pusat_list[df_pusat_list["NO_PUSAT"]==pilihan_pusat_semak]
                        # Get current count per sekolah in this pusat
                        sekolah_count_semak = {}
                        if not df_lantik_pusat.empty:
                            for _, r in df_lantik_pusat.iterrows():
                                ks = str(r.get("kod_sekolah_asal") or "").upper().strip()
                                sekolah_count_semak[ks] = sekolah_count_semak.get(ks, 0) + 1
                        st.caption(f"Pusat {pilihan_pusat_semak} sudah ada {len(df_lantik_pusat)} petugas. Max 3 per sekolah. Count: {sekolah_count_semak}")

                    df_pool_filtered = df_belum_pool.copy()
                    if filter_jawatan_semak != "Semua Jawatan":
                        def match_filter(r, target):
                            jaw = str(r.get("JAWATAN_CADANGAN") or r.get("jawatan_cadangan") or "").upper()
                            tgt = target.upper()
                            if "KETUA PENGAWAS" in tgt and "TIMBALAN" not in tgt:
                                return "KETUA PENGAWAS" in jaw and "TIMBALAN" not in jaw
                            elif "TIMBALAN" in tgt:
                                return "TIMBALAN" in jaw
                            elif "PENGAWAS PEPERIKSAAN" in tgt:
                                return "PENGAWAS PEPERIKSAAN" in jaw or jaw.strip()=="PENGAWAS"
                            elif "PENYELIA" in tgt:
                                return "PENYELIA" in jaw
                            else:
                                return tgt in jaw
                        df_pool_filtered = df_pool_filtered[df_pool_filtered.apply(lambda r: match_filter(r, filter_jawatan_semak), axis=1)].copy()

                    # Filter out sekolah tuan rumah and max3
                    # Get kod tuan rumah
                    kod_tuan_semak = ""
                    try:
                        df_pusat_raw_all = get_pusat_df()
                        for _, pr in df_pusat_raw_all.iterrows():
                            d = pr.get("data") if isinstance(pr.get("data"), dict) else {}
                            if isinstance(d, str):
                                try: d = json.loads(d)
                                except: d = {}
                            no_p = str(pr.get("no_pusat") or pr.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                            if no_p == pilihan_pusat_semak:
                                kod_tuan_semak = str(pr.get("kod_sekolah_tuan_rumah") or pr.get("kod_sekolah") or d.get("KOD_SEKOLAH") or "").upper().strip()
                                break
                    except:
                        kod_tuan_semak = ""

                    df_pool_layak = df_pool_filtered.copy()
                    if kod_tuan_semak:
                        df_pool_layak = df_pool_layak[~df_pool_layak.apply(lambda r: str(r.get("KOD_SEKOLAH_ASAL") or r.get("kod_sekolah_asal") or "").upper().strip() == kod_tuan_semak, axis=1)]

                    # Check max3
                    def check_max3_semak(row):
                        kod = str(row.get("KOD_SEKOLAH_ASAL") or row.get("kod_sekolah_asal") or "").upper().strip()
                        return sekolah_count_semak.get(kod, 0) < 3 if kod else True
                    df_pool_layak = df_pool_layak[df_pool_layak.apply(check_max3_semak, axis=1)].copy()

                    st.markdown(f"**{len(df_pool_layak)} calon layak untuk isi kekosongan di {pilihan_pusat_semak} (selepas filter {filter_jawatan_semak}, elak sekolah sendiri & max3):**")

                    if df_pool_layak.empty:
                        st.warning("Tiada calon layak untuk pusat ini")
                    else:
                        display_pool = []
                        for _, r in df_pool_layak.iterrows():
                            display_pool.append({
                                "id": r.get("id",""),
                                "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                                "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                                "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                                "POSKOD": r.get("POSKOD_RUMAH","") or r.get("poskod_rumah",""),
                                "STATUS": r.get("STATUS","") or r.get("status","")
                            })
                        df_pool_disp = __import__("pandas").DataFrame(display_pool)
                        st.dataframe(df_pool_disp, use_container_width=True, hide_index=True)

                        pilih_guru_isi = st.multiselect(
                            f"Pilih guru untuk isi kekosongan di {pilihan_pusat_semak}",
                            df_pool_disp["id"].tolist(),
                            format_func=lambda x: f"{df_pool_disp[df_pool_disp['id']==x]['NAMA GURU'].values[0]} - {df_pool_disp[df_pool_disp['id']==x]['SEKOLAH ASAL'].values[0]} - {df_pool_disp[df_pool_disp['id']==x]['JAWATAN'].values[0]}" if not df_pool_disp[df_pool_disp['id']==x].empty else str(x),
                            key=f"pilih_guru_isi_{pilihan_pusat_semak}"
                        )

                        if pilih_guru_isi:
                            if st.button(f"✅ Lantik {len(pilih_guru_isi)} Guru Terpilih ke {pilihan_pusat_semak} Untuk Isi Kekosongan", type="primary", use_container_width=True, key=f"btn_lantik_isi_{pilihan_pusat_semak}"):
                                try:
                                    berjaya = 0
                                    for gid in pilih_guru_isi:
                                        supa.table("cadangan_sup").update({"kod_pusat": pilihan_pusat_semak, "status": "DILANTIK PPD", "status": "DILANTIK PPD"}).eq("id", gid).execute()
                                        berjaya+=1
                                    st.success(f"✅ Berjaya lantik {berjaya} guru untuk isi kekosongan di {pilihan_pusat_semak}")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Gagal lantik: {e}")




        elif menu == "kelulusan":
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
                <h2 style="margin:0; color:white;">✅ Kelulusan - PPD {kod_ppd} - {PPD_MAP.get(kod_ppd,'')}</h2>
                <p style="margin:5px 0 0 0; color:#ffffff;">Pilihan: Kelulusan Keseluruhan (Lulus Semua & Jana Surat Keseluruhan) atau Lulus Mengikut Pusat (Pilih Pusat & Lulus Jana Surat) - No Surat Berturutan Ikut Daerah, Tak Berulang, Auto Sequential</p>
            </div>
            """, unsafe_allow_html=True)

            # Helper to get max no surat for this PPD to ensure sequential no repeat
            def get_max_no_surat_ppd(kod_ppd_filter):
                try:
                    res = supa.table("cadangan_sup").select("no_surat").eq("kod_ppd", kod_ppd_filter).not_.is_("no_surat", "null").limit(10000).execute()
                    max_no = 0
                    import re
                    for r in (res.data or []):
                        ns = str(r.get("no_surat") or "").strip()
                        if not ns:
                            continue
                        # Cari angka di akhir: contoh JPN.SEL/PPD.BA/SPM/2026/0001 -> 1
                        nums = re.findall(r'(\d+)', ns)
                        if nums:
                            try:
                                val = int(nums[-1])
                                if val > max_no:
                                    max_no = val
                            except:
                                pass
                    return max_no
                except Exception as e:
                    return 0

            def get_next_no_surat_format(kod_ppd_filter, seq_no):
                # Guna rujukan yang PPD type: contoh JPN.SPP.HHJH + bilangan surat
                rujukan = st.session_state.get("selenggara_rujukan_format") or st.session_state.get("input_no_rujukan_ppd") or f"JPN.SEL/PPD.{kod_ppd_filter}/SPM/{datetime.date.today().year}"
                # Jika rujukan sudah ada / di hujung, tambah bilangan sahaja
                rujukan_clean = rujukan.rstrip('/')
                return f"{rujukan_clean}/{seq_no:04d}"

            def sebab_belum_lulus(r):
                st_ = str(r.get("status") or r.get("STATUS") or "").strip()
                ns_ = str(r.get("no_surat") or r.get("NO_SURAT") or "").strip().lower()
                if "LULUS" not in st_.upper():
                    return f"Status belum LULUS ({st_ or 'kosong'})"
                if ns_ in ("", "nan", "none", "null"):
                    return "Status LULUS tetapi No Surat kosong"
                return "-"

            def paparkan_sebab_belum(df_b, tajuk):
                if df_b is None or df_b.empty:
                    return
                with st.expander(f"🔎 Kenapa {len(df_b)} guru ini masih dalam senarai belum lulus? ({tajuk})", expanded=False):
                    _rows = []
                    for _, _r in df_b.iterrows():
                        _rows.append({
                            "ID": _r.get("id", ""),
                            "NAMA": _r.get("NAMA_GURU", "") or _r.get("nama_guru", ""),
                            "IC": _r.get("IC_GURU", "") or _r.get("ic_guru", ""),
                            "PUSAT": _r.get("kod_pusat", "") or _r.get("KOD_PUSAT", ""),
                            "STATUS": _r.get("status", "") or _r.get("STATUS", ""),
                            "NO SURAT": _r.get("no_surat", "") or _r.get("NO_SURAT", ""),
                            "SEBAB": sebab_belum_lulus(_r),
                        })
                    st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True)

            def semak_selepas_lulus(df_b, ns_map):
                """Baca semula dari DB: pastikan setiap guru betul-betul LULUS + ada No Surat. Cuba simpan semula yang gagal.
                Pulangkan senarai nama yang masih gagal."""
                gagal = []
                try:
                    ids = [r.get("id") for _, r in df_b.iterrows() if r.get("id")]
                    ok_ids = set()
                    if ids:
                        chk = supa.table("cadangan_sup").select("id,status,no_surat").in_("id", ids).execute()
                        for x in (chk.data or []):
                            if "LULUS" in str(x.get("status") or "").upper() and str(x.get("no_surat") or "").strip().lower() not in ("", "nan", "none", "null"):
                                ok_ids.add(x.get("id"))
                    for _, r in df_b.iterrows():
                        id_x = r.get("id")
                        if not id_x or id_x in ok_ids:
                            continue
                        ns_x = ns_map.get(id_x) or str(r.get("no_surat") or "").strip()
                        try:
                            supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT DIHANTAR KE SEKOLAH ASAL", "no_surat": ns_x}).eq("id", id_x).execute()
                            chk2 = supa.table("cadangan_sup").select("id,status,no_surat").eq("id", id_x).limit(1).execute()
                            d2 = (chk2.data or [{}])[0]
                            if not ("LULUS" in str(d2.get("status") or "").upper() and str(d2.get("no_surat") or "").strip()):
                                gagal.append(f"{r.get('NAMA_GURU','') or r.get('nama_guru','')} (ID {id_x})")
                        except Exception as e_retry:
                            gagal.append(f"{r.get('NAMA_GURU','') or r.get('nama_guru','')} (ID {id_x}): {e_retry}")
                except Exception as e_chk:
                    gagal.append(f"Semakan gagal: {e_chk}")
                return gagal

            # Get all data for PPD
            df_cad_all = get_cadangan_df(kod_ppd=kod_ppd)
            df_pusat_raw = get_pusat_df()

            # Build pusat map for display
            pusat_map = {}
            try:
                for _, r in df_pusat_raw.iterrows():
                    d = r.get("data") if isinstance(r.get("data"), dict) else {}
                    if isinstance(d, str):
                        try: d = json.loads(d)
                        except: d = {}
                    no_p = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                    nama_p = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                    if no_p:
                        pusat_map[no_p] = nama_p
            except:
                pass

            # ===== SUB MENU KELULUSAN =====
            sub_kelulusan = "✅ Kelulusan Keseluruhan (Lulus Semua & Jana Surat Keseluruhan)" if fly_cur == "keseluruhan" else "🏫 Lulus Mengikut Pusat (Pilih Pusat & Lulus Jana Surat)"

            max_no_global = get_max_no_surat_ppd(kod_ppd)
            # BUANG PENYATAAN No Surat terakhir - tak perlu info panjang



            # ===== RUANG SELENGGARA NO SURAT DI ATAS - PPD TYPE NO RUJUKAN & BILANGAN SURAT SAHAJA - ADA COLUM UNTUK ISI =====
            st.markdown("### 🔐 Selenggara No Surat")

            # Check max existing
            try:
                max_exist = get_max_no_surat_ppd(kod_ppd)
            except:
                max_exist = 0

            # ALWAYS SHOW COLUM UNTUK PPD TYPE NO RUJUKAN DAN NO SURAT - BUANG PENYATAAN
            col_ruj1, col_ruj2 = st.columns(2)
            with col_ruj1:
                no_rujukan_input = st.text_input(
                    "No Rujukan (Contoh: JPN.SPP.HHJH)",
                    value=st.session_state.get("input_no_rujukan_ppd", f"JPN.SPP.HHJH/PPD.{kod_ppd}"),
                    placeholder="Taip contoh: JPN.SPP.HHJH",
                    key="input_no_rujukan_ppd_final"
                )
            with col_ruj2:
                bil_surat_input = st.number_input(
                    "Bilangan Surat / No Surat",
                    min_value=1,
                    value=int(st.session_state.get("input_bil_surat_ppd", max_exist+1 if max_exist>0 else 1)),
                    step=1,
                    key="input_bil_surat_ppd_final"
                )

            st.markdown(f"**Preview No Surat: {no_rujukan_input}/{bil_surat_input:04d}**")

            # Save to session
            st.session_state["selenggara_rujukan_format"] = no_rujukan_input
            st.session_state["selenggara_bil_mula"] = bil_surat_input

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button(f"🔐 Sahkan No Surat {no_rujukan_input}/{bil_surat_input:04d}", type="primary", use_container_width=True, key="btn_sahkan_no_surat_final"):
                    try:
                        df_pusat_all = get_pusat_df()
                        try:
                            marker_found = False
                            for _, r in df_pusat_all.iterrows():
                                d = r.get("data") if isinstance(r.get("data"), dict) else {}
                                if isinstance(d, str):
                                    try: d = json.loads(d)
                                    except: d = {}
                                no_p = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                                if no_p.startswith(kod_ppd.upper()):
                                    rec_id = r.get("id")
                                    d["SELENGGARA_NO_SURAT_DONE"] = True
                                    d["SELENGGARA_NO_SURAT_TARIKH"] = str(datetime.date.today())
                                    d["SELENGGARA_NO_SURAT_OLEH"] = kod_ppd
                                    d["SELENGGARA_NO_SURAT_RUJUKAN"] = no_rujukan_input
                                    d["SELENGGARA_NO_SURAT_MULA"] = bil_surat_input
                                    d["SELENGGARA_NO_SURAT_FORMAT"] = f"{no_rujukan_input}/{bil_surat_input:04d}"
                                    supa.table("pusat_master").update({"data": d}).eq("id", rec_id).execute()
                                    marker_found = True
                                    break
                            if not marker_found:
                                log_data = {
                                    "SELENGGARA_NO_SURAT_DONE": True,
                                    "SELENGGARA_NO_SURAT_TARIKH": str(datetime.date.today()),
                                    "SELENGGARA_NO_SURAT_OLEH": kod_ppd,
                                    "SELENGGARA_NO_SURAT_RUJUKAN": no_rujukan_input,
                                    "SELENGGARA_NO_SURAT_MULA": bil_surat_input,
                                    "NO_PUSAT": f"{kod_ppd}-LOG-SURAT",
                                    "NAMA_PUSAT": f"LOG SELENGGARA NO SURAT PPD {kod_ppd}"
                                }
                                supa.table("pusat_master").insert({"no_pusat": f"{kod_ppd}-LOG-SURAT", "kod_ppd": kod_ppd, "nama_pusat": f"LOG SELENGGARA NO SURAT PPD {kod_ppd}", "data": log_data}).execute()
                        except Exception as e_inner:
                            pass
                        st.success(f"✅ No Surat Disahkan: {no_rujukan_input}/{bil_surat_input:04d} - Akan guna untuk jana surat")
                        st.balloons()
                    except Exception as e:
                        st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")
            with col_btn2:
                if max_exist > 0:
                    st.caption(f"Sedia ada max: {max_exist} | Seterusnya: {max_exist+1}")
                else:
                    st.caption("Belum ada No Surat - mula dari 1")

            st.markdown("---")

            # ===== OPTION 1: KELULUSAN KESELURUHAN =====
            st.markdown("---")

            # ===== OPTION 1: KELULUSAN KESELURUHAN =====
            st.markdown("---")

            # ===== OPTION 1: KELULUSAN KESELURUHAN =====
            if st.session_state.get("kelulusan_amaran"):
                st.error("⚠️ Guru berikut TIDAK berjaya disimpan sebagai LULUS dalam pangkalan data (sila semak kebenaran/jadual Supabase):\n\n" + "\n".join(f"- {x}" for x in st.session_state["kelulusan_amaran"]))
                if st.button("Tutup amaran", key="btn_tutup_amaran_kelulusan"):
                    st.session_state["kelulusan_amaran"] = []
                    st.rerun()

            # ===== OPTION 1: KELULUSAN KESELURUHAN =====
            if "Keseluruhan" in sub_kelulusan:
                st.markdown("### ✅ Kelulusan Keseluruhan - Lulus Semua & Jana Surat Keseluruhan")
                st.caption("Semua guru yang telah dilantik (DILANTIK PPD) di PPD ini akan diluluskan sekaligus. No Surat auto berturutan ikut daerah, tak berulang.")

                def is_valid_no_surat_fix(ns):
                    s = str(ns or "").strip()
                    return s != "" and s.lower() not in ("nan","none","null","")
                def is_true_lulus_fix(row):
                    status = str(row.get("status") or row.get("STATUS") or "").upper()
                    ns = row.get("no_surat") or ""
                    return "LULUS" in status and is_valid_no_surat_fix(ns)
                def is_belum_lulus_fix(row):
                    return not is_true_lulus_fix(row)
                df_sudah = df_cad_all[df_cad_all.apply(lambda r: str(r.get("kod_pusat") or r.get("KOD_PUSAT") or "").strip() != "" and str(r.get("kod_pusat") or "").lower() not in ("none","null","nan"), axis=1)].copy() if not df_cad_all.empty else pd.DataFrame()
                df_belum_lulus = df_sudah[df_sudah.apply(is_belum_lulus_fix, axis=1)].copy() if not df_sudah.empty else pd.DataFrame()
                df_sudah_lulus = df_sudah[df_sudah.apply(is_true_lulus_fix, axis=1)].copy() if not df_sudah.empty else pd.DataFrame()

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Dilantik", len(df_sudah))
                col2.metric("Belum Lulus (Perlu Lulus)", len(df_belum_lulus))
                col3.metric("Sudah Lulus Ada No Surat", len(df_sudah_lulus))
                col4.metric("No Surat Seterusnya", f"{max_no_global+1:04d}")

                if df_sudah.empty:
                    st.warning("Belum ada guru dilantik di PPD ini - sila jana di Jana Keseluruhan / Manual dulu")
                    st.stop()

                with st.expander(f"📋 Lihat {len(df_sudah)} Guru Telah Dilantik di PPD {kod_ppd} (Semua Pusat)", expanded=False):
                    display_cols = [c for c in ["NAMA_GURU","IC_GURU","JAWATAN_CADANGAN","KOD_SEKOLAH_ASAL","kod_pusat","KOD_PUSAT","status","no_surat"] if c in df_sudah.columns]
                    st.dataframe(df_sudah[display_cols] if display_cols else df_sudah, use_container_width=True, hide_index=True)

                if df_belum_lulus.empty:
                    st.success(f"✅ Semua {len(df_sudah)} guru sudah LULUS dan ada No Surat - tiada yang perlu diluluskan lagi")
                else:
                    st.markdown(f"#### 📝 {len(df_belum_lulus)} Guru Perlu Diluluskan - No Surat Berturutan {max_no_global+1} hingga {max_no_global+len(df_belum_lulus)}")
                    paparkan_sebab_belum(df_belum_lulus, "Kelulusan Keseluruhan")

                    # Preview
                    preview_rows = []
                    cur_no = max_no_global + 1
                    for _, r in df_belum_lulus.iterrows():
                        existing_ns = str(r.get("no_surat") or "").strip()
                        if existing_ns:
                            no_baru = existing_ns
                        else:
                            no_baru = get_next_no_surat_format(kod_ppd, cur_no)
                            cur_no += 1
                        preview_rows.append({
                            "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                            "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                            "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                            "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                            "PUSAT TUGAS": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                            "NAMA PUSAT": pusat_map.get(str(r.get("kod_pusat","") or "").upper().strip(), ""),
                            "NO SURAT BARU": no_baru,
                            "STATUS SEKARANG": r.get("status","") or r.get("STATUS","")
                        })
                    df_preview_keseluruhan = pd.DataFrame(preview_rows)
                    st.dataframe(df_preview_keseluruhan, use_container_width=True, hide_index=True)

                    col_lulus_all, col_jana_all = st.columns(2)
                    with col_lulus_all:
                        if st.button(f"✅ LULUS KESELURUHAN {len(df_belum_lulus)} GURU - Jana No Surat {max_no_global+1} hingga {max_no_global+len(preview_rows)}", type="primary", use_container_width=True, key="btn_lulus_keseluruhan"):
                            try:
                                berjaya = 0
                                cur_no = max_no_global + 1
                                surat_list_all = []
                                _map_ns_all = {}
                                for _, r in df_belum_lulus.iterrows():
                                    id_g = r.get("id","")
                                    existing_ns = str(r.get("no_surat") or "").strip()
                                    if existing_ns:
                                        no_surat_baru = existing_ns
                                    else:
                                        no_surat_baru = get_next_no_surat_format(kod_ppd, cur_no)
                                        cur_no += 1

                                    # Generate surat HTML untuk hantar ke sekolah asal
                                    nama_g = r.get("NAMA_GURU","") or r.get("nama_guru","")
                                    ic_g = r.get("IC_GURU","") or r.get("ic_guru","")
                                    jaw_g = r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan","")
                                    sek_asal = r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal","")
                                    pusat_tugas = r.get("kod_pusat","") or r.get("KOD_PUSAT","")
                                    nama_pusat_tugas = pusat_map.get(str(pusat_tugas).upper().strip(), "")

                                    # Simpan surat HTML dalam data json untuk hantar ke sekolah asal
                                    try:
                                        tarikh_surat = datetime.date.today().strftime('%d %B %Y')
                                        html_surat_single = generate_surat_html(nama_g, ic_g, jaw_g, sek_asal, sek_asal, pusat_tugas, nama_pusat_tugas, no_surat_baru, kod_ppd, PPD_MAP.get(kod_ppd,""), tarikh_surat)
                                    except:
                                        html_surat_single = ""

                                    data_update = {}
                                    if html_surat_single:
                                        data_update = {"surat_html": html_surat_single, "surat_tarikh": str(datetime.date.today()), "surat_no": no_surat_baru}

                                    if id_g:
                                        # Update dengan no_surat, status LULUS, dan data surat untuk sekolah asal
                                        try:
                                            existing_data = supa.table("cadangan_sup").select("data").eq("id", id_g).limit(1).execute()
                                            old_data = {}
                                            if existing_data.data:
                                                old_data = existing_data.data[0].get("data") or {}
                                                if isinstance(old_data, str):
                                                    try: old_data = json.loads(old_data)
                                                    except: old_data = {}
                                            old_data.update(data_update)
                                            old_data["SURAT_DIHANTAR_KE_SEKOLAH_ASAL"] = True
                                            supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT DIHANTAR KE SEKOLAH ASAL", "no_surat": no_surat_baru, "data": old_data}).eq("id", id_g).execute()
                                        except:
                                            supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT DIHANTAR KE SEKOLAH ASAL", "no_surat": no_surat_baru}).eq("id", id_g).execute()
                                    else:
                                        supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT DIHANTAR KE SEKOLAH ASAL", "no_surat": no_surat_baru}).eq("ic_guru", r.get("IC_GURU","") or r.get("ic_guru","")).execute()

                                    surat_list_all.append({"nama": nama_g, "ic": ic_g, "sekolah_asal": sek_asal, "pusat": pusat_tugas, "no_surat": no_surat_baru, "html": html_surat_single})
                                    if id_g:
                                        _map_ns_all[id_g] = no_surat_baru
                                    berjaya += 1

                                # Semak semula dari pangkalan data - pastikan semua betul-betul LULUS
                                st.session_state["kelulusan_amaran"] = semak_selepas_lulus(df_belum_lulus, _map_ns_all)

                                # Simpan surat kolektif untuk PPD download HTML
                                full_html_all = f'<html><head><meta charset="UTF-8"><title>Surat Lantikan Keseluruhan PPD {kod_ppd}</title><style>body{{font-family:Arial;margin:20px;}} .surat{{border:2px solid #000; padding:20px; margin:20px 0; page-break-after:always;}}</style></head><body>'
                                full_html_all += f'<h1 style="text-align:center;">SURAT LANTIKAN PETUGAS PEPERIKSAAN SPM 2026 - KESELURUHAN PPD {kod_ppd}</h1><p style="text-align:center;">No Surat: {max_no_global+1} hingga {cur_no-1}</p><hr>'
                                for s in surat_list_all:
                                    full_html_all += s["html"]
                                full_html_all += '</body></html>'
                                st.session_state[f"surat_keseluruhan_html_{kod_ppd}"] = full_html_all
                                st.session_state[f"surat_keseluruhan_list_{kod_ppd}"] = surat_list_all

                                st.success(f"✅ Berjaya LULUS KESELURUHAN {berjaya} guru! No Surat {max_no_global+1} hingga {cur_no-1} - Surat HTML dijana & DIHANTAR KE SEKOLAH ASAL GURU untuk SUP cetak & bagi pada guru berkenaan")
                                st.balloons()
                                st.info(f"📄 Surat yang sama telah dihantar ke sekolah asal guru (SUP boleh lihat di menu Surat Lantikan Saya > ada surat - untuk SUP cetak dan bagi pada guru di mana dia kena bertugas)")
                                st.components.v1.html(full_html_all[:15000], height=700, scrolling=True)
                                try:
                                    pdf_bytes_all = generate_surat_kolektif_pdf_bytes(surat_list_all, kod_ppd, PPD_MAP.get(kod_ppd,""), f"SURAT LANTIKAN KESELURUHAN PPD {kod_ppd}")
                                    if pdf_bytes_all:
                                        st.download_button("📥 Download Surat Keseluruhan (PDF)", data=pdf_bytes_all, file_name=f"Surat_Lantikan_Keseluruhan_{kod_ppd}_{datetime.date.today()}.pdf", mime="application/pdf", use_container_width=True, key="dl_surat_keseluruhan_pdf_after_lulus")
                                except:
                                    pass
                                st.download_button("📥 Download Surat Keseluruhan (HTML) - Untuk PPD", data=full_html_all.encode('utf-8'), file_name=f"Surat_Lantikan_Keseluruhan_{kod_ppd}_{datetime.date.today()}.html", mime="text/html", use_container_width=True, key="dl_surat_keseluruhan_after_lulus")
                                # Also PDF individual zip? For now collective PDF

                                st.cache_data.clear()   # segar semula data supaya bilangan "Belum Lulus" betul
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error lulus keseluruhan: {e}")

                    with col_jana_all:
                        if st.button(f"📄 Jana Surat Keseluruhan {len(df_belum_lulus)} Guru (No Berturutan)", use_container_width=True, key="btn_jana_surat_keseluruhan"):
                            tarikh = datetime.date.today().strftime('%d %B %Y')
                            full_html = f'<html><head><meta charset="UTF-8"><title>Surat Lantikan Keseluruhan PPD {kod_ppd}</title><style>body{{font-family:Arial;margin:20px;}} .surat{{border:1px solid #ccc; padding:20px; margin:20px 0; page-break-after:always;}} h2{{text-align:center;}}</style></head><body>'
                            full_html += f'<h1 style="text-align:center;">SURAT LANTIKAN PETUGAS PEPERIKSAAN SPM 2026</h1><h2 style="text-align:center;">PPD {kod_ppd} - {PPD_MAP.get(kod_ppd,"")} - KESELURUHAN</h2><p style="text-align:center;">No Surat Berturutan: {max_no_global+1} hingga {max_no_global+len(df_preview_keseluruhan)} - Ikut Daerah {kod_ppd} - Siapa Jana Dahulu No Dia Dahulu</p><hr>'
                            for s in preview_rows:
                                full_html += generate_surat_html(s["NAMA GURU"], s["IC"], s["JAWATAN"], s["SEKOLAH ASAL"], s["NAMA GURU"], s["PUSAT TUGAS"], s["NAMA PUSAT"], s["NO SURAT BARU"], kod_ppd, PPD_MAP.get(kod_ppd,""), tarikh)
                            full_html += '</body></html>'
                            st.session_state["surat_keseluruhan_html"] = full_html
                            st.success(f"Surat Keseluruhan {len(preview_rows)} guru berjaya dijana! No Surat {max_no_global+1} hingga {max_no_global+len(preview_rows)} berturutan")
                            st.components.v1.html(full_html[:10000], height=600, scrolling=True)
                            try:
                                pdf_k = generate_surat_kolektif_pdf_bytes([{"nama": s["NAMA GURU"], "ic": s["IC"], "jawatan": s["JAWATAN"], "sekolah_asal": s["SEKOLAH ASAL"], "pusat": s["PUSAT"], "no_surat": s["NO SURAT BARU"], "nama_pusat": s["NAMA PUSAT"]} for s in preview_rows], kod_ppd, PPD_MAP.get(kod_ppd,""), f"SURAT LANTIKAN KESELURUHAN PPD {kod_ppd}")
                                if pdf_k:
                                    st.download_button("📥 Download Surat Keseluruhan (PDF)", data=pdf_k, file_name=f"Surat_Lantikan_Keseluruhan_{kod_ppd}_{datetime.date.today()}.pdf", mime="application/pdf", use_container_width=True, key="dl_surat_keseluruhan_pdf")
                            except:
                                pass
                            st.download_button("📥 Download Surat Keseluruhan (HTML)", data=full_html.encode('utf-8'), file_name=f"Surat_Lantikan_Keseluruhan_{kod_ppd}_{datetime.date.today()}.html", mime="text/html", use_container_width=True, key="dl_surat_keseluruhan")

            # ===== OPTION 2: LULUS MENGIKUT PUSAT =====
            else:
                st.markdown("### 🏫 Lulus Mengikut Pusat - Pilih Pusat & Lulus Jana Surat")
                st.caption("Pilih satu pusat, luluskan guru di pusat tersebut sahaja. No Surat tetap berturutan untuk semua (ikut daerah), tak berulang - siapa jana dulu no dia dahulu.")

                # Build pusat list that has dilantik guru
                df_sudah_all = df_cad_all[df_cad_all.apply(lambda r: str(r.get("kod_pusat") or r.get("KOD_PUSAT") or "").strip() != "" and str(r.get("kod_pusat") or "").lower() not in ("none","null","nan"), axis=1)].copy() if not df_cad_all.empty else pd.DataFrame()

                if df_sudah_all.empty:
                    st.warning("Belum ada guru dilantik di PPD ini")
                    st.stop()

                # Group by pusat
                pusat_groups = {}
                for _, r in df_sudah_all.iterrows():
                    kp = str(r.get("kod_pusat") or r.get("KOD_PUSAT") or "").upper().strip()
                    if kp:
                        if kp not in pusat_groups:
                            pusat_groups[kp] = []
                        pusat_groups[kp].append(r)

                pilihan_pusat_lulus = st.selectbox(
                    "📍 Pilih Pusat Untuk Lulus Mengikut Pusat",
                    sorted(pusat_groups.keys()),
                    format_func=lambda x: f"{x} - {pusat_map.get(x,'')} ({len(pusat_groups[x])} guru dilantik)",
                    key="pilih_pusat_kelulusan_mengikut_pusat"
                )

                if pilihan_pusat_lulus:
                    guru_pusat_list = pusat_groups[pilihan_pusat_lulus]
                    st.markdown(f"#### {pilihan_pusat_lulus} - {pusat_map.get(pilihan_pusat_lulus,'')} - {len(guru_pusat_list)} guru dilantik")

                    df_pusat_lulus = pd.DataFrame(guru_pusat_list)

                    # Belum lulus vs sudah lulus
                    def _is_lulus_pusat(r):
                        _st = str(r.get("status") or r.get("STATUS") or "").upper()
                        _ns = str(r.get("no_surat") or r.get("NO_SURAT") or "").strip().lower()
                        return ("LULUS" in _st) and (_ns not in ("", "nan", "none", "null"))
                    df_belum_pusat = df_pusat_lulus[~df_pusat_lulus.apply(_is_lulus_pusat, axis=1)].copy()
                    df_sudah_lulus_pusat = df_pusat_lulus[df_pusat_lulus.apply(_is_lulus_pusat, axis=1)].copy()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Dilantik di Pusat", len(df_pusat_lulus))
                    col2.metric("Belum Lulus (Perlu Lulus)", len(df_belum_pusat))
                    col3.metric("Sudah Lulus Ada No Surat", len(df_sudah_lulus_pusat))

                    # Display table
                    rows_pusat = []
                    for r in guru_pusat_list:
                        rows_pusat.append({
                            "id": r.get("id",""),
                            "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                            "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                            "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                            "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                            "PUSAT": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                            "STATUS": r.get("status","") or r.get("STATUS",""),
                            "NO SURAT": r.get("no_surat","") or ""
                        })
                    df_display_pusat = pd.DataFrame(rows_pusat)
                    st.dataframe(df_display_pusat, use_container_width=True, hide_index=True)

                    if df_belum_pusat.empty:
                        st.success(f"✅ Semua guru di {pilihan_pusat_lulus} sudah LULUS dan ada No Surat")
                    else:
                        st.markdown(f"#### 📝 {len(df_belum_pusat)} Guru di {pilihan_pusat_lulus} Perlu Diluluskan - No Surat Berturutan Bermula {max_no_global+1}")
                        paparkan_sebab_belum(df_belum_pusat, pilihan_pusat_lulus)

                        preview_pusat = []
                        cur_no = max_no_global + 1
                        for _, r in df_belum_pusat.iterrows():
                            existing_ns = str(r.get("no_surat") or "").strip()
                            if existing_ns:
                                no_baru = existing_ns
                            else:
                                no_baru = get_next_no_surat_format(kod_ppd, cur_no)
                                cur_no += 1
                            preview_pusat.append({
                                "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                                "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                                "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                                "PUSAT": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                                "NO SURAT BARU": no_baru
                            })
                        df_preview_pusat = pd.DataFrame(preview_pusat)
                        st.dataframe(df_preview_pusat, use_container_width=True, hide_index=True)

                        col_lulus_pusat, col_jana_pusat = st.columns(2)
                        with col_lulus_pusat:
                            if st.button(f"✅ Lulus {len(df_belum_pusat)} Guru di {pilihan_pusat_lulus} - No {max_no_global+1} hingga {cur_no-1} & Hantar ke Sekolah Asal", type="primary", use_container_width=True, key=f"btn_lulus_pusat_{pilihan_pusat_lulus}"):
                                try:
                                    berjaya = 0
                                    cur_no2 = max_no_global + 1
                                    surat_list_pusat = []
                                    _map_ns_p = {}
                                    for _, r in df_belum_pusat.iterrows():
                                        id_g = r.get("id","")
                                        existing_ns = str(r.get("no_surat") or "").strip()
                                        if existing_ns:
                                            no_baru = existing_ns
                                        else:
                                            no_baru = get_next_no_surat_format(kod_ppd, cur_no2)
                                            cur_no2 += 1

                                        nama_g = r.get("NAMA_GURU","") or r.get("nama_guru","")
                                        ic_g = r.get("IC_GURU","") or r.get("ic_guru","")
                                        jaw_g = r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan","")
                                        sek_asal = r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal","")

                                        try:
                                            tarikh_surat = datetime.date.today().strftime('%d %B %Y')
                                            html_single = generate_surat_html(nama_g, ic_g, jaw_g, sek_asal, sek_asal, pilihan_pusat_lulus, pusat_map.get(pilihan_pusat_lulus,""), no_baru, kod_ppd, PPD_MAP.get(kod_ppd,""), tarikh_surat)
                                        except:
                                            html_single = ""

                                        try:
                                            existing_data = supa.table("cadangan_sup").select("data").eq("id", id_g).limit(1).execute() if id_g else None
                                            old_data = {}
                                            if existing_data and existing_data.data:
                                                old_data = existing_data.data[0].get("data") or {}
                                                if isinstance(old_data, str):
                                                    try: old_data = json.loads(old_data)
                                                    except: old_data = {}
                                            old_data.update({"surat_html": html_single, "surat_tarikh": str(datetime.date.today()), "surat_no": no_baru, "SURAT_DIHANTAR_KE_SEKOLAH_ASAL": True})
                                            if id_g:
                                                supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT DIHANTAR KE SEKOLAH ASAL", "no_surat": no_baru, "data": old_data}).eq("id", id_g).execute()
                                            else:
                                                supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT DIHANTAR KE SEKOLAH ASAL", "no_surat": no_baru}).eq("ic_guru", r.get("IC_GURU","") or r.get("ic_guru","")).execute()
                                        except:
                                            if id_g:
                                                supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT DIHANTAR KE SEKOLAH ASAL", "no_surat": no_baru}).eq("id", id_g).execute()

                                        surat_list_pusat.append({"nama": nama_g, "ic": ic_g, "sekolah_asal": sek_asal, "pusat": pilihan_pusat_lulus, "no_surat": no_baru, "html": html_single})
                                        if id_g:
                                            _map_ns_p[id_g] = no_baru
                                        berjaya += 1

                                    # Semak semula dari pangkalan data - pastikan semua betul-betul LULUS
                                    st.session_state["kelulusan_amaran"] = semak_selepas_lulus(df_belum_pusat, _map_ns_p)

                                    # Generate full HTML for this pusat
                                    full_html_pusat = f'<html><head><meta charset="UTF-8"><title>Surat {pilihan_pusat_lulus}</title><style>body{{font-family:Arial;margin:20px;}} .surat{{border:2px solid #000; padding:20px; margin:20px 0; page-break-after:always;}}</style></head><body>'
                                    full_html_pusat += f'<h1 style="text-align:center;">SURAT LANTIKAN SPM 2026 - {pilihan_pusat_lulus} - {pusat_map.get(pilihan_pusat_lulus,"")}</h1><p style="text-align:center;">PPD {kod_ppd} - No Surat {max_no_global+1} hingga {cur_no2-1}</p><hr>'
                                    for s in surat_list_pusat:
                                        full_html_pusat += s["html"]
                                    full_html_pusat += '</body></html>'
                                    st.session_state[f"surat_pusat_{pilihan_pusat_lulus}_html"] = full_html_pusat

                                    st.success(f"✅ Berjaya Lulus {berjaya} guru di {pilihan_pusat_lulus}! No Surat {max_no_global+1} hingga {cur_no2-1} - Surat DIHANTAR KE SEKOLAH ASAL GURU untuk SUP cetak & bagi pada guru berkenaan")
                                    st.balloons()
                                    st.info(f"📄 Surat yang sama telah sampai ke sekolah asal guru - SUP boleh lihat di Surat Lantikan Saya untuk cetak & bagi pada guru di mana dia kena bertugas ({pilihan_pusat_lulus})")
                                    st.components.v1.html(full_html_pusat[:15000], height=700, scrolling=True)
                                    try:
                                        pdf_pusat = generate_surat_kolektif_pdf_bytes(surat_list_pusat, kod_ppd, PPD_MAP.get(kod_ppd,""), f"SURAT LANTIKAN {pilihan_pusat_lulus}")
                                        if pdf_pusat:
                                            st.download_button(f"📥 Download Surat {pilihan_pusat_lulus} (PDF) & Hantar ke Sekolah Asal", data=pdf_pusat, file_name=f"Surat_{pilihan_pusat_lulus}_{kod_ppd}_{datetime.date.today()}.pdf", mime="application/pdf", use_container_width=True, key=f"dl_surat_pusat_pdf_after_{pilihan_pusat_lulus}")
                                    except:
                                        pass
                                    st.download_button(f"📥 Download Surat {pilihan_pusat_lulus} (HTML) & Hantar ke Sekolah Asal", data=full_html_pusat.encode('utf-8'), file_name=f"Surat_{pilihan_pusat_lulus}_{kod_ppd}_{datetime.date.today()}.html", mime="text/html", use_container_width=True, key=f"dl_surat_pusat_after_{pilihan_pusat_lulus}")
                                    st.cache_data.clear()   # segar semula data supaya bilangan "Belum Lulus" betul
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error lulus pusat: {e}")

                        with col_jana_pusat:
                            if st.button(f"📄 Jana Surat {pilihan_pusat_lulus} - {len(df_belum_pusat)} Guru", use_container_width=True, key=f"btn_jana_surat_pusat_{pilihan_pusat_lulus}"):
                                tarikh = datetime.date.today().strftime('%d %B %Y')
                                full_html = f'<html><head><meta charset="UTF-8"><title>Surat Lantikan {pilihan_pusat_lulus}</title><style>body{{font-family:Arial;margin:20px;}} .surat{{border:1px solid #ccc; padding:20px; margin:20px 0; page-break-after:always;}}</style></head><body>'
                                full_html += f'<h1 style="text-align:center;">SURAT LANTIKAN SPM 2026 - {pilihan_pusat_lulus}</h1><h2 style="text-align:center;">{pusat_map.get(pilihan_pusat_lulus,"")} - PPD {kod_ppd}</h2><p style="text-align:center;">No Surat Berturutan: {max_no_global+1} hingga {max_no_global+len(preview_pusat)} - Ikut Daerah {kod_ppd}</p><hr>'
                                for s in preview_pusat:
                                    full_html += generate_surat_html(s["NAMA GURU"], s["IC"], s["JAWATAN"], s["SEKOLAH ASAL"], s["NAMA GURU"], s["PUSAT"], pusat_map.get(s["PUSAT"],""), s["NO SURAT BARU"], kod_ppd, PPD_MAP.get(kod_ppd,""), tarikh)
                                full_html += '</body></html>'
                                st.session_state[f"surat_pusat_{pilihan_pusat_lulus}"] = full_html
                                st.success(f"Surat {pilihan_pusat_lulus} berjaya dijana! {len(preview_pusat)} guru")
                                st.components.v1.html(full_html[:10000], height=600, scrolling=True)
                                try:
                                    pdf_k2 = generate_surat_kolektif_pdf_bytes([{"nama": s["NAMA GURU"], "ic": s["IC"], "jawatan": s["JAWATAN"], "sekolah_asal": s["SEKOLAH ASAL"], "pusat": s["PUSAT"], "no_surat": s["NO SURAT BARU"]} for s in preview_pusat], kod_ppd, PPD_MAP.get(kod_ppd,""), f"SURAT LANTIKAN {pilihan_pusat_lulus}")
                                    if pdf_k2:
                                        st.download_button(f"📥 Download Surat {pilihan_pusat_lulus} (PDF)", data=pdf_k2, file_name=f"Surat_Lantikan_{pilihan_pusat_lulus}_{kod_ppd}_{datetime.date.today()}.pdf", mime="application/pdf", use_container_width=True, key=f"dl_surat_pusat_pdf_{pilihan_pusat_lulus}")
                                except:
                                    pass
                                st.download_button(f"📥 Download Surat {pilihan_pusat_lulus}", data=full_html.encode('utf-8'), file_name=f"Surat_Lantikan_{pilihan_pusat_lulus}_{kod_ppd}_{datetime.date.today()}.html", mime="text/html", use_container_width=True, key=f"dl_surat_pusat_{pilihan_pusat_lulus}")



        elif menu == "selenggara":
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px; border:2px solid #002171;">
                <h2 style="margin:0; color:white;">🔐 Selenggara Bilik Kebal - PPD {kod_ppd} - {PPD_MAP.get(kod_ppd,'')}</h2>
                <p style="margin:5px 0 0 0; color:#bbdefb;">Tapak Bilik Kebal Master - PPD isi data bilik kebal ikut daerah. Penyelia Kawasan akan ditempatkan ke bilik kebal ini. SUP tidak nampak menu ini.</p>
            </div>
            """, unsafe_allow_html=True)

            def get_bilik_kebal_df(kod_ppd_filter=None):
                try:
                    q = supa.table("bilik_kebal_master").select("*").limit(10000)
                    if kod_ppd_filter:
                        q = q.eq("kod_ppd", kod_ppd_filter)
                    res = q.execute()
                    return pd.DataFrame(res.data or [])
                except Exception as e:
                    st.error(f"Error load bilik_kebal_master: {e}")
                    return pd.DataFrame()

            df_bk = get_bilik_kebal_df(kod_ppd)

            c1,c2,c3 = st.columns(3)
            c1.metric("Bilik Kebal di PPD", len(df_bk))
            c2.metric("Daerah", PPD_MAP.get(kod_ppd,''))
            try:
                res_cad = supa.table("cadangan_sup").select("*", count="exact").eq("kod_ppd", kod_ppd.lower()).limit(1).execute()
                total_guru_ppd = res_cad.count if hasattr(res_cad,'count') else 0
            except:
                total_guru_ppd = 0
            c3.metric("Guru PPD", total_guru_ppd)

            # [FLYOUT] st.tabs diganti sub menu flyout

            if fly_cur == "form":
                st.markdown("### Borang Daftar Bilik Kebal Baru")
                st.caption("PPD isi form ini, data terus masuk Supabase table bilik_kebal_master")
                with st.form("form_bilik_kebal"):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        kod_bk = st.text_input("KOD_BILIK_KEBAL *", placeholder="Contoh: BK-BA001 atau BA-BK01")
                        nama_bk = st.text_input("NAMA_BILIK_KEBAL *", placeholder="Contoh: Bilik Kebal PPD Klang")
                        kod_ppd_form = st.text_input("KOD_PPD", value=kod_ppd, disabled=True)
                    with col_f2:
                        alamat_bk = st.text_area("ALAMAT *", placeholder="Alamat penuh bilik kebal", height=100)
                        catatan = st.text_area("Catatan / DATA JSON (optional)", placeholder='Contoh: {"kapasiti": 50}', height=100)
                    submit_bk = st.form_submit_button("Simpan Bilik Kebal ke Supabase", type="primary", use_container_width=True)
                    if submit_bk:
                        if not kod_bk or not nama_bk or not alamat_bk:
                            st.error("Sila isi KOD, NAMA dan ALAMAT wajib!")
                        else:
                            try:
                                data_json = {}
                                if catatan:
                                    try:
                                        data_json = json.loads(catatan)
                                    except:
                                        data_json = {"catatan": catatan}
                                existing = supa.table("bilik_kebal_master").select("*").eq("kod_bilik_kebal", kod_bk.upper().strip()).limit(1).execute()
                                if existing.data:
                                    st.error(f"KOD {kod_bk} sudah wujud!")
                                else:
                                    payload = {
                                        "kod_bilik_kebal": kod_bk.upper().strip(),
                                        "nama_bilik_kebal": nama_bk.upper().strip(),
                                        "alamat": alamat_bk.strip(),
                                        "kod_ppd": kod_ppd.upper().strip(),
                                        "data": data_json
                                    }
                                    supa.table("bilik_kebal_master").insert(payload).execute()
                                    st.success(f"Berjaya simpan {kod_bk} - {nama_bk}")
                                    st.balloons()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error simpan: {e}")

            if fly_cur == "senarai":
                st.markdown(f"### Senarai Bilik Kebal PPD {kod_ppd}")
                if df_bk.empty:
                    st.info("Belum ada bilik kebal didaftarkan untuk PPD ini.")
                else:
                    cari_bk = st.text_input("Cari bilik kebal (kod / nama / alamat)", key="cari_bk")
                    if cari_bk:
                        mask = df_bk.apply(lambda r: cari_bk.lower() in str(r.get("kod_bilik_kebal","")).lower() or cari_bk.lower() in str(r.get("nama_bilik_kebal","")).lower() or cari_bk.lower() in str(r.get("alamat","")).lower(), axis=1)
                        df_show = df_bk[mask]
                    else:
                        df_show = df_bk
                    st.dataframe(df_show, use_container_width=True, hide_index=True)
                    col_exp1, col_exp2 = st.columns(2)
                    with col_exp1:
                        st.download_button("Download Senarai Bilik Kebal (Excel)", to_excel(df_show), file_name=f"bilik_kebal_{kod_ppd}_{datetime.date.today()}.xlsx", use_container_width=True)
                    with col_exp2:
                        if st.button("Refresh", use_container_width=True):
                            st.rerun()
                    st.markdown("---")
                    st.markdown("### Buang Bilik Kebal")
                    if not df_show.empty:
                        pilih_buang = st.selectbox("Pilih Bilik Kebal untuk buang", df_show["kod_bilik_kebal"].tolist() if "kod_bilik_kebal" in df_show.columns else [], key="buang_bk")
                        if st.button(f"Buang {pilih_buang}", type="secondary", use_container_width=True):
                            try:
                                supa.table("bilik_kebal_master").delete().eq("kod_bilik_kebal", pilih_buang).execute()
                                st.success(f"Berjaya buang {pilih_buang}")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))

            if fly_cur == "import":
                st.markdown("### Import Pukal Bilik Kebal dari Excel")
                st.info("Format Excel mesti ada column: KOD_BILIK_KEBAL, NAMA_BILIK_KEBAL, ALAMAT, KOD_PPD")
                df_template = pd.DataFrame([
                    {"KOD_BILIK_KEBAL": f"BK-{kod_ppd}01", "NAMA_BILIK_KEBAL": f"BILIK KEBAL PPD {PPD_MAP.get(kod_ppd,'')} 1", "ALAMAT": "SMK CONTOH 1, KLANG", "KOD_PPD": kod_ppd},
                    {"KOD_BILIK_KEBAL": f"BK-{kod_ppd}02", "NAMA_BILIK_KEBAL": f"BILIK KEBAL PPD {PPD_MAP.get(kod_ppd,'')} 2", "ALAMAT": "SMK CONTOH 2, KLANG", "KOD_PPD": kod_ppd},
                ])
                st.download_button("Download Template Excel Bilik Kebal", to_excel(df_template), file_name=f"template_bilik_kebal_{kod_ppd}.xlsx", use_container_width=True)
                st.markdown("---")
                up_bk = st.file_uploader("Upload Excel Bilik Kebal", type=["xlsx","xls"], key="up_bk_excel")
                if up_bk:
                    try:
                        df_up = pd.read_excel(up_bk, sheet_name=0)
                        st.write(f"Ada {len(df_up)} baris.")
                        st.dataframe(df_up.head(10), use_container_width=True)
                        if st.button(f"Import {len(df_up)} Bilik Kebal ke Supabase", type="primary", use_container_width=True):
                            bar = st.progress(0)
                            ok = 0
                            err = 0
                            for idx, row in df_up.iterrows():
                                try:
                                    kod = str(row.get("KOD_BILIK_KEBAL") or row.get("kod_bilik_kebal") or "").upper().strip()
                                    nama = str(row.get("NAMA_BILIK_KEBAL") or row.get("nama_bilik_kebal") or "").upper().strip()
                                    alamat = str(row.get("ALAMAT") or row.get("alamat") or "").strip()
                                    kppd = str(row.get("KOD_PPD") or row.get("kod_ppd") or kod_ppd).upper().strip()
                                    if not kod or not nama:
                                        err += 1
                                        continue
                                    dup = supa.table("bilik_kebal_master").select("*").eq("kod_bilik_kebal", kod).limit(1).execute()
                                    if dup.data:
                                        err += 1
                                        continue
                                    supa.table("bilik_kebal_master").insert({"kod_bilik_kebal": kod, "nama_bilik_kebal": nama, "alamat": alamat, "kod_ppd": kppd, "data": {}}).execute()
                                    ok += 1
                                except:
                                    err += 1
                                bar.progress((idx+1)/len(df_up))
                            st.success(f"Selesai: {ok} berjaya, {err} gagal/duplicate")
                            st.balloons()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error baca Excel: {e}")

            if fly_cur == "penyelia":
                st.markdown(f"### Penempatan Penyelia Kawasan ke Bilik Kebal - PPD {kod_ppd}")
                st.caption("STEP 1: Pilih Bilik Kebal → STEP 2: Pilih Pusat di bawah Bilik Kebal (contoh 12 pusat) → STEP 3: Agihkan pusat tu kepada setiap Penyelia Kawasan (bukan bagi semua untuk sorang)")
                if df_bk.empty:
                    st.warning("Belum ada bilik kebal. Sila daftar bilik kebal dulu di tab Tambah / Import.")
                else:
                    df_cad_all_bk = get_cadangan_df(kod_ppd=kod_ppd)
                    if not df_cad_all_bk.empty:
                        col_jaw = "JAWATAN_CADANGAN" if "JAWATAN_CADANGAN" in df_cad_all_bk.columns else "jawatan_cadangan" if "jawatan_cadangan" in df_cad_all_bk.columns else None
                        if col_jaw:
                            df_penyelia_all = df_cad_all_bk[df_cad_all_bk[col_jaw].astype(str).str.contains("Penyelia Kawasan", case=False, na=False)].copy()
                        else:
                            df_penyelia_all = pd.DataFrame()
                        # FIX: Keluarkan yang sudah dilantik - hanya tinggalkan belum dilantik
                        def is_belum_penyelia(r):
                            kp = str(r.get("kod_pusat") or r.get("KOD_PUSAT") or r.get("kod_bilik_kebal") or "").strip()
                            return kp == "" or kp.lower() in ("none","null","nan","nat","-")
                        if not df_penyelia_all.empty:
                            df_penyelia = df_penyelia_all[df_penyelia_all.apply(is_belum_penyelia, axis=1)].copy()
                            sudah = len(df_penyelia_all) - len(df_penyelia)
                        else:
                            df_penyelia = pd.DataFrame()
                            sudah = 0
                    else:
                        df_penyelia = pd.DataFrame()
                        sudah = 0

                    if sudah > 0:
                        st.info(f"Ada {len(df_penyelia_all)} Penyelia dicadangkan, {sudah} sudah dilantik (disembunyikan), {len(df_penyelia)} belum dilantik - hanya yang belum dilantik dipaparkan untuk pilihan")
                    else:
                        st.info(f"Ada {len(df_penyelia)} Penyelia Kawasan dicadangkan SUP untuk PPD {kod_ppd} (belum dilantik)")

                    if not df_penyelia.empty:
                        df_pusat_raw_all = get_pusat_df()
                        pusat_list_ppd = []
                        for _, r in df_pusat_raw_all.iterrows():
                            d = r.get("data") if isinstance(r.get("data"), dict) else {}
                            if isinstance(d, str):
                                try:
                                    d = json.loads(d)
                                except:
                                    d = {}
                            no_p = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                            if not no_p.startswith(kod_ppd.upper()):
                                continue
                            nama_p = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                            pusat_list_ppd.append({"NO_PUSAT": no_p, "NAMA_PUSAT": nama_p})
                        df_pusat_ppd_list = pd.DataFrame(pusat_list_ppd)

                        # STEP 1: Pilih Bilik Kebal
                        st.markdown("#### STEP 1: Pilih Bilik Kebal")
                        pilih_bk_tempat = st.selectbox("Pilih Bilik Kebal", df_bk["kod_bilik_kebal"].tolist() if "kod_bilik_kebal" in df_bk.columns else [], format_func=lambda x: f"{x} - {df_bk[df_bk['kod_bilik_kebal']==x]['nama_bilik_kebal'].values[0][:30] if not df_bk[df_bk['kod_bilik_kebal']==x].empty and 'nama_bilik_kebal' in df_bk.columns else x}", key="pilih_bk_tempat_v8")

                        # STEP 2: Pilih Pusat di bawah Bilik Kebal ini
                        st.markdown(f"#### STEP 2: Pilih Pusat-Pusat Di Bawah Bilik Kebal {pilih_bk_tempat}")
                        st.caption("Contoh: 1 bilik kebal jaga 12 pusat. Pilih semua pusat yang bernaung bawah bilik kebal ini dulu.")
                        if not df_pusat_ppd_list.empty:
                            pilih_pusat_bawah_bk = st.multiselect(f"Pilih Pusat-Pusat Di Bawah {pilih_bk_tempat} (Tick semua pusat di bawah bilik kebal ini)", df_pusat_ppd_list["NO_PUSAT"].tolist() if "NO_PUSAT" in df_pusat_ppd_list.columns else [], format_func=lambda x: f"{x} - {df_pusat_ppd_list[df_pusat_ppd_list['NO_PUSAT']==x]['NAMA_PUSAT'].values[0][:25] if not df_pusat_ppd_list[df_pusat_ppd_list['NO_PUSAT']==x].empty else x}", key="pilih_pusat_bawah_bk_v8")
                            if pilih_pusat_bawah_bk:
                                st.success(f"✅ {len(pilih_pusat_bawah_bk)} pusat dipilih di bawah {pilih_bk_tempat}: {', '.join(pilih_pusat_bawah_bk)}")
                                # Simpan ke session untuk guna di step 3
                                st.session_state[f"pusat_bawah_{pilih_bk_tempat}"] = pilih_pusat_bawah_bk
                        else:
                            pilih_pusat_bawah_bk = []
                            st.warning("Tiada pusat dalam PPD ini")

                        # Load saved pusat if exists
                        saved_pusat_bawah = st.session_state.get(f"pusat_bawah_{pilih_bk_tempat}", pilih_pusat_bawah_bk if 'pilih_pusat_bawah_bk' in locals() else [])

                        if not saved_pusat_bawah:
                            st.warning("⚠️ Sila pilih pusat di bawah bilik kebal dulu di STEP 2")
                            st.stop()

                        st.markdown("---")
                        st.markdown("#### STEP 3: Pilih Penyelia Kawasan & Agihkan Pusat Jagaan")
                        st.caption(f"Pusat yang boleh diagihkan hanya dari senarai yang dipilih untuk {pilih_bk_tempat} tadi ({len(saved_pusat_bawah)} pusat), bukan semua pusat PPD. Agihkan supaya sorang Penyelia tidak pegang semua.")

                        def get_col2(df, *cands):
                            # V29: case-insensitive search
                            cols_lower = {str(c).lower(): c for c in df.columns}
                            for cand in cands:
                                if cand in df.columns:
                                    return cand
                                if cand.lower() in cols_lower:
                                    return cols_lower[cand.lower()]
                            return None

                        c_nama = get_col2(df_penyelia, "NAMA_GURU","nama_guru")
                        c_ic = get_col2(df_penyelia, "IC_GURU","ic_guru")
                        c_sek = get_col2(df_penyelia, "KOD_SEKOLAH_ASAL","kod_sekolah_asal")
                        c_sek_nama = get_col2(df_penyelia, "NAMA_SEKOLAH_ASAL","nama_sekolah_asal")
                        c_tel = get_col2(df_penyelia, "TELEFON_GURU","telefon_guru")
                        c_pusat = get_col2(df_penyelia, "KOD_PUSAT","kod_pusat")

                        cols_disp = [c for c in [c_nama,c_ic,c_sek,c_sek_nama,c_tel,c_pusat] if c]
                        if cols_disp:
                            df_disp = df_penyelia[cols_disp].copy()
                            rename_map = {}
                            if c_nama:
                                rename_map[c_nama] = "NAMA PENYELIA"
                            if c_ic:
                                rename_map[c_ic] = "IC"
                            if c_sek:
                                rename_map[c_sek] = "KOD SEKOLAH ASAL"
                            if c_sek_nama and c_sek_nama != c_sek:
                                rename_map[c_sek_nama] = "NAMA SEKOLAH ASAL"
                            if c_tel:
                                rename_map[c_tel] = "NO TELEFON"
                            if c_pusat:
                                rename_map[c_pusat] = "BILIK KEBAL / PUSAT"
                            df_disp = df_disp.rename(columns=rename_map)
                            st.dataframe(df_disp.head(100), use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(df_penyelia.head(100), use_container_width=True, hide_index=True)

                        id_col = "id" if "id" in df_penyelia.columns else None
                        if id_col:
                            id_list = df_penyelia[id_col].tolist()
                            def format_penyelia(x):
                                try:
                                    row = df_penyelia[df_penyelia[id_col].astype(str) == str(x)]
                                    if row.empty:
                                        row = df_penyelia[df_penyelia[id_col] == x]
                                    if not row.empty:
                                        nama = str(row.iloc[0].get(c_nama,"") if c_nama else "")[:30]
                                        sek = str(row.iloc[0].get(c_sek,"") if c_sek else "")[:15]
                                        tel = str(row.iloc[0].get(c_tel,"") if c_tel else "")[:15]
                                        return f"{nama} | {sek} | {tel} (ID:{x})"
                                    else:
                                        return f"ID:{x}"
                                except:
                                    return f"ID:{x}"

                            pilih_penyelia_bk = st.multiselect("Pilih Penyelia Kawasan (akan keluar nama + sekolah + telefon)", id_list, format_func=format_penyelia, key="pilih_penyelia_bk_v8")

                            if pilih_penyelia_bk:
                                st.markdown(f"##### Agihkan Pusat Jagaan Untuk {len(pilih_penyelia_bk)} Penyelia Terpilih")
                                st.caption(f"Setiap Penyelia hanya boleh pilih pusat dari {len(saved_pusat_bawah)} pusat yang dipilih untuk {pilih_bk_tempat} tadi. Contoh: Penyelia 1 jaga 6 pusat, Penyelia 2 jaga 6 pusat lain.")

                                # For each selected penyelia, show multiselect for pusat jagaan (only from saved list)
                                penyelia_pusat_map = {}
                                for pid in pilih_penyelia_bk:
                                    row = df_penyelia[df_penyelia[id_col].astype(str) == str(pid)]
                                    if row.empty:
                                        row = df_penyelia[df_penyelia[id_col] == pid]
                                    if not row.empty:
                                        nama_peny = str(row.iloc[0].get(c_nama,"") if c_nama else f"ID:{pid}")[:30]
                                        sek_peny = str(row.iloc[0].get(c_sek,"") if c_sek else "")
                                        tel_peny = str(row.iloc[0].get(c_tel,"") if c_tel else "")
                                    else:
                                        nama_peny = f"ID:{pid}"
                                        sek_peny = ""
                                        tel_peny = ""

                                    st.markdown(f"**{nama_peny} - {sek_peny} - {tel_peny}**")
                                    # Multiselect pusat untuk penyelia ini sahaja, option dari saved_pusat_bawah
                                    selected_pusat_for_this = st.multiselect(f"Pilih pusat jagaan untuk {nama_peny} (dari {len(saved_pusat_bawah)} pusat di bawah {pilih_bk_tempat})", saved_pusat_bawah, format_func=lambda x: f"{x} - {df_pusat_ppd_list[df_pusat_ppd_list['NO_PUSAT']==x]['NAMA_PUSAT'].values[0][:25] if not df_pusat_ppd_list[df_pusat_ppd_list['NO_PUSAT']==x].empty else x}", key=f"pusat_untuk_{pid}_v8")
                                    penyelia_pusat_map[pid] = selected_pusat_for_this
                                    if selected_pusat_for_this:
                                        st.caption(f"→ {nama_peny} akan jaga {len(selected_pusat_for_this)} pusat: {', '.join(selected_pusat_for_this)}")
                                    st.markdown("---")

                                # Preview before save
                                if any(penyelia_pusat_map.values()):
                                    st.markdown("**Preview Penempatan (dengan Sekolah Asal & Telefon):**")
                                    preview_rows = []
                                    for pid, pusat_list in penyelia_pusat_map.items():
                                        if not pusat_list:
                                            continue
                                        row = df_penyelia[df_penyelia[id_col].astype(str) == str(pid)]
                                        if not row.empty:
                                            r = row.iloc[0]
                                            preview_rows.append({
                                                "NAMA PENYELIA": r.get(c_nama,"") if c_nama else "",
                                                "IC": r.get(c_ic,"") if c_ic else "",
                                                "SEKOLAH ASAL": r.get(c_sek,"") if c_sek else "",
                                                "NAMA SEKOLAH ASAL": r.get(c_sek_nama,"") if c_sek_nama else "",
                                                "NO TELEFON": r.get(c_tel,"") if c_tel else "",
                                                "BILIK KEBAL": pilih_bk_tempat,
                                                "PUSAT JAGAAN": ", ".join(pusat_list),
                                                "BIL PUSAT": len(pusat_list)
                                            })
                                    if preview_rows:
                                        df_preview = pd.DataFrame(preview_rows)
                                        st.dataframe(df_preview, use_container_width=True, hide_index=True)

                                # Save button
                                if st.button(f"✅ Lantik & Simpan {len(pilih_penyelia_bk)} Penyelia ke {pilih_bk_tempat} dengan Pusat Jagaan", type="primary", use_container_width=True, key="btn_tempat_penyelia_bk_v8"):
                                    try:
                                        for pid, pusat_list in penyelia_pusat_map.items():
                                            if not pusat_list:
                                                continue
                                            pusat_str = ",".join(pusat_list)
                                            existing_row = df_penyelia[df_penyelia[id_col].astype(str) == str(pid)]
                                            existing_data = {}
                                            if not existing_row.empty:
                                                ed = existing_row.iloc[0].get("data")
                                                if isinstance(ed, dict):
                                                    existing_data = ed
                                                elif isinstance(ed, str):
                                                    try:
                                                        existing_data = json.loads(ed)
                                                    except:
                                                        existing_data = {}
                                            existing_data["kod_bilik_kebal"] = pilih_bk_tempat
                                            existing_data["pusat_jagaan"] = pusat_list
                                            existing_data["pusat_jagaan_str"] = pusat_str
                                            existing_data["pusat_bawah_bilik_kebal"] = saved_pusat_bawah

                                            # V33 FIX: kod_bilik_kebal = CB01 (bilik kebal), kod_pusat = pusat jagaan (BA021, BA053) untuk Penyelia Kawasan
                                            pusat_jagaan_str = ",".join(pusat_list) if isinstance(pusat_list, list) else str(pusat_list)
                                            existing_data["kod_bilik_kebal"] = pilih_bk_tempat
                                            existing_data["kod_bilik_kebal_explicit"] = pilih_bk_tempat
                                            existing_data["pusat_jagaan"] = pusat_list
                                            existing_data["pusat_jagaan_str"] = pusat_jagaan_str
                                            existing_data["pusat_bawah_bilik_kebal"] = saved_pusat_bawah

                                            # V33: kod_pusat = pusat jagaan sebenar, kod_bilik_kebal = bilik kebal
                                            # Contoh: kod_bilik_kebal=CB01, kod_pusat=BA021, BA053
                                            payloads_try = [
                                                {"kod_bilik_kebal": pilih_bk_tempat, "kod_pusat": pusat_jagaan_str, "status": "DITEMPATKAN BILIK KEBAL", "data": existing_data},
                                                {"kod_bilik_kebal": pilih_bk_tempat, "kod_pusat": pusat_jagaan_str, "status": "DITEMPATKAN BILIK KEBAL"},
                                                {"kod_bilik_kebal": pilih_bk_tempat, "status": "DITEMPATKAN BILIK KEBAL", "data": existing_data},
                                                {"kod_bilik_kebal": pilih_bk_tempat, "status": "DITEMPATKAN BILIK KEBAL"},
                                                {"kod_pusat": pusat_jagaan_str, "status": "DITEMPATKAN BILIK KEBAL", "data": existing_data},
                                            ]
                                            last_err = None
                                            success = False
                                            for payload in payloads_try:
                                                try:
                                                    supa.table("cadangan_sup").update(payload).eq("id", pid).execute()
                                                    success = True
                                                    break
                                                except Exception as e:
                                                    last_err = e
                                                    continue
                                            if not success and last_err:
                                                raise last_err
                                        st.success(f"✅ {len([v for v in penyelia_pusat_map.values() if v])} Penyelia berjaya ditempatkan ke {pilih_bk_tempat}")
                                        st.balloons()
                                        st.rerun()
                                    except Exception as e:
                                        st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")
                            else:
                                st.info("Pilih Penyelia Kawasan di atas")
                        else:
                            st.warning("Tiada id column")

                    st.markdown("---")
                    st.markdown("### 📊 Ringkasan Penempatan Penyelia ke Bilik Kebal (Column Berasingan Ikut Bilangan Penyelia)")
                    st.caption("Setiap Penyelia ada column sendiri: NAMA, IC, SEKOLAH ASAL, TELEFON, PUSAT JAGAAN. Kalau ada 2 penyelia, akan ada 2 set column. Kalau 6, akan ada 6 set.")
                    # V27 FIX: Ringkasan penempatan - 1 baris per Penyelia, bukan semua dalam 1 baris
                    ringkas_bk = []
                    df_cad_all_bk2 = get_cadangan_df(kod_ppd=kod_ppd)
                    for _, bk_row in df_bk.iterrows():
                        kod_bk_r = bk_row.get("kod_bilik_kebal","") or bk_row.get("KOD_BILIK_KEBAL","")
                        nama_bk_r = str(bk_row.get("nama_bilik_kebal",""))[:30]
                        alamat_bk_r = str(bk_row.get("alamat",""))[:40]
                        penyelia_assigned = []
                        if not df_cad_all_bk2.empty:
                            for _, c in df_cad_all_bk2.iterrows():
                                p = str(c.get("kod_bilik_kebal") or c.get("kod_pusat") or c.get("KOD_PUSAT") or c.get("KOD_BILIK_KEBAL") or "").upper()
                                if p == kod_bk_r.upper():
                                    jaw = str(c.get("JAWATAN_CADANGAN") or c.get("jawatan_cadangan") or "").upper()
                                    if "PENYELIA" in jaw:
                                        nama_g = str(c.get("NAMA_GURU") or c.get("nama_guru") or "")
                                        ic_g = str(c.get("IC_GURU") or c.get("ic_guru") or "")
                                        sek_g = str(c.get("KOD_SEKOLAH_ASAL") or c.get("kod_sekolah_asal") or "")
                                        sek_nama_g = str(c.get("NAMA_SEKOLAH_ASAL") or c.get("nama_sekolah_asal") or "")[:30]
                                        tel_g = str(c.get("TELEFON_GURU") or c.get("telefon_guru") or "")
                                        d = c.get("data") if isinstance(c.get("data"), dict) else {}
                                        if isinstance(d, str):
                                            try:
                                                d = json.loads(d)
                                            except:
                                                d = {}
                                        # V34 FIX: Baca pusat jagaan dari data JSON, fallback ke kod_pusat jika data kosong
                                        pusat_j = d.get("pusat_jagaan_str") or d.get("pusat_jagaan") or ""
                                        if isinstance(pusat_j, list):
                                            pusat_j = ",".join(pusat_j)
                                        # Jika pusat_j masih kosong, cuba baca dari kod_pusat column (untuk data baru V33)
                                        if not pusat_j or pusat_j == "-" or pusat_j.strip() == "":
                                            raw_kod_pusat = str(c.get("kod_pusat") or c.get("KOD_PUSAT") or "").strip()
                                            # Jika kod_pusat bukan bilik kebal (CB, BK, BILIK), anggap itu pusat jagaan
                                            if raw_kod_pusat and not any(x in raw_kod_pusat.upper() for x in ["CB", "BK-", "BILIK"]) or "," in raw_kod_pusat:
                                                pusat_j = raw_kod_pusat
                                            # Jika kod_pusat adalah CB01 tapi data ada pusat_bawah, guna pusat_bawah sebagai fallback lama
                                            elif not pusat_j:
                                                pusat_j = d.get("pusat_bawah_bilik_kebal") or ""
                                                if isinstance(pusat_j, list):
                                                    pusat_j = ",".join(pusat_j)

                                        pusat_bawah = d.get("pusat_bawah_bilik_kebal") or d.get("pusat_bawah") or ""
                                        if isinstance(pusat_bawah, list):
                                            pusat_bawah = ",".join(pusat_bawah)
                                        # Jika pusat_bawah kosong, fallback ke semua pusat bawah bilik kebal dari kod_bilik_kebal
                                        if not pusat_bawah:
                                            pusat_bawah = d.get("kod_bilik_kebal") or c.get("kod_bilik_kebal") or ""
                                        penyelia_assigned.append({
                                            "nama": nama_g,
                                            "ic": ic_g,
                                            "sekolah": sek_g,
                                            "sekolah_nama": sek_nama_g,
                                            "telefon": tel_g,
                                            "pusat_jagaan": pusat_j,
                                            "pusat_bawah": pusat_bawah,
                                            "id": c.get("id")
                                        })

                        # V27: Buat 1 baris per penyelia, bukan gabung dalam 1 baris
                        if penyelia_assigned:
                            for idx, pen in enumerate(penyelia_assigned, 1):
                                row_dict = {
                                    "BIL": idx,
                                    "KOD BILIK KEBAL": kod_bk_r,
                                    "NAMA BILIK KEBAL": nama_bk_r,
                                    "ALAMAT": alamat_bk_r,
                                    "PENYELIA KE": f"{idx} dari {len(penyelia_assigned)}",
                                    "NAMA PENYELIA": pen["nama"],
                                    "IC PENYELIA": pen["ic"],
                                    "SEKOLAH ASAL": pen["sekolah"],
                                    "NAMA SEK ASAL": pen["sekolah_nama"],
                                    "TELEFON": pen["telefon"],
                                    "PUSAT JAGAAN (Di bawah Penyelia Ini)": pen["pusat_jagaan"],
                                    "SEMUA PUSAT DI BAWAH BILIK KEBAL": pen["pusat_bawah"],
                                    "BIL PUSAT JAGAAN": len(pen["pusat_jagaan"].split(",")) if pen["pusat_jagaan"] and pen["pusat_jagaan"] != "-" else 0,
                                    "ID": pen["id"]
                                }
                                ringkas_bk.append(row_dict)
                        else:
                            # Jika kosong, buat 1 baris kosong
                            ringkas_bk.append({
                                "BIL": 0,
                                "KOD BILIK KEBAL": kod_bk_r,
                                "NAMA BILIK KEBAL": nama_bk_r,
                                "ALAMAT": alamat_bk_r,
                                "PENYELIA KE": "0",
                                "NAMA PENYELIA": "-",
                                "IC PENYELIA": "-",
                                "SEKOLAH ASAL": "-",
                                "NAMA SEK ASAL": "-",
                                "TELEFON": "-",
                                "PUSAT JAGAAN (Di bawah Penyelia Ini)": "-",
                                "SEMUA PUSAT DI BAWAH BILIK KEBAL": "-",
                                "BIL PUSAT JAGAAN": 0,
                                "ID": "-"
                            })

                    if ringkas_bk:
                        df_ringkas_bk = pd.DataFrame(ringkas_bk)
                        df_ringkas_bk = df_ringkas_bk.fillna("-")
                        # Sort by bilik kebal then penyelia ke
                        try:
                            df_ringkas_bk = df_ringkas_bk.sort_values(by=["KOD BILIK KEBAL", "BIL"])
                        except:
                            pass
                        st.dataframe(df_ringkas_bk, use_container_width=True, hide_index=True)
                        # Highlight if more than 1 penyelia per bilik kebal
                        try:
                            bil_bk_counts = df_ringkas_bk[df_ringkas_bk["NAMA PENYELIA"] != "-"].groupby("KOD BILIK KEBAL").size()
                            for bk_code, cnt in bil_bk_counts.items():
                                if cnt > 1:
                                    st.info(f"📌 Bilik Kebal {bk_code} ada {cnt} Penyelia Kawasan - setiap penyelia ada baris sendiri di atas")
                        except:
                            pass
                        st.download_button("📥 Export Ringkasan Bilik Kebal (1 Baris = 1 Penyelia)", to_excel(df_ringkas_bk), file_name=f"ringkasan_bilik_kebal_{kod_ppd}_1baris_1penyelia_{datetime.date.today()}.xlsx", use_container_width=True)
                    else:
                        st.info("Belum ada ringkasan")

                    st.markdown("---")
                    st.markdown("### 🗑️ Batal Penempatan Penyelia Kawasan")
                    st.caption("Pilih bilik kebal, kemudian batalkan penempatan penyelia di bilik kebal tersebut. Data akan kembali ke status DICADANGKAN dan pusat jagaan akan dipadam.")
                    if not df_bk.empty:
                        pilih_bk_batal = st.selectbox("Pilih Bilik Kebal untuk Batal Penempatan", df_bk["kod_bilik_kebal"].tolist() if "kod_bilik_kebal" in df_bk.columns else [], key="pilih_bk_batal_v8")
                        if st.button(f"🗑️ Batal Semua Penempatan Penyelia di {pilih_bk_batal}", type="secondary", use_container_width=True, key="btn_batal_penyelia"):
                            try:
                                df_cad_batal = get_cadangan_df(kod_ppd=kod_ppd)
                                count_batal = 0
                                for _, c in df_cad_batal.iterrows():
                                    p = str(c.get("kod_bilik_kebal") or c.get("kod_pusat") or c.get("KOD_PUSAT") or c.get("KOD_BILIK_KEBAL") or "").upper()
                                    if p == pilih_bk_batal.upper():
                                        jaw = str(c.get("JAWATAN_CADANGAN") or c.get("jawatan_cadangan") or "").upper()
                                        if "PENYELIA" in jaw:
                                            # Reset balik ke pool cadangan - kosongkan bilik kebal & pusat jagaan
                                            supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN SEMULA - BATAL BILIK KEBAL", "no_surat": None, "data": {}}).eq("id", c.get("id")).execute()
                                            count_batal += 1
                                st.success(f"✅ {count_batal} penempatan di {pilih_bk_batal} telah dibatalkan. Cadangan kembali ke PPD > Cadangan SUP & SUP > Cadangan Lantikan dengan status DICADANGKAN")
                                # Clear session pusat bawah
                                if f"pusat_bawah_{pilih_bk_batal}" in st.session_state:
                                    del st.session_state[f"pusat_bawah_{pilih_bk_batal}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error batal: {e}")

                        # Batal individu
                        st.markdown("**Batal Individu Penyelia:**")
                        df_cad_batal_ind = get_cadangan_df(kod_ppd=kod_ppd)
                        df_batal_list = []
                        for _, c in df_cad_batal_ind.iterrows():
                            p = str(c.get("kod_bilik_kebal") or c.get("kod_pusat") or c.get("KOD_PUSAT") or c.get("KOD_BILIK_KEBAL") or "").upper()
                            if p == pilih_bk_batal.upper():
                                jaw = str(c.get("JAWATAN_CADANGAN") or c.get("jawatan_cadangan") or "").upper()
                                if "PENYELIA" in jaw:
                                    df_batal_list.append(c)
                        if df_batal_list:
                            df_batal_df = pd.DataFrame(df_batal_list)
                            id_col_batal = "id" if "id" in df_batal_df.columns else None
                            if id_col_batal:
                                def fmt_batal(x):
                                    row = df_batal_df[df_batal_df[id_col_batal].astype(str)==str(x)]
                                    if not row.empty:
                                        return f"{row.iloc[0].get('NAMA_GURU','')} - {row.iloc[0].get('KOD_SEKOLAH_ASAL','')}"
                                    return str(x)
                                pilih_batal_ind = st.multiselect("Pilih Penyelia untuk Batal", df_batal_df[id_col_batal].tolist(), format_func=fmt_batal, key="batal_ind_v8")
                                if pilih_batal_ind and st.button(f"🗑️ Batal {len(pilih_batal_ind)} Penyelia Terpilih", use_container_width=True, key="btn_batal_ind"):
                                    try:
                                        for pid in pilih_batal_ind:
                                            supa.table("cadangan_sup").update({"kod_pusat": None, "status": "DICADANGKAN SEMULA - BATAL BILIK KEBAL", "no_surat": None, "data": {}}).eq("id", pid).execute()
                                        st.success(f"✅ Berjaya batal {len(pilih_batal_ind)} penyelia. Mereka kembali ke pool cadangan - boleh lihat di PPD > Cadangan SUP")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                            else:
                                st.info("Tiada penyelia untuk dibatalkan di bilik kebal ini")
                        else:
                            st.info(f"Tiada penyelia ditempatkan di {pilih_bk_batal}")




            if fly_cur == "surat":
                st.markdown(f"### 📄 Jana Surat Lantikan Penyelia Kawasan - PPD {kod_ppd}")
                st.caption("Surat akan dijana dengan Nama, IC, Sekolah Asal, Bilik Kebal, Pusat Jagaan. Boleh download HTML dan hantar ke sekolah asal. SUP akan nampak di Petugas di Sekolah Saya.")

                # Load bilik kebal and penyelia assigned
                df_cad_all_surat = get_cadangan_df(kod_ppd=kod_ppd)
                if df_cad_all_surat.empty:
                    st.warning("Belum ada cadangan")
                else:
                    # Filter penyelia yang sudah ditempatkan di bilik kebal
                    df_surat = []
                    seen_ids_surat = set()
                    for _, c in df_cad_all_surat.iterrows():
                        p = str(c.get("kod_bilik_kebal") or c.get("kod_pusat") or c.get("KOD_PUSAT") or c.get("KOD_BILIK_KEBAL") or "").upper()
                        jaw = str(c.get("JAWATAN_CADANGAN") or c.get("jawatan_cadangan") or "").upper()
                        c_id = str(c.get("id") or c.get("IC_GURU") or c.get("ic_guru") or "") + "_" + str(c.get("KOD_SEKOLAH_ASAL") or "")
                        # Check if already added
                        if c_id in seen_ids_surat:
                            continue
                        if "PENYELIA" in jaw and p:
                            # Check if p is bilik kebal
                            is_bk = False
                            try:
                                for _, bk in df_bk.iterrows():
                                    if str(bk.get("kod_bilik_kebal","")).upper() == p:
                                        is_bk = True
                                        break
                            except:
                                pass
                            if is_bk or "BK-" in p or "CB" in p or p.startswith(kod_ppd+"-BK") or "BILIK" in p:
                                df_surat.append(c)
                                seen_ids_surat.add(c_id)
                                continue
                        # Also include if status DITEMPATKAN BILIK KEBAL
                        if str(c.get("status") or c.get("STATUS") or "").upper() == "DITEMPATKAN BILIK KEBAL":
                            if c_id not in seen_ids_surat:
                                df_surat.append(c)
                                seen_ids_surat.add(c_id)

                    df_surat = pd.DataFrame(df_surat) if df_surat else pd.DataFrame()

                    if df_surat.empty:
                        st.info("Belum ada Penyelia Kawasan yang ditempatkan ke Bilik Kebal. Sila tempatkan dulu di tab Tempatkan Penyelia Kawasan.")
                    else:
                        st.success(f"Ada {len(df_surat)} Penyelia Kawasan telah ditempatkan ke Bilik Kebal dan sedia untuk jana surat")

                        # Select penyelia to generate surat
                        def get_col_s(df, *cands):
                            for cand in cands:
                                if cand in df.columns:
                                    return cand
                            return None

                        c_nama_s = get_col_s(df_surat, "NAMA_GURU","nama_guru")
                        c_ic_s = get_col_s(df_surat, "IC_GURU","ic_guru")
                        c_sek_s = get_col_s(df_surat, "KOD_SEKOLAH_ASAL","kod_sekolah_asal")
                        c_sek_nama_s = get_col_s(df_surat, "NAMA_SEKOLAH_ASAL","nama_sekolah_asal")
                        c_tel_s = get_col_s(df_surat, "TELEFON_GURU","telefon_guru","TELEFON","telefon")
                        c_pusat_s = get_col_s(df_surat, "KOD_PUSAT","kod_pusat")
                        c_id_s = "id" if "id" in df_surat.columns else None

                        # Display
                        cols_s = [c for c in [c_nama_s,c_ic_s,c_sek_s,c_sek_nama_s,c_tel_s,c_pusat_s] if c]
                        if cols_s:
                            st.dataframe(df_surat[cols_s].head(50), use_container_width=True, hide_index=True)

                        # Pilih penyelia
                        if c_id_s:
                            id_list_s = df_surat[c_id_s].tolist()
                            def fmt_surat(x):
                                row = df_surat[df_surat[c_id_s].astype(str)==str(x)]
                                if row.empty:
                                    row = df_surat[df_surat[c_id_s]==x]
                                if not row.empty:
                                    nama = str(row.iloc[0].get(c_nama_s,"") if c_nama_s else "")[:25]
                                    bk = str(row.iloc[0].get(c_pusat_s,"") if c_pusat_s else "")[:15]
                                    return f"{nama} - {bk} (ID:{x})"
                                return f"ID:{x}"

                            pilih_surat = st.multiselect("Pilih Penyelia Kawasan untuk Jana Surat", id_list_s, format_func=fmt_surat, key="pilih_surat_penyelia")

                            # No surat settings - FIX: Ikut no berturutan daerah (sama seperti petugas lain)
                            st.markdown("#### 🔢 No Surat Berturutan Ikut Daerah (Sama seperti petugas lain)")
                            try:
                                # Get max no surat sedia ada di daerah ini dari semua petugas (termasuk KP, TKP, Pengawas)
                                max_no_global = 0
                                try:
                                    df_all_cad_for_no = get_cadangan_df(kod_ppd=kod_ppd)
                                    if not df_all_cad_for_no.empty:
                                        for _, rc in df_all_cad_for_no.iterrows():
                                            ns = str(rc.get("no_surat") or "").strip()
                                            if ns:
                                                # Extract last number from format like JPN.SEL/PPD.BA/SPM/2026/0028 or PPD.BA/SPM/PK/2026/0001
                                                try:
                                                    parts = ns.split("/")
                                                    last_part = parts[-1].strip()
                                                    num = int(''.join(filter(str.isdigit, last_part)))
                                                    if num > max_no_global:
                                                        max_no_global = num
                                                except:
                                                    pass
                                except:
                                    max_no_global = 0
                                st.info(f"📌 No Surat terakhir di PPD {kod_ppd} (semua petugas): {max_no_global} - Surat Penyelia baru akan mula dari {max_no_global+1} berturutan")
                            except:
                                max_no_global = 0

                            col_no1, col_no2, col_no3 = st.columns(3)
                            with col_no1:
                                # Default prefix ikut format standard daerah - sama seperti petugas lain
                                default_prefix = f"JPN.SEL/PPD.{kod_ppd}/SPM/2026/"
                                prefix_surat = st.text_input("Prefix No Surat (ikut format daerah)", value=default_prefix, key="prefix_surat_pk", help="No surat Penyelia akan ikut format yang sama seperti petugas lain di daerah ini, cuma berturutan")
                            with col_no2:
                                no_mula_auto = max_no_global + 1
                                no_mula = st.number_input("No Mula (auto ikut daerah)", min_value=1, value=no_mula_auto, key="no_mula_pk", help=f"Auto dikira dari max sedia ada di daerah {kod_ppd} - jika petugas lain sudah ada no 1-100, Penyelia akan mula 101")
                            with col_no3:
                                tarikh_surat = st.date_input("Tarikh Surat", value=datetime.date.today(), key="tarikh_surat_pk")

                            if pilih_surat and st.button(f"📄 Jana {len(pilih_surat)} Surat Penyelia Kawasan (No Berturutan Daerah {kod_ppd})", type="primary", use_container_width=True, key="btn_jana_surat_pk"):
                                try:
                                    tarikh_str = tarikh_surat.strftime("%d %B %Y")
                                    surat_html_all = ""
                                    surat_list_data = []
                                    current_no = no_mula

                                    for pid in pilih_surat:
                                        row = df_surat[df_surat[c_id_s].astype(str)==str(pid)]
                                        if row.empty:
                                            row = df_surat[df_surat[c_id_s]==pid]
                                        if row.empty:
                                            continue
                                        r = row.iloc[0]
                                        nama = str(r.get(c_nama_s,"") if c_nama_s else "")
                                        ic = str(r.get(c_ic_s,"") if c_ic_s else "")
                                        sek = str(r.get(c_sek_s,"") if c_sek_s else "")
                                        nama_sek = str(r.get(c_sek_nama_s,"") if c_sek_nama_s else sek)
                                        tel = str(r.get(c_tel_s,"") if c_tel_s else "")
                                        # V35 FIX: kod_bk dari column kod_bilik_kebal, bukan kod_pusat
                                        kod_bk = str(r.get("kod_bilik_kebal") or r.get("KOD_BILIK_KEBAL") or r.get(c_pusat_s,"") if c_pusat_s else "").strip()
                                        # Jika kod_bk masih nampak macam pusat jagaan (BA021), cuba cari dalam data
                                        d = r.get("data") if isinstance(r.get("data"), dict) else {}
                                        if isinstance(d, str):
                                            try:
                                                d = json.loads(d)
                                            except:
                                                d = {}
                                        # Jika kod_bk adalah BA... bukan CB/BK, ambil dari data
                                        if kod_bk and not any(x in kod_bk.upper() for x in ["CB", "BK-", "BK", "BILIK"]) or "," in kod_bk:
                                            # kod_bk sekarang sebenarnya pusat jagaan, jadi cari bilik kebal sebenar dalam data
                                            real_bk = d.get("kod_bilik_kebal") or d.get("kod_bilik_kebal_explicit") or ""
                                            if real_bk:
                                                kod_bk = str(real_bk).strip()

                                        # V36 FIX: CB01 SMK RAJA ZARINA - ensure lookup works
                                        bk_row = pd.DataFrame()
                                        if not df_bk.empty and "kod_bilik_kebal" in df_bk.columns:
                                            try:
                                                mask = df_bk["kod_bilik_kebal"].astype(str).str.upper().str.strip() == kod_bk.upper().strip()
                                                bk_row = df_bk[mask]
                                            except:
                                                pass
                                        if not bk_row.empty:
                                            nama_bk = str(bk_row.iloc[0].get("nama_bilik_kebal","")).strip()
                                            alamat_bk = str(bk_row.iloc[0].get("alamat","")).strip()
                                            # If CB01 should be SMK RAJA ZARINA, ensure name
                                            if kod_bk.upper() == "CB01" and "RAJA ZARINA" not in nama_bk.upper():
                                                # Keep existing name but note CB01 is SMK RAJA ZARINA
                                                if not nama_bk or nama_bk == kod_bk:
                                                    nama_bk = "SMK RAJA ZARINA - BILIK KEBAL CB01"
                                        else:
                                            # Fallback: Try from data JSON or hardcode CB01
                                            nama_bk = str(d.get("nama_bilik_kebal","") or d.get("nama_bk","") or "").strip()
                                            alamat_bk = str(d.get("alamat_bilik_kebal","") or d.get("alamat","") or "").strip()
                                            if not nama_bk or nama_bk == kod_bk:
                                                if kod_bk.upper() == "CB01":
                                                    nama_bk = "SMK RAJA ZARINA"
                                                    alamat_bk = alamat_bk or "SMK RAJA ZARINA, KLANG"
                                                else:
                                                    nama_bk = kod_bk
                                            # If still CB01, ensure SMK RAJA ZARINA
                                            if kod_bk.upper() == "CB01" and "RAJA ZARINA" not in nama_bk.upper():
                                                if len(nama_bk) < 5:
                                                    nama_bk = "SMK RAJA ZARINA"

                                        # V35 FIX: Get pusat jagaan - dari kod_pusat ATAU data JSON
                                        pusat_jagaan = d.get("pusat_jagaan") or d.get("pusat_jagaan_str") or []
                                        if not pusat_jagaan:
                                            # Fallback: kod_pusat sekarang adalah pusat jagaan (BA021, BA053) untuk V33+
                                            raw_kod_pusat = str(r.get("kod_pusat") or r.get("KOD_PUSAT") or r.get(c_pusat_s,"") if c_pusat_s else "").strip()
                                            if raw_kod_pusat and raw_kod_pusat.upper() != kod_bk.upper():
                                                pusat_jagaan = raw_kod_pusat
                                        if isinstance(pusat_jagaan, str):
                                            pusat_jagaan = [p.strip() for p in pusat_jagaan.split(",") if p.strip()]
                                        if not isinstance(pusat_jagaan, list):
                                            pusat_jagaan = [str(pusat_jagaan)] if pusat_jagaan else []

                                        no_surat = f"{prefix_surat}{current_no:04d}"
                                        current_no += 1

                                        html_surat = generate_surat_penyelia_kawasan_html(
                                            nama=nama,
                                            ic=ic,
                                            sek_asal=sek,
                                            nama_sek_asal=nama_sek,
                                            telefon=tel,
                                            kod_bilik_kebal=kod_bk,
                                            nama_bilik_kebal=nama_bk,
                                            alamat_bilik_kebal=alamat_bk,
                                            pusat_jagaan_list=pusat_jagaan,
                                            no_surat=no_surat,
                                            kod_ppd=kod_ppd,
                                            ppd_name=PPD_MAP.get(kod_ppd,""),
                                            tarikh=tarikh_str
                                        )
                                        surat_html_all += html_surat + "\n"
                                        surat_list_data.append({
                                            "id": pid,
                                            "nama": nama,
                                            "ic": ic,
                                            "sekolah_asal": sek,
                                            "bilik_kebal": kod_bk,
                                            "nama_bilik_kebal": nama_bk,
                                            "pusat_jagaan": pusat_jagaan,
                                            "no_surat": no_surat,
                                            "html": html_surat
                                        })

                                    # Generate PDF bytes untuk setiap surat juga (untuk download PDF & hantar ke sekolah asal)
                                    for s_data in surat_list_data:
                                        try:
                                            # Generate PDF untuk surat ini
                                            pdf_bytes_ind = None
                                            try:
                                                pdf_bytes_ind = generate_surat_pdf_bytes(
                                                    s_data["nama"], s_data["ic"], "Penyelia Kawasan",
                                                    s_data["sekolah_asal"], "", s_data["bilik_kebal"], s_data.get("nama_bilik_kebal",""),
                                                    s_data["no_surat"], kod_ppd, PPD_MAP.get(kod_ppd,""),
                                                    tarikh_str, s_data["no_surat"]
                                                )
                                            except:
                                                # Fallback to HTML as PDF bytes
                                                pdf_bytes_ind = s_data.get("html","").encode('utf-8')
                                            s_data["pdf_bytes"] = pdf_bytes_ind
                                        except:
                                            s_data["pdf_bytes"] = None

                                    # Save to session for download and hantar
                                    st.session_state[f"surat_pk_html_{kod_ppd}"] = surat_html_all
                                    st.session_state[f"surat_pk_list_{kod_ppd}"] = surat_list_data

                                    st.success(f"✅ Berjaya jana {len(surat_list_data)} surat Penyelia Kawasan - No Surat {no_mula} hingga {current_no-1} (bertuturan daerah {kod_ppd} ikut petugas lain)")
                                    st.balloons()
                                    st.components.v1.html(surat_html_all[:10000], height=600, scrolling=True)

                                    # Auto generate ZIP PDF individu untuk Penyelia
                                    try:
                                        import io, zipfile
                                        zip_buffer = io.BytesIO()
                                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                                            for s_data in surat_list_data:
                                                if s_data.get("pdf_bytes"):
                                                    safe_nama = "".join(c if c.isalnum() else "_" for c in s_data["nama"])[:20]
                                                    fname = f"{s_data['no_surat'].replace('/','_')}_{safe_nama}_Penyelia_{s_data['bilik_kebal']}.pdf"
                                                    zf.writestr(fname, s_data["pdf_bytes"])
                                        zip_bytes = zip_buffer.getvalue()
                                        st.session_state[f"surat_pk_zip_{kod_ppd}"] = zip_bytes
                                    except Exception as e:
                                        st.caption(f"ZIP error: {e}")

                                except Exception as e:
                                    st.error(f"Error jana surat: {e}")

                            # Show generated surat if exists
                            if f"surat_pk_html_{kod_ppd}" in st.session_state:
                                st.markdown("---")
                                st.markdown("### 📄 Surat Telah Dijana")
                                html_all = st.session_state[f"surat_pk_html_{kod_ppd}"]
                                list_data = st.session_state.get(f"surat_pk_list_{kod_ppd}", [])

                                st.components.v1.html(html_all[:12000], height=700, scrolling=True)

                                col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
                                with col_dl1:
                                    st.download_button("📥 Download Semua Surat (HTML)", data=html_all.encode('utf-8'), file_name=f"Surat_Penyelia_Kawasan_{kod_ppd}_{datetime.date.today()}.html", mime="text/html", use_container_width=True, key="dl_all_surat_pk")
                                with col_dl2:
                                    # Excel list
                                    df_dl = pd.DataFrame([{"NAMA": s["nama"], "IC": s["ic"], "SEKOLAH ASAL": s["sekolah_asal"], "BILIK KEBAL": s["bilik_kebal"], "NO SURAT": s["no_surat"]} for s in list_data])
                                    st.download_button("📥 Download Senarai (Excel)", to_excel(df_dl), file_name=f"Senarai_Surat_PK_{kod_ppd}.xlsx", use_container_width=True, key="dl_excel_pk")
                                with col_dl3:
                                    # PDF individu ZIP
                                    if f"surat_pk_zip_{kod_ppd}" in st.session_state:
                                        st.download_button("📥 Download ZIP PDF Individu (Penyelia)", data=st.session_state[f"surat_pk_zip_{kod_ppd}"], file_name=f"Surat_Penyelia_Kawasan_{kod_ppd}_Individu_{datetime.date.today()}.zip", mime="application/zip", use_container_width=True, key="dl_zip_pk")
                                    else:
                                        st.caption("Jana semula untuk dapat ZIP PDF")
                                with col_dl4:
                                    if st.button(f"📤 Hantar Surat ke Sekolah Asal + PDF (SUP boleh download)", type="primary", use_container_width=True, key="btn_hantar_surat_pk"):
                                        try:
                                            berjaya = 0
                                            for s in list_data:
                                                try:
                                                    # Simpan surat_html + pdf info ke data json untuk sekolah asal
                                                    existing = supa.table("cadangan_sup").select("data").eq("id", s["id"]).limit(1).execute()
                                                    old_data = {}
                                                    if existing.data:
                                                        old_data = existing.data[0].get("data") or {}
                                                        if isinstance(old_data, str):
                                                            try:
                                                                pass  # json sudah diimport di spm_core
                                                                old_data = json.loads(old_data)
                                                            except:
                                                                old_data = {}
                                                    old_data.update({
                                                        "surat_html": s.get("html",""),
                                                        "surat_tarikh": str(datetime.date.today()),
                                                        "surat_no": s["no_surat"],
                                                        "SURAT_DIHANTAR_KE_SEKOLAH_ASAL": True,
                                                        "jenis": "Penyelia Kawasan",
                                                        "bilik_kebal": s.get("bilik_kebal",""),
                                                        "pusat_jagaan": s.get("pusat_jagaan", [])
                                                    })
                                                    supa.table("cadangan_sup").update({"status": "LULUS PPD - SURAT PK DIHANTAR KE SEKOLAH ASAL", "no_surat": s["no_surat"], "data": old_data}).eq("id", s["id"]).execute()
                                                except:
                                                    # Fallback simple
                                                    supa.table("cadangan_sup").update({"status": "SURAT PK DIHANTAR", "no_surat": s["no_surat"]}).eq("id", s["id"]).execute()
                                                berjaya += 1
                                            st.success(f"✅ {berjaya} surat Penyelia Kawasan (No {list_data[0]['no_surat']} hingga {list_data[-1]['no_surat']}) telah DIHANTAR ke sekolah asal! SUP boleh lihat & download PDF di menu Surat Lantikan Saya")
                                            st.balloons()
                                            st.info(f"📄 Surat telah dihantar ke sekolah asal guru - No surat ikut berturutan daerah {kod_ppd} (sama seperti petugas lain). SUP boleh cetak PDF di Surat Lantikan Saya")
                                        except Exception as e:
                                            st.error(f"Error hantar: {e}")


        elif menu == "jana_surat":
            surat_panel("PPD", kod_ppd=kod_ppd)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
                <h2 style="margin:0; color:white;">📄 Janaan Surat Lantikan - PPD {kod_ppd} - {PPD_MAP.get(kod_ppd,'')}</h2>
                <p style="margin:5px 0 0 0; color:#bbdefb;">Surat yang telah diluluskan PPD - PPD boleh lihat, jana semula & download PDF. Surat yang sama juga dihantar ke sekolah asal guru untuk SUP cetak.</p>
            </div>
            """, unsafe_allow_html=True)

            df_cad_all_surat = get_cadangan_df(kod_ppd=kod_ppd)
            if df_cad_all_surat.empty:
                st.warning("Belum ada cadangan di PPD ini")
                st.stop()

            # Build pusat map
            df_pusat_raw_surat = get_pusat_df()
            pusat_map_surat = {}
            try:
                for _, r in df_pusat_raw_surat.iterrows():
                    d = r.get("data") if isinstance(r.get("data"), dict) else {}
                    if isinstance(d, str):
                        try: d = json.loads(d)
                        except: d = {}
                    no_p = str(r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                    nama_p = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                    if no_p:
                        pusat_map_surat[no_p] = nama_p
            except:
                pass

            # Filter yang ada no_surat / sudah LULUS
            def has_surat_ppd(row):
                ns = str(row.get("no_surat") or "").strip()
                stt = str(row.get("status") or "").upper()
                return (ns != "" and ns.lower() not in ("none","null","nan")) or ("LULUS" in stt)

            df_lulus_surat = df_cad_all_surat[df_cad_all_surat.apply(has_surat_ppd, axis=1)].copy() if not df_cad_all_surat.empty else pd.DataFrame()
            df_belum_surat = df_cad_all_surat[~df_cad_all_surat.apply(has_surat_ppd, axis=1)].copy() if not df_cad_all_surat.empty else pd.DataFrame()

            def papar_belum_surat_ppd(df_belum, pusat_map):
                """Senarai nama guru yang belum ada surat. Hanya dipanggil jika ada yang belum."""
                st.markdown(f"#### ⏳ Senarai Guru Belum Ada Surat ({len(df_belum)} orang)")
                rows_b = []
                for i_b, (_, r) in enumerate(df_belum.iterrows(), start=1):
                    kp = str(r.get("kod_pusat", "") or r.get("KOD_PUSAT", "") or "").strip()
                    if kp.lower() in ("none", "null", "nan"):
                        kp = ""
                    rows_b.append({
                        "BIL": i_b,
                        "NAMA GURU": r.get("NAMA_GURU", "") or r.get("nama_guru", ""),
                        "IC": r.get("IC_GURU", "") or r.get("ic_guru", ""),
                        "JAWATAN": r.get("JAWATAN_CADANGAN", "") or r.get("jawatan_cadangan", ""),
                        "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL", "") or r.get("kod_sekolah_asal", ""),
                        "PUSAT TUGAS": kp or "-",
                        "NAMA PUSAT": str(pusat_map.get(kp.upper(), ""))[:30] if kp else "",
                        "STATUS": r.get("status", "") or r.get("STATUS", ""),
                        "SEBAB": "Belum ditempatkan ke pusat" if not kp else "Belum diluluskan (menu Kelulusan)",
                    })
                df_b_show = pd.DataFrame(rows_b)
                st.dataframe(df_b_show, use_container_width=True, hide_index=True, height=min(420, 38 + 35 * len(df_b_show)))
                st.download_button("📥 Export Senarai Belum Ada Surat (Excel)", to_excel(df_b_show),
                                   file_name=f"belum_ada_surat_{kod_ppd}_{datetime.date.today()}.xlsx",
                                   key="dl_belum_ada_surat_ppd")

            if df_belum_surat.empty:
                # Tiada yang belum ada surat -> kotak "Belum Ada Surat" tidak dipaparkan
                c1, c2 = st.columns(2)
                c1.metric("Total Cadangan PPD", len(df_cad_all_surat))
                c2.metric("✅ Sudah Lulus Ada Surat", len(df_lulus_surat))
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Cadangan PPD", len(df_cad_all_surat))
                c2.metric("✅ Sudah Lulus Ada Surat", len(df_lulus_surat))
                c3.metric("⏳ Belum Ada Surat", len(df_belum_surat))
                papar_belum_surat_ppd(df_belum_surat, pusat_map_surat)

            if df_lulus_surat.empty:
                st.warning("Belum ada surat yang diluluskan di PPD ini - sila luluskan di menu Kelulusan dahulu")
                st.info("Pergi ke Kelulusan > Lulus Keseluruhan atau Lulus Mengikut Pusat untuk luluskan dan jana surat")
                st.stop()

            # Tabs for view
            # [FLYOUT] st.tabs diganti sub menu flyout

            if fly_cur == "keseluruhan":
                st.markdown(f"### 📄 Semua Surat Lantikan PPD {kod_ppd} - {len(df_lulus_surat)} Surat - Template JPN Selaras")
                st.info(f"🔹 Template surat diambil dari function JPN `surat_templates_jpn` - JPN cipta, PPD guna. Jika JPN belum cipta template untuk jawatan, akan guna fallback PPD.")

                display_rows = []
                for _, r in df_lulus_surat.iterrows():
                    display_rows.append({
                        "id": r.get("id",""),
                        "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                        "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                        "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                        "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                        "NAMA SEKOLAH ASAL": str(r.get("NAMA_SEKOLAH_ASAL","") or r.get("nama_sekolah_asal",""))[:30],
                        "PUSAT TUGAS": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                        "NAMA PUSAT": pusat_map_surat.get(str(r.get("kod_pusat","") or "").upper().strip(), "")[:30],
                        "NO SURAT": r.get("no_surat","") or "",
                        "STATUS": r.get("status","") or ""
                    })
                df_display_all = pd.DataFrame(display_rows)
                st.dataframe(df_display_all, use_container_width=True, hide_index=True)

                # ===== NEW V33: JANA DENGAN TEMPLATE JPN + ZIP + HANTAR KE SEKOLAH ASAL =====
                col_gen1, col_gen2, col_gen3 = st.columns(3)
                with col_gen1:
                    if st.button(f"📄 Jana Surat {len(df_display_all)} (Template JPN)", type="primary", use_container_width=True, key="btn_jana_pdf_keseluruhan_v33"):
                        with st.spinner(f"Menjana {len(df_display_all)} surat guna template JPN..."):
                            try:
                                surat_list = []
                                for _, r in df_display_all.iterrows():
                                    surat_list.append({
                                        "nama": r["NAMA GURU"],
                                        "ic": r["IC"],
                                        "jawatan": r["JAWATAN"],
                                        "sekolah_asal": r["SEKOLAH ASAL"],
                                        "nama_sekolah_asal": r["NAMA SEKOLAH ASAL"],
                                        "pusat": r["PUSAT TUGAS"],
                                        "nama_pusat": r["NAMA PUSAT"],
                                        "no_surat": r["NO SURAT"]
                                    })
                                # 1. PDF Kolektif guna JPN template
                                pdf_kolektif = generate_surat_kolektif_pdf_bytes_JPN(surat_list, kod_ppd, PPD_MAP.get(kod_ppd,""), f"SURAT LANTIKAN KESELURUHAN PPD {kod_ppd} - {len(surat_list)} GURU - JPN SELARAS")
                                if pdf_kolektif:
                                    st.session_state[f"pdf_keseluruhan_{kod_ppd}"] = pdf_kolektif
                                # 2. ZIP Pukal individu guna JPN template
                                zip_bytes = create_zip_pukal_dari_JPN(surat_list, kod_ppd, PPD_MAP.get(kod_ppd,""))
                                if zip_bytes:
                                    st.session_state[f"zip_keseluruhan_{kod_ppd}"] = zip_bytes
                                # 3. Hantar ke sekolah asal petugas (auto update status)
                                jml_hantar = hantar_surat_ke_sekolah_asal_bulk(surat_list, kod_ppd)
                                st.session_state[f"surat_list_keseluruhan_{kod_ppd}"] = surat_list
                                st.success(f"✅ Berjaya! {len(surat_list)} surat dijana guna template JPN, {jml_hantar} surat sampai ke sekolah asal!")
                                st.balloons()
                            except Exception as e:
                                st.error("Maaf, surat tidak dapat dijana. Sila cuba lagi atau hubungi pentadbir sistem.")

                with col_gen2:
                    if f"pdf_keseluruhan_{kod_ppd}" in st.session_state:
                        pdf_data = st.session_state[f"pdf_keseluruhan_{kod_ppd}"]
                        st.download_button(f"📥 Download PDF Pukal Kolektif {len(df_display_all)} Surat (Template JPN)", data=pdf_data, file_name=f"Surat_Kolektif_JPN_{kod_ppd}_{datetime.date.today()}.pdf", mime="application/pdf", use_container_width=True, key="dl_pdf_keseluruhan_main_v33")
                    else:
                        st.caption("Belum jana PDF kolektif")

                with col_gen3:
                    if f"zip_keseluruhan_{kod_ppd}" in st.session_state:
                        zip_data = st.session_state[f"zip_keseluruhan_{kod_ppd}"]
                        st.download_button(f"📦 Download ZIP Pukal Individu {len(df_display_all)} PDF (Template JPN)", data=zip_data, file_name=f"ZIP_Surat_Individu_JPN_{kod_ppd}_{datetime.date.today()}.zip", mime="application/zip", use_container_width=True, key="dl_zip_keseluruhan_main_v33", type="primary")
                        st.caption(f"✅ {len(df_display_all)} fail PDF individu dalam ZIP - senang edar")
                    else:
                        st.caption("Belum jana ZIP pukal")

                # Preview if exists
                if f"pdf_keseluruhan_{kod_ppd}" in st.session_state:
                    st.success(f"✅ PDF & ZIP telah dijana guna template JPN. Surat auto sampai ke sekolah asal guru untuk SUP cetak. ({len(df_display_all)} surat)")
                    # Tunjuk breakdown ikut sekolah asal
                    if f"surat_list_keseluruhan_{kod_ppd}" in st.session_state:
                        sl = st.session_state[f"surat_list_keseluruhan_{kod_ppd}"]
                        from collections import Counter
                        cnt = Counter([s.get("sekolah_asal","") for s in sl])
                        st.markdown("**📊 Surat sampai ke sekolah asal:**")
                        cols = st.columns(4)
                        for i, (sek, jml) in enumerate(cnt.most_common(12)):
                            cols[i % 4].metric(sek, f"{jml} surat")

            if fly_cur == "pusat":
                st.markdown("### 🏫 Janaan Surat Ikut Pusat - Template JPN + ZIP")
                st.info("Guna template JPN selaras, jana PDF kolektif + ZIP pukal individu, auto sampai ke sekolah asal")
                # Group by pusat
                pusat_groups_surat = {}
                for _, r in df_lulus_surat.iterrows():
                    kp = str(r.get("kod_pusat") or r.get("KOD_PUSAT") or "").upper().strip()
                    if kp:
                        if kp not in pusat_groups_surat:
                            pusat_groups_surat[kp] = []
                        pusat_groups_surat[kp].append(r)

                pilih_pusat_jana = st.selectbox(
                    "Pilih Pusat Untuk Jana Surat PDF",
                    sorted(pusat_groups_surat.keys()),
                    format_func=lambda x: f"{x} - {pusat_map_surat.get(x,'')} ({len(pusat_groups_surat[x])} surat)",
                    key="pilih_pusat_jana_surat"
                )

                if pilih_pusat_jana:
                    guru_pusat = pusat_groups_surat[pilih_pusat_jana]
                    df_pusat_surat = pd.DataFrame([{
                        "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                        "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                        "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                        "SEKOLAH ASAL": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                        "NO SURAT": r.get("no_surat",""),
                        "STATUS": r.get("status","")
                    } for r in guru_pusat])
                    st.dataframe(df_pusat_surat, use_container_width=True, hide_index=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"📄 Jana {len(guru_pusat)} Surat {pilih_pusat_jana} (JPN + ZIP)", type="primary", use_container_width=True, key=f"btn_jana_pdf_pusat_{pilih_pusat_jana}_v33"):
                            with st.spinner(f"Menjana {len(guru_pusat)} surat..."):
                                try:
                                    surat_list_p = []
                                    for r in guru_pusat:
                                        surat_list_p.append({
                                            "nama": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                            "ic": r.get("IC_GURU","") or r.get("ic_guru",""),
                                            "jawatan": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                                            "sekolah_asal": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                                            "nama_sekolah_asal": r.get("NAMA_SEKOLAH_ASAL","") or r.get("nama_sekolah_asal",""),
                                            "pusat": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                                            "nama_pusat": pusat_map_surat.get(str(r.get("kod_pusat","") or "").upper().strip(), ""),
                                            "no_surat": r.get("no_surat","")
                                        })
                                    pdf_pusat = generate_surat_kolektif_pdf_bytes_JPN(surat_list_p, kod_ppd, PPD_MAP.get(kod_ppd,""), f"SURAT LANTIKAN {pilih_pusat_jana} - {pusat_map_surat.get(pilih_pusat_jana,'')} - JPN SELARAS")
                                    zip_pusat = create_zip_pukal_dari_JPN(surat_list_p, kod_ppd, PPD_MAP.get(kod_ppd,""))
                                    jml_hantar = hantar_surat_ke_sekolah_asal_bulk(surat_list_p, kod_ppd)
                                    if pdf_pusat:
                                        st.session_state[f"pdf_pusat_{pilih_pusat_jana}"] = pdf_pusat
                                    if zip_pusat:
                                        st.session_state[f"zip_pusat_{pilih_pusat_jana}"] = zip_pusat
                                    st.success(f"✅ PDF+ZIP {pilih_pusat_jana} {len(surat_list_p)} surat berjaya dijana (Template JPN) + {jml_hantar} sampai sekolah asal!")
                                except Exception as e:
                                    st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")
                    with c2:
                        if f"pdf_pusat_{pilih_pusat_jana}" in st.session_state:
                            pdf_d = st.session_state[f"pdf_pusat_{pilih_pusat_jana}"]
                            st.download_button(f"📥 PDF Kolektif {pilih_pusat_jana} ({len(guru_pusat)}) - JPN", data=pdf_d, file_name=f"Surat_{pilih_pusat_jana}_{kod_ppd}_{datetime.date.today()}_JPN.pdf", mime="application/pdf", use_container_width=True, key=f"dl_pdf_pusat_{pilih_pusat_jana}_v33")
                        if f"zip_pusat_{pilih_pusat_jana}" in st.session_state:
                            zip_d = st.session_state[f"zip_pusat_{pilih_pusat_jana}"]
                            st.download_button(f"📦 ZIP Pukal Individu {pilih_pusat_jana} ({len(guru_pusat)}) - JPN", data=zip_d, file_name=f"ZIP_{pilih_pusat_jana}_{kod_ppd}_{datetime.date.today()}_JPN.zip", mime="application/zip", use_container_width=True, key=f"dl_zip_pusat_{pilih_pusat_jana}_v33", type="primary")
                        if f"pdf_pusat_{pilih_pusat_jana}" in st.session_state:
                            st.info(f"Surat {pilih_pusat_jana} auto sampai ke sekolah asal guru untuk SUP cetak")

            if fly_cur == "sekolah":
                st.markdown("### 🏫 Surat Ikut Sekolah Asal - Untuk Hantar ke SUP Cetak - Template JPN + ZIP")
                st.caption("Surat yang telah diluluskan akan sampai ke sekolah asal guru - SUP boleh cetak dan bagi pada guru berkenaan. Guna template JPN selaras + ZIP pukal.")

                # Group by sekolah asal
                sekolah_groups_surat = {}
                for _, r in df_lulus_surat.iterrows():
                    ks = str(r.get("KOD_SEKOLAH_ASAL") or r.get("kod_sekolah_asal") or "").upper().strip()
                    if ks:
                        if ks not in sekolah_groups_surat:
                            sekolah_groups_surat[ks] = []
                        sekolah_groups_surat[ks].append(r)

                pilih_sekolah_surat = st.selectbox(
                    "Pilih Sekolah Asal Untuk Lihat Surat Yang Sampai",
                    sorted(sekolah_groups_surat.keys()),
                    format_func=lambda x: f"{x} - {len(sekolah_groups_surat[x])} surat sampai (untuk SUP cetak) - Template JPN",
                    key="pilih_sekolah_surat_jana"
                )

                if pilih_sekolah_surat:
                    guru_sekolah = sekolah_groups_surat[pilih_sekolah_surat]
                    df_sek_surat = pd.DataFrame([{
                        "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                        "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                        "JAWATAN": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                        "PUSAT TUGAS": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                        "NAMA PUSAT": pusat_map_surat.get(str(r.get("kod_pusat","") or "").upper().strip(), "")[:30],
                        "NO SURAT": r.get("no_surat",""),
                        "STATUS": r.get("status","")
                    } for r in guru_sekolah])
                    st.dataframe(df_sek_surat, use_container_width=True, hide_index=True)
                    st.success(f"✅ {len(guru_sekolah)} surat telah sampai ke sekolah asal {pilih_sekolah_surat} - SUP boleh cetak (Template JPN)")

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"📄 Jana PDF {pilih_sekolah_surat} - {len(guru_sekolah)} Guru (JPN+ZIP)", type="primary", use_container_width=True, key=f"btn_jana_pdf_sekolah_{pilih_sekolah_surat}_v33"):
                            with st.spinner(f"Menjana {len(guru_sekolah)} surat sekolah asal..."):
                                try:
                                    surat_list_s = []
                                    for r in guru_sekolah:
                                        surat_list_s.append({
                                            "nama": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                            "ic": r.get("IC_GURU","") or r.get("ic_guru",""),
                                            "jawatan": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                                            "sekolah_asal": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal",""),
                                            "nama_sekolah_asal": r.get("NAMA_SEKOLAH_ASAL","") or r.get("nama_sekolah_asal","") or pilih_sekolah_surat,
                                            "pusat": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                                            "nama_pusat": pusat_map_surat.get(str(r.get("kod_pusat","") or "").upper().strip(), ""),
                                            "no_surat": r.get("no_surat","")
                                        })
                                    pdf_sek = generate_surat_kolektif_pdf_bytes_JPN(surat_list_s, kod_ppd, PPD_MAP.get(kod_ppd,""), f"SURAT LANTIKAN SEKOLAH ASAL {pilih_sekolah_surat} - {len(surat_list_s)} GURU - UNTUK SUP CETAK - JPN SELARAS")
                                    zip_sek = create_zip_pukal_dari_JPN(surat_list_s, kod_ppd, PPD_MAP.get(kod_ppd,""))
                                    if pdf_sek:
                                        st.session_state[f"pdf_sekolah_{pilih_sekolah_surat}"] = pdf_sek
                                    if zip_sek:
                                        st.session_state[f"zip_sekolah_{pilih_sekolah_surat}"] = zip_sek
                                    st.success(f"✅ PDF+ZIP Sekolah Asal {pilih_sekolah_surat} {len(surat_list_s)} surat berjaya dijana (JPN)!")
                                except Exception as e:
                                    st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")
                    with c2:
                        if f"pdf_sekolah_{pilih_sekolah_surat}" in st.session_state:
                            pdf_s = st.session_state[f"pdf_sekolah_{pilih_sekolah_surat}"]
                            st.download_button(f"📥 PDF Sekolah Asal {pilih_sekolah_surat} ({len(guru_sekolah)}) - JPN", data=pdf_s, file_name=f"Surat_SekolahAsal_{pilih_sekolah_surat}_{kod_ppd}_{datetime.date.today()}_JPN.pdf", mime="application/pdf", use_container_width=True, key=f"dl_pdf_sekolah_{pilih_sekolah_surat}_v33")
                        if f"zip_sekolah_{pilih_sekolah_surat}" in st.session_state:
                            zip_s = st.session_state[f"zip_sekolah_{pilih_sekolah_surat}"]
                            st.download_button(f"📦 ZIP Sekolah Asal {pilih_sekolah_surat} ({len(guru_sekolah)}) - JPN", data=zip_s, file_name=f"ZIP_SekolahAsal_{pilih_sekolah_surat}_{kod_ppd}_{datetime.date.today()}_JPN.zip", mime="application/zip", use_container_width=True, key=f"dl_zip_sekolah_{pilih_sekolah_surat}_v33", type="primary")
                        if f"pdf_sekolah_{pilih_sekolah_surat}" in st.session_state:
                            st.info(f"📄 Surat ini akan dicetak oleh SUP {pilih_sekolah_surat} dan diberi kepada guru berkenaan (Template JPN selaras)")




        elif menu == "batal":
            st.header(f"🗑️ Batal - PPD {kod_ppd} - Batal Semua Penempatan / Cadangan")
            st.warning("⚠️ Tindakan ini hanya untuk PPD anda sahaja. Daerah lain tidak terjejas kerana sistem guna scoped_db.")
            
            from ppd_cadangan import batal_semua_penempatan_ppd, batal_semua_cadangan_ppd
            
            tab1, tab2 = st.tabs(["1️⃣ Batal Semua Penempatan", "2️⃣ Batal Semua Cadangan"])
            
            with tab1:
                st.subheader("Batal Semua Penempatan")
                st.caption("Fungsi: Clear kod_pusat + reset status jadi TERPILIH PPD. Cadangan SUP kekal, cuma penempatan PPD direset.")
                try:
                    df_c = get_cadangan_df(kod_ppd=kod_ppd)
                    cnt_penempatan = len(df_c[df_c.get("kod_pusat","").astype(str).str.strip()!=""]) if not df_c.empty else 0
                except:
                    cnt_penempatan = 0
                st.metric("Jumlah ada penempatan sekarang", cnt_penempatan)
                
                c1, c2 = st.columns(2)
                confirm_penempatan = c1.text_input("Taip BATAL PENEMPATAN untuk sahkan", key="confirm_batal_penempatan", placeholder="BATAL PENEMPATAN")
                if c2.button("🔴 Batal Semua Penempatan", key="btn_batal_penempatan", type="primary", disabled=confirm_penempatan!="BATAL PENEMPATAN", use_container_width=True):
                    with st.spinner("Membatalkan penempatan..."):
                        ok, msg = batal_semua_penempatan_ppd(kod_ppd)
                    if msg and ok==0:
                        st.error(f"Gagal: {msg}")
                    else:
                        st.success(f"✅ {ok} penempatan berjaya dibatalkan. Status reset ke TERPILIH PPD.")
                        st.cache_data.clear()
                        st.rerun()
            
            with tab2:
                st.subheader("Batal Semua Cadangan")
                st.caption("Fungsi: Padam / reset semua cadangan SUP dalam PPD anda. Guna bila nak mula semula.")
                st.error("⛔ Berbahaya: Semua cadangan SUP untuk PPD anda akan hilang!")
                try:
                    df_all = get_cadangan_df(kod_ppd=kod_ppd)
                    cnt_all = len(df_all) if df_all is not None and not df_all.empty else 0
                except:
                    cnt_all = 0
                st.metric("Jumlah cadangan sekarang", cnt_all)
                
                pilihan_batal = st.radio("Pilih tindakan", ["Reset status ke HANTAR KE PPD (selamat, masih ada data)", "Padam terus dari database (DELETE)"], key="pilihan_batal_cadangan")
                mode = "reset" if "Reset" in pilihan_batal else "delete"
                
                c1, c2 = st.columns(2)
                confirm_cadangan = c1.text_input("Taip BATAL CADANGAN untuk sahkan", key="confirm_batal_cadangan", placeholder="BATAL CADANGAN")
                if c2.button("🔴 Batal Semua Cadangan", key="btn_batal_cadangan", type="primary", disabled=confirm_cadangan!="BATAL CADANGAN", use_container_width=True):
                    with st.spinner("Membatalkan cadangan..."):
                        ok, msg = batal_semua_cadangan_ppd(kod_ppd, mode=mode)
                    if msg and ok==0:
                        st.error(f"Gagal: {msg}")
                    else:
                        if mode=="delete":
                            st.success(f"✅ {ok} cadangan berjaya DIPADAM terus dari database.")
                        else:
                            st.success(f"✅ {ok} cadangan berjaya direset ke HANTAR KE PPD.")
                        st.cache_data.clear()
                        st.rerun()


        elif menu == "export":
            st.header(f"Export Data PPD {kod_ppd}")

            st.header(f"Export Data PPD {kod_ppd}")


            df_cad = get_cadangan_df(kod_ppd=kod_ppd)
            if not df_cad.empty:
                st.download_button("📥 Export Cadangan PPD (Excel)", to_excel(df_cad), file_name=f"laporan_PPD_{kod_ppd}_{datetime.date.today()}.xlsx", use_container_width=True)
            try:
                res = supa.table("guru_master").select("*").eq("kod_ppd", kod_ppd.lower()).limit(5000).execute()
                df_guru = pd.DataFrame(res.data or [])
                if not df_guru.empty:
                    st.download_button("📥 Export Guru PPD (Excel)", to_excel(df_guru), file_name=f"guru_PPD_{kod_ppd}.xlsx", use_container_width=True)
            except Exception as e:
                st.error(str(e))

# ================= ROLE: JPN =================
