# Sentry validation

Use this runbook to prove that release-time errors reach Sentry before production rollout.

## Inputs

- `.env.staging` or `.env.production` with a real `SENTRY_DSN`
- Access to the target Sentry project
- Backend image or local backend virtualenv with dependencies installed

## 1. Validate the env file first

```bash
python scripts/release_preflight.py --env-file .env.staging --expected-env staging --require-sentry
```

Pass criteria:

- `SENTRY_DSN` is present
- no placeholder secrets remain in the release env file

## 2. Send a controlled backend event

Run this from the repo root on the same machine or container that will run the backend:

```bash
python scripts/sentry_smoke.py --env-file .env.staging --component backend --mode message
python scripts/sentry_smoke.py --env-file .env.staging --component backend --mode exception
```

Pass criteria:

- both commands exit `0`
- both events appear in the expected Sentry project
- tags show the expected `app_env`, `component`, and `git_revision`

## 3. Send a worker event

Run the same smoke script from the worker runtime or inside the worker container:

```bash
docker compose --env-file .env.staging exec worker python /app/scripts/sentry_smoke.py --env-file /app/.env.staging --component worker --mode exception
```

Pass criteria:

- the worker event arrives in Sentry
- event metadata clearly identifies the worker component

## 4. Frontend note

This repo currently wires Sentry on the backend side. If browser-side Sentry is part of the release requirement,
add and validate frontend instrumentation separately before calling observability complete.

## 5. Exit criteria

Sentry validation is complete only when:

- backend delivery is confirmed
- worker delivery is confirmed
- the release owner knows where to watch errors during rollout
