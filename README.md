# Sistem Pelantikan Petugas SPM Selangor 2026 - SATU URL

Satu repo GitHub, satu deploy (Streamlit), satu Supabase. Fail utama (Main file path): **app.py**

Halaman utama memilih: **JPN Selangor** atau satu daripada 10 PPD
(Klang BA, Kuala Langat BB, Kuala Selangor BC, Hulu Langat BD, Hulu Selangor BE, Sabak Bernam BF,
Gombak BG, Petaling Perdana BH, Sepang BJ, Petaling Utama BK).

- Daerah: SUP (pilih sekolah, baca `guru_master`) dan PPD (baca `cadangan_sup`) - HANYA data daerah itu.
- JPN: semua daerah.
- Skop daerah disimpan PER SESI dan semua cache dikunci dengan skop, jadi pengguna Klang dan Gombak boleh guna URL
  yang sama serentak tanpa data bercampur.

## Pindah dari repo lama
1. Sandarkan repo lama. Padam `app_BA.py` ... `app_BK.py`, `app_JPN.py` (jika ada) dan `apply_patch.py`.
2. Salin SEMUA fail dalam zip ini ke akar repo (ganti `app.py` lama). Pastikan folder `.streamlit/` turut masuk.
3. Salin semula fail imej surat dari repo lama ke akar repo: `jata_negara_hd.png`, `tandatangan_pengarah_hd.png`.
4. Streamlit Cloud: satu app, Main file path = `app.py`. Padam app daerah/JPN yang lama.
5. Settings > Secrets:
   ```
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "kunci-anda"
   JPN_PASSWORD = "kata-laluan-kuat-jpn"          # menggantikan kata laluan lalai JPN
   DISABLE_MASTER_PASSWORD = "true"               # mematikan kata laluan induk 'a' (SUP/PPD/JPN) dan a-j (PPD)
   ```
6. Supabase > SQL Editor, jalankan sekali `zon_bilik_kebal.sql` (untuk menu Penempatan Zon).

## Surat: logo, tandatangan, muat turun, padam
- **JPN > Template Surat > "Logo & Tandatangan"**: muat naik logo dan tandatangan terus dalam sistem (disimpan dalam Supabase, jadual
  `surat_templates_jpn`). Tiada fail imej dalam repo diperlukan. Dalam templat HTML guna `{{LOGO}}` dan `{{TANDATANGAN}}`;
  `<img src="jata_negara_hd.png">` lama turut diganti automatik.
- **Panel "Semakan Sistem Surat"** (menu surat SUP/PPD/JPN): papar enjin PDF (xhtml2pdf/reportlab/pypdf), templat JPN yang ada, logo,
  tandatangan, ralat terakhir, dan butang "Uji jana 1 surat contoh" (dengan muat turun).
- **Padam Surat Janaan** (SUP, PPD, JPN): kosongkan no surat & status surat supaya surat boleh dijana semula. Penempatan pusat kekal.
  Matikan di produksi: `DISABLE_PADAM_SURAT = "true"` dalam Secrets.
- `requirements.txt` kini ada `pypdf` dan `pillow`; `packages.txt` (cairo) membantu pemasangan `xhtml2pdf` di Streamlit Cloud.

## Program: SPM, UBBM, UBBI (satu kod asas)
Pilih program dengan `PROGRAM` dalam Secrets / `/etc/spm-<PROGRAM>.env`: `SPM` (lalai), `UBBM` atau `UBBI`. Gunakan projek Supabase berasingan bagi setiap program.

| Program | Jawatan | Kuota satu pusat ikut bilik ujian |
|---|---|---|
| UBBM | Penyelia Kawasan, Ketua Pentaksir Pusat Ujian (KPPU), Pentaksir Pusat Ujian (PPU), Pengawas Calon | 1 bilik: 1 KPPU, 1 PPU, 4 Pengawas; 2 bilik: 1 KPPU, 3 PPU, 4 Pengawas; 3 bilik: 1 KPPU, 5 PPU, 8 Pengawas (maks 3 bilik) |
| UBBI | Penyelia Kawasan, Assesor, Interlocutor, Pengawas Calon | 1 bilik: 1 Assesor, 1 Interlocutor, 4 Pengawas; 2 bilik: 2 Assesor, 2 Interlocutor, 4 Pengawas (maks 2 bilik) |

- **Bilik ujian** pusat = lajur *jumlah_kelas* pusat (menu PPD > Pusat di PPD). Jika kosong, dianggar 1 bilik bagi setiap 20 calon (dihadkan kepada bilik maksimum).
- **JPN > Tetapan Program**: ubah kuota setiap bilik ujian tanpa mengubah kod (disimpan dalam Supabase).
- **SUP**: pilihan jawatan, kotak keperluan petugas (kuota pusat sekolah) dan kiraan cadangan mengikut program.
- **PPD**: Jana Keseluruhan dan Penempatan Zon mengikut kuota setiap jawatan; guru tidak ditempatkan di sekolah asal; dalam zon hanya guru & pusat dalam zon.
  Hasil Janaan: status Cukup hanya jika setiap jawatan penuh mengikut kuota.
- **Surat**: tajuk mengikut program. KADAR ELAUN UBBM/UBBI ialah teks sementara ("Mengikut kadar yang ditetapkan oleh Jabatan") - kemas kini `elaun_ikhtisas` dalam `program_config.py`
  atau guna templat JPN. Surat Penyelia Kawasan masih format SPM.
- **Belum disesuaikan untuk UBBM/UBBI**: Penempatan Manual, Jana auto SPM (diganti Jana program), label Dashboard PPD (istilah "Kelas"), surat Penyelia Kawasan.

## Guru Master: templat Excel
JPN > Guru Master > Import: butang **Muat Turun Templat Guru Master** (lajur tepat, panduan, contoh, senarai kod PPD; IC/telefon/poskod berformat teks).
Fail yang diupload disemak dahulu (IC 12 digit, KOD PPD sah, IC pendua, lajur wajib); hanya baris sah diimport dan laporan ralat boleh dimuat turun.

## Kemas kini terkini
- **Kata laluan dalam Supabase** (bukan dalam kod): jalankan `kata_laluan.sql`, isi `SUPABASE_SERVICE_KEY` dalam Secrets, kemudian JPN > menu **Kata Laluan**
  untuk tetapkan / jana pukal (disimpan sebagai hash PBKDF2). Akaun yang ada baris DB tidak lagi menerima kata laluan lama dalam kod.
  `AUTH_DB_ONLY=true` memaksa semua akaun guna pangkalan data. 5 percubaan salah = dikunci 5 minit.
- **Hasil Janaan (PPD)**: cache cadangan dikosongkan automatik selepas sebarang tulisan (hasil terus muncul); pusat lalai = pusat pertama yang ada hasil;
  mesej pusat kosong menunjukkan pusat yang sudah ada hasil; status **Cukup** hanya jika 1 KP, 1 TKP dan pengawas penuh (PERLU - 2).
- **Surat**: susun atur asas disamakan dengan surat lantikan sebenar (pengepala, Melalui, tajuk, elaun, tandatangan, bar kaki surat);
  logo & tandatangan daripada surat contoh dalam folder `assets/`.
- **VPS**: lihat `deploy/README_VPS.md` (tiada perubahan kod diperlukan).

## Struktur
| Fail | Fungsi |
|---|---|
| app.py, main_app.py | pintu masuk tunggal + halaman pilih JPN/daerah |
| daerah_app.py | pilih sekolah (SUP) + log masuk SUP/PPD satu daerah |
| jpn_app.py | log masuk JPN |
| role_sup.py / role_ppd.py / role_jpn.py | menu setiap peranan |
| ppd_cadangan.py | Senarai Nama Cadangan, Senarai Simpanan, tapis Jana, jadual Hasil Janaan |
| ppd_zon.py | Penempatan Zon (bilik kebal) |
| spm_core.py | fungsi kongsi (surat, PDF, loader, skop sesi, cache berskop) |
| scoped_db.py | penapis daerah automatik untuk semua bacaan Supabase |
| ui_theme.py, .streamlit/config.toml | susun atur, warna, kontras tulisan/jadual, butang putih |

## Nota
- Semua pengguna kini berkongsi satu pelayan: pantau penggunaan memori jika ramai pengguna serentak.
- Butang Refresh mengosongkan cache semua pengguna (bukan hanya sesi sendiri).
- Aliran PPD: Senarai Nama Cadangan (tick = TERPILIH, tidak tick = SIMPANAN) -> Penempatan Zon / Jana -> Hasil Janaan -> Surat.
