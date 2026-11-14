# -*- coding: utf-8 -*-
"""patch_guru.py - tambah templat & semakan pada JPN > Guru Master > Import (role_jpn.py). Boleh dijalankan berulang kali."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "role_jpn.py"
s = open(p, encoding="utf-8").read()
steps = [
    ("import", "from guru_import import", "from ppd_program import render_tetapan_program\n",
     "from ppd_program import render_tetapan_program\nfrom guru_import import render_templat_guru, semak_fail_guru\n"),
    ("butang templat", "render_templat_guru()", '                up_master = st.file_uploader("Upload MASTER 60K Excel"',
     '                render_templat_guru()\n                up_master = st.file_uploader("Upload MASTER 60K Excel"'),
    ("semakan fail", "semak_fail_guru(up_master)", "df_m = pd.read_excel(up_master, sheet_name=0)", "df_m = semak_fail_guru(up_master)"),
    ("no_pusat_asal bukan lagi BA142", '"no_pusat_asal": d.get("NO PUSAT ASAL", "")', '"no_pusat_asal": "BA142",', '"no_pusat_asal": d.get("NO PUSAT ASAL", ""),'),
]
for nama, tanda, lama, baru in steps:
    if tanda in s:
        print(f"  - {nama}: sudah ada"); continue
    if s.count(lama) != 1:
        sys.exit(f"RALAT: '{nama}' - jumpa {s.count(lama)} padanan (jangkaan 1).")
    s = s.replace(lama, baru, 1); print(f"  + {nama}")
open(p, "w", encoding="utf-8").write(s)
print("SIAP")
