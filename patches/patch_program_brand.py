# -*- coding: utf-8 -*-
"""patch_program_brand.py - tajuk sistem & teks surat ikut PROGRAM. Boleh dijalankan berulang kali."""
import re, sys

def patch_file(path, steps):
    s = open(path, encoding="utf-8").read()
    for nama, tanda, fn in steps:
        if tanda in s:
            print(f"  - {path}: {nama} (sudah ada)"); continue
        s2 = fn(s)
        if s2 == s:
            sys.exit(f"RALAT {path}: '{nama}' - tiada padanan.")
        s = s2; print(f"  + {path}: {nama}")
    open(path, "w", encoding="utf-8").write(s)

def once(old, new):
    def f(s):
        assert s.count(old) == 1, (s.count(old), old[:70])
        return s.replace(old, new, 1)
    return f

# ---- program_config: teks surat ----
def pc_teks(s):
    s = s.replace('"nama_ujian": "SIJIL PELAJARAN MALAYSIA (SPM) 2026", "pengalaman": "Pengalaman SPM (Tahun)",',
                  '"nama_ujian": "SIJIL PELAJARAN MALAYSIA (SPM) 2026", "pengalaman": "Pengalaman SPM (Tahun)",\n        "ujian_kata": "peperiksaan", "elaun_ikhtisas": "RM 281.25 + S (S = Bil. Sesi)",', 1)
    s = s.replace('"nama_ujian": "UJIAN BERTUTUR BAHASA MELAYU (UBBM) 2026", "pengalaman": "Pengalaman UBBM (Tahun)",',
                  '"nama_ujian": "UJIAN BERTUTUR BAHASA MELAYU (UBBM) 2026", "pengalaman": "Pengalaman UBBM (Tahun)",\n        "ujian_kata": "ujian", "elaun_ikhtisas": "Mengikut kadar yang ditetapkan oleh Jabatan",   # KEMAS KINI kadar sebenar UBBM',  1)
    s = s.replace('"nama_ujian": "UJIAN BERTUTUR BAHASA INGGERIS (UBBI) 2026", "pengalaman": "Pengalaman UBBI (Tahun)",',
                  '"nama_ujian": "UJIAN BERTUTUR BAHASA INGGERIS (UBBI) 2026", "pengalaman": "Pengalaman UBBI (Tahun)",\n        "ujian_kata": "ujian", "elaun_ikhtisas": "Mengikut kadar yang ditetapkan oleh Jabatan",   # KEMAS KINI kadar sebenar UBBI', 1)
    return s
patch_file("program_config.py", [("kata & elaun surat", '"ujian_kata"', pc_teks)])

# ---- spm_core: teks surat ----
def sc_tajuk(s):
    old = 'tajuk_full = f"SIJIL PELAJARAN MALAYSIA (SPM) 2026 :<br/>PELANTIKAN {tajuk_jawatan} SPM BERTULIS 2026"'
    new = ('from program_config import tajuk_surat as _tajuk_surat, cfg as _pcfg, adalah_spm as _adalah_spm\n'
           '            _t1, _t2 = _tajuk_surat(tajuk_jawatan)\n'
           '            tajuk_full = f"{_t1}<br/>{_t2}"')
    assert s.count(old) == 1
    return s.replace(old, new, 1)
def sc_para2(s):
    old = 'bagi peperiksaan di atas. Berikut adalah pusat peperiksaan di bawah pengawasan tuan:'
    new = 'bagi {_pcfg()["ujian_kata"]} di atas. Berikut adalah pusat {_pcfg()["ujian_kata"]} di bawah pengawasan tuan:'
    assert s.count(old) == 1
    return s.replace(old, new, 1)
def sc_elaun(s):
    old = 'Paragraph("<b>RM 281.25 + S (S = Bil. Sesi)</b>", style_small)'
    new = 'Paragraph(f"<b>{_pcfg()[\'elaun_ikhtisas\']}</b>", style_small)'
    assert s.count(old) == 1
    return s.replace(old, new, 1)
def sc_para4(s):
    old = '        story.append(Paragraph(para4, style_normal))\n'
    new = ('        if not _adalah_spm():          # UBBM/UBBI: tiada Pengawas Pengiring\n'
           '            para4 = re.sub(r"\\s*Tuan boleh dilantik oleh Ketua Pengawas sebagai <b>Pengawas Pengiring</b> mengikut keperluan ke bilik kebal\\.", "", para4)\n'
           '        story.append(Paragraph(para4, style_normal))\n')
    assert s.count(old) == 1
    return s.replace(old, new, 1)
patch_file("spm_core.py", [
    ("tajuk surat ikut program", "_tajuk_surat(tajuk_jawatan)", sc_tajuk),
    ("perkataan peperiksaan/ujian", '_pcfg()["ujian_kata"]', sc_para2),
    ("elaun ikhtisas ikut program", "_pcfg()['elaun_ikhtisas']", sc_elaun),
    ("perenggan 4 ikut program", "_adalah_spm():          # UBBM/UBBI", sc_para4),
])

# ---- tajuk sistem ----
def landing_fstring(s):
    m = re.search(r'st\.markdown\("""\n    <div class="land-top">.*?""", unsafe_allow_html=True\)', s, re.S)
    blok = m.group(0)
    baru = blok.replace('st.markdown("""', 'st.markdown(f"""', 1)
    baru = re.sub(r"(Sistem )?Pelantikan Petugas SPM Selangor 2026", lambda mm: ("{esc(nama_sistem())}" if mm.group(1) else "Pelantikan Petugas {esc(cfg()['singkatan'])} Selangor 2026"), baru)
    return s.replace(blok, baru, 1)
patch_file("main_app.py", [
    ("import program_config", "from program_config import nama_sistem", once("from ui_theme import esc\n", "from ui_theme import esc\nfrom program_config import nama_sistem\n")),
    ("tajuk halaman utama", "{esc(nama_sistem())}", landing_fstring),
])
patch_file("jpn_app.py", [
    ("import program_config", "from program_config import cfg", once("import auth_db\n", "import auth_db\nfrom program_config import cfg\nfrom ui_theme import esc\n")),
    ("tajuk log masuk JPN", "{esc(cfg()['singkatan'])}", landing_fstring),
])
patch_file("daerah_app.py", [
    ("import program_config", "from program_config import cfg", once("import auth_db\n", "import auth_db\nfrom program_config import cfg\n")),
    ("tajuk halaman pilih sekolah", "{esc(cfg()['singkatan'])}", once("Pelantikan Petugas SPM Selangor 2026 &nbsp;", "Pelantikan Petugas {esc(cfg()['singkatan'])} Selangor 2026 &nbsp;")),
])
patch_file("ui_theme.py", [
    ("tajuk dashboard JPN", "__import__('program_config')", once('"Dashboard JPN Selangor - Pelantikan SPM 2026"',
        'f"Dashboard JPN Selangor - Pelantikan {__import__(\'program_config\').cfg()[\'singkatan\']} 2026"')),
])
def app_title(s):
    old = 'st.set_page_config(page_title="SPM 2026 - Selangor"'
    new = ('import os\n'
           'try:\n    _P = str(st.secrets.get("PROGRAM", os.environ.get("PROGRAM", "SPM"))).strip().upper()\nexcept Exception:\n    _P = os.environ.get("PROGRAM", "SPM").strip().upper()\n'
           '_P = _P if _P in ("UBBM", "UBBI") else "SPM"\n'
           'st.set_page_config(page_title=f"{_P} 2026 - Selangor"')
    assert s.count(old) == 1
    return s.replace(old, new, 1)
patch_file("app.py", [("tajuk tab pelayar", "_P = _P if _P in", app_title)])
print("SIAP")
