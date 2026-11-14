# -*- coding: utf-8 -*-
"""sup_warna.py - warna nama cadangan SUP: HIJAU = sudah hantar ke PPD, KUNING = belum hantar.

Satu peraturan status untuk pewarnaan, kiraan dan butang Hantar (menu Cadangan > Senarai & menu Hantar ke PPD).
  BELUM hantar : status kosong / DICADANGKAN (termasuk "DICADANGKAN SEMULA ...") / BARU / TOLAK (dipulangkan PPD)
  SUDAH hantar : semua status lain - HANTAR KE PPD, TERPILIH, SIMPANAN, DIJANA, DILANTIK, DITEMPATKAN, LULUS, SURAT..., SAMPAI...
"""
import pandas as pd

HIJAU_NAMA = "background-color:#a5d6a7;color:#1b5e20;font-weight:800;"
HIJAU_BARIS = "background-color:#e8f5e9;color:#0b1b33;"
KUNING_NAMA = "background-color:#ffe082;color:#5d4037;font-weight:800;"
KUNING_BARIS = "background-color:#fff8e1;color:#0b1b33;"

LEGEND_HTML = (
    '<div style="background:#ffffff;border-left:4px solid #0d47a1;padding:8px 12px;border-radius:6px;margin-bottom:10px;">'
    '<b>Panduan Warna:</b> Nama guru '
    f'<span style="{HIJAU_NAMA}padding:2px 8px;border-radius:4px;">HIJAU</span> = Sudah hantar ke PPD &nbsp;|&nbsp; '
    f'<span style="{KUNING_NAMA}padding:2px 8px;border-radius:4px;">KUNING</span> = Belum hantar ke PPD</div>')


def sudah_hantar(status):
    s = str(status if status is not None else "").upper().strip()
    if s in ("", "NAN", "NONE", "NULL"):
        return False
    return not any(x in s for x in ("DICADANGKAN", "BARU", "TOLAK"))


def _kolum_status(df):
    for c in df.columns:
        if str(c).upper() == "STATUS":
            return c
    return None


def style_cadangan_hantar(df_input):
    """Pulang Styler (hijau/kuning) dengan lajur 'HANTAR PPD' (🟢/🟡) supaya status tetap jelas walau warna tidak dipaparkan.
    Jika tiada lajur STATUS, jadual dipulangkan tanpa warna."""
    try:
        df = df_input.copy()
        df = df.loc[:, ~pd.Index([str(c).lower() for c in df.columns]).duplicated()].reset_index(drop=True)
        sc = _kolum_status(df)
        if sc is None:
            return df
        sent = df[sc].apply(sudah_hantar)
        pos = 1 if any("NAMA" in str(c).upper() for c in df.columns[:1]) else 0
        df.insert(1 if pos else 0, "HANTAR PPD", sent.map({True: "🟢 Sudah Hantar", False: "🟡 Belum Hantar"}))

        def warna(row):
            ok = sent.iloc[row.name]
            out = []
            for c in row.index:
                cu = str(c).upper()
                if "NAMA_GURU" in cu or cu in ("NAMA GURU", "NAMA", "HANTAR PPD"):
                    out.append(HIJAU_NAMA if ok else KUNING_NAMA)
                else:
                    out.append(HIJAU_BARIS if ok else KUNING_BARIS)
            return out
        return df.style.apply(warna, axis=1)
    except Exception:
        return df_input


def kira_hantar(df):
    """(sudah, belum) mengikut peraturan yang sama."""
    if df is None or len(df) == 0:
        return 0, 0
    sc = _kolum_status(df)
    if sc is None:
        return 0, len(df)
    n = int(df[sc].apply(sudah_hantar).sum())
    return n, len(df) - n
