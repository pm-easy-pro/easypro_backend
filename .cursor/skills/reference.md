# EasyPro production reference

## Public URLs

- Frontend: https://easypro.mn (and www)
- API: https://api.easypro.mn/api/
- Django admin: https://api.easypro.mn/admin/ (if enabled)

## Repos / paths

- Backend on server: `/home/ubuntu/easypro_backend`
- Separate git repos: `easypro_backend`, `easypro_frontend` under workspace `easypro/`

## Environment flags

| Variable | Production typical |
|----------|-------------------|
| `DJANGO_DEBUG` | `False` |
| `DB_ENGINE` | `mysql` |
| `DJANGO_ALLOWED_HOSTS` | includes `api.easypro.mn` |
| `CORS_ALLOWED_ORIGINS` | `https://easypro.mn`, `https://www.easypro.mn` |
| `OTP_DEBUG` | `false` |

## MySQL backup (example)

```bash
mysqldump -u easypro -p easypro > easypro_backup_$(date +%Y%m%d_%H%M).sql
```

Store off-server. Test restore on staging before relying on it.

## Forbidden on production (unless explicit user + backup)

```bash
python manage.py flush
python manage.py seed_demo_data          # use --force only if user insists after warning
python manage.py sqlflush
# Raw SQL: DROP, TRUNCATE, DELETE FROM without WHERE
```

## Allowed maintenance

- `createsuperuser` — new staff account
- `seed_master_data --skip-locations` — packages only
- Media: Spaces CDN or server `media/` — do not delete bucket without inventory

## Rollback strategy

1. Redeploy previous git tag/commit on backend + frontend.
2. If migration already applied: restore DB from backup **or** ship forward-fix migration — never delete migration rows from `django_migrations` on prod without DBA plan.

## Cursor project assets

- Rules: `.cursor/rules/production-data-safety.mdc`, `easypro-project.mdc`
- Human doc: `docs/PRODUCTION.md`
- Agent entry: `AGENTS.md`
