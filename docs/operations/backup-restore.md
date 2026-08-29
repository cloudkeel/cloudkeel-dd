---
title: "Backup & restore"
description: "What to back up - PostgreSQL and the Fernet key - and how to restore Cloudkeel-DD without losing stored credentials."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/operations/backup-restore/](https://cloudkeel.io/docs/operations/backup-restore/)**

Everything Cloudkeel-DD needs to reconstruct itself lives in **PostgreSQL** —
integrations, encrypted credentials, discovered resources, and drift history.
Back up the database and safeguard the Fernet key, and you can restore fully.

## What to back up

| Item | Where | Why |
|---|---|---|
| **PostgreSQL** | Your database | All state: integrations, resources, scans, drift, history |
| **Fernet key** | Your secret manager | Without it, restored credential rows are undecryptable |
| **Helm values** | Version control (secrets referenced, not inlined) | Reproduce the exact install |

Redis holds only transient queue/rate-limit data — it does **not** need backup;
it rebuilds itself.

## Backing up PostgreSQL

Use your managed database's snapshot/backup feature, or `pg_dump`:

```bash
pg_dump --format=custom --no-owner "$DATABASE_URL" > d-detective-$(date +%F).dump
```

Automate it on your normal database backup schedule. Findings are re-derivable on
the next scan, but history and acknowledgements are not — so back up regularly.

## Restoring

1. Provision a database and restore the dump:
   ```bash
   pg_restore --clean --no-owner -d "$NEW_DATABASE_URL" d-detective-YYYY-MM-DD.dump
   ```
2. Install/point Cloudkeel-DD at the restored database with the **same Fernet
   key** it had when the backup was taken.
3. Start the app; it picks up all integrations and history. Run a scan to
   refresh live state.

> [!WARNING]
> **The Fernet key is part of your backup**
>
> A database backup without the matching Fernet key can restore *inventory and
> history* but **not** usable cloud credentials — you'd reconnect every
> integration. Store the key alongside your backup policy, in your secret
> manager. See [Secrets](https://cloudkeel.io/docs/configuration/secrets/).


## Disaster recovery

For a full cluster loss: restore PostgreSQL from backup, reinstall the chart with
the same Fernet key and values, point at the restored DB. Recovery time is
dominated by the database restore; the app itself comes up in minutes.
