---
title: "Monitoring & health"
description: "The liveness and readiness endpoints, what the deep health check round-trips, and what to alert on."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/operations/monitoring/](https://cloudkeel.io/docs/operations/monitoring/)**

## Health endpoints

| Endpoint | Meaning |
|---|---|
| `/health` | Liveness — the API process is up |
| `/health/detailed` | Readiness — checks database, Redis, and policy engine reachability |

The frontend serves a static `200` health route of its own. Wire these as your
liveness/readiness probes (the chart does this by default).

## What to watch

- **Pod health** — API, worker, beat, frontend all `Running`; watch for
  `CrashLoopBackOff` or `ImagePullBackOff` (usually a mis-pinned image tag — see
  [Upgrades](https://cloudkeel.io/docs/operations/upgrades/)).
- **Migration Job** — on each release, it should complete `Succeeded` before app
  pods roll.
- **Scan outcomes** — a scan can finish `completed`, `partial` (some sources
  failed, others kept), or `failed`. A rising `failed`/`partial` rate usually
  means an expired credential or a scope that lost access.
- **Worker backlog** — if scans queue faster than they finish, add worker
  replicas (keep **beat at one**).

## Where scan status shows

- **In the UI** — each integration shows its last scan status and **last error**.
  A failed scan's error message is the first place to look.
- **Drift counts** — "open" and "risky" totals reflect real detected findings,
  not errors. They clear when the underlying drift is reverted, acknowledged, or
  suppressed.

## Logs

Standard `kubectl logs` on the API and worker pods. The worker logs the scan
pipeline (ingest → live read → diff → record); the API logs requests and auth.

## Common signals and causes

| Symptom | Likely cause |
|---|---|
| Scan `partial` with a `403` | A credential lost access to one source/scope |
| "No live comparison available" on resources | Cross-check credential missing, or its **scope not enabled** |
| Kubernetes scan `401` | Exec-plugin kubeconfig, or an expired ServiceAccount token |
| No cloud drift ever appears (Azure) | Discovered subscription scope not enabled |

Full failure-mode table: [Troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/).
