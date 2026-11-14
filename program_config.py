# -*- coding: utf-8 -*-
"""
program_config.py - Satu kod asas, tiga program: SPM / UBBM / UBBI.

Program dipilih dengan tetapan PROGRAM (Secrets / pembolehubah persekitaran), lalai SPM:
    PROGRAM = "UBBI"      # atau "UBBM" atau "SPM"

Kuota UBBM/UBBI ikut bilangan BILIK UJIAN dalam satu pusat (daripada JPN; boleh diubah dalam menu JPN > Tetapan Program):
  UBBM : 1 bilik = 1 KPPU, 1 PPU, 4 Pengawas | 2 bilik = 1 KPPU, 3 PPU, 4 Pengawas | 3 bilik = 1 KPPU, 5 PPU, 8 Pengawas  (maks 3 bilik)
  UBBI : 1 bilik = 1 Assesor, 1 Interlocutor, 4 Pengawas | 2 bilik = 2 Assesor, 2 Interlocutor, 4 Pengawas              (maks 2 bilik)
Bilangan bilik ujian = lajur "jumlah_kelas" pusat (dipaparkan sebagai Bilik Ujian). Jika kosong, dianggar daripada jumlah calon
(1 bilik setiap 20 calon, dihadkan kepada bilik maksimum).
SPM: tingkah laku asal TIDAK berubah (KP 1, TKP 1, pengawas = keperluan pusat - 2).
"""
import json
import math
import re

import spm_core as core

_SPM_PILIHAN = ["Ketua Pengawas", "Timbalan Ketua Pengawas", "Penyelia Kawasan", "Pengawas Peperiksaan", "Juru Tulis", "Juru Baca",
                "Ketua Pengawas Hospital", "Pengawas Hospital", "Pengawas Pengiring", "Pengemas Bilik"]
_SPM_BETUL = ["Ketua Pengawas (WAJIB 1)", "Timbalan Ketua Pengawas (WAJIB 1)", "Penyelia Kawasan (Optional)", "Pengawas Peperiksaan (Ikut Kelas)",
              "Juru Tulis", "Juru Baca", "Ketua Pengawas Hospital", "Pengawas Hospital", "Pengawas Pengiring", "Pengemas Bilik"]

PROGRAMS = {
    "SPM": {
        "kod": "SPM", "singkatan": "SPM", "nama_sistem": "Sistem Pelantikan Petugas SPM Selangor 2026",
        "nama_ujian": "SIJIL PELAJARAN MALAYSIA (SPM) 2026", "pengalaman": "Pengalaman SPM (Tahun)",
        "ujian_kata": "peperiksaan", "elaun_ikhtisas": "RM 281.25 + S (S = Bil. Sesi)",
        "jawatan_pilihan": _SPM_PILIHAN, "jawatan_betul": _SPM_BETUL, "pk": "Penyelia Kawasan",
        "roles": [("KP", "KP", "KP"), ("TKP", "TKP", "TKP"), ("PENGAWAS", "Pengawas", "PENGAWAS")],   # (kunci, nama mesej, lajur jadual)
        "maks_bilik": 0, "kuota_lalai": {},
    },
    "UBBM": {
        "kod": "UBBM", "singkatan": "UBBM", "nama_sistem": "Sistem Pelantikan Petugas UBBM Selangor 2026",
        "nama_ujian": "UJIAN BERTUTUR BAHASA MELAYU (UBBM) 2026", "pengalaman": "Pengalaman UBBM (Tahun)",
        "ujian_kata": "ujian", "elaun_ikhtisas": "Mengikut kadar yang ditetapkan oleh Jabatan",   # KEMAS KINI kadar sebenar UBBM
        "jawatan_pilihan": ["Penyelia Kawasan", "Ketua Pentaksir Pusat Ujian", "Pentaksir Pusat Ujian", "Pengawas Calon"],
        "jawatan_betul": ["Penyelia Kawasan (Optional)", "Ketua Pentaksir Pusat Ujian (KPPU)", "Pentaksir Pusat Ujian (PPU)", "Pengawas Calon (Ikut Kuota)"],
        "pk": "Penyelia Kawasan",
        "roles": [("KPPU", "KPPU", "KPPU"), ("PPU", "PPU", "PPU"), ("PENGAWAS_CALON", "Pengawas Calon", "PENGAWAS CALON")],
        "maks_bilik": 3,
        "kuota_lalai": {1: {"KPPU": 1, "PPU": 1, "PENGAWAS_CALON": 4},
                        2: {"KPPU": 1, "PPU": 3, "PENGAWAS_CALON": 4},
                        3: {"KPPU": 1, "PPU": 5, "PENGAWAS_CALON": 8}},
    },
    "UBBI": {
        "kod": "UBBI", "singkatan": "UBBI", "nama_sistem": "Sistem Pelantikan Petugas UBBI Selangor 2026",
        "nama_ujian": "UJIAN BERTUTUR BAHASA INGGERIS (UBBI) 2026", "pengalaman": "Pengalaman UBBI (Tahun)",
        "ujian_kata": "ujian", "elaun_ikhtisas": "Mengikut kadar yang ditetapkan oleh Jabatan",   # KEMAS KINI kadar sebenar UBBI
        "jawatan_pilihan": ["Penyelia Kawasan", "Assesor", "Interlocutor", "Pengawas Calon"],
        "jawatan_betul": ["Penyelia Kawasan (Optional)", "Assesor (Ikut Kuota)", "Interlocutor (Ikut Kuota)", "Pengawas Calon (Ikut Kuota)"],
        "pk": "Penyelia Kawasan",
        "roles": [("ASESOR", "Assesor", "ASSESOR"), ("INTERLOCUTOR", "Interlocutor", "INTERLOCUTOR"), ("PENGAWAS_CALON", "Pengawas Calon", "PENGAWAS CALON")],
        "maks_bilik": 2,
        "kuota_lalai": {1: {"ASESOR": 1, "INTERLOCUTOR": 1, "PENGAWAS_CALON": 4},
                        2: {"ASESOR": 2, "INTERLOCUTOR": 2, "PENGAWAS_CALON": 4}},
    },
}
RESERVED_KEY = "__TETAPAN_PROGRAM__"


def program_kod():
    k = str(core._secret("PROGRAM", "SPM")).strip().upper()
    return k if k in PROGRAMS else "SPM"


def cfg(kod=None):
    return PROGRAMS[kod or program_kod()]


def adalah_spm():
    return program_kod() == "SPM"


def nama_sistem():
    return cfg()["nama_sistem"]


def jawatan_pilihan():
    return list(cfg()["jawatan_pilihan"])


def jawatan_betul():
    return list(cfg()["jawatan_betul"])


def roles(kod=None):
    return list(cfg(kod)["roles"])


def role_of(jawatan, kod=None):
    """Peranan kuota ('KP','TKP','PENGAWAS' | 'KPPU','PPU','ASESOR','INTERLOCUTOR','PENGAWAS_CALON'), 'PK' (penyelia) atau 'LAIN'."""
    kod = kod or program_kod()
    j = re.sub(r"\s+", " ", str(jawatan or "").upper()).strip()
    if kod == "SPM":                                         # tingkah laku asal - tidak diubah
        if "TIMBALAN" in j:
            return "TKP"
        if "KETUA PENGAWAS" in j:
            return "KP"
        if "PENGAWAS" in j:
            return "PENGAWAS"
        return "LAIN"
    if "PENYELIA" in j:
        return "PK"
    if kod == "UBBM":
        if "KETUA PENTAKSIR" in j or re.search(r"\bKPPU\b", j):
            return "KPPU"
        if "PENTAKSIR" in j or re.search(r"\bPPU\b", j):
            return "PPU"
    if kod == "UBBI":
        if any(x in j for x in ("ASESOR", "ASSESOR", "ASSESSOR")):
            return "ASESOR"
        if "INTERLOCUTOR" in j or "INTERLOKUTOR" in j:
            return "INTERLOCUTOR"
    if "PENGAWAS CALON" in j or j == "PENGAWAS":
        return "PENGAWAS_CALON"
    return "LAIN"


def urutan_jawatan(kod=None):
    return [j.upper() for j in cfg(kod)["jawatan_pilihan"]]


# ------------------------------------------------------------------ kuota
def _muat_semua():
    try:
        res = core.get_supabase().table("surat_templates_jpn").select("template_html").eq("jawatan", RESERVED_KEY).limit(1).execute()
        return json.loads(((res.data or [{}])[0].get("template_html")) or "{}")
    except Exception:
        return {}


def tetapan(kod=None):
    """Jadual kuota semasa {bilik:int -> {role_key: n}} = lalai program + pindaan JPN (Supabase). Kosong bagi SPM."""
    kod = kod or program_kod()
    out = {int(b): dict(v) for b, v in cfg(kod)["kuota_lalai"].items()}
    for b, v in (_muat_semua().get(kod) or {}).items():
        try:
            b = int(b)
        except Exception:
            continue
        if b in out and isinstance(v, dict):
            for rk, n in v.items():
                if rk in out[b] and str(n).lstrip("-").isdigit():
                    out[b][rk] = max(0, int(n))
    return out


def simpan_tetapan(jadual, kod=None):
    """jadual: {bilik: {role_key: n}}. Pulang (ok, mesej)."""
    kod = kod or program_kod()
    try:
        semua = _muat_semua()
        semua[kod] = {str(b): v for b, v in jadual.items()}
        core.get_supabase().table("surat_templates_jpn").delete().eq("jawatan", RESERVED_KEY).execute()
        core.get_supabase().table("surat_templates_jpn").insert({"jawatan": RESERVED_KEY, "template_html": json.dumps(semua)}).execute()
        return True, ""
    except Exception as e:
        return False, str(e)[:160]


def bilik_ujian(kelas=0, calon=0, kod=None):
    """Bilangan bilik ujian sesebuah pusat (UB): lajur jumlah_kelas; jika kosong dianggar 1 bilik/20 calon; dihadkan kepada bilik maksimum."""
    kod = kod or program_kod()
    mk = int(cfg(kod).get("maks_bilik", 0) or 0)
    n = int(kelas or 0)
    if n <= 0 and int(calon or 0) > 0:
        n = math.ceil(int(calon) / 20)
    return min(n, mk) if mk else n


def kuota_roles(bilik=None, calon=None, petugas=None, kod=None, jadual=None):
    """Kuota setiap peranan bagi SATU pusat -> {role_key: n}.
    SPM : petugas = keperluan pusat (kelas+9) -> KP 1, TKP 1, PENGAWAS = petugas - 2.
    UB  : ikut jadual bilik ujian; bilik 0 / tiada dalam jadual -> semua 0."""
    kod = kod or program_kod()
    if kod == "SPM":
        p = int(petugas or 0)
        if p <= 0:
            return {"KP": 0, "TKP": 0, "PENGAWAS": 0}
        return {"KP": 1, "TKP": 1, "PENGAWAS": max(0, p - 2)}
    n = bilik_ujian(bilik, calon, kod)
    jadual = jadual if jadual is not None else tetapan(kod)
    row = jadual.get(n) or {}
    return {key: int(row.get(key, 0)) for key, _n, _k in roles(kod)}


def status_kuota(counts, kuota, jumlah):
    """Status satu pusat mengikut peranan. counts/kuota: {role_key: n}. Pulang (status, catatan).
    'Cukup' HANYA jika setiap peranan penuh mengikut kuota. Label sama seperti Dashboard."""
    nama = {k: n for k, n, _ in roles()}
    if sum(kuota.values()) <= 0:
        return ("🔴 Belum Ada", "Kuota pusat belum ditetapkan") if jumlah == 0 else ("🟡 Belum Cukup", "Kuota pusat belum ditetapkan (isi bilik ujian / calon pusat)")
    if jumlah == 0:
        return "🔴 Belum Ada", "Perlu " + ", ".join(f"{kuota[k]} {nama[k]}" for k in kuota if kuota[k] > 0)
    kurang = [f"{kuota[k] - counts.get(k, 0)} {nama[k]}" for k in kuota if counts.get(k, 0) < kuota[k]]
    lebih = [f"{counts.get(k, 0) - kuota[k]} {nama[k]}" for k in kuota if counts.get(k, 0) > kuota[k]]
    if kurang:
        return "🟡 Belum Cukup", "Kurang: " + ", ".join(kurang) + ((" | Lebih: " + ", ".join(lebih)) if lebih else "")
    return "🟢 Cukup", "Kuota penuh" + ((" | Lebih: " + ", ".join(lebih)) if lebih else "")


def tajuk_surat(jawatan):
    """(baris1, baris2) tajuk perkara surat."""
    c = cfg()
    j = str(jawatan or "").upper()
    if c["kod"] == "SPM":
        return "SIJIL PELAJARAN MALAYSIA (SPM) 2026 :", f"PELANTIKAN {j} SPM BERTULIS 2026"
    return f"{c['nama_ujian']} :", f"PELANTIKAN {j} {c['singkatan']} 2026"
