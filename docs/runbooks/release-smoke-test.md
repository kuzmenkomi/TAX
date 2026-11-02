# Release smoke test

Run this after staging deployment is healthy and before production release approval.

## Test account

- Use a brand-new email address
- Start with no wallets, exchanges, or imported transactions

## 1. Registration and login

1. Register a new user.
2. Confirm the success state and, if enabled, email verification flow.
3. Log in.
4. Refresh the browser and verify the session persists.
5. Log out and log back in.

Pass criteria:

- Registration succeeds without server errors
- Session survives refresh
- Logout clears the session

## 2. Onboarding

1. Complete onboarding questions.
2. Confirm the selected jurisdiction and profile settings are saved.
3. Reload the page and confirm onboarding state persists.

Pass criteria:

- User lands on the dashboard
- Onboarding is not shown again after reload

## 3. Exchange and wallet flows

1. Connect one exchange using staging-safe credentials.
2. Import one wallet address.
3. Run the relevant sync actions.
4. Watch backend and worker logs during the sync.

Pass criteria:

- Exchange connection is saved
- Wallet import completes
- Sync jobs finish without uncaught exceptions

## 4. Dashboard and analytics

1. Open the dashboard.
2. Switch across major tabs used in the release.
3. Confirm charts, balances, and analytics cards render.

Pass criteria:

- No blank sections or infinite loaders
- No failed API requests in browser devtools

## 5. Tax analysis and export

1. Run tax analysis on imported data.
2. Open the results view.
3. Export at least one report/file supported by the release.

Pass criteria:

- Analysis completes successfully
- Export downloads and is readable

## 6. Evidence to capture

- staging URL and test account email
- screenshots for register, dashboard, and export success
- backend log excerpt for sync and analysis
- any failed request payloads or stack traces

## Result

Mark the smoke test complete only if every section passes or any failures are explicitly accepted as release blockers with owners and follow-up dates.
