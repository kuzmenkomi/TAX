from __future__ import annotations

import argparse
import sys
from pathlib import Path

from release_checks import format_report, parse_env_file, run_preflight


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate staging or production env files before release.")
    parser.add_argument("--env-file", default=".env.staging", help="Path to the env file to validate.")
    parser.add_argument(
        "--expected-env",
        choices=("staging", "production"),
        help="Expected APP_ENV value for this validation run.",
    )
    parser.add_argument(
        "--require-sentry",
        action="store_true",
        help="Fail when SENTRY_DSN is blank or placeholder-like.",
    )
    parser.add_argument(
        "--require-billing",
        action="store_true",
        help="Fail when Stripe release variables are not fully configured.",
    )
    parser.add_argument(
        "--allow-localhost",
        action="store_true",
        help="Allow localhost values for DOMAIN and FRONTEND_* during local staging-like checks.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    env_file = Path(args.env_file).resolve()
    if not env_file.exists():
        print(f"Release preflight failed: env file not found: {env_file}")
        return 1

    env = parse_env_file(env_file)
    report = run_preflight(
        env,
        env_file=env_file,
        expected_env=args.expected_env,
        require_sentry=args.require_sentry,
        require_billing=args.require_billing,
        allow_localhost=args.allow_localhost,
    )
    print(format_report(report, title=f"Release preflight for {env_file.name}"))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
