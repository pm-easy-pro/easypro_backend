# EasyPro Backend — Agent заавар

Production API: https://api.easypro.mn — **бодит өгөгдөл байна.**

## Дүрэм

- `.cursor/rules/production-data-safety.mdc` — flush, demo seed, bulk delete хориг
- `.cursor/rules/easypro-backend.mdc` — deploy, командууд

## Production skill

`.cursor/skills/easypro-production/SKILL.md` — migrate, backup, deploy дараалал

## Баримт

- [docs/PRODUCTION.md](docs/PRODUCTION.md)
- [DEPLOY.md](DEPLOY.md)

## Seed

| Command | Production |
|---------|------------|
| `seed_master_data` | Тийм (idempotent) |
| `seed_demo_data` | Үгүй (`DEBUG=False` → CommandError) |
