# Pasang di VPS (Ubuntu 22.04 / 24.04)

**Kod sistem TIDAK perlu diubah.** Tetapan (Supabase, kata laluan) dibaca daripada pembolehubah persekitaran jika tiada `secrets.toml`.
Supabase kekal di awan; VPS hanya menjalankan aplikasi.

## Langkah
1. Beli VPS (disyorkan: 2 vCPU, 4 GB RAM, Ubuntu 24.04; pilih lokasi Singapura - dekat Supabase) dan sebuah domain; arahkan DNS **A record** ke IP VPS.
2. SSH ke VPS, clone repo privet (guna *deploy key* atau token GitHub): `sudo git clone <repo> /opt/spm`
3. `sudo bash /opt/spm/deploy/setup_vps.sh domain.anda.com emel@anda.com`
4. `sudo nano /etc/spm.env` - isi SUPABASE_URL, SUPABASE_KEY dan tetapan lain (lihat `spm.env.example`), kemudian `sudo systemctl restart spm`
5. Buka `https://domain.anda.com`.

## Kemas kini kod
`cd /opt/spm && sudo -u spm git pull && sudo -u spm venv/bin/pip install -r requirements.txt && sudo systemctl restart spm`

## Semak masalah
- Log aplikasi: `journalctl -u spm -f`  |  status: `systemctl status spm`  |  nginx: `nginx -t`
- Halaman kosong / "Please wait": WebSocket dihalang - pastikan `nginx-spm.conf` (Upgrade/Connection) digunakan.

## Perlu diingat (tanggungjawab anda di VPS)
- Kemas kini sistem (`apt upgrade`), matikan log masuk SSH dengan kata laluan (guna kunci SSH), simpan sandaran (data di Supabase).
- Semua pengguna berkongsi satu proses Streamlit: 2 vCPU / 4 GB cukup untuk puluhan pengguna serentak; jana PDF pukal agak berat CPU.
- Ketetapan wajib di `/etc/spm.env`: `JPN_PASSWORD`, `DISABLE_MASTER_PASSWORD=true`; pertimbang `SUPABASE_SERVICE_KEY` + `kata_laluan.sql`.

## Tiga program (SPM, UBBM, UBBI) pada satu VPS
Satu kod, tiga sistem berasingan. Setiap program: domain sendiri, port sendiri, tetapan `PROGRAM` sendiri dan projek Supabase sendiri.
- `sudo bash deploy/tambah_program.sh UBBI ubbi.domain.anda.com 8502 emel@anda.com`
- `sudo bash deploy/tambah_program.sh UBBM ubbm.domain.anda.com 8503 emel@anda.com`
- Sunting `/etc/spm-UBBI.env` dan `/etc/spm-UBBM.env` (SUPABASE_URL, SUPABASE_KEY, kata laluan), kemudian `sudo systemctl restart spm@UBBI spm@UBBM`.
- Kemas kini kod sekali (`git pull`) dan mulakan semula ketiga-tiga servis: `sudo systemctl restart 'spm@*'`.
- Streamlit Cloud: tetapkan `PROGRAM = "UBBI"` dalam Secrets setiap app (satu app bagi setiap program).
