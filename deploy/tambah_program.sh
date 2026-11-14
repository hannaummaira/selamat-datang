#!/usr/bin/env bash
# Tambah satu program (SPM / UBBM / UBBI) pada VPS yang sudah dipasang dengan setup_vps.sh.
# Guna:  sudo bash deploy/tambah_program.sh UBBI ubbi.domain.anda.com 8502 emel@anda.com
# Setiap program: domain sendiri, port sendiri, fail /etc/spm-<PROGRAM>.env sendiri (guna projek Supabase BERASINGAN).
set -euo pipefail
PROG="${1:?Program: SPM, UBBM atau UBBI}"; DOMAIN="${2:?Domain}"; PORT="${3:?Port, cth 8502}"; EMAIL="${4:?Emel}"
case "$PROG" in SPM|UBBM|UBBI) ;; *) echo "Program mesti SPM, UBBM atau UBBI"; exit 1;; esac
APP_DIR=/opt/spm
ENVF="/etc/spm-$PROG.env"
if [ ! -f "$ENVF" ]; then
  cp "$APP_DIR/deploy/spm.env.example" "$ENVF"
  printf '\nPROGRAM=%s\nPORT=%s\n' "$PROG" "$PORT" >> "$ENVF"
  chmod 600 "$ENVF"
  echo ">> SUNTING $ENVF (isi SUPABASE_URL / SUPABASE_KEY projek Supabase untuk $PROG), kemudian: systemctl restart spm@$PROG"
fi
cp "$APP_DIR/deploy/spm@.service" /etc/systemd/system/spm@.service
sed -e "s/__DOMAIN__/$DOMAIN/g" -e "s/127.0.0.1:8501/127.0.0.1:$PORT/g" "$APP_DIR/deploy/nginx-spm.conf" > "/etc/nginx/sites-available/spm-$PROG"
ln -sf "/etc/nginx/sites-available/spm-$PROG" "/etc/nginx/sites-enabled/spm-$PROG"
nginx -t
systemctl daemon-reload
systemctl enable --now "spm@$PROG"
systemctl reload nginx
certbot --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos --no-eff-email --redirect -n
echo "SIAP: https://$DOMAIN  (log: journalctl -u spm@$PROG -f)"
