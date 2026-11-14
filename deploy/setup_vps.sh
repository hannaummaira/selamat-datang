#!/usr/bin/env bash
# Pasang sistem SPM Selangor pada VPS Ubuntu 22.04 / 24.04.
# Guna:  sudo bash deploy/setup_vps.sh domain.anda.com emel@anda.com
# Prasyarat: kod sudah ada di /opt/spm (git clone repo privet) dan DNS A record domain -> IP VPS.
set -euo pipefail
DOMAIN="${1:?Nyatakan domain, cth: spm.contoh.com}"
EMAIL="${2:?Nyatakan emel untuk sijil HTTPS}"
APP_DIR=/opt/spm
APP_USER=spm

apt-get update
apt-get install -y python3-venv python3-pip build-essential libcairo2-dev pkg-config python3-dev nginx certbot python3-certbot-nginx ufw git

id -u "$APP_USER" >/dev/null 2>&1 || useradd -r -m -s /bin/bash "$APP_USER"
[ -f "$APP_DIR/app.py" ] || { echo "RALAT: $APP_DIR/app.py tiada. Clone repo ke $APP_DIR dahulu."; exit 1; }
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [ ! -f /etc/spm.env ]; then
  cp "$APP_DIR/deploy/spm.env.example" /etc/spm.env
  chmod 600 /etc/spm.env
  chown root:root /etc/spm.env
  echo ">> SUNTING /etc/spm.env (isi SUPABASE_URL, SUPABASE_KEY dan lain-lain) sebelum teruskan, kemudian: systemctl restart spm"
fi

cp "$APP_DIR/deploy/spm.service" /etc/systemd/system/spm.service
sed "s/__DOMAIN__/$DOMAIN/g" "$APP_DIR/deploy/nginx-spm.conf" > /etc/nginx/sites-available/spm
ln -sf /etc/nginx/sites-available/spm /etc/nginx/sites-enabled/spm
rm -f /etc/nginx/sites-enabled/default
nginx -t

systemctl daemon-reload
systemctl enable --now spm
systemctl reload nginx

ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

certbot --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos --no-eff-email --redirect -n
echo "SIAP: https://$DOMAIN   (log: journalctl -u spm -f)"
