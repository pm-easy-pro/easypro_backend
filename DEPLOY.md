# EasyPro Backend — Ubuntu + Gunicorn (Unix Socket) + Nginx

Production API: **https://api.easypro.mn**  
Кодын байршил: **/home/ubuntu/easypro_backend**

---

## 1. Урьдчилсан шаардлага

- Ubuntu 22.04 / 24.04 LTS
- `api.easypro.mn` DNS A record → серверийн public IP
- SSH хандалт (`ubuntu` хэрэглэгч)
- MySQL (production) / SQLite (local dev)

---

## 2. Системийн багц суулгах

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  python3 python3-pip python3-venv \
  mysql-server \
  nginx \
  certbot python3-certbot-nginx \
  git pkg-config
```

---

## 3. MySQL тохируулах

```bash
sudo mysql
```

```sql
CREATE DATABASE easypro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'easypro'@'localhost' IDENTIFIED BY 'YOUR_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON easypro.* TO 'easypro'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Managed MySQL (DigitalOcean, RDS гэх мэт) ашиглаж байвал зөвхөн `.env` дээр host/user/password тохируулна.

---

## 4. Код татах

```bash
cd /home/ubuntu

# GitHub-аас (жишээ)
git clone https://github.com/pm-easy-pro/easypro_backend.git easypro_backend

cd /home/ubuntu/easypro_backend
```

---

## 5. Python virtual environment

```bash
cd /home/ubuntu/easypro_backend

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

> **Зөвлөмж:** `gunicorn`-ийг `requirements.txt` дээр нэмж commit хий.

---

## 6. Production `.env`

```bash
cp .env.example .env
nano .env
```

Жишээ production утгууд:

```env
DJANGO_SECRET_KEY=generate-a-long-random-string-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api.easypro.mn,127.0.0.1

DB_ENGINE=mysql
MYSQL_DB=easypro
MYSQL_USER=easypro
MYSQL_PASSWORD=YOUR_STRONG_PASSWORD
MYSQL_HOST=localhost
MYSQL_PORT=3306

CORS_ALLOWED_ORIGINS=https://easypro.mn,https://www.easypro.mn

# DigitalOcean Spaces (зураг CDN) — хоосон үлдвэл /home/ubuntu/easypro_backend/media/ ашиглана
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_LOCATION=easypro
AWS_DEFAULT_ACL=public-read
AWS_S3_ENDPOINT_URL=https://sgp1.digitaloceanspaces.com
AWS_S3_CUSTOM_DOMAIN=
AWS_S3_REGION_NAME=sgp1

# CallPro SMS
CALLPRO_SMS_API_URL=https://api-text.callpro.mn/v1/sms/send
CALLPRO_SMS_API_KEY=your-callpro-key
CALLPRO_SMS_FROM=72727040
OTP_DEBUG=false
```

Secret key үүсгэх:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 7. Django migration & static

```bash
cd /home/ubuntu/easypro_backend
source venv/bin/activate

python manage.py migrate
python manage.py seed_master_data
python manage.py collectstatic --noinput

# Анхны админ (сонголттой)
python manage.py createsuperuser

# Demo өгөгдөл (сонголттой, production-д ихэвчлэн хэрэггүй)
# python manage.py seed_demo_data
```

---

## 8. Gunicorn — Unix socket

Socket файл: `/run/easypro/gunicorn.sock`

### 8.1 Gunicorn config (сонголттой, зөвлөмж)

```bash
nano /home/ubuntu/easypro_backend/gunicorn.conf.py
```

```python
import multiprocessing

bind = "unix:/run/easypro/gunicorn.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

umask = 0o007
```

### 8.2 systemd service

```bash
sudo nano /etc/systemd/system/easypro-gunicorn.service
```

```ini
[Unit]
Description=EasyPro Gunicorn (api.easypro.mn)
After=network.target mysql.service
Requires=mysql.service

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/easypro_backend
EnvironmentFile=/home/ubuntu/easypro_backend/.env

RuntimeDirectory=easypro
RuntimeDirectoryMode=0755

ExecStart=/home/ubuntu/easypro_backend/venv/bin/gunicorn \
    --config /home/ubuntu/easypro_backend/gunicorn.conf.py \
    config.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

`Group=www-data` + `umask=0o007` нь Nginx (`www-data`) socket-д хандах боломжийг олгоно.

### 8.3 Service асаах

```bash
sudo systemctl daemon-reload
sudo systemctl enable easypro-gunicorn
sudo systemctl start easypro-gunicorn
sudo systemctl status easypro-gunicorn
```

Socket шалгах:

```bash
ls -la /run/easypro/gunicorn.sock
# drwxr-s--- ubuntu www-data ... gunicorn.sock
```

---

## 9. Nginx reverse proxy

```bash
sudo nano /etc/nginx/sites-available/api.easypro.mn
```

```nginx
upstream easypro_backend {
    server unix:/run/easypro/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name api.easypro.mn;

    client_max_body_size 20M;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_pass http://easypro_backend;
    }

    # Django admin CSS/JS (collectstatic хийсний дараа)
    location /static/ {
        alias /home/ubuntu/easypro_backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Spaces ашиглахгүй бол локал media serve хийнэ
    location /media/ {
        alias /home/ubuntu/easypro_backend/media/;
        expires 30d;
        add_header Cache-Control "public";
    }
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/api.easypro.mn /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 10. SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d api.easypro.mn
```

Certbot Nginx config-ийг HTTPS руу автоматаар шинэчилнэ. Дахин шалгах:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 11. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Gunicorn socket нь зөвхөн локал (`/run/easypro/`) тул гаднаас шууд нээгдэхгүй — зөв тохиргоо.

---

## 12. Frontend (Vercel) холбох

Vercel project → **Environment Variables**:

```
NEXT_PUBLIC_API_URL=https://api.easypro.mn/api
```

Backend `.env` дээр frontend domain CORS-д байгаа эсэхийг шалга:

```
CORS_ALLOWED_ORIGINS=https://easypro.mn,https://www.easypro.mn
```

---

## 13. Шалгалт

```bash
# Gunicorn log
sudo journalctl -u easypro-gunicorn -f

# Nginx log
sudo tail -f /var/log/nginx/error.log

# API health check
curl -I https://api.easypro.mn/api/filter-options/
curl https://api.easypro.mn/api/properties/
```

Амжилттай бол JSON хариу ирнэ.

Admin panel: **https://api.easypro.mn/admin/**

---

## 14. Шинэ хувилбар deploy (update)

```bash
cd /home/ubuntu/easypro_backend
source venv/bin/activate

git pull origin main
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_master_data
python manage.py collectstatic --noinput

sudo systemctl restart easypro-gunicorn
sudo systemctl status easypro-gunicorn
```

---

## 15. Түгээмэл асуудал

| Асуудал | Шийдэл |
|--------|--------|
| `502 Bad Gateway` | `sudo systemctl status easypro-gunicorn` — socket байгаа эсэх шалга |
| `Permission denied` on socket | Service дээр `Group=www-data`, gunicorn config дээр `umask=0o007` |
| `DisallowedHost` | `.env` → `DJANGO_ALLOWED_HOSTS=api.easypro.mn` |
| CORS алдаа | `.env` → `CORS_ALLOWED_ORIGINS` дээр frontend URL нэм |
| Static/admin CSS алдаа | `python manage.py collectstatic --noinput` дахин ажиллуул |
| DB холбогдохгүй | MySQL ажиллаж байгаа эсэх, `DB_ENGINE=mysql`, `MYSQL_*` credential шалга |

---

## 16. Файлуудын хураангуй

| Файл | Зориулалт |
|------|-----------|
| `/home/ubuntu/easypro_backend/.env` | Production нууц тохиргоо |
| `/home/ubuntu/easypro_backend/gunicorn.conf.py` | Gunicorn тохиргоо |
| `/etc/systemd/system/easypro-gunicorn.service` | Gunicorn systemd service |
| `/run/easypro/gunicorn.sock` | Unix socket (Gunicorn ↔ Nginx) |
| `/etc/nginx/sites-available/api.easypro.mn` | Nginx virtual host |
