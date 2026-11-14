# -*- coding: utf-8 -*-
"""Peranan SUP - bacaan dari guru_master (satu sekolah)."""
import spm_core as _core
import ui_theme as _ui
globals().update({k: v for k, v in vars(_core).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(_ui).items() if not k.startswith("__")})
from program_config import adalah_spm, jawatan_pilihan, jawatan_betul, cfg as program_cfg
from ppd_program import keperluan_ub_sekolah, metrik_cadangan_ub
from sup_warna import sudah_hantar, style_cadangan_hantar, kira_hantar, LEGEND_HTML
style_nama_hijau_hantar = style_cadangan_hantar      # hijau = sudah hantar PPD, kuning = belum hantar

def render_sup():
    kod = st.session_state.kod
    info = st.session_state.info

    kod = st.session_state.kod
    info = st.session_state.info
    if SCOPE["ppd"] and str(info.get("kod_ppd", "")).upper() != SCOPE["ppd"]:
        st.session_state.clear(); st.rerun()
    no_pusat_list_sidebar = sup_no_pusat_list(kod)
    MENU_SUP = [('dashboard', '📊 Dashboard'), ('senarai', '📋 Senarai Guru'), ('tambah', '➕ Tambah Guru'),
                    ('import', '📤 Import Excel'), ('buang', '🗑️ Buang Guru'), ('cadangan', '📝 Cadangan Lantikan'),
                    ('hantar', '📤 Hantar ke PPD'), ('petugas', '👥 Petugas Hadir di Sekolah Saya'), ('surat', '📄 Surat Lantikan Saya'), ('keluar', '🚪 Log Keluar')]
    if "sup_dash_sub" not in st.session_state:
        st.session_state.sup_dash_sub = "utama"
    shell_header_sup(kod, info, no_pusat_list_sidebar)
    menu, fly_cur, col_main = shell_layout("sup_menu_sel", MENU_SUP, FLY_SUP, "sup_dash_sub", "fly_sup")

    with col_main:
        show_flash()
        df_guru = get_guru_df(kod)

        if menu == "keluar":
            st.session_state.clear()
            st.rerun()

        elif menu == "dashboard":
            try:
                df_pusat_all = get_pusat_df()
                pusat_sekolah = []
                for _, r in df_pusat_all.iterrows():
                    d = r.get("data") if isinstance(r.get("data"), dict) else {}
                    if isinstance(d, str):
                        try: d = json.loads(d)
                        except: d = {}
                    ks_tuan = str(r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or r.get("KOD_SEKOLAH") or d.get("KOD_SEKOLAH") or d.get("KOD SEKOLAH") or d.get("KOD_SEKOLAH_TUAN_RUMAH") or "").upper().strip()
                    ks_biasa = str(r.get("kod_sekolah") or d.get("KOD_SEKOLAH") or "").upper().strip()
                    if ks_tuan == kod.upper().strip() or ks_biasa == kod.upper().strip():
                        calon = r.get("jumlah_calon") or r.get("calon") or r.get("JUMLAH_CALON") or d.get("JUMLAH_CALON") or d.get("CALON") or 0
                        try: calon_i = int(float(str(calon) or 0))
                        except: calon_i = 0
                        kelas = kira_kelas_dari_calon(calon_i)
                        petugas_k9 = kira_petugas_dari_kelas(kelas)
                        sekolah_perlu = kira_sekolah_perlu_calonkan(kelas)
                        no_pusat_val = str(r.get("no_pusat") or r.get("kod_pusat") or r.get("NO_PUSAT") or d.get("NO_PUSAT") or d.get("NO PUSAT") or d.get("KOD_PUSAT") or "").upper().strip()
                        nama_pusat_val = str(r.get("nama_pusat") or r.get("NAMA_PUSAT") or d.get("NAMA_PUSAT") or d.get("NAMA PUSAT") or "").upper().strip()
                        pusat_sekolah.append({"NO_PUSAT": no_pusat_val, "NAMA_PUSAT": nama_pusat_val, "CALON": calon_i, "KELAS": kelas, "PETUGAS_K9": petugas_k9, "SEKOLAH_PERLU": sekolah_perlu})
            except Exception as e:
                st.error(f"Error load pusat: {e}")
                pusat_sekolah = []

            if pusat_sekolah:
                total_calon = sum([p["CALON"] for p in pusat_sekolah])
                total_kelas = sum([p["KELAS"] for p in pusat_sekolah])
                total_petugas = sum([p["PETUGAS_K9"] for p in pusat_sekolah])
                total_perlu = sum([p["SEKOLAH_PERLU"] for p in pusat_sekolah])
                no_pusat_list = ", ".join([f"{p['NO_PUSAT']}" for p in pusat_sekolah if p['NO_PUSAT']])
            else:
                total_calon = 0; total_kelas = 0; total_petugas = 0; total_perlu = 0; no_pusat_list = "-"

            sub = st.session_state.get("sup_dash_sub", "utama")

            if sub == "utama":
                if pusat_sekolah:
                    try:
                        st.markdown(jpn_kad_pusat(no_pusat_list, total_kelas, total_petugas, total_perlu, kod), unsafe_allow_html=True)
                    except:
                        st.markdown(f"<div style='background:white; padding:20px; border-radius:12px; border:3px solid #1565c0; margin-bottom:20px;'><h3>🏫 KEPERLUAN PENGAWAS - {kod}</h3><div>NO PUSAT: <b>{no_pusat_list}</b> | Kelas: {total_kelas} | Petugas: {total_petugas} | Perlu: {total_perlu}</div></div>", unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ Tiada pusat dijumpai untuk sekolah {kod}")
                st.markdown("<div style='background:#E3F2FD; border:1px dashed #CFDBF0; border-radius:8px; padding:8px 12px; font-size:0.8rem; color:#0D47A1; text-align:center; margin-bottom:12px;'>📌 Sub-menu ada di sebelah kiri (popup) - pilih di kotak sebelah kanan Dashboard</div>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Jumlah Guru", len(df_guru))
                with c2:
                    try:
                        cnt = supa.table("guru_master").select("id", count="exact").execute()
                        st.metric(f"Total Guru {scope_label()}", cnt.count)
                    except: st.metric(f"Total Guru {scope_label()}", "-")
                with c3: st.metric("Pusat Sekolah Ini", len(pusat_sekolah))
                with c4:
                    try:
                        cad = get_cadangan_df(kod_sekolah=kod)
                        st.metric("Cadangan Dihantar", len(cad))
                    except: st.metric("Cadangan", "0")
                st.markdown("---")
                st.subheader("Guru Terkini (Ringkasan 5 Terbaru)")
                if not df_guru.empty:
                    st.dataframe(df_guru[["NAMA GURU", "IC", "TELEFON", "JAWATAN CADANGAN"]].head(5), use_container_width=True, hide_index=True)
                else:
                    st.warning("Belum ada guru. Sila Tambah Guru atau Import Excel.")

            elif sub == "pusat":
                st.markdown(f"<div style='background:white; border:2px solid #0D47A1; border-radius:12px; padding:14px 16px; margin-bottom:14px;'><div style='font-weight:900; color:#0D47A1; font-size:1.1rem;'>📍 Senarai Pusat Sekolah Anda - {kod}</div><div style='font-size:0.85rem; color:#0D47A1; margin-top:4px;'>Paparan dashboard utama disembunyikan. Klik Utama di popup sebelah untuk kembali.</div></div>", unsafe_allow_html=True)
                if pusat_sekolah:
                    df_pusat_display = pd.DataFrame(pusat_sekolah)
                    cols_order = ["NO_PUSAT", "NAMA_PUSAT", "CALON", "KELAS", "PETUGAS_K9", "SEKOLAH_PERLU"]
                    df_pusat_display = df_pusat_display[cols_order] if all(c in df_pusat_display.columns for c in cols_order) else df_pusat_display
                    st.dataframe(df_pusat_display, use_container_width=True, hide_index=True)
                    st.success(f"Ada {len(pusat_sekolah)} pusat | {total_calon} calon | {total_kelas} kelas")
                else:
                    st.warning("Tiada pusat dijumpai")

            elif sub == "guru":
                st.markdown(f"<div style='background:white; border:2px solid #0D47A1; border-radius:12px; padding:14px 16px; margin-bottom:14px;'><div style='font-weight:900; color:#0D47A1; font-size:1.1rem;'>👥 Guru Terkini - {kod}</div><div style='font-size:0.85rem; color:#0D47A1; margin-top:4px;'>Paparan dashboard utama disembunyikan. Klik Utama di popup sebelah untuk kembali.</div></div>", unsafe_allow_html=True)
                if not df_guru.empty:
                    cols_show = [c for c in ["NAMA GURU", "IC", "TELEFON", "JAWATAN CADANGAN", "POSKOD_RUMAH"] if c in df_guru.columns]
                    st.dataframe(df_guru[cols_show] if cols_show else df_guru, use_container_width=True, hide_index=True)
                    st.info(f"Jumlah: {len(df_guru)} guru")
                else:
                    st.warning("Belum ada guru. Sila Tambah Guru atau Import Excel.")

        elif menu == "senarai":
            st.header(f"Senarai Guru - {kod} - Lengkap")
            if df_guru.empty:
                st.info("guru_master kosong untuk sekolah ini. Sila Tambah Guru atau Import Excel.")
            else:
                st.success(f"Ada {len(df_guru)} guru di {kod}")

                # ===== FILTER IKUT JAWATAN - SUP SENARAI GURU (BARU) =====
                if fly_cur == "filter":
                    st.markdown("### 🔍 Filter Ikut Jawatan - Senarai Guru")
                    jawatan_sup_list = []
                    col_jawatan_sup = "JAWATAN CADANGAN" if "JAWATAN CADANGAN" in df_guru.columns else "JAWATAN_CADANGAN" if "JAWATAN_CADANGAN" in df_guru.columns else None
                    if col_jawatan_sup:
                        for _, r in df_guru.iterrows():
                            j = str(r.get(col_jawatan_sup, "")).strip()
                            if j and j not in jawatan_sup_list:
                                jawatan_sup_list.append(j)
                    order_j = jawatan_pilihan()
                    jawatan_sup_sorted = sorted(jawatan_sup_list, key=lambda x: (order_j.index(x) if x in order_j else 99, x))

                    if "filter_jawatan_sup_senarai" not in st.session_state:
                        st.session_state["filter_jawatan_sup_senarai"] = []

                    col_f1_sup, col_f2_sup, col_f3_sup, col_f4_sup = st.columns([2,1,1,1])
                    with col_f1_sup:
                        safe_default_sup = [x for x in st.session_state["filter_jawatan_sup_senarai"] if x in jawatan_sup_sorted]
                        if not jawatan_sup_sorted:
                            jawatan_sup_sorted = jawatan_pilihan()
                            safe_default_sup = st.session_state["filter_jawatan_sup_senarai"]
                        if st.session_state["filter_jawatan_sup_senarai"] and not safe_default_sup:
                            for v in st.session_state["filter_jawatan_sup_senarai"]:
                                if v not in jawatan_sup_sorted:
                                    jawatan_sup_sorted.append(v)
                            safe_default_sup = st.session_state["filter_jawatan_sup_senarai"]
                        filter_jawatan_sup = st.multiselect("Filter Jawatan", jawatan_sup_sorted, default=safe_default_sup, placeholder="Kosong = semua jawatan")
                        if filter_jawatan_sup != st.session_state["filter_jawatan_sup_senarai"]:
                            st.session_state["filter_jawatan_sup_senarai"] = filter_jawatan_sup
                    with col_f2_sup:
                        current_sup_filter = filter_jawatan_sup if filter_jawatan_sup else st.session_state.get("filter_jawatan_sup_senarai", [])
                        if current_sup_filter:
                            filtered_count = len(df_guru[df_guru[col_jawatan_sup].astype(str).str.strip().isin(current_sup_filter)]) if col_jawatan_sup else 0
                            st.metric(f"Filter: {len(current_sup_filter)}", f"{filtered_count} guru")
                        else:
                            st.metric("Semua", f"{len(df_guru)} guru")
                    with col_f3_sup:
                        if st.button("🔐 Hanya Penyelia", use_container_width=True, key="btn_filter_pk_sup"):
                            st.session_state["filter_jawatan_sup_senarai"] = ["Penyelia Kawasan"]
                            st.rerun()
                    with col_f4_sup:
                        if st.button("🔄 Clear", use_container_width=True, key="btn_clear_sup"):
                            st.session_state["filter_jawatan_sup_senarai"] = []
                            st.rerun()

                    current_sup_filter2 = st.session_state.get("filter_jawatan_sup_senarai", [])
                    df_guru_filtered = df_guru
                    if current_sup_filter2 and col_jawatan_sup:
                        df_guru_filtered = df_guru[df_guru[col_jawatan_sup].astype(str).str.strip().isin(current_sup_filter2)].copy()
                        st.success(f"✅ Filter: {', '.join(current_sup_filter2)} - {len(df_guru_filtered)} guru")

                    # Pecahan ikut jawatan
                    if not df_guru_filtered.empty and col_jawatan_sup:
                        j_counts = df_guru_filtered[col_jawatan_sup].value_counts().to_dict()
                        if j_counts:
                            st.markdown("#### 📊 Pecahan Ikut Jawatan")
                            cols_j_sup = st.columns(len(j_counts))
                            for idx, (j, cnt) in enumerate(sorted(j_counts.items(), key=lambda x: (order_j.index(x[0]) if x[0] in order_j else 99, x[0]))):
                                with cols_j_sup[idx % len(cols_j_sup)]:
                                    icon = "👑" if "Ketua Pengawas" in j and "Timbalan" not in j else "🎖️" if "Timbalan" in j else "🔐" if "Penyelia" in j else "👨‍🏫"
                                    st.metric(f"{icon} {j}", cnt)

                    cols_to_show = [c for c in ["NAMA GURU", "IC", "JANTINA", "POSKOD_RUMAH", "ALAMAT_RUMAH", "TELEFON_GURU", "EMAIL_GURU", "JAWATAN CADANGAN", "JAWATAN_CADANGAN", "PENGALAMAN_SPM", "KOD_SEKOLAH_ASAL", "NAMA_SEKOLAH_ASAL", "NO_PUSAT_ASAL"] if c in df_guru_filtered.columns]
                    if cols_to_show:
                        st.dataframe(df_guru_filtered[cols_to_show], use_container_width=True, hide_index=True)
                        kosong = df_guru_filtered[df_guru_filtered["JANTINA"].isin(["", "KOSONG"]) | df_guru_filtered["POSKOD_RUMAH"].isin(["", "KOSONG"]) | df_guru_filtered["TELEFON_GURU"].isin(["", "KOSONG"])] if "JANTINA" in df_guru_filtered.columns and "POSKOD_RUMAH" in df_guru_filtered.columns and "TELEFON_GURU" in df_guru_filtered.columns else pd.DataFrame()
                        if not kosong.empty:
                            st.warning(f"⚠️ Ada {len(kosong)} guru dengan data KOSONG (JANTINA/POSKOD/ALAMAT/TELEFON/EMAIL). Sila edit di bawah.")

                    st.download_button(" Export Excel Lengkap (Ikut Filter)", to_excel(df_guru_filtered), file_name=f"guru_{kod}_lengkap_{'_'.join(filter_jawatan_sup) if filter_jawatan_sup else 'semua'}.xlsx", use_container_width=True)
                if fly_cur == "edit":
                    st.markdown("---")
                    st.subheader("✏️ Edit Data Guru (Lengkapkan yang kosong)")
                    # Use filtered list for edit too
                    df_for_edit = df_guru_filtered if 'df_guru_filtered' in locals() else df_guru
                    edit_ic = st.selectbox("Pilih IC guru untuk edit", df_for_edit["IC"].tolist() if "IC" in df_for_edit.columns else [], format_func=lambda x: f"{x} - {df_for_edit[df_for_edit['IC']==x]['NAMA GURU'].values[0] if not df_for_edit[df_for_edit['IC']==x].empty else x}")
                    if edit_ic:
                        guru_edit = df_guru[df_guru["IC"] == edit_ic].iloc[0] if not df_guru[df_guru["IC"] == edit_ic].empty else None
                        if guru_edit is not None:
                            with st.form(f"edit_{edit_ic}"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    e_nama = st.text_input("NAMA GURU", value=guru_edit.get("NAMA GURU", ""))
                                    e_ic = st.text_input("IC", value=edit_ic, disabled=True)
                                    e_jantina = st.selectbox("JANTINA", ["LELAKI", "PEREMPUAN"], index=0 if guru_edit.get("JANTINA", "") == "LELAKI" else 1)
                                    e_poskod = st.text_input("POSKOD RUMAH", value=guru_edit.get("POSKOD_RUMAH", ""))
                                    e_alamat = st.text_area("ALAMAT RUMAH", value=guru_edit.get("ALAMAT_RUMAH", ""))
                                with c2:
                                    e_tel = st.text_input("TELEFON GURU", value=guru_edit.get("TELEFON_GURU", "") or guru_edit.get("TELEFON", ""))
                                    e_email = st.text_input("EMAIL GURU", value=guru_edit.get("EMAIL_GURU", ""))
                                    e_jawatan = st.selectbox("JAWATAN CADANGAN", jawatan_pilihan(), index=0)
                                    e_pengalaman = st.text_input("PENGALAMAN SPM", value=guru_edit.get("PENGALAMAN_SPM", ""))
                                    e_no_pusat = st.text_input("NO PUSAT ASAL", value=guru_edit.get("NO_PUSAT_ASAL", ""))

                                if st.form_submit_button("💾 Update Guru", type="primary"):
                                    try:
                                        res = supa.table("guru_master").select("id,data").eq("ic_guru", edit_ic).eq("kod_sekolah", kod).execute()
                                        if not res.data:
                                            res = supa.table("guru_master").select("id,data").eq("ic_guru", edit_ic).execute()
                                        for row in res.data or []:
                                            old_data = row.get("data") or {}
                                            if isinstance(old_data, str):
                                                try: old_data = json.loads(old_data)
                                                except: old_data = {}
                                            new_data = {**old_data, **{"NAMA GURU": e_nama.upper(), "IC": edit_ic, "JANTINA": e_jantina, "POSKOD_RUMAH": e_poskod, "ALAMAT_RUMAH": e_alamat, "TELEFON_GURU": e_tel, "EMAIL_GURU": e_email, "JAWATAN_CADANGAN": e_jawatan, "PENGALAMAN_SPM": e_pengalaman, "NO_PUSAT_ASAL": e_no_pusat, "KOD_SEKOLAH": kod, "KOD_PPD": info.get("kod_ppd", "BH"), "NAMA_SEKOLAH_ASAL": info.get("nama_sekolah", ""), "KOD_SEKOLAH_ASAL": kod}}
                                            supa.table("guru_master").update({"nama_guru": e_nama.upper(), "ic_guru": edit_ic, "data": new_data}).eq("id", row["id"]).execute()
                                        st.success(f"✅ {e_nama} berjaya update!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Gagal update: {e}")

        elif menu == "tambah":
            st.header(f"Tambah Guru - {kod} - Lengkap Semua Maklumat")
            with st.form("tambah_guru", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nama = st.text_input("NAMA GURU * (Wajib)")
                    ic = st.text_input("NO IC * (12 digit, Wajib)")
                    jantina = st.selectbox("JANTINA *", ["LELAKI", "PEREMPUAN"])
                    poskod = st.text_input("POSKOD RUMAH *")
                    alamat = st.text_area("ALAMAT RUMAH * (Wajib)")
                with col2:
                    tel = st.text_input("NO TELEFON GURU * (Wajib)")
                    email = st.text_input("EMAIL GURU")
                    jaw = st.selectbox("JAWATAN CADANGAN (Betul)", jawatan_pilihan())
                    pengalaman = st.text_input("PENGALAMAN SPM (Tahun) - SUP isi", placeholder="Contoh: 3 tahun")
                    no_pusat_asal = st.text_input("NO PUSAT ASAL", placeholder="Contoh: BA142")

                submit = st.form_submit_button("💾 Simpan Guru Lengkap", use_container_width=True, type="primary")
                if submit:
                    if not nama or not ic or not tel or not alamat:
                        st.error("Nama, IC, Telefon, Alamat wajib isi!")
                    else:
                        data = {"NAMA GURU": nama.upper(), "IC": ic, "JANTINA": jantina, "POSKOD_RUMAH": poskod, "ALAMAT_RUMAH": alamat, "NO TELEFON GURU": tel, "TELEFON_GURU": tel, "EMAIL_GURU": email, "JAWATAN_CADANGAN": jaw, "JAWATAN CADANGAN": jaw, "PENGALAMAN_SPM": pengalaman, "PENGALAMAN": pengalaman, "NO_PUSAT_ASAL": no_pusat_asal, "KOD_SEKOLAH": kod, "KOD_SEKOLAH_ASAL": kod, "NAMA_SEKOLAH_ASAL": info.get("nama_sekolah", ""), "KOD_PPD": info.get("kod_ppd", "BH"), "KOD_PPD_ASAL": info.get("kod_ppd", "BH"), "TARIKH DAFTAR": str(datetime.date.today())}
                        try:
                            supa.table("guru_master").insert({"kod_ppd": info.get("kod_ppd", "BH").lower(), "kod_sekolah": kod, "nama_guru": nama.upper(), "ic_guru": ic, "jantina": jantina, "poskod_rumah": poskod, "alamat_rumah": alamat, "telefon_guru": tel, "email_guru": email, "jawatan_cadangan": jaw, "pengalaman_spm": pengalaman, "no_pusat_asal": no_pusat_asal, "kod_ppd_asal": info.get("kod_ppd", "BH"), "kod_sekolah_asal": kod, "nama_sekolah_asal": info.get("nama_sekolah", ""), "data": data}).execute()
                            st.success(f"✅ {nama.upper()} berjaya tambah ke {kod} dengan data lengkap!")
                            st.balloons()
                        except Exception as e:
                            try:
                                supa.table("guru_master").insert({"kod_ppd": info.get("kod_ppd", "BH").lower(), "kod_sekolah": kod, "nama_guru": nama.upper(), "ic_guru": ic, "data": data}).execute()
                                st.success(f"✅ {nama.upper()} berjaya tambah (fallback)!")
                                st.balloons()
                            except Exception as e2:
                                st.error(f"Gagal: {e2}")

        elif menu == "import":
            st.header(f"Import Excel Guru - {kod}")
            st.info("Format Excel: NAMA GURU, IC, JANTINA, NO TELEFON GURU, EMAIL GURU, ALAMAT RUMAH, KOD SEKOLAH, KOD PPD")
            st.download_button("📥 Download Template Guru (Excel Sah)", to_excel(get_template_guru()), file_name="template_guru.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            uploaded = st.file_uploader("Upload Excel Guru", type=["xlsx", "xls"])
            if uploaded:
                try:
                    df_up = pd.read_excel(uploaded)
                    st.write(f"Preview {len(df_up)} baris:")
                    st.dataframe(df_up.head(20), use_container_width=True)
                    batch_size = 500 if len(df_up) > 1000 else 1
                    if st.button(f"Import {len(df_up)} guru (Batch {batch_size})", type="primary"):
                        bar = st.progress(0)
                        status = st.empty()
                        ok = 0
                        if batch_size > 1:
                            for start in range(0, len(df_up), batch_size):
                                end = min(start + batch_size, len(df_up))
                                batch_df = df_up.iloc[start:end]
                                batch = []
                                for _, row in batch_df.iterrows():
                                    try:
                                        d = {}
                                        for k, v in row.to_dict().items():
                                            d[k] = "" if pd.isna(v) else str(v)
                                        nama = d.get("NAMA GURU", "").upper().strip()
                                        if not nama or nama == "NAN": continue
                                        kod_sek = d.get("KOD SEKOLAH", kod).upper().strip() or kod
                                        kod_ppd_val = d.get("KOD PPD", info.get("kod_ppd", "BH")).lower().strip() or info.get("kod_ppd", "BH").lower()
                                        batch.append({"kod_ppd": kod_ppd_val, "kod_sekolah": kod_sek, "nama_guru": nama, "ic_guru": d.get("IC", ""), "data": d})
                                    except: continue
                                if batch:
                                    try:
                                        supa.table("guru_master").insert(batch).execute()
                                        ok += len(batch)
                                    except Exception as e:
                                        st.warning(f"Batch {start}-{end} error: {e}")
                                bar.progress(end / len(df_up))
                                status.write(f"Progress: {end}/{len(df_up)} | OK: {ok}")
                        else:
                            for i, row in df_up.iterrows():
                                try:
                                    nama = str(row.get("NAMA GURU", "")).upper()
                                    ic = str(row.get("IC", ""))
                                    if not nama or nama == "NAN": continue
                                    d = {k: ("" if pd.isna(v) else str(v)) for k, v in row.to_dict().items()}
                                    d["KOD SEKOLAH"] = kod
                                    supa.table("guru_master").insert({"kod_ppd": info.get("kod_ppd", "BH").lower(), "kod_sekolah": kod, "nama_guru": nama, "ic_guru": ic, "data": d}).execute()
                                    ok += 1
                                except Exception as e:
                                    st.warning(f"Baris {i}: {e}")
                                bar.progress((i + 1) / len(df_up))
                        st.success(f"✅ Berjaya import {ok}/{len(df_up)} guru!")
                        st.balloons()
                except Exception as e:
                    st.error(f"Excel error: {e}")

        elif menu == "buang":
            st.header(f"Buang Guru - {kod}")
            if df_guru.empty:
                st.info("Tiada guru untuk dibuang.")
            else:
                st.dataframe(df_guru[["NAMA GURU", "IC", "TELEFON"]], use_container_width=True)
                pilih = st.multiselect("Pilih IC untuk buang (boleh pilih banyak)", df_guru["IC"].tolist(), format_func=lambda x: f"{x} - {df_guru[df_guru['IC']==x]['NAMA GURU'].values[0] if not df_guru[df_guru['IC']==x].empty else x}")
                if pilih:
                    st.warning(f"Kau nak buang {len(pilih)} guru: {', '.join(pilih)}")
                    if st.button(f"🗑️ Confirm Buang {len(pilih)} Guru", type="primary"):
                        for ic in pilih:
                            try:
                                res = supa.table("guru_master").select("id").eq("ic_guru", ic).eq("kod_sekolah", kod).execute()
                                for r in res.data or []:
                                    supa.table("guru_master").delete().eq("id", r["id"]).execute()
                            except Exception as e:
                                st.error(f"{ic}: {e}")
                        st.success(f"✅ Berjaya buang {len(pilih)} guru")
                        st.rerun()

        elif menu == "cadangan":
            st.header(f"Cadangan Lantikan - {kod} - {info.get('nama_sekolah', '')}")
            try:
                df_pusat_all2 = get_pusat_df()
                pusat_sek = []
                for _, r in df_pusat_all2.iterrows():
                    d = r.get("data") if isinstance(r.get("data"), dict) else {}
                    if isinstance(d, str):
                        try: d = json.loads(d)
                        except: d = {}
                    ks = r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or d.get("KOD_SEKOLAH") or d.get("KOD SEKOLAH") or ""
                    if ks.upper().strip() == kod.upper().strip():
                        calon = r.get("jumlah_calon") or r.get("calon") or d.get("JUMLAH_CALON") or 0
                        try: calon_i = int(float(str(calon) or 0))
                        except: calon_i = 0
                        kelas = kira_kelas_dari_calon(calon_i)
                        pusat_sek.append({"calon": calon_i, "kelas": kelas})

                total_kelas_alert = sum([p["kelas"] for p in pusat_sek]) if pusat_sek else 0
                total_calon_alert = sum([p["calon"] for p in pusat_sek]) if pusat_sek else 0
                total_need_simple = kira_sekolah_perlu_calonkan(total_kelas_alert) if total_kelas_alert > 0 else 18

                kuota_ub = {}
                if not adalah_spm():
                    total_kelas_alert, total_need_simple, kuota_ub = keperluan_ub_sekolah(str(info.get("kod_ppd", "")).upper(), kod)
                elif pusat_sek:
                    st.markdown(f"""
                    <div style="background:#e3f2fd; padding:15px; border-radius:10px; border-left:5px solid #0d47a1; margin-bottom:20px;">
                        <h4 style="margin:0; color:#0d47a1;">📢 KEPERLUAN WAJIB SEKOLAH ANDA - {kod}</h4>
                        <p style="margin:5px 0;">Pusat: {len(pusat_sek)} | Calon: {total_calon_alert} | Kelas: {total_kelas_alert} (1 kelas=20 calon)</p>
                        <p style="margin:5px 0; font-size:15px;">
                            <b style="color:#0d47a1;">WAJIB:</b> Ketua Pengawas 1 orang + Timbalan Ketua 1 orang<br>
                            <b style="color:#0d47a1;">OPTIONAL:</b> Penyelia Kawasan 1 orang<br>
                            <b style="color:#1565c0;">Pengawas Peperiksaan: {total_kelas_alert} orang</b> (ikut jumlah kelas)<br>
                            <b>Total Sekolah Perlu Calonkan: {total_need_simple} orang</b> (Formula: {total_calon_alert} calon /20 = {total_kelas_alert} kelas, {total_kelas_alert}+9={total_kelas_alert+9} petugas, +3 KP/TKP/Penyelia = {total_need_simple})
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"Tiada pusat untuk {kod}. Contoh: 105 calon = 6 kelas = Ketua 1 + Timbalan 1 + Penyelia 1 (optional) + Pengawas 6 = 9 wajib, total 18 dengan extra.")
            except:
                total_kelas_alert = 6
                total_need_simple = 18

            if df_guru.empty:
                st.warning("Tiada guru untuk dicadang. Tambah guru dulu.")
            else:
                df_cad_existing = get_cadangan_df(kod_sekolah=kod)
                JAWATAN_BETUL = jawatan_betul()
                if fly_cur == "pilih":
                    st.markdown("### Pilih Guru (EMAIL kosong dibenarkan)")
                    guru_pilih = st.multiselect("Pilih Guru untuk dicadangkan (boleh pilih ramai)", df_guru["IC"].tolist(), format_func=lambda x: f"{df_guru[df_guru['IC']==x]['NAMA GURU'].values[0]} - {x}", key="guru_pilih_simple")
                    col_jawatan, col_exp = st.columns(2)
                    with col_jawatan:
                        jawatan_cadang = st.selectbox("Jawatan Lantikan (Betul)", JAWATAN_BETUL, key="jawatan_simple")
                        jawatan_clean = jawatan_cadang.split(" (")[0]
                    with col_exp:
                        pengalaman_input = st.text_input(f"{program_cfg()['pengalaman']} - SUP isi", placeholder="Contoh: 3 tahun", key="pengalaman_simple")

                    pusat_pilih = "BA142"
                    no_pusat_asal_input = "BA142"

                    if guru_pilih:
                        st.markdown("**Preview Data Guru Dipilih (EMAIL kosong dibenarkan - akan lepas simpan):**")
                        preview_rows = []
                        for ic_prev in guru_pilih[:10]:
                            gr_prev = df_guru[df_guru["IC"] == ic_prev]
                            if not gr_prev.empty:
                                r = gr_prev.iloc[0]
                                preview_rows.append({"IC": ic_prev, "NAMA": r.get("NAMA GURU", "")[:20], "JANTINA": r.get("JANTINA", "") or "-", "POSKOD": r.get("POSKOD_RUMAH", "") or "-", "ALAMAT": (r.get("ALAMAT_RUMAH", "")[:20] or "-"), "TELEFON": r.get("TELEFON_GURU", "") or r.get("TELEFON", "") or "-", "EMAIL": r.get("EMAIL_GURU", "") or "-"})
                        if preview_rows:
                            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

                        catatan = ""
                        if st.button(f" Simpan Cadangan - {len(guru_pilih) if 'guru_pilih' in locals() and guru_pilih else 0} guru", type="primary", key="btn_simpan_simple"):
                            if not guru_pilih:
                                st.error("Pilih sekurang-kurangnya 1 guru")
                            else:
                                st.info(f"Menyimpan {len(guru_pilih)} guru...")
                                ok_count = 0
                                fail_msg = ""
                                for ic in guru_pilih:
                                    guru_row = df_guru[df_guru["IC"] == ic]
                                    if guru_row.empty: continue
                                    gr = guru_row.iloc[0]
                                    nama = gr.get("NAMA GURU", "") or ic
                                    jantina = gr.get("JANTINA", "")
                                    poskod = gr.get("POSKOD_RUMAH", "")
                                    alamat = gr.get("ALAMAT_RUMAH", "") or gr.get("ALAMAT", "")
                                    telefon = gr.get("TELEFON_GURU", "") or gr.get("TELEFON", "")
                                    email = str(gr.get("EMAIL_GURU", "") or gr.get("EMAIL", "") or "").strip()
                                    pengalaman = pengalaman_input or gr.get("PENGALAMAN_SPM", "") or gr.get("PENGALAMAN", "")
                                    kod_ppd_guru = (gr.get("KOD_PPD", "") or info.get("kod_ppd", "BA")).upper()
                                    kod_sek_guru = gr.get("KOD_SEKOLAH", "") or kod
                                    nama_sek_guru = gr.get("NAMA_SEKOLAH_ASAL", "") or gr.get("NAMA_SEKOLAH", "") or info.get("nama_sekolah", "")
                                    no_pusat_asal = no_pusat_asal_input or gr.get("NO_PUSAT_ASAL", "")
                                    pusat_pilih = "BA142"
                                    if no_pusat_asal and no_pusat_asal.strip() != "":
                                        pusat_pilih = no_pusat_asal.strip()
                                    if kod.upper() == "BFT0003":
                                        pusat_pilih = "BA142"

                                    kod_ppd_guru = kod_ppd_guru.upper()
                                    kod_sek_guru = kod_sek_guru.upper()
                                    if not no_pusat_asal or no_pusat_asal.strip() == "":
                                        no_pusat_asal = "BA142"
                                    if not kod_sek_guru or kod_sek_guru.strip() == "":
                                        kod_sek_guru = kod.upper()
                                    if not nama_sek_guru or nama_sek_guru.strip() == "":
                                        nama_sek_guru = info.get("nama_sekolah", "SAM NURUL IMAN")

                                    email = email or ""
                                    clean_insert = {"kod_ppd": kod_ppd_guru.upper(), "kod_sekolah": kod_sek_guru, "kod_sekolah_asal": kod_sek_guru, "nama_sekolah_asal": nama_sek_guru, "ic_guru": ic, "nama_guru": nama, "jantina": jantina or "L", "poskod_rumah": poskod or "0", "alamat_rumah": alamat or "-", "telefon_guru": telefon, "email_guru": email, "jawatan_cadangan": jawatan_clean, "pengalaman_spm": pengalaman, "no_pusat_asal": no_pusat_asal or "BA142", "kod_pusat": None, "kod_ppd_asal": kod_ppd_guru.upper(), "status": "DICADANGKAN", "tarikh_cadang": str(datetime.date.today()), "data": {"KOD_PPD": kod_ppd_guru.upper(), "KOD_SEKOLAH_ASAL": kod_sek_guru.upper(), "NAMA_SEKOLAH_ASAL": nama_sek_guru, "IC_GURU": ic, "NAMA_GURU": nama, "JANTINA": jantina, "POSKOD_RUMAH": poskod, "ALAMAT_RUMAH": alamat, "TELEFON_GURU": telefon, "EMAIL_GURU": email, "JAWATAN_CADANGAN": jawatan_clean, "PENGALAMAN_SPM": pengalaman, "NO_PUSAT_ASAL": no_pusat_asal or pusat_pilih, "status": "DICADANGKAN"}}

                                    minimal_insert = {"kod_ppd": kod_ppd_guru.upper(), "kod_sekolah": kod_sek_guru.upper(), "ic_guru": ic, "nama_guru": nama, "status": "DICADANGKAN"}

                                    inserted = False
                                    for attempt in [clean_insert, clean_insert, {"kod_ppd": kod_ppd_guru.upper(), "kod_sekolah": kod_sek_guru.upper(), "ic_guru": ic, "nama_guru": nama, "kod_pusat": no_pusat_asal, "jawatan_cadangan": jawatan_clean, "status": "DICADANGKAN", "tarikh_cadang": str(datetime.date.today()), "jantina": jantina or "L", "poskod_rumah": poskod or "0", "alamat_rumah": alamat or "-", "telefon_guru": telefon or "-", "email_guru": email or "", "pengalaman_spm": pengalaman or "0", "no_pusat_asal": no_pusat_asal, "kod_ppd_asal": kod_ppd_guru.upper(), "kod_sekolah_asal": kod_sek_guru.upper(), "nama_sekolah_asal": nama_sek_guru}, minimal_insert]:
                                        try:
                                            supa.table("cadangan_sup").insert(attempt).execute()
                                            inserted = True
                                            ok_count += 1
                                            break
                                        except Exception as e:
                                            fail_msg = str(e)
                                            if "duplicate" in fail_msg.lower() or "already exists" in fail_msg.lower():
                                                try:
                                                    supa.table("cadangan_sup").update(attempt).eq("ic_guru", ic).eq("kod_sekolah", kod_sek_guru.upper()).execute()
                                                    inserted = True
                                                    ok_count += 1
                                                    break
                                                except: pass
                                            continue

                                    if not inserted:
                                        st.error(f"❌ Gagal {ic} - {nama}: {fail_msg[:500]}")

                                if ok_count > 0:
                                    st.success(f"✅ Berjaya cadang {ok_count}/{len(guru_pilih)} guru sebagai {jawatan_clean} ke pusat {pusat_pilih} - SEMUA maklumat lengkap!")
                                    st.balloons()
                                    st.rerun()

                if fly_cur == "senarai":
                    st.markdown("---")
                    st.subheader(f"Senarai Cadangan Sekolah Ini - Perlu {total_need_simple if 'total_need_simple' in locals() else 18} orang")
                    st.markdown(LEGEND_HTML, unsafe_allow_html=True)
                    df_cad = get_cadangan_df(kod_sekolah=kod)
                    if df_cad.empty:
                        st.info("Belum ada cadangan")
                    else:
                        try:
                            counts = df_cad["JAWATAN_CADANGAN"].value_counts() if "JAWATAN_CADANGAN" in df_cad.columns else (df_cad["jawatan_cadangan"].value_counts() if "jawatan_cadangan" in df_cad.columns else pd.Series())
                            if not adalah_spm():
                                metrik_cadangan_ub(df_cad, kuota_ub if 'kuota_ub' in locals() else {})
                            else:
                                c1, c2, c3, c4 = st.columns(4)
                                c1.metric("Ketua Pengawas", counts.get("Ketua Pengawas", 0), delta="WAJIB 1" if counts.get("Ketua Pengawas", 0) >= 1 else "BELUM CUKUP", delta_color="normal" if counts.get("Ketua Pengawas", 0) >= 1 else "inverse")
                                c2.metric("Timbalan Ketua", counts.get("Timbalan Ketua Pengawas", 0), delta="WAJIB 1" if counts.get("Timbalan Ketua Pengawas", 0) >= 1 else "BELUM CUKUP", delta_color="normal" if counts.get("Timbalan Ketua Pengawas", 0) >= 1 else "inverse")
                                c3.metric("Penyelia Kawasan", counts.get("Penyelia Kawasan", 0))
                                c4.metric("Pengawas Peperiksaan", counts.get("Pengawas Peperiksaan", 0), delta=f"Perlu {total_kelas_alert if 'total_kelas_alert' in locals() else 6}")
                        except: pass
                        # V24 FIX: Show clean without duplicate id columns
                        clean_cols = ["NAMA_GURU", "IC_GURU", "JANTINA", "POSKOD_RUMAH", "ALAMAT_RUMAH", "TELEFON_GURU", "EMAIL_GURU", "JAWATAN_CADANGAN", "STATUS", "NAMA_SEKOLAH_ASAL"]
                        # V29: find columns case-insensitive
                        cols_map = {str(c).lower(): c for c in df_cad.columns}
                        clean_show = []
                        for wanted in clean_cols:
                            if wanted in df_cad.columns:
                                clean_show.append(wanted)
                            elif wanted.lower() in cols_map:
                                clean_show.append(cols_map[wanted.lower()])
                        df_clean_show = df_cad[clean_show] if clean_show else df_cad
                        # Remove any duplicate columns by lowercase name
                        try:
                            df_clean_show = df_clean_show.loc[:, ~df_clean_show.columns.str.lower().duplicated()]
                        except:
                            pass
                        # === WARNA HIJAU UNTUK SUDAH HANTAR ===
                        try:
                            styled = style_nama_hijau_hantar(df_clean_show)
                            st.dataframe(styled, use_container_width=True)
                            st.caption("🟢 Hijau = Sudah hantar ke PPD (termasuk yang sudah diproses PPD)  |  🟡 Kuning = Belum hantar / dipulangkan PPD")
                            # Juga tunjuk legend count
                            hantar_cnt, baru_cnt = kira_hantar(df_clean_show)
                            c1, c2 = st.columns(2)
                            c1.success(f"🟢 Sudah Hantar: {hantar_cnt} guru")
                            c2.warning(f"🟡 Belum Hantar: {baru_cnt} guru")
                        except Exception as e:
                            st.dataframe(df_clean_show, use_container_width=True)
                            st.caption(f"Style error: {e}")
                        # === END WARNA ===
                        st.download_button("📥 Export Cadangan", to_excel(df_clean_show), file_name=f"cadangan_{kod}.xlsx")

        elif menu == "hantar":
            st.header(f"Hantar Cadangan ke PPD {info.get('kod_ppd', 'BA')}")
            df_cad = get_cadangan_df(kod_sekolah=kod)
            if df_cad.empty:
                st.warning("Belum ada cadangan. Pergi menu Cadangan Lantikan dulu.")
            else:
                kod_ppd_sup = str(info.get('kod_ppd', 'BA')).upper()
                # V23 FIX: check both STATUS and status columns
                if "STATUS" in df_cad.columns:
                    status_s = df_cad["STATUS"].astype(str)
                elif "status" in df_cad.columns:
                    status_s = df_cad["status"].astype(str)
                else:
                    status_s = pd.Series([""] * len(df_cad), index=df_cad.index)
                status_s = status_s.fillna("").astype(str).str.upper()
                # Also check alternative column if empty
                if "status" in df_cad.columns and (status_s == "").all():
                    status_s = df_cad["status"].fillna("").astype(str).str.upper()
                m_lulus = status_s.str.contains("LULUS", na=False)
                _sent = status_s.apply(sudah_hantar)
                m_hantar = _sent & ~m_lulus                 # sudah hantar (HANTAR / TERPILIH / SIMPANAN / DILANTIK / SURAT ...)
                m_baru = ~_sent                             # DICADANGKAN / TOLAK PPD / kosong - belum hantar, boleh dihantar
                bil_baru = int(m_baru.sum())

                # V24 FIX: Clean duplicate columns - only show unique, readable columns
                # Remove duplicate lowercase columns if uppercase exists
                cols_to_show = ["NAMA_GURU", "IC_GURU", "JANTINA", "POSKOD_RUMAH", "ALAMAT_RUMAH", "TELEFON_GURU", "EMAIL_GURU", "JAWATAN_CADANGAN", "PENGALAMAN_SPM", "NO_PUSAT_ASAL", "KOD_SEKOLAH_ASAL", "NAMA_SEKOLAH_ASAL", "STATUS"]
                display_cols = [c for c in cols_to_show if c in df_cad.columns]
                # Deduplicate columns list itself
                seen = set()
                uniq_display = []
                for c in display_cols:
                    if c.lower() not in seen:
                        uniq_display.append(c)
                        seen.add(c.lower())
                # Also ensure df_cad doesn't have duplicate columns (lower + upper)
                # Keep only upper case versions for display
                df_display = df_cad[uniq_display].copy() if uniq_display else df_cad
                # === WARNA HIJAU UNTUK SUDAH HANTAR DI MENU HANTAR ===
                try:
                    styled_hantar = style_nama_hijau_hantar(df_display)
                    st.dataframe(styled_hantar, use_container_width=True)
                    st.markdown(LEGEND_HTML, unsafe_allow_html=True)
                except:
                    st.dataframe(df_display, use_container_width=True)
                # === END WARNA ===

                k1, k2, k3 = st.columns(3)
                with k1: st.metric("Belum dihantar", bil_baru)
                with k2: st.metric("Sudah dihantar", int(m_hantar.sum()))
                with k3: st.metric("Lulus PPD", int(m_lulus.sum()))

                sasaran = df_cad[m_baru]
                def _kosong(col):
                    if col not in sasaran.columns: return pd.Series(False, index=sasaran.index)
                    return sasaran[col].astype(str).str.strip().isin(["", "KOSONG", "nan", "None"])

                tak_lengkap = sasaran[_kosong("POSKOD_RUMAH") | _kosong("ALAMAT_RUMAH") | _kosong("TELEFON_GURU")]
                if bil_baru and not tak_lengkap.empty:
                    st.warning(f"⚠️ {len(tak_lengkap)} cadangan belum lengkap (POSKOD / ALAMAT / TELEFON kosong) - PPD tak boleh jana ikut terdekat. Sila lengkapkan di Senarai Guru > Edit. Contoh: " + ", ".join(tak_lengkap["NAMA_GURU"].astype(str).head(3)))
                elif bil_baru:
                    st.success(f"✅ {bil_baru} cadangan ada POSKOD, ALAMAT & TELEFON lengkap.")

                col_hantar, col_batal, col_reset = st.columns(3)
                with col_hantar:
                    if bil_baru == 0: st.info("Semua cadangan sudah dihantar / lulus.")
                    if st.button(f"📤 Hantar {bil_baru} Cadangan ke PPD", type="primary", use_container_width=True, disabled=bil_baru == 0, key="btn_hantar_ppd"):
                        ids = [_id_py(x) for x in sasaran["id"].tolist()] if "id" in sasaran.columns else []
                        if not ids:
                            st.error("Tiada ID cadangan - data tak lengkap, hubungi admin.")
                        else:
                            berjaya, gagal = hantar_ke_ppd(ids, kod_ppd_sup, df_sasaran=sasaran)
                            if berjaya:
                                flash("success", f"✅ Berjaya hantar {berjaya} cadangan ke PPD {kod_ppd_sup} - {PPD_MAP.get(kod_ppd_sup, '')}!")
                                # V25: Clear cache to force fresh data
                                try:
                                    st.cache_data.clear()
                                    st.cache_resource.clear()
                                except:
                                    pass
                                # Force small delay to let Supabase replicate
                                import time
                                time.sleep(1)
                            if gagal: flash("error", "Sebahagian gagal dihantar: " + "; ".join(gagal[:3]))
                            st.rerun()

                with col_batal:
                    st.markdown("**Batal Cadangan (Selagi PPD Belum Lantik)**")
                    label_batal = {}
                    if "id" in df_cad.columns:
                        for _, r_ in df_cad.iterrows():
                            label_batal[_id_py(r_["id"])] = f"{r_.get('NAMA_GURU', '')} | {r_.get('IC_GURU', '')} | {r_.get('STATUS', '')}"
                    batal_ids = st.multiselect("Pilih untuk batal", list(label_batal.keys()), format_func=lambda x: label_batal.get(x, str(x)))
                    if st.button("❌ Batal Terpilih", use_container_width=True, key="btn_batal_cad"):
                        if not batal_ids: st.warning("Pilih sekurang-kurangnya 1")
                        else:
                            berjaya_b = 0
                            for bid in batal_ids:
                                try:
                                    if "LULUS" in str(df_cad[df_cad["id"] == bid].iloc[0].get("STATUS", "")).upper():
                                        flash("error", f"Tak boleh batal {label_batal.get(bid, bid)} - sudah LULUS PPD!")
                                        continue
                                    supa.table("cadangan_sup").delete().eq("id", bid).execute()
                                    berjaya_b += 1
                                except Exception as e:
                                    flash("error", f"Gagal batal {label_batal.get(bid, bid)}: {e}")
                            if berjaya_b: flash("success", f"✅ Berjaya batal {berjaya_b} cadangan!")
                            st.rerun()

                with col_reset:
                    st.markdown("**Reset Semua (Clear & Isi Semula)**")
                    sah_reset = st.checkbox("Ya, padam semua cadangan (kecuali yang sudah LULUS)", key="sah_reset_cad")
                    if st.button("🔄 Reset Semua Cadangan", use_container_width=True, type="secondary", disabled=not sah_reset, key="btn_reset_cad"):
                        count_del = 0
                        for _, row in df_cad.iterrows():
                            if "LULUS" in str(row.get("STATUS", "")).upper(): continue
                            try:
                                supa.table("cadangan_sup").delete().eq("id", _id_py(row["id"])).execute()
                                count_del += 1
                            except Exception as e:
                                flash("error", f"Gagal padam {row.get('NAMA_GURU', '')}: {e}")
                        flash("success", f"✅ Reset {count_del} cadangan!")
                        st.rerun()

                st.markdown("---")
                st.caption("ℹ️ Cadangan yang sudah LULUS PPD tidak akan diubah atau dipadam oleh butang di atas.")

        elif menu == "petugas":
            st.markdown(f'<div style="background: linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;"><h2 style="margin:0; color:white;">👥 Petugas Yang Akan Hadir Bertugas Di Sekolah Saya - {kod}</h2><p style="margin:5px 0 0 0; color:#e3f2fd;">Pilih pusat yang ada di sekolah anda, lihat senarai petugas yang akan hadir bertugas</p></div>', unsafe_allow_html=True)

            # Get pusat di sekolah ini
            try:
                df_pusat_all = get_pusat_df()
                pusat_di_sekolah = []
                for _, r in df_pusat_all.iterrows():
                    d = r.get("data") if isinstance(r.get("data"), dict) else {}
                    if isinstance(d, str):
                        try: d = json.loads(d)
                        except: d = {}
                    ks_tuan = str(r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or r.get("KOD_SEKOLAH") or d.get("KOD_SEKOLAH") or "").upper().strip()
                    if ks_tuan == kod.upper().strip():
                        no_p = str(r.get("no_pusat") or r.get("kod_pusat") or r.get("NO_PUSAT") or d.get("NO_PUSAT") or "").upper().strip()
                        nama_p = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                        calon = r.get("jumlah_calon") or d.get("JUMLAH_CALON") or 0
                        try: calon_i = int(float(str(calon) or 0))
                        except: calon_i = 0
                        pusat_di_sekolah.append({"NO_PUSAT": no_p, "NAMA_PUSAT": nama_p, "CALON": calon_i})
            except Exception as e:
                st.error(f"Error load pusat: {e}")
                pusat_di_sekolah = []

            if not pusat_di_sekolah:
                st.warning(f"Tiada pusat dijumpai untuk sekolah {kod}. Hubungi PPD.")
            else:
                st.success(f"Sekolah anda {kod} - {info.get('nama_sekolah','')} ada {len(pusat_di_sekolah)} pusat:")
                for p in pusat_di_sekolah:
                    st.markdown(f"- **{p['NO_PUSAT']}** - {p['NAMA_PUSAT']} ({p['CALON']} calon)")

                st.markdown("---")
                st.markdown("### Pilih Pusat Untuk Lihat Petugas Hadir")
                pilih_pusat_sup = st.selectbox(
                    "Pilih Pusat Di Sekolah Anda",
                    [p["NO_PUSAT"] for p in pusat_di_sekolah],
                    format_func=lambda x: f"{x} - {next((p['NAMA_PUSAT'] for p in pusat_di_sekolah if p['NO_PUSAT']==x), '')[:40]}",
                    key="pilih_pusat_sup_petugas"
                )

                if pilih_pusat_sup:
                    # ===== FIX PETUGAS HADIR - HANYA LULUS PPD & BUKAN SEKOLAH SENDIRI =====
                    try:
                        res_cad = supa.table("cadangan_sup").select("*").eq("kod_pusat", pilih_pusat_sup).limit(5000).execute()
                        df_petugas_all = pd.DataFrame(res_cad.data or [])
                        if df_petugas_all.empty:
                            res_cad2 = supa.table("cadangan_sup").select("*").ilike("kod_pusat", f"%{pilih_pusat_sup}%").limit(5000).execute()
                            df_petugas_all = pd.DataFrame(res_cad2.data or [])
                    except Exception as e:
                        st.error(f"Error load petugas: {e}")
                        df_petugas_all = pd.DataFrame()

                    if df_petugas_all.empty:
                        st.warning(f"⏳ Belum ada petugas dilantik untuk pusat {pilih_pusat_sup} - PPD belum buat lantikan.")
                        st.info("Button ini hanya akan paparkan nama selepas PPD lantik dan jana surat. Cikgu dari sekolah sendiri tidak akan dipaparkan kerana tidak boleh bertugas di sekolah asal.")
                    else:
                        def get_status_val(row):
                            return str(row.get("status") or row.get("STATUS") or "").upper()
                        df_petugas_all["STATUS_NORM"] = df_petugas_all.apply(get_status_val, axis=1)
                        lulus_keywords = ["LULUS", "SURAT", "DILANTIK", "DITEMPATKAN", "DIJANA", "SAH", "LANTIK"]
                        mask_lulus = df_petugas_all["STATUS_NORM"].apply(lambda x: any(k in x for k in lulus_keywords))
                        def has_surat(row):
                            ns = str(row.get("no_surat") or row.get("NO_SURAT") or "").strip()
                            return ns != "" and ns.lower() not in ("none","null","nan","")
                        mask_surat = df_petugas_all.apply(has_surat, axis=1)
                        df_lulus_sahaja = df_petugas_all[mask_lulus | mask_surat].copy()

                        if df_lulus_sahaja.empty:
                            st.warning(f"⏳ Ada {len(df_petugas_all)} cadangan untuk pusat {pilih_pusat_sup} tapi belum diluluskan PPD.")
                            st.info(f"Status: {df_petugas_all['STATUS_NORM'].unique().tolist()[:5]} - Tunggu PPD buat lantikan.")
                        else:
                            def get_sekolah_asal(row):
                                return str(row.get("kod_sekolah_asal") or row.get("KOD_SEKOLAH_ASAL") or row.get("kod_sekolah") or "").upper().strip()
                            df_lulus_sahaja["SEKOLAH_ASAL_NORM"] = df_lulus_sahaja.apply(get_sekolah_asal, axis=1)
                            kod_semasa = kod.upper().strip()
                            df_final = df_lulus_sahaja[df_lulus_sahaja["SEKOLAH_ASAL_NORM"] != kod_semasa].copy()
                            excluded_count = len(df_lulus_sahaja) - len(df_final)
                            if excluded_count > 0:
                                st.info(f"ℹ️ {excluded_count} petugas dari sekolah sendiri ({kod_semasa}) disembunyikan kerana tidak boleh bertugas di sekolah asal.")

                            if df_final.empty:
                                st.warning(f"Tiada petugas luar untuk pusat {pilih_pusat_sup} - Semua yang lulus adalah dari sekolah sendiri.")
                            else:
                                st.success(f"✅ {len(df_final)} Petugas Luar Akan Hadir di {pilih_pusat_sup} (Sudah dilantik PPD)")
                                def get_jawatan(row):
                                    return str(row.get("jawatan_cadangan") or row.get("JAWATAN_CADANGAN") or "").strip()
                                df_final["JAWATAN_NORM"] = df_final.apply(get_jawatan, axis=1)
                                kp_list = df_final[df_final["JAWATAN_NORM"].str.contains("Ketua Pengawas", case=False, na=False) & ~df_final["JAWATAN_NORM"].str.contains("Timbalan", case=False, na=False)]
                                tkp_list = df_final[df_final["JAWATAN_NORM"].str.contains("Timbalan", case=False, na=False)]
                                peng_list = df_final[~df_final["JAWATAN_NORM"].str.contains("Ketua Pengawas|Timbalan", case=False, na=False, regex=True)]
                                col_kp, col_tkp, col_peng, col_jt, col_jb, col_pb = st.columns(6)
                                with col_kp: st.metric("Ketua Pengawas (Luar)", len(kp_list))
                                with col_tkp: st.metric("Timbalan KP (Luar)", len(tkp_list))
                                with col_peng: st.metric("Pengawas (Luar)", len(peng_list))
                                rows_petugas = []
                                for _, r in df_final.iterrows():
                                    rows_petugas.append({
                                        "NAMA GURU": r.get("nama_guru", "") or r.get("NAMA_GURU", ""),
                                        "IC": r.get("ic_guru", "") or r.get("IC_GURU", ""),
                                        "JAWATAN": r.get("jawatan_cadangan", "") or r.get("JAWATAN_CADANGAN", ""),
                                        "SEKOLAH ASAL": r.get("kod_sekolah_asal", "") or r.get("KOD_SEKOLAH_ASAL", ""),
                                        "NAMA SEKOLAH ASAL": str(r.get("nama_sekolah_asal", "") or r.get("NAMA_SEKOLAH_ASAL", ""))[:40],
                                        "NO SURAT": r.get("no_surat", "") or "",
                                        "STATUS": r.get("status", "") or ""
                                    })
                                df_display_petugas = pd.DataFrame(rows_petugas)
                                st.dataframe(df_display_petugas, use_container_width=True, hide_index=True)
                                st.download_button(f"📥 Export Petugas Luar {pilih_pusat_sup}", to_excel(df_display_petugas), file_name=f"petugas_LUAR_{pilih_pusat_sup}_{kod}.xlsx", use_container_width=True)
                    # ===== END FIX PETUGAS =====

        elif menu == "surat":
            st.markdown(f'<div style="background: linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;"><h2 style="margin:0; color:white;">📄 Surat Lantikan Saya - {kod} - {info.get("nama_sekolah","")}</h2><p style="margin:5px 0 0 0; color:#e3f2fd;">Surat lantikan petugas dari sekolah anda - Asing ikut jawatan untuk rujukan SUP</p></div>', unsafe_allow_html=True)

            df_cad_sup = get_cadangan_df(kod_sekolah=kod)
            if df_cad_sup.empty:
                st.warning("Belum ada cadangan. Sila buat cadangan di menu Cadangan Lantikan dahulu.")
            else:
                def get_status(row):
                    return str(row.get("STATUS") or row.get("status") or "").upper().strip()
                def get_jawatan(row):
                    return str(row.get("JAWATAN_CADANGAN") or row.get("jawatan_cadangan") or "").strip()
                def has_surat(row):
                    ns = str(row.get("no_surat") or row.get("NO_SURAT") or row.get("no_surat_lantikan") or "").strip()
                    return ns != "" and ns.lower() not in ("none", "null", "nan", "")

                df_cad_sup["STATUS_NORM"] = df_cad_sup.apply(lambda r: get_status(r), axis=1)
                df_cad_sup["JAWATAN_NORM"] = df_cad_sup.apply(lambda r: get_jawatan(r), axis=1)
                df_cad_sup["ADA_SURAT"] = df_cad_sup.apply(lambda r: has_surat(r), axis=1)

                total_cad = len(df_cad_sup)
                ada_surat_cnt = int(df_cad_sup["ADA_SURAT"].sum())
                tunggu_cnt = total_cad - ada_surat_cnt

                if fly_cur == "jadual":
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("Total Cadangan Sekolah", total_cad)
                    c2.metric("✅ Sudah Ada Surat", ada_surat_cnt)
                    c3.metric("⏳ Tunggu Surat", tunggu_cnt)
                    with c4:
                        if ada_surat_cnt > 0:
                            if st.button(f"📦 Jana ZIP {ada_surat_cnt} Surat PDF Individu", type="primary", use_container_width=True, key=f"btn_zip_sup_{kod}"):
                                try:
                                    df_lulus_zip = df_cad_sup[df_cad_sup["ADA_SURAT"] == True].copy()
                                    surat_list_sup = []
                                    for _, r in df_lulus_zip.iterrows():
                                        surat_list_sup.append({
                                            "nama": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                            "ic": r.get("IC_GURU","") or r.get("ic_guru",""),
                                            "jawatan": r.get("JAWATAN_CADANGAN","") or r.get("jawatan_cadangan",""),
                                            "sekolah_asal": r.get("KOD_SEKOLAH_ASAL","") or r.get("kod_sekolah_asal","") or kod,
                                            "nama_sekolah_asal": r.get("NAMA_SEKOLAH_ASAL","") or r.get("nama_sekolah_asal","") or info.get('nama_sekolah',''),
                                            "pusat": r.get("kod_pusat","") or r.get("KOD_PUSAT",""),
                                            "nama_pusat": "",
                                            "no_surat": r.get("no_surat","") or r.get("NO_SURAT","")
                                        })
                                    # FIX: guna build_pusat_map_from_master() ikut NO PUSAT column refer pusat_master
                                    try:
                                        pusat_map_tmp = build_pusat_map_from_master()
                                        for s in surat_list_sup:
                                            s["nama_pusat"] = pusat_map_tmp.get(str(s["pusat"]).upper().strip(), "")
                                            # Jika masih kosong, cuba cari tanpa strip
                                            if not s["nama_pusat"]:
                                                s["nama_pusat"] = pusat_map_tmp.get(str(s["pusat"]).strip(), "")
                                    except:
                                        pass
                                    zip_bytes = create_zip_of_individual_pdfs(surat_list_sup, info.get('kod_ppd',''), PPD_MAP.get(info.get('kod_ppd',''), ''))
                                    if zip_bytes:
                                        st.session_state[f"zip_sup_{kod}"] = zip_bytes
                                        st.success(f"✅ ZIP {len(surat_list_sup)} surat individu berjaya dijana!")
                                    else:
                                        st.error("Gagal jana ZIP")
                                except Exception as e:
                                    st.error(f"Error jana ZIP: {e}")
                            if f"zip_sup_{kod}" in st.session_state:
                                st.download_button(f"📥 Download ZIP {ada_surat_cnt} Surat Individu (SUP {kod})", data=st.session_state[f"zip_sup_{kod}"], file_name=f"Surat_Individu_SUP_{kod}_{__import__('datetime').date.today()}.zip", mime="application/zip", use_container_width=True, key=f"dl_zip_sup_{kod}")

                    def papar_table_jawatan(df_input, tajuk, icon, keyword_list, warna_header):
                        if keyword_list:
                            mask = df_input["JAWATAN_NORM"].str.upper().apply(lambda x: any(k.upper() in x.upper() for k in keyword_list))
                            df_j = df_input[mask].copy()
                        else:
                            df_j = df_input.copy()
                        if df_j.empty:
                            return
                        st.markdown(f"""
                    <div style="background:{warna_header}; padding:12px 16px; border-radius:8px; margin:20px 0 10px 0; border-left:6px solid #0d47a1;">
                        <h3 style="margin:0; color:white;">{icon} {tajuk} - {len(df_j)} orang</h3>
                    </div>
                    """, unsafe_allow_html=True)
                        df_ada = df_j[df_j["ADA_SURAT"] == True].copy()
                        df_tunggu = df_j[df_j["ADA_SURAT"] == False].copy()
                        col_ada, col_tunggu = st.columns([1.2, 1])
                        with col_ada:
                            st.markdown(f"#### ✅ Ada Surat ({len(df_ada)})")
                            if df_ada.empty:
                                st.info(f"Belum ada surat untuk {tajuk}")
                            else:
                                # FIX: papar NAMA PUSAT ikut pusat_master
                                try:
                                    _pmap_disp = build_pusat_map_from_master()
                                except:
                                    _pmap_disp = {}
                                display_rows = []
                                for _, r in df_ada.iterrows():
                                    kod_pusat_raw = r.get("KOD_PUSAT") or r.get("kod_pusat") or r.get("PUSAT") or ""
                                    nama_pusat_disp = _pmap_disp.get(str(kod_pusat_raw).upper().strip(), "")
                                    display_rows.append({
                                        "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                        "IC": r.get("IC_GURU","") or r.get("ic_guru",""),
                                        "JAWATAN": r.get("JAWATAN_NORM",""),
                                        "PUSAT": kod_pusat_raw,
                                        "NAMA PUSAT": nama_pusat_disp,
                                        "NO SURAT": r.get("no_surat") or r.get("NO_SURAT") or "",
                                        "STATUS": r.get("STATUS_NORM",""),
                                    })
                                df_show = pd.DataFrame(display_rows)
                                st.dataframe(df_show, use_container_width=True, hide_index=True)
                                st.download_button(f"📥 Export {tajuk} - Ada Surat", to_excel(df_show), file_name=f"surat_{tajuk.replace(' ','_')}_ada_surat_{kod}.xlsx", key=f"exp_ada_{tajuk}_{kod}", use_container_width=True)
                        with col_tunggu:
                            st.markdown(f"#### ⏳ Tunggu Surat ({len(df_tunggu)})")
                            if df_tunggu.empty:
                                st.success(f"Semua {tajuk} sudah ada surat!")
                            else:
                                display_tunggu = []
                                for _, r in df_tunggu.iterrows():
                                    display_tunggu.append({
                                        "NAMA GURU": r.get("NAMA_GURU","") or r.get("nama_guru",""),
                                        "JAWATAN": r.get("JAWATAN_NORM",""),
                                        "STATUS": r.get("STATUS_NORM",""),
                                        "CATATAN": "Menunggu PPD jana surat" if "LULUS" in r.get("STATUS_NORM","") else "Belum hantar ke PPD" if "DICADANGKAN" in r.get("STATUS_NORM","") else r.get("STATUS_NORM","")
                                    })
                                df_tunggu_show = pd.DataFrame(display_tunggu)
                                st.dataframe(df_tunggu_show, use_container_width=True, hide_index=True)
                                st.download_button(f"📥 Export {tajuk} - Tunggu", to_excel(df_tunggu_show), file_name=f"surat_{tajuk.replace(' ','_')}_tunggu_{kod}.xlsx", key=f"exp_tunggu_{tajuk}_{kod}", use_container_width=True)
                        st.markdown("---")

                    if adalah_spm():
                        papar_table_jawatan(df_cad_sup, "TABLE 1: Penyelia Kawasan", "🔐", ["Penyelia Kawasan", "Penyelia"], "linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)")
                        papar_table_jawatan(df_cad_sup, "TABLE 2: Ketua Pengawas & Timbalan", "👑", ["Ketua Pengawas", "Timbalan Ketua"], "linear-gradient(135deg, #0d47a1 0%, #1976d2 100%)")
                        papar_table_jawatan(df_cad_sup, "TABLE 3: Pengawas Peperiksaan", "👨‍🏫", ["Pengawas Peperiksaan", "Pengawas"], "linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)")
                    else:
                        for _i, _j in enumerate(jawatan_pilihan()):
                            papar_table_jawatan(df_cad_sup, f"TABLE {_i + 1}: {_j}", "🔐" if _j == "Penyelia Kawasan" else "👨‍🏫", [_j], "linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)")

                if fly_cur == "individu":
                    st.markdown("## 📄 Paparan Surat Lantikan (Yang Ada Surat Sahaja) - Individu")
                    df_lulus = df_cad_sup[df_cad_sup["ADA_SURAT"] == True].copy()
                    if df_lulus.empty:
                        st.info("Belum ada surat lantikan.")
                    else:
                        st.success(f"Ada {len(df_lulus)} surat lantikan untuk sekolah {kod} - SUP boleh download ZIP individu atau PDF seorang-seorang di bawah")

                        # Search & Pagination untuk SUP juga (elak panjang kalau 1000)
                        col_s1, col_s2 = st.columns([2,1])
                        with col_s1:
                            search_sup = st.text_input("🔍 Cari Nama Guru / IC / Pusat di Surat Saya", placeholder="Taip nama atau pusat...", key=f"search_sup_surat_{kod}")
                        with col_s2:
                            per_page_sup = st.selectbox("Per Page", [10,20,50], index=1, key=f"per_page_sup_{kod}")

                        df_lulus_filtered = df_lulus.copy()
                        if search_sup:
                            s = search_sup.lower()
                            df_lulus_filtered = df_lulus_filtered[df_lulus_filtered.apply(lambda r: s in str(r.get("NAMA_GURU","") or r.get("nama_guru","")).lower() or s in str(r.get("IC_GURU","") or r.get("ic_guru","")).lower() or s in str(r.get("kod_pusat","") or r.get("KOD_PUSAT","")).lower(), axis=1)]

                        total_pages_sup = max(1, (len(df_lulus_filtered) + per_page_sup -1)//per_page_sup)
                        page_sup = st.number_input(f"Halaman SUP 1-{total_pages_sup}", min_value=1, max_value=total_pages_sup, value=1, step=1, key=f"page_sup_{kod}")
                        start_sup = (page_sup-1)*per_page_sup
                        end_sup = start_sup + per_page_sup
                        df_lulus_page = df_lulus_filtered.iloc[start_sup:end_sup]

                        # Quick select dropdown
                        if not df_lulus_filtered.empty:
                            options_sup = [f"{i+1}. {r.get('NAMA_GURU','') or r.get('nama_guru','')} | {r.get('IC_GURU','') or r.get('ic_guru','')} | {r.get('kod_pusat','') or r.get('KOD_PUSAT','')} | {r.get('no_surat','')}" for i, (_, r) in enumerate(df_lulus_filtered.iterrows())]
                            pilih_sup_idx = st.selectbox("⚡ Pilih Guru untuk Download Cepat", range(len(options_sup)), format_func=lambda x: options_sup[x], key=f"select_sup_surat_{kod}")
                            if st.button("📥 Jana PDF Guru Terpilih (SUP)", type="primary", key=f"btn_sup_selected_{kod}"):
                                try:
                                    r_sel = df_lulus_filtered.iloc[pilih_sup_idx]
                                    nama = r_sel.get("NAMA_GURU", "") or r_sel.get("nama_guru", "")
                                    ic = r_sel.get("IC_GURU", "") or r_sel.get("ic_guru", "")
                                    jawatan = r_sel.get("JAWATAN_CADANGAN", "") or r_sel.get("jawatan_cadangan", "") or ""
                                    pusat = r_sel.get("kod_pusat", "") or r_sel.get("KOD_PUSAT", "") or ""
                                    no_surat = r_sel.get("no_surat", "") or ""
                                    telefon = r_sel.get("TELEFON_GURU", "") or r_sel.get("telefon_guru", "") or ""
                                    try:
                                        pdf_sel = generate_surat_pdf_bytes(nama, ic, jawatan, r_sel.get("KOD_SEKOLAH_ASAL", "") or kod, r_sel.get("NAMA_SEKOLAH_ASAL", "") or info.get('nama_sekolah',''), pusat, "", no_surat, r_sel.get("KOD_PPD", "") or info.get('kod_ppd',''), PPD_MAP.get(r_sel.get("KOD_PPD", "") or info.get('kod_ppd',''), ""), __import__("datetime").date.today().strftime('%d %B %Y'), no_surat)
                                        if pdf_sel:
                                            st.download_button(f"📥 Download PDF {nama}", data=pdf_sel, file_name=f"Surat_{nama.replace(' ','_')}_{no_surat.replace('/','_')}.pdf", mime="application/pdf", key=f"dl_sup_selected_{kod}_{pilih_sup_idx}", use_container_width=True)
                                    except Exception as e:
                                        st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")
                                except Exception as e:
                                    st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")

                        st.markdown(f"**Papar {len(df_lulus_page)} surat (Halaman {page_sup}/{total_pages_sup}) - Total {len(df_lulus_filtered)} surat:**")

                        for _, r in df_lulus_page.iterrows():
                            nama = r.get("NAMA_GURU", "") or r.get("nama_guru", "")
                            ic = r.get("IC_GURU", "") or r.get("ic_guru", "")
                            jawatan = r.get("JAWATAN_CADANGAN", "") or r.get("jawatan_cadangan", "") or ""
                            pusat = r.get("kod_pusat", "") or r.get("KOD_PUSAT", "") or ""
                            no_surat = r.get("no_surat", "") or ""
                            telefon = r.get("TELEFON_GURU", "") or r.get("telefon_guru", "") or r.get("NO_TELEFON", "") or ""

                            # Detect if this is Penyelia Kawasan placed in Bilik Kebal
                            is_penyelia_bk = "PENYELIA" in jawatan.upper() and ("BK-" in pusat.upper() or "CB" in pusat.upper() or "BILIK" in pusat.upper() or str(r.get("status","")).upper() in ["DITEMPATKAN BILIK KEBAL", "SURAT PK DIHANTAR", "SURAT PK DIHANTAR KE SEKOLAH"])
                            # Also check data json for bilik kebal
                            data_json = r.get("data") if isinstance(r.get("data"), dict) else {}
                            if isinstance(data_json, str):
                                try:
                                    data_json = json.loads(data_json)
                                except:
                                    data_json = {}
                            if data_json and ("kod_bilik_kebal" in str(data_json).lower() or "pusat_jagaan" in str(data_json).lower()):
                                is_penyelia_bk = True

                            label_bk = "🔐 Penyelia Kawasan - Bilik Kebal" if is_penyelia_bk else f"{jawatan}"

                            with st.expander(f"{nama} - {label_bk} - {pusat} - {no_surat}"):
                                try:
                                    pusat_nama = ""
                                    alamat_bk = ""
                                    nama_bk = pusat
                                    # Try get bilik kebal details
                                    if is_penyelia_bk:
                                        try:
                                            res_bk = supa.table("bilik_kebal_master").select("*").eq("kod_bilik_kebal", pusat.upper()).limit(1).execute()
                                            if res_bk.data:
                                                nama_bk = res_bk.data[0].get("nama_bilik_kebal", pusat)
                                                alamat_bk = res_bk.data[0].get("alamat", "")
                                                pusat_nama = nama_bk
                                        except:
                                            pass
                                    else:
                                        try:
                                            df_pusat = get_pusat_df()
                                            for _, pr in df_pusat.iterrows():
                                                d = pr.get("data") if isinstance(pr.get("data"), dict) else {}
                                                if isinstance(d, str):
                                                    try: d = json.loads(d)
                                                    except: d = {}
                                                no_p = str(pr.get("no_pusat") or d.get("NO_PUSAT") or "").upper().strip()
                                                if no_p == pusat.upper():
                                                    pusat_nama = pr.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                                                    break
                                        except:
                                            pusat_nama = ""

                                    # Get pusat jagaan for penyelia
                                    pusat_jagaan_list = []
                                    if is_penyelia_bk:
                                        if isinstance(data_json, dict):
                                            pj = data_json.get("pusat_jagaan") or data_json.get("pusat_jagaan_str") or []
                                            if isinstance(pj, str):
                                                pusat_jagaan_list = [p.strip() for p in pj.split(",") if p.strip()]
                                            elif isinstance(pj, list):
                                                pusat_jagaan_list = pj
                                        if not pusat_jagaan_list:
                                            pusat_jagaan_list = [pusat]

                                        html_surat = generate_surat_penyelia_kawasan_html(
                                            nama=nama,
                                            ic=ic,
                                            sek_asal=r.get("KOD_SEKOLAH_ASAL", "") or r.get("kod_sekolah_asal", "") or kod,
                                            nama_sek_asal=r.get("NAMA_SEKOLAH_ASAL", "") or r.get("nama_sekolah_asal", "") or info.get('nama_sekolah',''),
                                            telefon=telefon,
                                            kod_bilik_kebal=pusat,
                                            nama_bilik_kebal=nama_bk,
                                            alamat_bilik_kebal=alamat_bk,
                                            pusat_jagaan_list=pusat_jagaan_list,
                                            no_surat=no_surat,
                                            kod_ppd=r.get("KOD_PPD", "") or r.get("kod_ppd", "") or info.get('kod_ppd',''),
                                            ppd_name=PPD_MAP.get(r.get("KOD_PPD", "") or r.get("kod_ppd", "") or info.get('kod_ppd',''), ""),
                                            tarikh=datetime.date.today().strftime('%d %B %Y')
                                        )
                                    else:
                                        html_surat = generate_surat_html(
                                            nama, ic, jawatan,
                                            r.get("KOD_SEKOLAH_ASAL", "") or kod,
                                            r.get("NAMA_SEKOLAH_ASAL", "") or info.get('nama_sekolah',''),
                                            pusat, pusat_nama, no_surat,
                                            r.get("KOD_PPD", "") or info.get('kod_ppd',''),
                                            PPD_MAP.get(r.get("KOD_PPD", "") or info.get('kod_ppd',''), ""),
                                            datetime.date.today().strftime('%d %B %Y')
                                        )

                                    st.components.v1.html(html_surat, height=600, scrolling=True)
                                    try:
                                        pdf_single = generate_surat_pdf_bytes(nama, ic, jawatan, r.get("KOD_SEKOLAH_ASAL", "") or kod, r.get("NAMA_SEKOLAH_ASAL", "") or info.get('nama_sekolah',''), pusat, pusat_nama or nama_bk, no_surat, r.get("KOD_PPD", "") or info.get('kod_ppd',''), PPD_MAP.get(r.get("KOD_PPD", "") or info.get('kod_ppd',''), ""), datetime.date.today().strftime('%d %B %Y'), no_surat)
                                        if pdf_single:
                                            st.download_button(f"📥 Download Surat {nama} - {label_bk} (PDF)", data=pdf_single, file_name=f"Surat_{label_bk.replace(' ', '_')}_{nama.replace(' ', '_')}_{no_surat.replace('/', '_')}.pdf", mime="application/pdf", use_container_width=True, key=f"dl_pdf_{r.get('id','')}")
                                    except:
                                        pass
                                    st.download_button(f"📥 Download Surat {nama} - {label_bk}", data=html_surat.encode('utf-8'), file_name=f"Surat_{label_bk.replace(' ', '_')}_{nama.replace(' ', '_')}_{no_surat.replace('/', '_')}.html", mime="text/html", use_container_width=True, key=f"dl_{r.get('id','')}")

                                    # Show extra info for penyelia kawasan
                                    if is_penyelia_bk and pusat_jagaan_list:
                                        st.info(f"🔐 Penyelia Kawasan ini ditempatkan di Bilik Kebal {pusat} ({nama_bk}) dan bertanggungjawab atas {len(pusat_jagaan_list)} pusat: {', '.join(pusat_jagaan_list)}")

                                except Exception as e:
                                    st.error(f"Error generate surat: {e}")



# ================= ROLE: PPD =================
