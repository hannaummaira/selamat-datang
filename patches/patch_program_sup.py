# -*- coding: utf-8 -*-
"""patch_program_sup.py - sambungkan role_sup.py & ppd_cadangan.py kepada PROGRAM (SPM/UBBM/UBBI). Boleh dijalankan berulang kali."""
import re, sys

def patch_file(path, steps):
    s = open(path, encoding="utf-8").read()
    for nama, tanda, fn in steps:
        if tanda in s:
            print(f"  - {path}: {nama} (sudah ada)"); continue
        s2 = fn(s)
        if s2 == s:
            sys.exit(f"RALAT {path}: '{nama}' - tiada padanan. Semak fail secara manual.")
        s = s2; print(f"  + {path}: {nama}")
    open(path, "w", encoding="utf-8").write(s)

LIT = re.compile(r'\["Ketua Pengawas", "Timbalan Ketua Pengawas", "Penyelia Kawasan", "Pengawas Peperiksaan", "Juru Tulis", "Juru Baca", "Ketua Pengawas Hospital", "Pengawas Hospital", "Pengawas Pengiring", "Pengemas Bilik"\]')

def sup_lists(s):
    return LIT.sub("jawatan_pilihan()", s)

def sup_betul(s):
    return re.sub(r'JAWATAN_BETUL = \[\s*"Ketua Pengawas \(WAJIB 1\)".*?"Pengemas Bilik"\s*\]', "JAWATAN_BETUL = jawatan_betul()", s, flags=re.S)

def sup_import(s):
    anchor = "from sup_warna import"
    i = s.find(anchor)
    if i < 0:
        i = s.find("globals().update({k: v for k, v in vars(_ui).items()")
        i = s.find("\n", i) + 1
    else:
        i = s.rfind("\n", 0, i) + 1
    return s[:i] + "from program_config import adalah_spm, jawatan_pilihan, jawatan_betul, cfg as program_cfg\nfrom ppd_program import keperluan_ub_sekolah, metrik_cadangan_ub\n" + s[i:]

def sup_pengalaman(s):
    return s.replace('st.text_input("Pengalaman SPM (Tahun) - SUP isi"', 'st.text_input(f"{program_cfg()[\'pengalaman\']} - SUP isi"')

def sup_kotak(s):
    old = '''                if pusat_sek:
                    st.markdown(f"""
                    <div style="background:#e3f2fd; padding:15px; border-radius:10px; border-left:5px solid #0d47a1; margin-bottom:20px;">
                        <h4 style="margin:0; color:#0d47a1;">📢 KEPERLUAN WAJIB SEKOLAH ANDA - {kod}</h4>'''
    new = '''                kuota_ub = {}
                if not adalah_spm():
                    total_kelas_alert, total_need_simple, kuota_ub = keperluan_ub_sekolah(str(info.get("kod_ppd", "")).upper(), kod)
                elif pusat_sek:
                    st.markdown(f"""
                    <div style="background:#e3f2fd; padding:15px; border-radius:10px; border-left:5px solid #0d47a1; margin-bottom:20px;">
                        <h4 style="margin:0; color:#0d47a1;">📢 KEPERLUAN WAJIB SEKOLAH ANDA - {kod}</h4>'''
    return s.replace(old, new, 1)

def sup_metrik(s):
    a = s.index("                            c1, c2, c3, c4 = st.columns(4)\n                            c1.metric(\"Ketua Pengawas\"")
    b = s.index("                        except: pass", a)
    blok = s[a:b]
    ind = "".join("    " + ln + "\n" if ln.strip() else ln + "\n" for ln in blok.rstrip("\n").split("\n"))
    baru = ("                            if not adalah_spm():\n"
            "                                metrik_cadangan_ub(df_cad, kuota_ub if 'kuota_ub' in locals() else {})\n"
            "                            else:\n" + ind)
    return s[:a] + baru + s[b:]

def sup_tables(s):
    a = s.index('                    papar_table_jawatan(df_cad_sup, "TABLE 1: Penyelia Kawasan"')
    b = s.index('\n', s.index('papar_table_jawatan(df_cad_sup, "TABLE 3: Pengawas Peperiksaan"', a)) + 1
    blok = s[a:b]
    ind = "".join("    " + ln + "\n" for ln in blok.rstrip("\n").split("\n"))
    baru = ("                    if adalah_spm():\n" + ind +
            "                    else:\n"
            "                        for _i, _j in enumerate(jawatan_pilihan()):\n"
            "                            papar_table_jawatan(df_cad_sup, f\"TABLE {_i + 1}: {_j}\", \"🔐\" if _j == \"Penyelia Kawasan\" else \"👨‍🏫\", [_j], \"linear-gradient(135deg, #0d47a1 0%, #0d47a1 100%)\")\n")
    return s[:a] + baru + s[b:]

patch_file("role_sup.py", [
    ("import program_config", "from program_config import adalah_spm", sup_import),
    ("senarai jawatan SUP", "jawatan_pilihan()", sup_lists),
    ("JAWATAN_BETUL", "JAWATAN_BETUL = jawatan_betul()", sup_betul),
    ("label pengalaman", "program_cfg()['pengalaman']", sup_pengalaman),
    ("kotak keperluan UB", "keperluan_ub_sekolah(str(info", sup_kotak),
    ("kiraan cadangan UB", "metrik_cadangan_ub(df_cad", sup_metrik),
    ("jadual surat ikut jawatan", "for _i, _j in enumerate(jawatan_pilihan())", sup_tables),
])

# ---- ppd_cadangan: jenis_jawatan & susunan jawatan ikut program ----
def pc_jenis(s):
    a = s.index("def jenis_jawatan(jawatan):")
    b = s.index("def status_kuota_pusat", a)
    return s[:a] + '''def jenis_jawatan(jawatan):
    """Peranan kuota ikut program aktif (SPM: KP/TKP/PENGAWAS/LAIN - tidak sensitif huruf besar-kecil)."""
    from program_config import role_of
    return role_of(jawatan)


''' + s[b:]

def pc_order(s):
    old = '''def _jaw_sorted(vals):
    vals = list(vals)
    return sorted(vals, key=lambda x: (ORDER_JAWATAN.index(x) if x in ORDER_JAWATAN else 99, x))'''
    new = '''def _jaw_sorted(vals):
    from program_config import urutan_jawatan, adalah_spm
    vals = list(vals)
    order = ORDER_JAWATAN if adalah_spm() else urutan_jawatan()
    return sorted(vals, key=lambda x: (order.index(str(x).upper()) if str(x).upper() in order else 99, x))'''
    return s.replace(old, new, 1)

patch_file("ppd_cadangan.py", [
    ("jenis_jawatan ikut program", "from program_config import role_of", pc_jenis),
    ("susunan jawatan ikut program", "from program_config import urutan_jawatan", pc_order),
])
print("SIAP")
