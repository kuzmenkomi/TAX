# Security

## Reporting vulnerabilities

Email the maintainers privately; do not open public issues for security defects.

## Threat model (summary)

- **Assets**: user credentials, exchange API keys, tax positions, PII.
- **Adversaries**: credential stuffing, XSS, CSRF, SSRF to internal services, webhook forgery.
- **Controls**: httpOnly cookies + CSRF (staging/production), rate limits on auth, Stripe webhook signature verification, opaque API errors, Sentry PII scrubbing, production secret validation.

## Headers

Prefer configuring TLS and security headers at the reverse proxy (`nginx/nginx.conf`) and keep application headers consistent with the edge.

## Dependency updates

Run `pip-audit` / `npm audit` regularly; CI should block known-critical CVEs.
