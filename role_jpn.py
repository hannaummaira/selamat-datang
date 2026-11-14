# -*- coding: utf-8 -*-
"""Peranan JPN - pentadbir negeri (semua daerah)."""
import spm_core as _core
import ui_theme as _ui
globals().update({k: v for k, v in vars(_core).items() if not k.startswith("__")})
globals().update({k: v for k, v in vars(_ui).items() if not k.startswith("__")})
from surat_tools import surat_panel, surat_aset_panel, surat_diagnostik
from ppd_program import render_tetapan_program
from guru_import import render_templat_guru, semak_fail_guru
from auth_db import render_urus_kata_laluan

def render_jpn():
    MENU_JPN = [('dashboard', '📊 Dashboard JPN'), ('jpn_template_surat', '📄 Template Surat JPN (11 Jawatan)'), ('sekolah', '🏫 Semua Sekolah'), ('pusat', '🏫 Pusat Master'),
                    ('guru', '👨\u200d🏫 Guru Master'), ('cadangan', '📋 Semua Cadangan'), ('export', '📥 Export Negeri'),
                    ('kata_laluan', '🔑 Kata Laluan'), ('tetapan_program', '⚙️ Tetapan Program'), ('admin', '⚙️ Admin'), ('keluar', '🚪 Log Keluar')]
    shell_header_jpn()
    menu, fly_cur, col_main = shell_layout("jpn_menu_sel", MENU_JPN, FLY_JPN, None, "fly_jpn")

    with col_main:
        if menu == "keluar":
            st.session_state.clear()
            st.rerun()

        elif menu == "dashboard":
            st.header("Dashboard JPN Selangor - Pelantikan SPM 2026")
            if fly_cur == "ringkasan":
                cols = st.columns(5)
                for idx, t in enumerate(["sekolah_master", "pusat_master", "guru_master", "cadangan_sup"]):
                    try:
                        res = supa.table(t).select("*", count="exact").limit(1).execute()
                        cols[idx].metric(t, res.count)
                    except Exception as e:
                        cols[idx].error(f"{t}: {e}")

            if fly_cur == "ppd":
                st.markdown("---")
                st.subheader("Breakdown Ikut PPD")
                rows = []
                for ppd in KOD_DAERAH:
                    try:
                        c1 = supa.table("sekolah_master").select("kod_sekolah", count="exact").eq("kod_ppd", ppd).execute()
                        c2 = supa.table("guru_master").select("id", count="exact").eq("kod_ppd", ppd.lower()).execute()
                        c3 = supa.table("cadangan_sup").select("id", count="exact").eq("kod_ppd", ppd).execute()
                        rows.append({"PPD": f"{ppd} - {PPD_MAP[ppd]}", "Sekolah": c1.count, "Guru": c2.count, "Cadangan": c3.count})
                    except:
                        rows.append({"PPD": ppd, "Sekolah": 0, "Guru": 0, "Cadangan": 0})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        elif menu == "tetapan_program":
            render_tetapan_program()

        elif menu == "kata_laluan":
            render_urus_kata_laluan()

        elif menu == "jpn_template_surat":
            surat_aset_panel()
            surat_diagnostik("JPN")
            st.header("📄 Template Surat JPN - 11 Jawatan (LAJU)")
            st.caption("JPN selaraskan - PPD auto guna template ini")

            try:
                JAWATAN_11 = ["KETUA PENGAWAS","TIMBALAN KETUA PENGAWAS","PENGAWAS PEPERIKSAAN","JURU TULIS","JURU BACA","KETUA PENGAWAS HOSPITAL","PENGAWAS HOSPITAL","PENGAWAS PENGIRING","PENGEMAS BILIK","PENYELIA KAWASAN","SELENGGARA BILIK KEBAL"]
                DEFAULT_11 = {
                    "KETUA PENGAWAS": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN KETUA PENGAWAS</b><br><br>2. Dilantik sebagai <b>Ketua Pengawas</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 375.00 + 0.25C + 2S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "TIMBALAN KETUA PENGAWAS": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN TIMBALAN KETUA PENGAWAS</b><br><br>2. Dilantik sebagai <b>Timbalan Ketua Pengawas</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 375.00<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "PENGAWAS PEPERIKSAAN": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN PENGAWAS PEPERIKSAAN</b><br><br>2. Dilantik sebagai <b>Pengawas Peperiksaan</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 281.25 + S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "PENYELIA KAWASAN": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN PENYELIA KAWASAN</b><br><br>2. Dilantik sebagai <b>Penyelia Kawasan</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 437.50 + 10P + 2S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "KETUA PENGAWAS HOSPITAL": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN KETUA PENGAWAS HOSPITAL</b><br><br>2. Dilantik sebagai <b>Ketua Pengawas Hospital</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 375.00 + 0.25C + 2S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "PENGAWAS HOSPITAL": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN PENGAWAS HOSPITAL</b><br><br>2. Dilantik sebagai <b>Pengawas Hospital</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 281.25 + S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "JURU TULIS": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN JURU TULIS</b><br><br>2. Dilantik sebagai <b>Juru Tulis</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 281.25 + S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "JURU BACA": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN JURU BACA</b><br><br>2. Dilantik sebagai <b>Juru Baca</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 281.25 + S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "PENGAWAS PENGIRING": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN PENGAWAS PENGIRING</b><br><br>2. Dilantik sebagai <b>Pengawas Pengiring</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 281.25 + S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "PENGEMAS BILIK": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN PENGEMAS BILIK</b><br><br>2. Dilantik sebagai <b>Pengemas Bilik</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 281.25 + S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                    "SELENGGARA BILIK KEBAL": "<div style='font-family:Arial; padding:25px; border:1px solid #000;'><table style='width:100%; border:none;'><tr><td style='width:80px; vertical-align:top; border:none;'><img src='https://upload.wikimedia.org/wikipedia/commons/2/2a/Coat_of_arms_of_Malaysia.svg' style='width:70px;'></td><td style='vertical-align:top; border:none; text-align:left;'><b>KEMENTERIAN PENDIDIKAN MALAYSIA</b><br>JABATAN PENDIDIKAN NEGERI SELANGOR<br><small>Persiaran Tengku Ampuan Rahimah, Seksyen 20, 40300 Shah Alam, Selangor</small></td></tr></table><hr style='border:2px solid #000; margin:10px 0;'><div style='text-align:right; font-size:10pt;'>Ruj. Kami: {{NO_SURAT}}<br>Tarikh: {{TARIKH}}</div><div style='font-size:10pt; margin-top:12px;'><b>{{NAMA}}</b><br>Melalui:<br>PENGETUA<br><b>{{NAMA_SEKOLAH_ASAL}}</b><br>{{PPD}}<br><br>Tuan,<br><b>SPM 2026 : PELANTIKAN SELENGGARA BILIK KEBAL</b><br><br>2. Dilantik sebagai <b>Selenggara Bilik Kebal</b> di {{PUSAT}} - {{NAMA_PUSAT}}<br>Bilik Kebal: {{BILIK_KEBAL}}<br>Sekolah Asal: {{SEKOLAH_ASAL}} - {{NAMA_SEKOLAH_ASAL}}<br>No Surat: {{NO_SURAT}}<br><br>3. Elaun: RM 281.25 + S<br>4. Sulit - Akta Rahsia Rasmi 1972<br><br>MALAYSIA MADANI<br>BERKHIDMAT UNTUK NEGARA<br><br>(DATIN WAN NOR ASHIKIN)<br>Pengarah JPN Selangor</div></div>",
                }
                templates = get_jpn_templates_one()
                pilih = st.selectbox("Pilih Jawatan", JAWATAN_11, key="pilih_11_fix")
                curr = templates.get(pilih.upper()) or DEFAULT_11.get(pilih, "<div>Template {{NAMA}} - {{PUSAT}} - {{NO_SURAT}}</div>")
                edited = st.text_area(f"Template {pilih}", value=curr, height=280, key=f"edit_{pilih}_fix")
                c1,c2 = st.columns(2)
                with c1:
                    if st.button(f"💾 Simpan {pilih}", type="primary", use_container_width=True, key=f"save_{pilih}_fix"):
                        try:
                            ex = supa.table("surat_templates_jpn").select("id").eq("jawatan", pilih).execute()
                            if ex.data:
                                supa.table("surat_templates_jpn").update({"template_html": edited}).eq("jawatan", pilih).execute()
                            else:
                                supa.table("surat_templates_jpn").insert({"jawatan": pilih, "template_html": edited}).execute()
                            st.cache_data.clear()
                            st.success(f"✅ {pilih} disimpan - PPD akan guna JPN")
                        except Exception as e:
                            st.error(str(e))
                            st.code("CREATE TABLE IF NOT EXISTS surat_templates_jpn (id SERIAL PRIMARY KEY, jawatan TEXT UNIQUE, template_html TEXT);")
                with c2:
                    if st.button("🔄 Clear Cache", use_container_width=True, key="clear_fix"):
                        st.cache_data.clear()
                        st.rerun()
                # ===== V37: Panduan placeholder, preview sebenar & ujian PDF =====
                st.caption("Placeholder boleh guna (huruf besar/kecil sama): {{NAMA}} {{IC}} {{JAWATAN}} {{SEKOLAH_ASAL}} {{NAMA_SEKOLAH_ASAL}} {{SEKOLAH_ASAL_PENUH}} {{PUSAT}} {{NAMA_PUSAT}} {{PUSAT_PENUH}} {{BILIK_KEBAL}} {{NO_SURAT}} {{PPD}} {{PPD_NAME}} {{TARIKH}}")
                if enjin_pdf_templat_ada():
                    st.success("✅ Enjin PDF templat aktif - butang PDF / ZIP / kolektif PPD akan ikut templat ini.")
                else:
                    st.warning("⚠️ Enjin PDF templat (xhtml2pdf) belum dipasang di server. Surat PDF masih guna susun atur lama. Minta pentadbir tambah `xhtml2pdf` dalam requirements.txt (sekali sahaja).")
                _sample = {"NAMA":"ALI BIN ABU","IC":"800101-01-1234","JAWATAN":pilih,"SEKOLAH_ASAL":"BAA0001","NAMA_SEKOLAH_ASAL":"SK CONTOH","PUSAT":"BA001","NAMA_PUSAT":"SMK CONTOH","NO_SURAT":"JPNS.SPP 600-7/17/5 Jld.2 (01)","PPD":"BA","PPD_NAME":"KLANG","TARIKH":datetime.date.today().strftime("%d %B %Y"),"BILIK_KEBAL":"BK01"}
                _prev_html = edited
                for _k, _v in _sample.items():
                    _prev_html = re.sub(r"\{\{\s*" + re.escape(_k) + r"\s*\}\}", lambda m, _v=_v: _v, _prev_html, flags=re.IGNORECASE)
                    _prev_html = re.sub(r"\[" + re.escape(_k) + r"\]", lambda m, _v=_v: _v, _prev_html, flags=re.IGNORECASE)
                if st.checkbox("Preview", key=f"prev_check_{pilih}"):
                    import streamlit.components.v1 as _cv1
                    _cv1.html(_bungkus_html_surat(_prev_html), height=700, scrolling=True)
                _pdf_uji = html_to_pdf_bytes(_prev_html) if enjin_pdf_templat_ada() else None
                if _pdf_uji:
                    st.download_button("⬇️ Uji PDF (data contoh)", data=_pdf_uji, file_name=f"uji_{pilih.replace(' ','_')}.pdf", mime="application/pdf", key=f"uji_pdf_{pilih}")
            except Exception as e:
                st.error("Maaf, template tidak dapat dipaparkan. Sila cuba lagi.")

        elif menu == "sekolah":
            st.header("Semua Sekolah Master (369 Sekolah)")
            if fly_cur == "senarai":
                try:
                    res = supa.table("sekolah_master").select("*", count="exact").limit(5000).execute()
                    df_count = res.count
                    res2 = supa.table("sekolah_master").select("*").limit(1000).execute()
                    df = pd.DataFrame(res2.data or [])
                    st.write(f"Total dalam Supabase: **{df_count}** sekolah")
                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 Export Sekolah Master", to_excel(df), file_name="sekolah_master.xlsx")
                    else:
                        st.warning("sekolah_master kosong - belum push dari pusat_2026.csv. Sila import di bawah.")
                except Exception as e:
                    st.error(f"sekolah_master error: {e}")

            if fly_cur == "import":
                st.markdown("---")
                st.subheader("📤 Import Sekolah Master dari Pusat & Guru")
                st.info("File sekolah digenerate dari pusat_2026.csv (506 pusat = 369 sekolah unik) + guru 60K. Upload SEKOLAH_MASTER_FINAL_2026.xlsx untuk push masuk sekolah_master.")
                up_sek = st.file_uploader("Upload Sekolah Master Excel (KOD SEKOLAH, NAMA SEKOLAH, KOD PPD)", type=["xlsx", "csv"], key="sekolah_up")
                if up_sek:
                    try:
                        if up_sek.name.endswith(".csv"):
                            try: df_up = pd.read_csv(up_sek)
                            except:
                                up_sek.seek(0)
                                df_up = pd.read_csv(up_sek, encoding='latin1')
                        else:
                            df_up = pd.read_excel(up_sek)
                        st.write(f"Preview {len(df_up)} sekolah:")
                        st.dataframe(df_up.head(30), use_container_width=True)
                        if st.button(f"🚀 Import {len(df_up)} Sekolah ke Supabase", type="primary", use_container_width=True):
                            bar = st.progress(0)
                            stat = st.empty()
                            ok = 0
                            try:
                                supa.table("sekolah_master").delete().gt("id", 0).execute()
                                st.write("Old sekolah_master cleared")
                            except: pass
                            BATCH = 200
                            for start in range(0, len(df_up), BATCH):
                                end = min(start + BATCH, len(df_up))
                                bdf = df_up.iloc[start:end]
                                batch = []
                                for _, row in bdf.iterrows():
                                    try:
                                        kod = str(row.get("KOD SEKOLAH", "") or row.get("kod_sekolah", "") or row.get("KOD_SEKOLAH", "")).strip().upper()
                                        if not kod: continue
                                        nama = str(row.get("NAMA SEKOLAH", "") or row.get("nama_sekolah", "") or row.get("NAMA_PUSAT", "")).strip().upper()
                                        kod_ppd = str(row.get("KOD PPD", "") or row.get("kod_ppd", "") or row.get("PPD_CODE", "") or "BH").strip().upper()
                                        batch.append({"kod_sekolah": kod, "nama_sekolah": nama, "kod_ppd": kod_ppd, "data": {k: (" " if pd.isna(v) else str(v)) for k, v in row.to_dict().items()}})
                                    except: continue
                                if batch:
                                    try:
                                        supa.table("sekolah_master").insert(batch).execute()
                                        ok += len(batch)
                                    except Exception as e:
                                        st.warning(f"Batch {start}-{end}: {e}")
                                bar.progress(end / len(df_up))
                                stat.write(f"Progress {end}/{len(df_up)} | OK {ok}")
                            st.success(f"✅ Selesai import {ok}/{len(df_up)} sekolah!")
                            st.balloons()
                            st.rerun()
                    except Exception as e:
                        st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")

            if fly_cur == "auto":
                st.markdown("---")
                st.subheader("Auto Generate Sekolah dari Pusat 506")
                if st.button("⚡ Generate Sekolah Master dari pusat_master yang sedia ada (506 pusat)", use_container_width=True):
                    try:
                        res = supa.table("pusat_master").select("*").limit(1000).execute()
                        df_p = pd.DataFrame(res.data or [])
                        if df_p.empty:
                            st.error("pusat_master kosong, import pusat dulu")
                        else:
                            sekolah_list = []
                            seen = set()
                            for _, r in df_p.iterrows():
                                d = r.get("data") or {}
                                kod_sek = d.get("KOD_SEKOLAH", "") or r.get("kod_sekolah", "") or ""
                                kod_sek = str(kod_sek).upper().strip()
                                if not kod_sek or kod_sek in seen: continue
                                seen.add(kod_sek)
                                sekolah_list.append({"kod_sekolah": kod_sek, "nama_sekolah": r.get("nama_pusat", "") or d.get("NAMA_PUSAT", ""), "kod_ppd": r.get("kod_ppd", "BH"), "data": {"KOD SEKOLAH": kod_sek, "NAMA SEKOLAH": r.get("nama_pusat", ""), "KOD PPD": r.get("kod_ppd", "BH")}})
                            if sekolah_list:
                                try: supa.table("sekolah_master").delete().gt("id", 0).execute()
                                except: pass
                                for i in range(0, len(sekolah_list), 200):
                                    supa.table("sekolah_master").insert(sekolah_list[i:i + 200]).execute()
                                st.success(f"✅ Generated {len(sekolah_list)} sekolah dari pusat_master!")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error generate: {e}")

        elif menu == "pusat":
            st.header("Pusat Master - Selangor 2026 (506 Pusat) - FIX Jumlah Calon")
            try:
                total = safe_count("pusat_master")
                res = supa.table("pusat_master").select("*").limit(1000).execute()
                raw_data = res.data or []
                df = pd.DataFrame(raw_data)
                st.write(f"Total Pusat Sedia Ada: **{total}** / 506 pusat")
                display_rows = []
                for r in raw_data:
                    d = r.get("data") or {}
                    if isinstance(d, str):
                        try: d = json.loads(d)
                        except: d = {}
                    no_pusat = r.get("no_pusat") or r.get("kod_pusat") or d.get("NO_PUSAT") or d.get("KOD PUSAT") or ""
                    nama = r.get("nama_pusat") or d.get("NAMA_PUSAT") or ""
                    kod_sek = r.get("kod_sekolah_tuan_rumah") or r.get("kod_sekolah") or d.get("KOD_SEKOLAH") or ""
                    ppd = r.get("ppd") or d.get("PPD") or ""
                    j_calon = r.get("jumlah_calon") or r.get("calon") or r.get("JUMLAH_CALON") or d.get("JUMLAH_CALON") or d.get("CALON") or 0
                    j_kelas = r.get("jumlah_kelas") or r.get("bilik") or d.get("JUMLAH_KELAS") or d.get("BILIK") or 0
                    petugas = d.get("PETUGAS_NEEDED") or r.get("petugas_needed") or 0
                    try: j_calon_int = int(float(str(j_calon).replace(",", "").strip() or 0))
                    except: j_calon_int = 0
                    try: j_kelas_int = int(float(str(j_kelas).strip() or 0))
                    except: j_kelas_int = 0
                    display_rows.append({"NO_PUSAT": no_pusat, "NAMA_PUSAT": nama, "KOD_SEKOLAH": kod_sek, "PPD": ppd, "JUMLAH_CALON": j_calon_int, "JUMLAH_KELAS": j_kelas_int, "PETUGAS": petugas, "_id": r.get("id"), "_raw": r})

                df_display = pd.DataFrame(display_rows)
                if fly_cur == "senarai":
                    if not df_display.empty:
                        st.subheader(f"Senarai Pusat dengan Jumlah Calon (dari CSV)")
                        st.dataframe(df_display[["NO_PUSAT", "NAMA_PUSAT", "KOD_SEKOLAH", "PPD", "JUMLAH_CALON", "JUMLAH_KELAS", "PETUGAS"]].head(500), use_container_width=True)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Calon", int(df_display["JUMLAH_CALON"].sum()))
                        c2.metric("Total Kelas", int(df_display["JUMLAH_KELAS"].sum()))
                        c3.metric("Ada Calon", len(df_display[df_display["JUMLAH_CALON"] > 0]))
                        if len(df_display[df_display["JUMLAH_CALON"] == 0]) > 100:
                            st.error(f"⚠️ {len(df_display[df_display['JUMLAH_CALON']==0])} pusat JUMLAH_CALON = 0 / kosong! Kena fix dari CSV.")
                        st.download_button("📥 Export Pusat dengan Calon", to_excel(pd.DataFrame(display_rows)), file_name="pusat_master_dengan_calon.xlsx")
                    else:
                        st.warning("pusat_master kosong")

                if fly_cur == "fix":
                    st.markdown("---")
                    st.subheader("🔧 FIX: Update Jumlah Calon yang Hilang")
                    st.info("Kalau JUMLAH_CALON 0/kosong, upload pusat_2026.csv untuk update balik 506 pusat dengan jumlah calon betul.")
                    up_fix = st.file_uploader("Upload pusat_2026.csv untuk FIX jumlah calon", type=["csv", "xlsx"], key="fix_calon")
                    if up_fix:
                        try:
                            if up_fix.name.endswith(".csv"):
                                try: df_fix = pd.read_csv(up_fix)
                                except:
                                    up_fix.seek(0)
                                    df_fix = pd.read_csv(up_fix, encoding='latin1')
                            else:
                                df_fix = pd.read_excel(up_fix)
                            st.write(f"File fix ada {len(df_fix)} baris")
                            st.dataframe(df_fix.head(10), use_container_width=True)
                            if st.button(f"🚀 FIX Update {len(df_fix)} Pusat dengan Jumlah Calon", type="primary", use_container_width=True):
                                bar = st.progress(0)
                                stat = st.empty()
                                ok = 0
                                fail = 0
                                for idx, row in df_fix.iterrows():
                                    try:
                                        no_pusat = str(row.get("NO_PUSAT", "") or row.get("KOD PUSAT", "")).upper().strip()
                                        if not no_pusat: continue
                                        j_calon = row.get("JUMLAH_CALON", "0")
                                        j_kelas = row.get("JUMLAH_KELAS", "0")
                                        update_data = {"jumlah_calon": int(float(str(j_calon).strip() or 0)), "jumlah_kelas": int(float(str(j_kelas).strip() or 0)), "calon": int(float(str(j_calon).strip() or 0)), "bilik": int(float(str(j_kelas).strip() or 0))}
                                        try:
                                            supa.table("pusat_master").update(update_data).eq("no_pusat", no_pusat).execute()
                                            ok += 1
                                        except:
                                            try:
                                                supa.table("pusat_master").update(update_data).eq("kod_pusat", no_pusat).execute()
                                                ok += 1
                                            except: fail += 1
                                    except: fail += 1
                                    if idx % 20 == 0:
                                        bar.progress((idx + 1) / len(df_fix))
                                        stat.write(f"Progress {idx+1}/{len(df_fix)} OK {ok} Fail {fail}")
                                bar.progress(1.0)
                                st.success(f"✅ FIX selesai! OK {ok} Fail {fail} | Refresh page untuk lihat jumlah calon masuk!")
                                st.balloons()
                        except Exception as e:
                            st.error(f"Error fix: {e}")
            except Exception as e:
                st.error(f"pusat_master error: {e}")
                st.code("""
-- SQL FIX: Tambah column jumlah_calon kalau belum ada - Run di Supabase SQL Editor:
ALTER TABLE pusat_master ADD COLUMN IF NOT EXISTS jumlah_calon INT DEFAULT 0;
ALTER TABLE pusat_master ADD COLUMN IF NOT EXISTS jumlah_kelas INT DEFAULT 0;
ALTER TABLE pusat_master ADD COLUMN IF NOT EXISTS calon INT DEFAULT 0;
ALTER TABLE pusat_master ADD COLUMN IF NOT EXISTS bilik INT DEFAULT 0;
ALTER TABLE pusat_master ADD COLUMN IF NOT EXISTS petugas_needed INT DEFAULT 0;
ALTER TABLE pusat_master ADD COLUMN IF NOT EXISTS kod_pusat TEXT;
ALTER TABLE pusat_master ADD COLUMN IF NOT EXISTS nama_pusat TEXT;
""", language="sql")

            st.markdown("---")
            col1, col2 = st.columns(2)
            if fly_cur == "tambah":
                st.subheader("➕ Tambah Pusat Manual - Auto Kira SPM")
                st.caption("Formula: 1 kelas=20 calon, CEIL(calon/20)=kelas, petugas=kelas+9, sekolah perlu calonkan=kelas+12 (petugas+KP+TKP+Penyelia)")
                with st.form("tambah_pusat"):
                    kod_pusat = st.text_input("KOD PUSAT * (cth: BA001)")
                    nama_pusat = st.text_input("NAMA PUSAT *")
                    kod_ppd_pusat = st.selectbox("KOD PPD", KOD_DAERAH, format_func=lambda x: f"{x}-{PPD_MAP[x]}")
                    alamat_pusat = st.text_area("ALAMAT PUSAT (KOD SEKOLAH)")
                    calon_input = st.number_input("JUMLAH CALON * (contoh 105)", min_value=1, value=100, step=1, help="1 kelas = 20 calon. Auto kira kelas & petugas")
                    kelas_preview = kira_kelas_dari_calon(calon_input)
                    petugas_preview = kira_petugas_dari_kelas(kelas_preview)
                    sekolah_need_preview = kira_sekolah_perlu_calonkan(kelas_preview)
                    st.info(f" Auto Kira: {calon_input} calon → {kelas_preview} kelas (20/kelas) → {petugas_preview} petugas (kelas+9) → Sekolah perlu calonkan {sekolah_need_preview} orang (petugas+KP+TKP+Penyelia)")
                    submit_pusat = st.form_submit_button("💾 Simpan Pusat (Auto Kira)", type="primary", use_container_width=True)
                    if submit_pusat:
                        if not kod_pusat or not nama_pusat:
                            st.error("Kod & Nama Pusat wajib!")
                        else:
                            try:
                                kelas_calc = kira_kelas_dari_calon(calon_input)
                                petugas_calc = kira_petugas_dari_kelas(kelas_calc)
                                sekolah_need = kira_sekolah_perlu_calonkan(kelas_calc)
                                supa.table("pusat_master").insert({"kod_pusat": kod_pusat.upper(), "nama_pusat": nama_pusat.upper(), "kod_ppd": kod_ppd_pusat, "ppd": PPD_MAP.get(kod_ppd_pusat, ""), "alamat": alamat_pusat, "bilik": kelas_calc, "calon": int(calon_input), "jumlah_calon": int(calon_input), "jumlah_kelas": kelas_calc, "petugas_needed": petugas_calc, "data": {"NO_PUSAT": kod_pusat.upper(), "NAMA_PUSAT": nama_pusat.upper(), "KOD PPD": kod_ppd_pusat, "KOD_SEKOLAH": alamat_pusat, "JUMLAH_CALON": str(calon_input), "JUMLAH_KELAS": str(kelas_calc), "PETUGAS_NEEDED": str(petugas_calc), "SEKOLAH_PERLU_CALON": str(sekolah_need), "FORMULA": f"{calon_input} calon /20 = {kelas_calc} kelas, {kelas_calc}+9={petugas_calc} petugas, +3 KP/TKP/Penyelia = {sekolah_need} sekolah perlu calon"}}).execute()
                                st.success(f"✅ Pusat {kod_pusat} berjaya tambah! {calon_input} calon = {kelas_calc} kelas, {petugas_calc} petugas, sekolah perlu {sekolah_need} orang")
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal: {e}")

            if fly_cur == "import":
                st.subheader("📤 Import Excel/CSV Pusat (Batch)")
                st.info("Support: pusat_2026.csv (NO_PUSAT format) & Excel KOD PUSAT format | 506 pusat")
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.download_button("📥 Template Pusat", to_excel(pd.DataFrame([{"KOD PUSAT": "BA001", "NAMA PUSAT": "SMK DATO HAMZAH", "KOD PPD": "BA", "ALAMAT PUSAT": "Jalan Dato Hamzah", "BILIK": 10, "CALON": 250}])), "TEMPLATE_PUSAT.xlsx")
                with col_t2:
                    st.download_button("📥 Sample pusat_2026.csv", open("/mnt/data/pusat_2026.csv", "rb").read() if __import__("os").path.exists("/mnt/data/pusat_2026.csv") else b"", "pusat_2026_sample.csv")

                up = st.file_uploader("Upload Excel/CSV Pusat (Excel atau CSV)", type=["xlsx", "csv"], key="pusat_up")
                if up:
                    try:
                        if up.name.endswith(".csv"):
                            try: df_up = pd.read_csv(up)
                            except:
                                up.seek(0)
                                df_up = pd.read_csv(up, encoding='latin1')
                        else:
                            df_up = pd.read_excel(up)
                        st.write(f"Preview {len(df_up)} pusat:")
                        st.dataframe(df_up.head(20), use_container_width=True)
                        if st.button(f"🚀 Import {len(df_up)} Pusat (Batch 200)", type="primary", use_container_width=True):
                            bar = st.progress(0)
                            stat = st.empty()
                            ok = 0
                            BATCH = 200
                            ppd_name_map = {"klang": "BA", "kuala langat": "BB", "kuala selangor": "BC", "hulu langat": "BD", "hulu selangor": "BE", "sabak bernam": "BF", "gombak": "BG", "petaling perdana": "BH", "sepang": "BJ", "petaling utama": "BK"}
                            for start in range(0, len(df_up), BATCH):
                                end = min(start + BATCH, len(df_up))
                                bdf = df_up.iloc[start:end]
                                batch = []
                                for _, row in bdf.iterrows():
                                    try:
                                        d = {}
                                        for k, v in row.to_dict().items():
                                            d[k] = " " if pd.isna(v) else str(v)
                                        kod_p = d.get("NO_PUSAT", "") or d.get("KOD PUSAT", "") or d.get("kod_pusat", "")
                                        kod_p = kod_p.upper().strip()
                                        if not kod_p: continue
                                        kod_ppd_val = d.get("KOD PPD", "") or d.get("KOD_PPD", "") or d.get("PPD_CODE", "")
                                        if not kod_ppd_val:
                                            ppd_raw = d.get("PPD", "").lower()
                                            for name, code in ppd_name_map.items():
                                                if name in ppd_raw:
                                                    kod_ppd_val = code
                                                    break
                                        if not kod_ppd_val: kod_ppd_val = "BH"
                                        kod_ppd_val = kod_ppd_val.upper().strip()
                                        nama_p = d.get("NAMA_PUSAT", "") or d.get("NAMA PUSAT", "") or kod_p
                                        bilik_val = d.get("JUMLAH_KELAS", "") or d.get("BILIK", "") or "10"
                                        calon_val = d.get("JUMLAH_CALON", "") or d.get("CALON", "") or "200"
                                        try: bilik_int = int(float(bilik_val))
                                        except: bilik_int = 10
                                        try: calon_int = int(float(calon_val))
                                        except: calon_int = 200
                                        batch.append({"kod_pusat": kod_p, "nama_pusat": nama_p.upper(), "kod_ppd": kod_ppd_val, "ppd": d.get("PPD", "") or PPD_MAP.get(kod_ppd_val, ""), "alamat": d.get("KOD_SEKOLAH", "") or d.get("ALAMAT PUSAT", "") or d.get("ALAMAT", ""), "bilik": bilik_int, "calon": calon_int, "data": d})
                                    except: continue
                                if batch:
                                    try:
                                        supa.table("pusat_master").insert(batch).execute()
                                        ok += len(batch)
                                    except Exception as e:
                                        st.warning(f"Batch {start}-{end}: {e}")
                                bar.progress(end / len(df_up))
                                stat.write(f"Progress {end}/{len(df_up)} | OK {ok}")
                            st.success(f"✅ Selesai import {ok}/{len(df_up)} pusat! Total 506")
                            st.balloons()
                            st.rerun()
                    except Exception as e:
                        st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")

            if fly_cur == "kosong":
                st.markdown("---")
                if st.button("🗑️ Kosongkan Semua Pusat (Hati-hati!)", type="secondary"):
                    try:
                        supa.table("pusat_master").delete().gt("id", 0).execute()
                        st.success("Semua pusat dipadam")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        elif menu == "guru":
            st.header("Guru Master Seluruh Negeri")
            if fly_cur == "import":
                st.subheader(" Import MASTER 60K Guru Selangor")
                st.info("Upload file MASTER-GURU-SELANGOR-2026.xlsx (60K) di sini untuk restore balik data yang hilang. Guna batch 500 untuk laju.")
                render_templat_guru()
                up_master = st.file_uploader("Upload MASTER 60K Excel", type=["xlsx"], key="master60k")
                if up_master:
                    try:
                        df_m = semak_fail_guru(up_master)
                        st.write(f"File ada {len(df_m)} baris.")
                        st.dataframe(df_m.head(10), use_container_width=True)
                        if st.button(f"🚀 Import {len(df_m)} Guru ke Supabase (Batch 500)", type="primary", use_container_width=True):
                            bar = st.progress(0)
                            stat = st.empty()
                            ok = 0
                            BATCH = 500
                            for start in range(0, len(df_m), BATCH):
                                end = min(start + BATCH, len(df_m))
                                bdf = df_m.iloc[start:end]
                                batch = []
                                for _, row in bdf.iterrows():
                                    try:
                                        d = {}
                                        for k, v in row.to_dict().items():
                                            d[k] = "" if pd.isna(v) else str(v)
                                        nama = d.get("NAMA GURU", "").upper().strip()
                                        if not nama or nama == "NAN": continue
                                        batch.append({
                                            "kod_ppd": d.get("KOD PPD", "").lower().strip(),
                                            "kod_sekolah": d.get("KOD SEKOLAH", "").upper().strip(),
                                            "nama_guru": nama,
                                            "ic_guru": d.get("IC", ""),
                                            "jantina": d.get("JANTINA",""),
                                            "poskod_rumah": d.get("POSKOD RUMAH","") or d.get("POSKOD_RUMAH",""),
                                            "alamat_rumah": d.get("ALAMAT RUMAH","") or d.get("ALAMAT_RUMAH",""),
                                            "telefon_guru": d.get("NO TELEFON GURU","") or d.get("TELEFON_GURU",""),
                                            "email_guru": d.get("EMAIL GURU","") or d.get("EMAIL_GURU",""),
                                            "pengalaman_spm": d.get("PENGALAMAN SPM","") or d.get("PENGALAMAN_SPM",""),
                                            "kod_sekolah_asal": d.get("KOD SEKOLAH","").upper().strip(),
                                            "nama_sekolah_asal": d.get("NAMA SEKOLAH",""),
                                            "no_pusat_asal": d.get("NO PUSAT ASAL", ""),
                                            "data": d
                                        })
                                    except: continue
                                if batch:
                                    try:
                                        supa.table("guru_master").insert(batch).execute()
                                        ok += len(batch)
                                    except Exception as e:
                                        st.error(f"Batch {start}-{end} error: {e}")
                                bar.progress(end / len(df_m))
                                stat.write(f"Imported {end}/{len(df_m)} | OK {ok}")
                            st.success(f"✅ Selesai import {ok}/{len(df_m)} guru!")
                            st.balloons()
                    except Exception as e:
                        st.error("Maaf, berlaku masalah semasa memproses. Sila cuba lagi.")

            if fly_cur == "data":
                st.markdown("---")
                st.subheader("Data Sedia Ada")
                try:
                    res = supa.table("guru_master").select("*", count="exact").limit(5000).execute()
                    df = pd.DataFrame(res.data or [])
                    st.write(f"Total dalam Supabase: {res.count} records")
                    if not df.empty:
                        st.dataframe(df.head(100), use_container_width=True)
                        st.download_button("Export Guru Master (5000)", to_excel(df), file_name="guru_master_full.xlsx")
                except Exception as e:
                    st.error(str(e))

        elif menu == "cadangan":
            st.header("Semua Cadangan Seluruh Negeri")
            try:
                res = supa.table("cadangan_sup").select("*").limit(10000).execute()
                df = pd.DataFrame(res.data or [])
                st.dataframe(df, use_container_width=True)
                if not df.empty:
                    st.download_button("Export Semua Cadangan", to_excel(df), file_name=f"cadangan_negeri_{datetime.date.today()}.xlsx")
            except Exception as e:
                st.error(str(e))


        elif menu == "jana_surat":
            surat_panel("JPN")
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

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Cadangan PPD", len(df_cad_all_surat))
            c2.metric("✅ Sudah Lulus Ada Surat", len(df_lulus_surat))
            c3.metric("⏳ Belum Ada Surat", len(df_belum_surat))

            if df_lulus_surat.empty:
                st.warning("Belum ada surat yang diluluskan di PPD ini - sila luluskan di menu Kelulusan dahulu")
                st.info("Pergi ke Kelulusan > Lulus Keseluruhan atau Lulus Mengikut Pusat untuk luluskan dan jana surat")
                st.stop()

            # Tabs for view
            tab_keseluruhan, tab_pusat_surat, tab_sekolah_asal = st.tabs(["📄 Semua Surat (Keseluruhan)", "🏫 Ikut Pusat", "🏫 Ikut Sekolah Asal (Untuk Hantar)"])

            with tab_keseluruhan:
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

            with tab_pusat_surat:
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

            with tab_sekolah_asal:
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



        elif menu == "export":
            st.header("Export Laporan Negeri")
            try:
                res = supa.table("cadangan_sup").select("*").limit(10000).execute()
                df = pd.DataFrame(res.data or [])
                if not df.empty:
                    st.download_button("📥 Laporan Penuh Negeri (Excel)", to_excel(df), file_name=f"Laporan_JPN_Selangor_{datetime.date.today()}.xlsx", use_container_width=True, type="primary")
            except Exception as e:
                st.error(str(e))

        elif menu == "admin":
            st.header("⚙️ Status Sistem & Sambungan Pangkalan Data")
            if fly_cur == "status":
                for t in ["sekolah_master", "pusat_master", "guru_master", "cadangan_sup"]:
                    try:
                        res = supa.table(t).select("*", count="exact").limit(1).execute()
                        st.success(f"✅ {t}: {res.count} records")
                    except Exception as e:
                        st.error(f"❌ {t}: {e}")
            if fly_cur == "table":
                st.markdown("---")
                st.subheader("Buat Table cadangan_sup jika belum ada")
                st.code("""
-- Run di Supabase SQL Editor jika cadangan_sup belum wujud:
CREATE TABLE IF NOT EXISTS cadangan_sup (
id BIGSERIAL PRIMARY KEY,
kod_ppd TEXT,
kod_sekolah TEXT,
ic_guru TEXT,
nama_guru TEXT,
kod_pusat TEXT,
jawatan_cadangan TEXT,
catatan TEXT,
status TEXT DEFAULT 'DICADANGKAN',
tarikh_cadang DATE,
created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE cadangan_sup ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow all" ON cadangan_sup;
CREATE POLICY "allow all" ON cadangan_sup FOR ALL USING (true) WITH CHECK (true);
""", language="sql")
