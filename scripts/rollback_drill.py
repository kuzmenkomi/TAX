from __future__ import annotations

import argparse
import sys
from pathlib import Path

from release_checks import verify_git_revision

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate rollback drill inputs and print the drill steps.")
    parser.add_argument("--previous-revision", required=True, help="Previous known-good git revision.")
    parser.add_argument("--current-revision", default="HEAD", help="Current release revision, defaults to HEAD.")
    parser.add_argument("--env-file", default=".env.staging", help="Env file to use during rollback verification.")
    parser.add_argument("--backup-file", help="Optional pre-release backup file to verify.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    current_ok, current_resolved = verify_git_revision(args.current_revision, workdir=ROOT)
    previous_ok, previous_resolved = verify_git_revision(args.previous_revision, workdir=ROOT)

    failures: list[str] = []
    if not current_ok:
        failures.append(f"Current revision check failed: {current_resolved}")
    if not previous_ok:
        failures.append(f"Previous revision check failed: {previous_resolved}")
    if current_ok and previous_ok and current_resolved == previous_resolved:
        failures.append("Current revision and previous known-good revision resolve to the same commit.")

    env_file = Path(args.env_file).resolve()
    if not env_file.exists():
        failures.append(f"Env file not found: {env_file}")

    backup_file = Path(args.backup_file).resolve() if args.backup_file else None
    if backup_file and not backup_file.exists():
        failures.append(f"Backup file not found: {backup_file}")

    if failures:
        print("Rollback drill prerequisites failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Rollback drill prerequisites passed.")
    print(f"Current revision:  {current_resolved}")
    print(f"Rollback target:   {previous_resolved}")
    print(f"Env file:          {env_file}")
    if backup_file:
        print(f"Backup artifact:   {backup_file}")
    print()
    print("Suggested rollback drill:")
    print("1. Record the release SHA, previous known-good SHA, and backup filename in the release ticket.")
    print("2. Confirm the pre-release backup exists and keep it until the release is declared stable.")
    print("3. Deploy the target release revision and capture start timestamps.")
    print("4. If rollback triggers fire, execute:")
    print(f"   git checkout {previous_resolved}")
    print("   docker compose --env-file {0} build".format(env_file))
    print("   docker compose --env-file {0} up -d".format(env_file))
    print("5. Re-run health checks and smoke flows after rollback:")
    print("   docker compose --env-file {0} ps".format(env_file))
    print("   docker compose --env-file {0} exec backend curl -fsS http://localhost:8000/health".format(env_file))
    print("6. Restore PostgreSQL only if the application rollback alone does not recover the release path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
