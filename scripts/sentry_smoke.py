from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path

import sentry_sdk

from release_checks import parse_env_file, placeholder_like

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send a controlled Sentry smoke event from the backend runtime.")
    parser.add_argument("--env-file", default=".env.staging", help="Env file containing SENTRY_DSN and app settings.")
    parser.add_argument(
        "--mode",
        choices=("message", "exception"),
        default="message",
        help="Whether to send a message event or a caught exception.",
    )
    parser.add_argument("--component", default="backend", help="Component tag to attach to the smoke event.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Seconds to wait for Sentry flush.")
    return parser


def _git_revision() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip() or "unknown"


def main() -> int:
    args = build_parser().parse_args()
    env_file = Path(args.env_file).resolve()
    if not env_file.exists():
        print(f"Sentry smoke failed: env file not found: {env_file}")
        return 1

    for key, value in parse_env_file(env_file).items():
        os.environ[key] = value

    from app.core.config import get_settings
    from app.core.observability import setup_observability

    settings = get_settings()
    if not settings.SENTRY_DSN or placeholder_like(settings.SENTRY_DSN):
        print("Sentry smoke failed: SENTRY_DSN is blank or placeholder-like.")
        return 1

    setup_observability(settings)

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("release_smoke", "true")
        scope.set_tag("component", args.component)
        scope.set_tag("app_env", settings.APP_ENV)
        scope.set_tag("git_revision", _git_revision())
        scope.set_extra("host", socket.gethostname())
        scope.set_extra("env_file", env_file.name)

    if args.mode == "exception":
        try:
            raise RuntimeError(f"Declairo release smoke exception from {args.component}")
        except RuntimeError as exc:
            event_id = sentry_sdk.capture_exception(exc)
    else:
        event_id = sentry_sdk.capture_message(
            f"Declairo release smoke message from {args.component} ({settings.APP_ENV})",
            level="warning",
        )

    sentry_sdk.flush(timeout=args.timeout)
    print(f"Sentry smoke event sent. Event ID: {event_id or '<unknown>'}")
    print("Verify that the event arrived in the expected Sentry project before release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
