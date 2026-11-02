# Deployment and rollback

Use this on release day for both staging promotion and production rollback.

## Deployment

1. Confirm CI is green for backend tests, frontend tests, frontend build, and frontend typecheck.
2. Confirm the staging validation runbook and release smoke test are complete.
3. Back up PostgreSQL before deployment.
4. Pull the target revision on the host.
5. Update the environment file with reviewed secrets.
6. Rebuild and restart the stack.

```bash
docker compose pull
docker compose build
docker compose up -d
docker compose ps
```

7. Verify `backend`, `worker`, and `frontend` are healthy.
8. Run the abbreviated smoke checks: login, dashboard load, one sync action, one export.

## Rollback triggers

Roll back immediately if any of these happen after deployment:

- login or session persistence fails
- migrations succeed but backend health never stabilizes
- worker cannot consume jobs
- dashboard or export flow is broken for the release path

## Rollback procedure

1. Stop user-facing rollout communication and mark the release as degraded.
2. Restore the previous application revision.
3. Restart the prior known-good containers.

```bash
git checkout <previous-known-good-revision>
docker compose build
docker compose up -d
docker compose ps
```

Validate the drill inputs before release day:

```bash
python scripts/rollback_drill.py --previous-revision <previous-known-good-revision> --env-file .env.staging --backup-file backups/<pre-release-backup>.sql.gz
```

4. If the release included a destructive schema or data issue, restore PostgreSQL from the pre-release backup.
5. Re-run the abbreviated smoke checks.
6. Document the rollback time, trigger, and follow-up owner.

## Notes

- Do not roll back the database independently unless the application rollback alone is insufficient.
- Keep the pre-release backup until the release is declared stable.
