from __future__ import annotations

import base64
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

INSECURE_JWT_SECRETS = {
    "",
    "change-me-before-production",
    "dev-secret-key-change-in-production",
    "CHANGE_ME_IN_ENV_FOR_DEV_ONLY",
    "replace-with-a-random-secret",
}

PLACEHOLDER_MARKERS = (
    "CHANGE_ME",
    "YOUR_",
    "yourdomain.com",
    "example.com",
    "localhost",
    "admin@example.com",
    "ops@example.com",
    "noreply@example.com",
)


@dataclass(slots=True)
class Finding:
    level: str
    code: str
    message: str


@dataclass(slots=True)
class Report:
    findings: list[Finding]

    @property
    def failures(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "FAIL"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "WARN"]

    @property
    def passes(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "PASS"]

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def status(self) -> str:
        if self.failures:
            return "NOT READY"
        if self.warnings:
            return "READY WITH WARNINGS"
        return "READY"


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(raw_value.strip())
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def _strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    result: list[str] = []
    for char in value:
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            break
        result.append(char)
    return "".join(result).strip()


def placeholder_like(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    lowered = stripped.lower()
    return any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS)


def validate_fernet_key(value: str) -> bool:
    if not value:
        return False
    try:
        decoded = base64.urlsafe_b64decode(value.encode("ascii"))
    except Exception:
        return False
    return len(decoded) == 32


def run_preflight(
    env: dict[str, str],
    *,
    env_file: Path,
    expected_env: str | None = None,
    require_sentry: bool = False,
    require_billing: bool = False,
    allow_localhost: bool = False,
) -> Report:
    findings: list[Finding] = []
    app_env = (env.get("APP_ENV") or expected_env or "").strip().lower()

    if not env_file.exists():
        return Report([Finding("FAIL", "env-file", f"Environment file not found: {env_file}")])

    if app_env not in {"staging", "production"}:
        findings.append(
            Finding(
                "FAIL",
                "app-env",
                f"APP_ENV must be staging or production for release checks, got {app_env or '<missing>'}.",
            )
        )
        return Report(findings)

    findings.append(Finding("PASS", "app-env", f"APP_ENV={app_env}."))

    if expected_env and app_env != expected_env:
        findings.append(
            Finding(
                "FAIL",
                "target-env",
                f"Expected APP_ENV={expected_env}, found {app_env}.",
            )
        )
    else:
        findings.append(Finding("PASS", "target-env", f"Release target matches {app_env}."))

    domain_ok = _require_non_placeholder(findings, env, "DOMAIN", minimum=3, allow_localhost=allow_localhost)
    _require_non_placeholder(findings, env, "ADMIN_EMAIL", minimum=6)
    _require_non_placeholder(findings, env, "POSTGRES_USER", minimum=3)
    _require_non_placeholder(findings, env, "POSTGRES_PASSWORD", minimum=12)
    _require_non_placeholder(findings, env, "POSTGRES_DB", minimum=3)
    database_url_ok = _require_non_placeholder(findings, env, "DATABASE_URL", minimum=16)
    _require_non_placeholder(findings, env, "REDIS_PASSWORD", minimum=12)
    redis_url_ok = _require_non_placeholder(findings, env, "REDIS_URL", minimum=10)
    jwt_secret_ok = _require_non_placeholder(findings, env, "JWT_SECRET_KEY", minimum=32)
    frontend_url_ok = _require_non_placeholder(findings, env, "FRONTEND_URL", minimum=12, allow_localhost=allow_localhost)
    frontend_origins_ok = _require_non_placeholder(
        findings,
        env,
        "FRONTEND_ORIGINS",
        minimum=12,
        allow_localhost=allow_localhost,
    )

    encryption_key = env.get("ENCRYPTION_KEY", "").strip()
    encryption_keys = env.get("ENCRYPTION_KEYS", "").strip()
    if not encryption_key and not encryption_keys:
        findings.append(
            Finding(
                "FAIL",
                "encryption-key",
                "Set ENCRYPTION_KEY or ENCRYPTION_KEYS before release.",
            )
        )
    elif encryption_key and not validate_fernet_key(encryption_key):
        findings.append(
            Finding(
                "FAIL",
                "encryption-key",
                "ENCRYPTION_KEY is not a valid Fernet key.",
            )
        )
    else:
        findings.append(Finding("PASS", "encryption-key", "Encryption key configuration is present."))

    jwt_secret = env.get("JWT_SECRET_KEY", "").strip()
    if jwt_secret in INSECURE_JWT_SECRETS:
        findings.append(
            Finding(
                "FAIL",
                "jwt-secret",
                "JWT_SECRET_KEY matches an insecure default and must be rotated.",
            )
        )
    elif jwt_secret_ok and len(jwt_secret) >= 32:
        findings.append(Finding("PASS", "jwt-secret", "JWT secret length looks production-safe."))

    database_url = env.get("DATABASE_URL", "").strip()
    if database_url_ok and database_url.startswith("sqlite"):
        findings.append(Finding("FAIL", "database-url", "SQLite is not allowed for staging or production."))
    elif database_url_ok and database_url.startswith("postgresql"):
        findings.append(Finding("PASS", "database-url", "DATABASE_URL points to PostgreSQL."))

    redis_url = env.get("REDIS_URL", "").strip()
    if redis_url_ok and not redis_url.startswith("redis://"):
        findings.append(Finding("FAIL", "redis-url", "REDIS_URL must start with redis://"))
    elif redis_url_ok and redis_url.startswith("redis://:"):
        findings.append(Finding("PASS", "redis-url", "REDIS_URL includes an inline password."))
    elif redis_url_ok:
        findings.append(
            Finding(
                "WARN",
                "redis-url",
                "REDIS_URL does not embed a password. Make sure the deployment injects auth correctly.",
            )
        )

    frontend_url = env.get("FRONTEND_URL", "").strip()
    domain = env.get("DOMAIN", "").strip()
    parsed_frontend = urlparse(frontend_url)
    if frontend_url_ok and parsed_frontend.scheme != "https":
        findings.append(Finding("FAIL", "frontend-url", "FRONTEND_URL must use https outside development."))
    elif frontend_url_ok and domain_ok and parsed_frontend.hostname != domain:
        findings.append(
            Finding(
                "WARN",
                "frontend-url",
                f"FRONTEND_URL host ({parsed_frontend.hostname}) does not exactly match DOMAIN ({domain}).",
            )
        )
    elif frontend_url_ok and domain_ok:
        findings.append(Finding("PASS", "frontend-url", "FRONTEND_URL matches the release domain."))

    frontend_origins = {
        origin.strip()
        for origin in env.get("FRONTEND_ORIGINS", "").split(",")
        if origin.strip()
    }
    if frontend_url_ok and frontend_origins_ok and frontend_url not in frontend_origins:
        findings.append(
            Finding(
                "FAIL",
                "frontend-origins",
                "FRONTEND_ORIGINS must include FRONTEND_URL to avoid auth and CORS drift.",
            )
        )
    elif frontend_url_ok and frontend_origins_ok:
        findings.append(Finding("PASS", "frontend-origins", "FRONTEND_ORIGINS includes FRONTEND_URL."))

    cookie_domain = env.get("COOKIE_DOMAIN", "").strip()
    if cookie_domain:
        if not cookie_domain.startswith(".") and cookie_domain != domain:
            findings.append(
                Finding(
                    "WARN",
                    "cookie-domain",
                    "COOKIE_DOMAIN is set but does not look like a root domain (expected .example.com).",
                )
            )
        else:
            findings.append(Finding("PASS", "cookie-domain", f"COOKIE_DOMAIN={cookie_domain}."))
    else:
        findings.append(
            Finding(
                "WARN",
                "cookie-domain",
                "COOKIE_DOMAIN is blank. This is fine for a single-domain deploy, but cross-subdomain auth will not work.",
            )
        )

    sentry_dsn = env.get("SENTRY_DSN", "").strip()
    if sentry_dsn and not placeholder_like(sentry_dsn):
        findings.append(Finding("PASS", "sentry", "SENTRY_DSN is populated."))
    elif require_sentry:
        findings.append(
            Finding(
                "FAIL",
                "sentry",
                "SENTRY_DSN is required for release validation but is missing or placeholder-like.",
            )
        )
    else:
        findings.append(
            Finding(
                "WARN",
                "sentry",
                "SENTRY_DSN is blank. You will have limited production visibility until this is configured.",
            )
        )

    brevo_key = env.get("BREVO_API_KEY", "").strip()
    if brevo_key:
        findings.append(Finding("PASS", "email", "Email provider credentials are present."))
    else:
        findings.append(
            Finding(
                "WARN",
                "email",
                "BREVO_API_KEY is blank. Registration and notification mail flows will not be fully validated.",
            )
        )

    stripe_secret = env.get("STRIPE_SECRET_KEY", "").strip()
    stripe_webhook = env.get("STRIPE_WEBHOOK_SECRET", "").strip()
    stripe_price_pro = (env.get("STRIPE_PRICE_PRO") or env.get("STRIPE_PRICE_ID_PRO") or "").strip()
    stripe_price_business = (
        env.get("STRIPE_PRICE_BUSINESS") or env.get("STRIPE_PRICE_ID_BUSINESS") or ""
    ).strip()
    if stripe_secret:
        missing = []
        if not stripe_webhook:
            missing.append("STRIPE_WEBHOOK_SECRET")
        if not stripe_price_pro:
            missing.append("STRIPE_PRICE_PRO/STRIPE_PRICE_ID_PRO")
        if not stripe_price_business:
            missing.append("STRIPE_PRICE_BUSINESS/STRIPE_PRICE_ID_BUSINESS")
        if missing:
            findings.append(
                Finding(
                    "FAIL",
                    "stripe",
                    f"Stripe is partially configured; missing {', '.join(missing)}.",
                )
            )
        else:
            findings.append(Finding("PASS", "stripe", "Stripe release variables are consistent."))
    elif require_billing:
        findings.append(
            Finding(
                "FAIL",
                "stripe",
                "Billing is required for this release, but Stripe keys are missing.",
            )
        )
    else:
        findings.append(
            Finding(
                "WARN",
                "stripe",
                "Stripe is not configured. This is fine only if billing is intentionally out of scope for the release.",
            )
        )

    for key in ("COINBASE_CLIENT_ID", "COINBASE_CLIENT_SECRET", "ETHERSCAN_API_KEY", "BSCSCAN_API_KEY", "POLYGONSCAN_API_KEY"):
        if env.get(key, "").strip():
            findings.append(Finding("PASS", key.lower(), f"{key} is present."))
        else:
            findings.append(
                Finding(
                    "WARN",
                    key.lower(),
                    f"{key} is blank. Related integration smoke tests will remain unverified.",
                )
            )

    return Report(findings)


def format_report(report: Report, *, title: str) -> str:
    lines = [title, f"Status: {report.status}", ""]
    for finding in report.findings:
        lines.append(f"[{finding.level}] {finding.code}: {finding.message}")
    return "\n".join(lines)


def load_last_playwright_status(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get("status")


def collect_bundle_warnings(
    assets_dir: Path,
    *,
    warning_threshold_bytes: int = 500_000,
) -> list[Finding]:
    if not assets_dir.exists():
        return [Finding("WARN", "bundle", f"Missing built assets directory: {assets_dir}")]

    warnings: list[Finding] = []
    for asset in sorted(assets_dir.iterdir(), key=lambda item: item.stat().st_size, reverse=True):
        if not asset.is_file():
            continue
        size = asset.stat().st_size
        if size <= warning_threshold_bytes:
            break
        warnings.append(
            Finding(
                "WARN",
                "bundle",
                f"{asset.name} is {size / 1024:.1f} KiB and should be reviewed before release.",
            )
        )
    if not warnings:
        warnings.append(Finding("PASS", "bundle", "No oversized frontend assets above the warning threshold."))
    return warnings


def verify_git_revision(revision: str, *, workdir: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", revision],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip() or proc.stdout.strip() or f"Revision not found: {revision}"
    return True, proc.stdout.strip()


def _require_non_placeholder(
    findings: list[Finding],
    env: dict[str, str],
    key: str,
    *,
    minimum: int = 1,
    allow_localhost: bool = False,
) -> bool:
    value = env.get(key, "").strip()
    if len(value) < minimum:
        findings.append(Finding("FAIL", key.lower(), f"{key} is missing or too short."))
        return False
    if placeholder_like(value) and not (allow_localhost and "localhost" in value.lower()):
        findings.append(Finding("FAIL", key.lower(), f"{key} still contains a placeholder-like value."))
        return False
    findings.append(Finding("PASS", key.lower(), f"{key} is set."))
    return True
