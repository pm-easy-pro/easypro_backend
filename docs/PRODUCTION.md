# EasyPro — Production ба өгөгдлийн бодлого

> **Статус:** Production ажиллаж эхэлсэн. Бодит хэрэглэгч, зар, медиа, subscription өгөгдөл хадгалагдана.

## Зорилго

Код шинэчлэх, migration хийх, master data нэмэх үед **одоо байгаа өгөгдлийг устгахгүй**, санамсаргүй demo seed ажиллуулахгүй байх.

## Орчин

| Комponent | Production |
|-----------|------------|
| API | https://api.easypro.mn |
| Web | https://easypro.mn |
| Database | MySQL (`DB_ENGINE=mysql`) |
| Backend deploy | Ubuntu + Gunicorn + Nginx — [DEPLOY.md](../DEPLOY.md) |
| Frontend | Vercel, `NEXT_PUBLIC_API_URL=https://api.easypro.mn/api` |

## Зөвшөөрөгдсөн үйлдлүүд

1. **Код deploy** — `git pull`, `pip install`, `collectstatic`, Gunicorn restart.
2. **`python manage.py migrate`** — шинэ schema; deploy-ийн өмнө **backup** авна.
3. **`python manage.py seed_master_data`** — байршил, хороо, subscription багцыг `update_or_create`-ээр шинэчилнэ (идempotent).
4. **`createsuperuser`** — шинэ админ нэмэх.

## Хориглосон / маш болгоомжтой

| Үйлдэл | Яагаад |
|--------|--------|
| `flush` | Бүх хүснэгт цэвэрлэнэ |
| `seed_demo_data` | Demo хэрэглэгч + зар; prod-д **blocked** (`DEBUG=False`) |
| DB drop / truncate | Буцаах боломжгүй |
| Migration history гараар засах | Inconsistent state |

## Deploy checklist (backend)

- [ ] MySQL backup
- [ ] `.env` production утгууд сервер дээр л байна
- [ ] `migrate` → `collectstatic` → Gunicorn restart
- [ ] Smoke test: `/api/properties/`, OTP нэвтрэлт

## Cursor

- `.cursor/rules/production-data-safety.mdc`
- `AGENTS.md` (repo root)
