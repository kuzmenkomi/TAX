# ADR 001: Cookie-based auth with CSRF double-submit

## Status

Accepted

## Context

Bearer tokens in `localStorage` are vulnerable to XSS exfiltration.

## Decision

- Issue **httpOnly** `access_token` and `refresh_token` cookies on login/register/refresh.
- Use a readable `csrf_token` cookie plus `X-CSRF-Token` header for mutating requests in **production** and **staging** (`CsrfMiddleware`).
- Development skips CSRF enforcement for developer velocity.

## Consequences

- Frontend must use `credentials: "include"` and attach CSRF header from `document.cookie`.
- Cross-subdomain deployments require `COOKIE_DOMAIN` configuration.
