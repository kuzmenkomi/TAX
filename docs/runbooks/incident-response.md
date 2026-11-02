# Incident response

1. **Triage** — identify blast radius (auth, billing, data integrity).
2. **Contain** — revoke sessions if credential leak suspected (`_revoked_tokens` is in-memory; prefer Redis denylist in production).
3. **Communicate** — status page / user email per policy.
4. **Eradicate** — patch root cause, rotate keys if needed.
5. **Recover** — restore from backup if data corruption.
6. **Review** — postmortem within 5 business days.

## Logs

- Correlate via `X-Request-ID` from API responses.
- Sentry environment matches `APP_ENV`.
