# Secret management

## Production

- Do **not** commit `.env` files with production secrets.
- Use a secret manager (AWS Secrets Manager, GCP Secret Manager, Doppler, Vault) and inject env vars at deploy time.
- Rotate `JWT_SECRET_KEY` and encryption keys on a schedule; document runbooks under `docs/runbooks/`.

## Required variables (production)

- `JWT_SECRET_KEY` — strong random string, not in the insecure list enforced by `app.core.config`.
- `ENCRYPTION_KEY` / `ENCRYPTION_KEYS` — at least one Fernet-compatible key.
- `DATABASE_URL` — PostgreSQL only.
- `REDIS_PASSWORD` — required when using Redis workers.
- `STRIPE_WEBHOOK_SECRET` — required when `STRIPE_SECRET_KEY` is set.
