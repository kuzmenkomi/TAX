from __future__ import annotations

import argparse
import sys
from pathlib import Path

from release_checks import (
    Finding,
    Report,
    collect_bundle_warnings,
    format_report,
    load_last_playwright_status,
    parse_env_file,
    run_preflight,
)

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize local release readiness evidence.")
    parser.add_argument("--env-file", help="Optional env file to include in the release gate report.")
    parser.add_argument(
        "--expected-env",
        choices=("staging", "production"),
        default="staging",
        help="Expected APP_ENV when --env-file is provided.",
    )
    parser.add_argument("--require-sentry", action="store_true", help="Treat a blank SENTRY_DSN as a failure.")
    parser.add_argument("--require-billing", action="store_true", help="Treat missing Stripe config as a failure.")
    parser.add_argument(
        "--allow-localhost",
        action="store_true",
        help="Allow localhost values for DOMAIN and FRONTEND_* during local staging-like checks.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    findings: list[Finding] = []

    env_file = Path(args.env_file).resolve() if args.env_file else None
    if env_file:
        if env_file.exists():
            findings.extend(
                run_preflight(
                    parse_env_file(env_file),
                    env_file=env_file,
                    expected_env=args.expected_env,
                    require_sentry=args.require_sentry,
                    require_billing=args.require_billing,
                    allow_localhost=args.allow_localhost,
                ).findings
            )
        else:
            findings.append(Finding("FAIL", "env-file", f"Requested env file does not exist: {env_file}"))
    else:
        findings.append(
            Finding(
                "WARN",
                "env-file",
                "No env file supplied. External secret validation is still outstanding.",
            )
        )

    required_paths = {
        "compose": ROOT / "docker-compose.yml",
        "backup-script": ROOT / "scripts" / "production_backup.sh",
        "restore-script": ROOT / "scripts" / "postgresql_restore.sh",
        "rollback-runbook": ROOT / "docs" / "runbooks" / "deployment-rollback.md",
        "staging-runbook": ROOT / "docs" / "runbooks" / "staging-validation.md",
        "sentry-runbook": ROOT / "docs" / "runbooks" / "sentry-validation.md",
        "rollback-drill": ROOT / "scripts" / "rollback_drill.py",
        "sentry-smoke": ROOT / "scripts" / "sentry_smoke.py",
    }
    for code, path in required_paths.items():
        if path.exists():
            findings.append(Finding("PASS", code, f"Found {path.relative_to(ROOT)}."))
        else:
            findings.append(Finding("FAIL", code, f"Missing required release artifact: {path.relative_to(ROOT)}"))

    smoke_report = ROOT / "frontend" / "playwright-report" / "index.html"
    if smoke_report.exists():
        findings.append(Finding("PASS", "smoke-report", f"Found smoke report: {smoke_report.relative_to(ROOT)}"))
    else:
        findings.append(Finding("WARN", "smoke-report", "No Playwright HTML report found."))

    last_run_status = load_last_playwright_status(ROOT / "frontend" / "test-results" / ".last-run.json")
    if last_run_status == "passed":
        findings.append(Finding("PASS", "smoke-status", "Latest Playwright run is marked as passed."))
    elif last_run_status:
        findings.append(Finding("FAIL", "smoke-status", f"Latest Playwright run status is {last_run_status}."))
    else:
        findings.append(Finding("WARN", "smoke-status", "Could not determine the latest Playwright run status."))

    restore_artifact = ROOT / "backups" / "release_restore_test.sql"
    if restore_artifact.exists():
        findings.append(
            Finding(
                "PASS",
                "restore-artifact",
                f"Found restore evidence: {restore_artifact.relative_to(ROOT)}",
            )
        )
    else:
        findings.append(Finding("WARN", "restore-artifact", "No local restore artifact found under backups/."))

    findings.extend(collect_bundle_warnings(ROOT / "frontend" / "dist" / "assets"))

    frontend_sentry_hits = list((ROOT / "frontend" / "src").rglob("*.ts")) + list((ROOT / "frontend" / "src").rglob("*.tsx"))
    if any("sentry" in path.read_text(encoding="utf-8", errors="ignore").lower() for path in frontend_sentry_hits):
        findings.append(Finding("PASS", "frontend-sentry", "Frontend source references Sentry."))
    else:
        findings.append(
            Finding(
                "WARN",
                "frontend-sentry",
                "Frontend Sentry wiring was not detected in frontend/src. Browser-side error capture is likely still missing.",
            )
        )

    report = Report(findings)
    print(format_report(report, title="Local release gate"))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
