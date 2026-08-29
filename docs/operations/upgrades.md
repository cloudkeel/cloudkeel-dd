---
title: "Upgrades"
description: "How a helm upgrade runs the schema migration, what to check first, and how to pin image tags safely."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/operations/upgrades/](https://cloudkeel.io/docs/operations/upgrades/)**

Cloudkeel-DD upgrades are a `helm upgrade` with the schema migration handled
automatically.

## How an upgrade works

1. You bump the image tag(s) (or chart version) and run `helm upgrade`.
2. A **migration Job** runs Alembic to bring the database schema to the new
   version **before** the new app pods start. It has init containers that wait
   for the database to be reachable.
3. New API / worker / beat / frontend pods roll out.

The migration Job is deliberately **not** a Helm hook — it's a first-class Job in
the release so its status and logs are visible with `kubectl`.

## Before you upgrade

- **[Back up PostgreSQL](https://cloudkeel.io/docs/operations/backup-restore/).** Migrations move the schema
  forward; a backup is your rollback path.
- **Keep the same Fernet key.** Pass the identical
  [`secrets.fernetKey`](https://cloudkeel.io/docs/configuration/secrets/) — changing it orphans every
  stored credential.
- Read the [release notes](https://cloudkeel.io/docs/claims/release-notes/) for your target version.

## Upgrading to 0.3.0 turns the pilot timer on

`0.3.0` is the first chart that defaults `config.licenseEnforcementEnabled` to
`true`, so after upgrading an install stops *starting* new scans once its window
closes.

**It cannot cut your existing install short.** The window is anchored on
whichever is later — your first workspace, or the first time this install ran a
version that enforces the timer — so upgrading a long-running install gives it a
full window from the upgrade rather than expiring it on the spot.

Nothing is deleted when a window does close: findings, history, connected
integrations and login all keep working, and a scan already running finishes.
See [the pilot timer](https://cloudkeel.io/docs/configuration/helm-values/#the-pilot-timer) for
`config.licenseExpiresAt`, which extends a window, and
`config.licenseEnforcementEnabled: false`, which returns the timer to
reporting-only.

## Pin your tags

Pin `images.backend.tag` and `images.frontend.tag` to explicit versions in
production. They are **independent** — a backend-only release has no new frontend
image at that version, so tagging both with one value causes an
`ImagePullBackOff`. Bump only what changed; leave the other pinned.

## Running the upgrade

```bash
helm upgrade --install d-detective <chart> \
  -n ddetective \
  -f production-values.yaml \
  --set images.backend.tag=<new> \
  --wait --timeout 10m

kubectl get jobs,pods -n ddetective
```

`--wait` blocks until the migration Job and pods are ready.

## If an upgrade goes wrong

- **Migration Job failed:** read its logs (`kubectl logs job/<migration-job>`).
  The app won't start on a half-migrated schema by design. Fix the cause or
  restore the DB backup, then re-run.
- **New pods crashlooping / bad image:** `helm rollback d-detective <previous>`.
  The old pods keep serving during a failed upgrade, so this is usually a
  no-outage recovery.
- **Stuck `pending-upgrade`:** roll back to the last good revision and retry with
  correct tags.

## After the upgrade

- **Hard-reload open browser tabs.** A tab loaded before the upgrade keeps
  running the old UI code against the new API and can fail to render until it
  reloads.
- **Check your API scripts against the release notes.** Response shapes
  occasionally change between versions; breaking changes are listed under
  [Release notes](https://cloudkeel.io/docs/claims/release-notes/#breaking-changes).
