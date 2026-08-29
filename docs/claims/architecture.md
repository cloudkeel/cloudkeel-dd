---
title: "Architecture"
description: "The components Cloudkeel-DD runs in your cluster - API, worker, beat, frontend, PostgreSQL, Redis and OPA - and what leaves your environment."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/architecture/](https://cloudkeel.io/docs/claims/architecture/)**

Cloudkeel-DD is a small, self-contained application you run in your own
Kubernetes cluster. We operate no endpoints of our own, so there is no
telemetry, no analytics and no licence server. The traffic that does leave is the
read-only API calls it makes to verify your cloud, plus anything **you** wire up
yourself — see [data residency](#data-residency) below.

## Components

| Component | Role |
|---|---|
| **API** (FastAPI) | The web API and UI backend — integrations, scans, drift, auth. |
| **Worker** (Celery) | Runs scans asynchronously: ingest state, read live cloud, diff, record. |
| **Beat** (Celery beat) | Schedules recurring scans and scope/state re-discovery. |
| **Frontend** (Next.js) | The UI. Proxies `/api` to the backend itself at runtime — no ingress required to reach it (see below). |
| **PostgreSQL** | Stores integrations, resources, scans, drift events, history. |
| **Redis** | Celery broker/result backend and rate-limit store. |
| **OPA** (optional) | Policy evaluation sidecar; degrades gracefully if absent. |

The backend, worker, and beat are the **same image** run with different
commands. All images run as a non-root user.

## Request path

```
user ─► [Ingress, optional] ─► frontend  (static + SSR)
                                    └─► /api (proxied at runtime) ─► API ─► PostgreSQL / Redis
                                                                      │
worker ─► your Terraform state (read)                                │
       └► your cloud APIs (read-only) ◄──────────────────────────────┘
```

The frontend calls the API **same-origin under `/api`**. The frontend
container proxies those calls to the backend itself at request time, so
`kubectl port-forward` straight to the frontend Service is enough to reach a
fully working app — no ingress controller required. An Ingress is an optional
production upgrade for a stable, TLS-terminated hostname in front of the same
frontend Service.

## What it connects to (all read-only)

- **Terraform Cloud / Enterprise** API, or a **storage bucket** (S3 / GCS /
  Azure Blob) holding raw `.tfstate`.
- **Cloud provider APIs** (Azure Resource Manager, AWS, GCP) via a read-only
  credential, to read live resource configuration.
- **Kubernetes API** of each connected cluster, via a read-only ServiceAccount
  token, to read Helm releases and live workloads.

## Data residency

All state, credentials, and findings live in **your** PostgreSQL, inside your
cluster. Cloud credentials are encrypted at rest with a
[Fernet key](https://cloudkeel.io/docs/configuration/secrets/) that only your install holds.
**Cloud credentials never leave your environment** — nothing reads them out of
the database and sends them anywhere.

Findings are a different question, and worth stating precisely. There are no
Cloudkeel-DD-operated endpoints to send them to, but three paths do carry finding
data outward, and all three are ones **you** turn on:

| Path | What goes out | When |
|---|---|---|
| Notification webhooks | Finding details, to the URL on the rule | Only if you create a notification rule |
| GitHub remediation PRs | The proposed revert, to your GitHub | Only if you connect GitHub and open a PR |
| GitLab remediation PRs | The proposed revert, to your GitLab | Only if you connect GitLab and open an MR |

With none of those configured, the only outbound traffic is the read-only calls
to the endpoints you connect: your Terraform backend, your cloud, your clusters.

## Deployment shape

Installed with a **Helm chart**. A per-release migration Job runs Alembic to
build/upgrade the schema before the app starts. Bundled PostgreSQL and Redis are
fine for a pilot; production should point at managed/external instances — see
[production installation](https://cloudkeel.io/docs/getting-started/production-install/).
