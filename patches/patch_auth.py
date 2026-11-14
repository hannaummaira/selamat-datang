# -*- coding: utf-8 -*-
"""patch_auth.py - tambah menu JPN "Kata Laluan" ke role_jpn.py (selamat dijalankan berulang kali). Jalankan: python patch_auth.py"""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "role_jpn.py"
s = open(p, encoding="utf-8").read()
steps = [
    ("import", "from auth_db import render_urus_kata_laluan",
     "from surat_tools import surat_panel, surat_aset_panel, surat_diagnostik\n",
     "from surat_tools import surat_panel, surat_aset_panel, surat_diagnostik\nfrom auth_db import render_urus_kata_laluan\n"),
    ("menu", "('kata_laluan', '🔑 Kata Laluan')",
     "('admin', '⚙️ Admin'), ('keluar', '🚪 Log Keluar')]",
     "('kata_laluan', '🔑 Kata Laluan'), ('admin', '⚙️ Admin'), ('keluar', '🚪 Log Keluar')]"),
    ("cabang", "render_urus_kata_laluan()\n",
     '        elif menu == "jpn_template_surat":\n',
     '        elif menu == "kata_laluan":\n            render_urus_kata_laluan()\n\n        elif menu == "jpn_template_surat":\n'),
]
for nama, tanda, lama, baru in steps:
    if tanda in s:
        print(f"  - {nama}: sudah ada"); continue
    if s.count(lama) != 1:
        sys.exit(f"RALAT: tiada tepat 1 padanan untuk '{nama}' (jumpa {s.count(lama)}). Semak fail secara manual.")
    s = s.replace(lama, baru, 1); print(f"  + {nama}")
open(p, "w", encoding="utf-8").write(s)
print("SIAP")
