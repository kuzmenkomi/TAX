# Compliance notes (GDPR / LGPD)

## Data subject rights

- **Deletion**: `DELETE /api/v1/auth/me` removes the user and associated rows (see `auth_service.delete_user_data`).
- **Export**: `GET /api/v1/auth/export-summary` returns a minimal summary; extend with ZIP/CSV of transactions and profile data for full DSAR.

## Retention

Define retention periods per data class (raw exchange payloads vs derived tax reports) and implement TTL jobs (planned).

## Processors

Maintain a list of sub-processors (hosting, email, Sentry, Stripe) in your privacy policy.
