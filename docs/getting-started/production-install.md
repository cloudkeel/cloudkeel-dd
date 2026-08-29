---
title: "Production installation"
description: "Moving past the pilot: external PostgreSQL, TLS, and the settings to harden before running Cloudkeel-DD in production."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/getting-started/production-install/](https://cloudkeel.io/docs/getting-started/production-install/)**

The [pilot quickstart](https://cloudkeel.io/docs/getting-started/pilot/) gets you running fast with bundled PostgreSQL
and Redis. For production, harden three things: **an external database**, **TLS
at the ingress**, and **secret management**.

## Prerequisites

- A Kubernetes cluster (1.24+) and Helm 3.
- An **ingress controller** (e.g. ingress-nginx) — recommended for production
  so users reach the app at a stable, TLS-terminated hostname instead of
  `kubectl port-forward`. Not strictly required: the frontend proxies `/api`
  itself at runtime (`ingress.enabled=false`, the chart default), but a real
  production deployment almost always wants a real hostname.
- A managed **PostgreSQL** (14+) and **Redis** you control (recommended over the
  bundled ones for durability, backups, and HA).
- DNS + a TLS certificate for your chosen host (if using ingress).

## 1. Provide the immutable Fernet key up front

Cloudkeel-DD encrypts stored cloud credentials with a **Fernet key**. It is
**immutable for the life of the install** — losing or changing it makes every
stored credential undecryptable. Generate it once and keep it in your secret
manager:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

See [Secrets & the Fernet key](https://cloudkeel.io/docs/configuration/secrets/) for the full detail.

## 2. Point at external PostgreSQL and Redis

Disable the bundled dependencies and supply your own connection details via
Helm values (exact keys are in the
[Helm values reference](https://cloudkeel.io/docs/configuration/helm-values/)). Use a database user
scoped to Cloudkeel-DD's own database.

## 3. Enable ingress, TLS, and set your host

Set `ingress.enabled=true` and `ingress.host` to your real DNS name. Terminate
TLS at the ingress with your certificate (a `tls` secret, or cert-manager).

## 4. Size for your estate

Start points, scale with the number of resources and scan frequency:

| Component | Requests (start) | Notes |
|---|---|---|
| API | 250m / 512Mi | Scales with concurrent UI/API use |
| Worker | 500m / 1Gi | The heavy component — scans run here; add replicas for more parallel scans |
| Beat | 100m / 128Mi | Single scheduler; **do not** run more than one replica |
| Frontend | 100m / 256Mi | Static/SSR |

## 5. Install

Install the chart with your production values, then verify the migration Job
completed and all pods are `Running`:

```bash
helm upgrade --install d-detective <chart> \
  -n ddetective --create-namespace \
  -f production-values.yaml
kubectl get pods -n ddetective
kubectl get ingress -n ddetective   # only if ingress.enabled=true
```

## High availability

- Run **≥2 API and worker replicas**; keep **beat at exactly one**.
- Use an **external HA PostgreSQL and Redis**.
- The app tolerates rolling restarts; scans are idempotent and resume.

## After install

Connect your integrations ([overview](https://cloudkeel.io/docs/integrations/overview/)), enable the
cloud scopes, and run the first scan. Then read
[Operations](https://cloudkeel.io/docs/operations/upgrades/) for upgrades, backup, and monitoring.
