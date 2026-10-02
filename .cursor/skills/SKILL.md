---
name: easypro-production
description: >-
  Operates EasyPro in production without destroying live data. Covers deploy,
  migrate, seed_master_data vs seed_demo_data, MySQL backup, Gunicorn/Nginx,
  Vercel env. Use when user mentions production, api.easypro.mn, live data,
  deploy, migration on server, or asks not to delete data.
---

# EasyPro production

## Golden rule

**Live DB has real listings and users.** Default to non-destructive changes. Never run `flush`, bulk deletes, or `seed_demo_data` on production unless the user explicitly requests it in writing and accepts risk.

## Before any server DB work

1. Confirm environment: `DJANGO_DEBUG=False`, `DB_ENGINE=mysql`, host is production.
2. Prefer DB backup/snapshot (see [reference.md](reference.md)).
3. Use forward-only `migrate` — no manual table drops.

## Safe deploy sequence (backend)

On `/home/ubuntu/easypro_backend` (see `easypro_backend/DEPLOY.md`):

```bash
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart easypro-gunicorn   # or your unit name
```

Optional after migrate (idempotent):

```bash
python manage.py seed_master_data
```

## Seed commands

| Command | Production |
|---------|------------|
| `seed_master_data` | Yes — locations/packages upsert only |
| `seed_demo_data` | **No** — blocked when `DEBUG=False` unless `--force` |

## Frontend (Vercel)

- Set `NEXT_PUBLIC_API_URL=https://api.easypro.mn/api`
- Redeploy after env change

## When schema changes

1. Create migration locally; test on SQLite.
2. Deploy code + `migrate` on MySQL.
3. If migration rewrites large tables, plan maintenance window + backup.

## If user asks to "reset" or "clean" data

1. Ask which environment (local vs production).
2. On production: refuse wipe; offer export, soft-delete features, or staging DB.
3. On local: SQLite file delete or fresh venv DB is OK; still avoid suggesting prod commands.

## More detail

- [reference.md](reference.md) — URLs, portals, backup notes, forbidden commands
