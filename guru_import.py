# -*- coding: utf-8 -*-
"""
guru_import.py - Templat Excel & semakan fail untuk Import Guru Master (JPN > Guru Master > Import).

  bina_templat()        : fail Excel templat (lajur tepat seperti yang dibaca oleh import; IC/telefon/poskod format TEKS)
  semak_guru(df)        : bersihkan & semak setiap baris -> (baris_sah, laporan_ralat, ringkasan)
  semak_fail_guru(file) : baca fail yang diupload, papar laporan, pulang baris sah sahaja
  render_templat_guru() : butang muat turun templat
"""
import io
import re
import pandas as pd
import streamlit as st

KOLUM = [
    # (nama lajur, wajib, contoh, penerangan)
    ("NAMA GURU", True, "AHMAD BIN ALI", "Nama penuh guru (huruf besar)."),
    ("KOD PPD", True, "BG", "Kod PPD 2 huruf: BA Klang, BB Kuala Langat, BC Kuala Selangor, BD Hulu Langat, BE Hulu Selangor, BF Sabak Bernam, BG Gombak, BH Petaling Perdana, BJ Sepang, BK Petaling Utama."),
    ("KOD SEKOLAH", True, "BGA0001", "Kod sekolah (huruf besar), mesti sama dengan sekolah_master."),
    ("IC", True, "800101015555", "No kad pengenalan 12 digit, TANPA sengkang (-). Lajur ini berformat TEKS supaya sifar di depan tidak hilang."),
    ("NAMA SEKOLAH", False, "SMK GOMBAK JAYA", "Nama sekolah."),
    ("JANTINA", False, "L", "L atau P (LELAKI / PEREMPUAN juga diterima)."),
    ("POSKOD RUMAH", False, "68100", "5 digit. Digunakan untuk penempatan ikut poskod terdekat."),
    ("ALAMAT RUMAH", False, "NO 1 JALAN CONTOH, BATU CAVES", "Alamat rumah."),
    ("NO TELEFON GURU", False, "0123456789", "Digit sahaja, bermula 0 (cth 0123456789)."),
    ("EMAIL GURU", False, "ahmad@moe.edu.my", "Emel guru."),
    ("PENGALAMAN SPM", False, "5", "Bilangan tahun pengalaman (nombor)."),
]
NAMA = [k[0] for k in KOLUM]
WAJIB = [k[0] for k in KOLUM if k[1]]
# nama lajur alternatif -> nama piawai
ALIAS = {
    "NAMA": "NAMA GURU", "NAMA_GURU": "NAMA GURU", "KOD_PPD": "KOD PPD", "KOD_SEKOLAH": "KOD SEKOLAH", "NO IC": "IC", "NO. IC": "IC", "IC GURU": "IC", "IC_GURU": "IC",
    "NAMA_SEKOLAH": "NAMA SEKOLAH", "POSKOD_RUMAH": "POSKOD RUMAH", "POSKOD": "POSKOD RUMAH", "ALAMAT_RUMAH": "ALAMAT RUMAH", "ALAMAT": "ALAMAT RUMAH",
    "NO TELEFON": "NO TELEFON GURU", "TELEFON": "NO TELEFON GURU", "TELEFON_GURU": "NO TELEFON GURU", "NO_TELEFON_GURU": "NO TELEFON GURU", "NO TEL": "NO TELEFON GURU",
    "EMAIL": "EMAIL GURU", "EMAIL_GURU": "EMAIL GURU", "PENGALAMAN_SPM": "PENGALAMAN SPM", "PENGALAMAN UBBM": "PENGALAMAN SPM", "PENGALAMAN UBBI": "PENGALAMAN SPM",
}


def _kod_ppd_sah():
    try:
        import spm_core as core
        return [k.upper() for k in core.KOD_DAERAH]
    except Exception:
        return ["BA", "BB", "BC", "BD", "BE", "BF", "BG", "BH", "BJ", "BK"]


# ------------------------------------------------------------------ templat
def bina_templat():
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    kod = _kod_ppd_sah()
    nama_ppd = {}
    try:
        import spm_core as core
        nama_ppd = dict(core.PPD_MAP)
    except Exception:
        pass
    wb = Workbook()
    ws = wb.active
    ws.title = "GURU MASTER"
    biru = PatternFill("solid", fgColor="0D47A1"); kelabu = PatternFill("solid", fgColor="607D8B")
    tepi = Side(style="thin", color="B0BEC5"); border = Border(left=tepi, right=tepi, top=tepi, bottom=tepi)
    teks_kol = {"IC", "NO TELEFON GURU", "POSKOD RUMAH", "KOD PPD", "KOD SEKOLAH"}
    for c, (nama, wajib, contoh, _p) in enumerate(KOLUM, 1):
        h = ws.cell(row=1, column=c, value=nama)
        h.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
        h.fill = biru if wajib else kelabu
        h.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        h.border = border
        ws.column_dimensions[get_column_letter(c)].width = max(16, len(nama) + 4, 28 if nama in ("NAMA GURU", "ALAMAT RUMAH", "NAMA SEKOLAH") else 0)
        if nama in teks_kol:
            for r in range(2, 5002):
                ws.cell(row=r, column=c).number_format = "@"          # format TEKS
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    # semakan: KOD PPD mesti dalam senarai; IC 12 digit (amaran sahaja)
    dv = DataValidation(type="list", formula1=f"='KOD PPD'!$A$2:$A${len(kod) + 1}", allow_blank=True, showErrorMessage=True,
                        errorTitle="KOD PPD tidak sah", error="Pilih kod PPD daripada senarai (lihat helaian KOD PPD).")
    ws.add_data_validation(dv); dv.add("B2:B5000")
    dv_ic = DataValidation(type="custom", formula1='=AND(LEN(D2)=12,ISNUMBER(--D2))', allow_blank=True, showErrorMessage=True, errorStyle="warning",
                           errorTitle="IC tidak sah", error="IC mesti 12 digit, tanpa sengkang.")
    ws.add_data_validation(dv_ic); dv_ic.add("D2:D5000")

    pg = wb.create_sheet("PANDUAN")
    pg["A1"] = "PANDUAN ISI TEMPLAT GURU MASTER"; pg["A1"].font = Font(name="Arial", bold=True, size=13, color="0D47A1")
    for c, h in enumerate(["LAJUR", "WAJIB?", "CONTOH", "PENERANGAN / FORMAT"], 1):
        x = pg.cell(row=3, column=c, value=h); x.font = Font(name="Arial", bold=True, color="FFFFFF"); x.fill = biru; x.border = border
    for r, (nama, wajib, contoh, p) in enumerate(KOLUM, 4):
        for c, v in enumerate([nama, "YA" if wajib else "tidak", contoh, p], 1):
            x = pg.cell(row=r, column=c, value=v); x.font = Font(name="Arial", size=10, bold=(c == 1)); x.border = border
            x.alignment = Alignment(vertical="top", wrap_text=True)
    peraturan = ["Isi data pada helaian 'GURU MASTER' (helaian pertama). Jangan ubah nama lajur atau urutan helaian.",
                 "Satu baris = satu guru. Jangan tinggalkan baris kosong di tengah. Jangan padam lajur wajib (biru).",
                 "IC: 12 digit tanpa sengkang. Jika Excel membuang sifar di depan, sistem akan cuba membetulkan (11 digit -> tambah 0).",
                 "KOD PPD & KOD SEKOLAH: huruf besar. Baris dengan kod PPD tidak sah akan ditolak semasa semakan.",
                 "IC pendua dalam fail yang sama hanya diimport sekali. Import berulang untuk IC yang sudah ada akan menggandakan rekod - semak dahulu.",
                 "Data contoh ada di helaian 'CONTOH'. Jangan salin baris contoh ke helaian GURU MASTER."]
    pg.cell(row=5 + len(KOLUM), column=1, value="PERATURAN").font = Font(name="Arial", bold=True, color="0D47A1")
    for i, t in enumerate(peraturan, 6 + len(KOLUM)):
        pg.cell(row=i, column=1, value=f"{i - 5 - len(KOLUM)}. {t}").font = Font(name="Arial", size=10)
    for c, w in zip("ABCD", (22, 10, 28, 90)):
        pg.column_dimensions[c].width = w

    ct = wb.create_sheet("CONTOH")
    for c, (nama, _w, _c, _p) in enumerate(KOLUM, 1):
        x = ct.cell(row=1, column=c, value=nama); x.font = Font(name="Arial", bold=True, color="FFFFFF"); x.fill = kelabu
        ct.column_dimensions[get_column_letter(c)].width = max(16, len(nama) + 4)
    for r, (nm, ic, tel) in enumerate([("AHMAD BIN ALI", "800101015555", "0123456789"), ("SITI BINTI HASSAN", "850505105566", "0198765432")], 2):
        vals = [nm, "BG", "BGA0001", ic, "SMK GOMBAK JAYA", "L" if r == 2 else "P", "68100", "NO 1 JALAN CONTOH, BATU CAVES", tel, "contoh@moe.edu.my", "5"]
        for c, v in enumerate(vals, 1):
            x = ct.cell(row=r, column=c, value=v); x.number_format = "@"; x.font = Font(name="Arial", size=10)

    kp = wb.create_sheet("KOD PPD")
    kp["A1"] = "KOD PPD"; kp["B1"] = "DAERAH"
    for c in ("A1", "B1"):
        kp[c].font = Font(name="Arial", bold=True, color="FFFFFF"); kp[c].fill = biru
    for r, k in enumerate(kod, 2):
        kp.cell(row=r, column=1, value=k); kp.cell(row=r, column=2, value=nama_ppd.get(k, ""))
    kp.column_dimensions["A"].width = 12; kp.column_dimensions["B"].width = 26
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


# ------------------------------------------------------------------ semakan
def _bersih_ic(v):
    s = re.sub(r"\D", "", str(v or ""))
    if len(s) == 11:                       # sifar di depan hilang oleh Excel
        s = "0" + s
    return s


def _bersih_tel(v):
    s = re.sub(r"\D", "", str(v or ""))
    if not s:
        return ""
    if s.startswith("60"):
        s = "0" + s[2:]
    elif not s.startswith("0") and 9 <= len(s) <= 10:
        s = "0" + s
    return s


def semak_guru(df):
    """df mentah (semua teks). Pulang (sah, ralat, ringkasan). sah = lajur piawai, nilai dibersihkan."""
    df = df.copy()
    df.columns = [ALIAS.get(re.sub(r"\s+", " ", str(c).upper().replace("\n", " ")).strip(), re.sub(r"\s+", " ", str(c).upper()).strip()) for c in df.columns]
    df = df.loc[:, ~pd.Index(df.columns).duplicated()]
    hilang = [c for c in WAJIB if c not in df.columns]
    info = {"jumlah": len(df), "hilang_lajur": hilang, "dibetulkan": 0, "pendua": 0}
    if hilang:
        return pd.DataFrame(columns=NAMA), pd.DataFrame(), info
    for c in NAMA:
        if c not in df.columns:
            df[c] = ""
    df = df[NAMA].fillna("").astype(str).apply(lambda s: s.str.strip())
    df = df.replace({"nan": "", "NaN": "", "None": "", "NaT": ""})
    kod_sah = set(_kod_ppd_sah())
    sah, ralat, seen = [], [], set()
    for i, r in df.iterrows():
        baris = i + 2                                              # nombor baris dalam Excel (tajuk = baris 1)
        d = r.to_dict()
        if not any(d.values()):
            continue
        d["NAMA GURU"] = d["NAMA GURU"].upper()
        d["KOD PPD"] = d["KOD PPD"].upper()
        d["KOD SEKOLAH"] = d["KOD SEKOLAH"].upper()
        ic0 = d["IC"]; d["IC"] = _bersih_ic(ic0)
        if d["IC"] != re.sub(r"\D", "", ic0) or "-" in ic0:
            info["dibetulkan"] += 1
        tel0 = d["NO TELEFON GURU"]; d["NO TELEFON GURU"] = _bersih_tel(tel0)
        pk = re.sub(r"\D", "", d["POSKOD RUMAH"])
        d["POSKOD RUMAH"] = pk.zfill(5) if pk and len(pk) < 5 else pk
        sebab = []
        if not d["NAMA GURU"]:
            sebab.append("Nama guru kosong")
        if d["KOD PPD"] not in kod_sah:
            sebab.append(f"KOD PPD tidak sah ('{d['KOD PPD']}')")
        if not d["KOD SEKOLAH"]:
            sebab.append("KOD SEKOLAH kosong")
        if len(d["IC"]) != 12:
            sebab.append(f"IC mesti 12 digit (ada {len(d['IC'])})")
        elif d["IC"] in seen:
            sebab.append("IC pendua dalam fail ini")
            info["pendua"] += 1
        if d["POSKOD RUMAH"] and len(d["POSKOD RUMAH"]) != 5:
            sebab.append("Poskod mesti 5 digit")
        if sebab:
            ralat.append({"BARIS EXCEL": baris, "NAMA GURU": d["NAMA GURU"], "IC": ic0, "KOD PPD": d["KOD PPD"], "KOD SEKOLAH": d["KOD SEKOLAH"], "MASALAH": "; ".join(sebab)})
            continue
        seen.add(d["IC"])
        sah.append(d)
    info["sah"], info["ralat"] = len(sah), len(ralat)
    return pd.DataFrame(sah, columns=NAMA), pd.DataFrame(ralat), info


# ------------------------------------------------------------------ UI
def render_templat_guru():
    st.download_button("📥 Muat Turun Templat Guru Master (Excel)", bina_templat(), file_name="TEMPLAT_GURU_MASTER.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_templat_guru", use_container_width=True)
    st.caption("Templat ada lajur tepat seperti yang dibaca sistem, panduan setiap lajur, contoh data dan senarai kod PPD. "
               "Lajur wajib berwarna biru: NAMA GURU, KOD PPD, KOD SEKOLAH, IC.")


def semak_fail_guru(fail):
    """Baca fail upload (semua lajur sebagai teks), paparkan laporan semakan, pulang baris SAH sahaja."""
    raw = pd.read_excel(fail, sheet_name=0, dtype=str)
    sah, ralat, info = semak_guru(raw)
    if info["hilang_lajur"]:
        st.error("Lajur wajib tiada dalam fail: **" + ", ".join(info["hilang_lajur"]) + "**. Gunakan templat (butang di atas) dan jangan ubah nama lajur.")
        return pd.DataFrame(columns=NAMA)
    c1, c2, c3 = st.columns(3)
    c1.metric("Baris dalam fail", info["jumlah"])
    c2.metric("✅ Sah (akan diimport)", info["sah"])
    c3.metric("❌ Ditolak", info["ralat"])
    if info["dibetulkan"]:
        st.caption(f"ℹ️ {info['dibetulkan']} IC dibetulkan secara automatik (sengkang dibuang / sifar di depan ditambah).")
    if info["ralat"]:
        st.warning("Baris di bawah TIDAK akan diimport. Betulkan dalam Excel dan upload semula, atau teruskan dengan baris yang sah sahaja.")
        st.dataframe(ralat, use_container_width=True, hide_index=True)
        buf = io.BytesIO(); ralat.to_excel(buf, index=False)
        st.download_button("📥 Muat turun laporan ralat", buf.getvalue(), file_name="ralat_import_guru.xlsx", key="dl_ralat_guru")
    return sah
