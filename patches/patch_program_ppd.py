# -*- coding: utf-8 -*-
"""patch_program_ppd.py - sambungkan role_ppd.py, ppd_zon.py dan role_jpn.py kepada PROGRAM (SPM/UBBM/UBBI). Boleh dijalankan berulang kali."""
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

def once(old, new):
    def f(s):
        assert s.count(old) == 1, (s.count(old), old[:70])
        return s.replace(old, new, 1)
    return f

# ----------------------------- role_ppd.py -----------------------------
IMP_OLD = "from ppd_zon import render_penempatan_zon\n"
IMP_NEW = IMP_OLD + ("from program_config import adalah_spm, kuota_roles, roles as program_roles, status_kuota as status_program, cfg as program_cfg\n"
                     "from ppd_program import render_jana_program\n")

def ppd_perlu(s):
    m = re.search(r"def perlu_pusat\(d, jk\):\n(    \"\"\".*?\"\"\"\n)?", s, re.S)
    assert m, "perlu_pusat"
    ins = ("    if not adalah_spm():                       # UBBM/UBBI: keperluan pusat = jumlah kuota mengikut bilik ujian\n"
           "        return sum(kuota_roles(bilik=jk).values())\n")
    return s[:m.end()] + ins + s[m.end():]

def ppd_ringkas(s):
    s = s.replace('                    kp, tkp, peng = _jn.count("KP"), _jn.count("TKP"), _jn.count("PENGAWAS")\n',
                  '                    _cnt = {_k: _jn.count(_k) for _k, _n, _c in program_roles()}\n', 1)
    s = s.replace('                    _st, _ct = status_kuota_penuh(kp, tkp, peng, perlu, jumlah)\n',
                  '                    _q = kuota_roles(bilik=k.get("KELAS", 0), petugas=perlu)\n                    _st, _ct = status_program(_cnt, _q, jumlah)\n', 1)
    s = s.replace('                                        "KP": kp, "TKP": tkp, "PENGAWAS": peng,\n',
                  '                                        **{_c: _cnt[_k] for _k, _n, _c in program_roles()},\n', 1)
    return s

def ppd_hasil_order(s):
    m = re.search(r'^                order = \["Ketua Pengawas", "Timbalan Ketua Pengawas".*\]\n', s, re.M)
    assert m
    return s[:m.end()] + '                if not adalah_spm():\n                    order = program_cfg()["jawatan_pilihan"]\n' + s[m.end():]

def ppd_routing(s):
    old = '        elif menu == "jana":\n'
    new = ('        elif menu == "jana" and not adalah_spm():\n'
           '            render_jana_program(kod_ppd, "daerah")\n\n'
           '        elif menu == "manual" and not adalah_spm():\n'
           '            st.info("Penempatan Manual belum disesuaikan untuk program ini. Guna Jana Keseluruhan atau Penempatan Zon (mengikut kuota bilik ujian).")\n\n'
           '        elif menu == "jana":\n')
    assert s.count(old) == 1
    return s.replace(old, new, 1)

patch_file("role_ppd.py", [
    ("import program", "from program_config import adalah_spm", once(IMP_OLD, IMP_NEW)),
    ("perlu_pusat ikut bilik ujian (UB)", "UBBM/UBBI: keperluan pusat", ppd_perlu),
    ("ringkasan hasil ikut peranan", "_cnt = {_k: _jn.count(_k)", ppd_ringkas),
    ("susunan jawatan hasil", 'order = program_cfg()["jawatan_pilihan"]', ppd_hasil_order),
    ("label jawatan hasil", 'if adalah_spm() else f"{jawatan} - {len(guru_list)} orang"',
     once('label = f"Pengawas Peperiksaan - {len(guru_list)} orang"',
          'label = f"Pengawas Peperiksaan - {len(guru_list)} orang" if adalah_spm() else f"{jawatan} - {len(guru_list)} orang"')),
    ("mesej pusat hasil", "if adalah_spm() else f\"{pilihan_pusat_hasil}",
     once('st.success(f"{pilihan_pusat_hasil} - {pusat_nama_h} | {len(df_hasil)} petugas: 1 Ketua, 1 Timbalan, {len(df_hasil)-2} Pengawas")',
          'st.success(f"{pilihan_pusat_hasil} - {pusat_nama_h} | {len(df_hasil)} petugas: 1 Ketua, 1 Timbalan, {len(df_hasil)-2} Pengawas" if adalah_spm() else f"{pilihan_pusat_hasil} - {pusat_nama_h} | {len(df_hasil)} petugas")')),
    ("laluan menu Jana / Manual (UB)", 'elif menu == "jana" and not adalah_spm():', ppd_routing),
])

# ----------------------------- ppd_zon.py -----------------------------
patch_file("ppd_zon.py", [
    ("Jana Penempatan Zon (UB)", "ppd_program.render_jana_program(kod_ppd, \"zon\")",
     once('    if fly_cur == "tempat":\n        _view_jana(kod_ppd, db_ok)\n',
          '    if fly_cur == "tempat":\n        import program_config\n        if not program_config.adalah_spm():\n            import ppd_program\n            ppd_program.render_jana_program(kod_ppd, "zon")\n            return\n        _view_jana(kod_ppd, db_ok)\n')),
])

# ----------------------------- role_jpn.py -----------------------------
patch_file("role_jpn.py", [
    ("import tetapan program", "from ppd_program import render_tetapan_program",
     once("from surat_tools import surat_panel, surat_aset_panel, surat_diagnostik\n",
          "from surat_tools import surat_panel, surat_aset_panel, surat_diagnostik\nfrom ppd_program import render_tetapan_program\n")),
    ("menu Tetapan Program", "('tetapan_program', '⚙️ Tetapan Program')",
     once("('kata_laluan', '🔑 Kata Laluan'),", "('kata_laluan', '🔑 Kata Laluan'), ('tetapan_program', '⚙️ Tetapan Program'),")),
    ("cabang Tetapan Program", "render_tetapan_program()\n",
     once('        elif menu == "kata_laluan":\n',
          '        elif menu == "tetapan_program":\n            render_tetapan_program()\n\n        elif menu == "kata_laluan":\n')),
])
print("SIAP")
