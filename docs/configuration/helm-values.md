---
title: "Helm values reference"
description: "The Helm values you will most often set - images, secrets, database, Redis, ingress, resource limits and the pilot timer."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/configuration/helm-values/](https://cloudkeel.io/docs/configuration/helm-values/)**

Cloudkeel-DD installs from the `d-detective` Helm chart. This page covers the
values you'll most often set. Run `helm show values <chart>` for the complete,
authoritative list shipped with your version.

## Images

| Value | Default | Notes |
|---|---|---|
| `images.backend.repository` | `driftdetective/ddetective-backend` | Backend/worker/beat image (one image, three commands) |
| `images.backend.tag` | chart `appVersion` | Pin to a specific version in production |
| `images.frontend.repository` | `driftdetective/ddetective-frontend` | UI image |
| `images.frontend.tag` | chart `appVersion` | |
| `imagePullSecrets` | `[]` | Only needed for a private registry without workload-identity pull |

## Ingress (optional)

The frontend proxies `/api` to the backend itself at runtime, so no Ingress
controller is required to reach a fully working app — `helm install` then
`kubectl port-forward svc/<release>-frontend 3000:3000` is enough. Enable
ingress for a stable, TLS-terminated hostname instead of port-forwarding
(typical for production).

| Value | Default | Notes |
|---|---|---|
| `ingress.enabled` | `false` | Set `true` for a stable hostname/TLS |
| `ingress.className` | `""` | Your ingress controller's class (only used when enabled) |
| `ingress.host` | `d-detective.example.com` | **Set this** to your DNS name (only used when enabled) |
| `ingress.tls.enabled` / `.secretName` | `false` / `""` | Enable and supply a TLS secret in production |
| `frontend.service.type` | `ClusterIP` | Set `LoadBalancer`/`NodePort` for external access without ingress |

## Secrets

| Value | Notes |
|---|---|
| `secrets.fernetKey` | **Immutable** credential-encryption key. Set once; never change. See [Secrets](https://cloudkeel.io/docs/configuration/secrets/) |
| `secrets.jwtSecret` | Signs user session tokens. Rotating it logs everyone out |

> [!CAUTION]
> **The Fernet key is immutable**
>
> Changing `secrets.fernetKey` after install makes every stored cloud
> credential undecryptable. Keep it in your secret manager and pass the same
> value on every upgrade.


## Database & cache

| Value | Notes |
|---|---|
| `postgresql.enabled` | Set `false` in production and point at managed PostgreSQL |
| `postgresql.auth.password` | Bundled-PostgreSQL password (pilot only) |
| External DB / Redis | Supply host/port/credentials per your chart version's keys |

## Scanning

| Value | Notes |
|---|---|
| Scan schedule | Configurable per integration in the UI, or a global cadence |
| Worker replicas | Increase for more parallel scans; **beat stays at 1** |

## The pilot timer

From chart `0.3.0` an install scans for a fixed window and then stops *starting*
new scans. It is a local date comparison against the values below — nothing
phones home, there is no licence server, and an air-gapped install behaves
identically.

| Value | Default | Notes |
|---|---|---|
| `config.licenseTrialDays` | `30` | Days from the **first workspace** before the window closes |
| `config.licenseExpiresAt` | `""` | An explicit UTC date (`2026-12-31` or `2026-12-31T23:59:59Z`). When set it **wins over** `licenseTrialDays` — this is how a window is extended |
| `config.licenseEnforcementEnabled` | `true` | Set `false` to run the timer in reporting-only mode: state is still computed and shown, nothing is blocked |
| `secrets.licenseKey` | `""` | A licence key, applied at install/upgrade time. Optional - without one the install runs its pilot window and then the Free allowance. **Wins over** a key entered in Settings. Chart 0.3.4+. See [Licensing](https://cloudkeel.io/docs/configuration/licensing/) |

All three live in the ConfigMap, not the Secret — the expiry is not a secret,
and storing it as one would imply a protection it does not have.

Changing them is a plain `helm upgrade`. The backend, worker and beat pods carry
a checksum annotation over this ConfigMap, so they roll themselves; there is no
separate restart to remember.

> [!NOTE]
> **What expiry does *not* do**
>
> It stops new scans from starting. It does not delete anything. Findings,
> history, connected integrations and login all keep working, and a scan already
> running finishes normally.


> [!TIP]
> **An upgrade cannot cut an existing install short**
>
> The window is anchored on **whichever is later** — your first workspace, or the
> first time this install ran a version that enforces the timer. An install that
> predates enforcement gets a full window from the upgrade, never a retroactive
> expiry.


## Applying values

Keep a version-controlled `production-values.yaml` (secrets referenced from your
secret manager, never committed) and apply with `helm upgrade --install ... -f
production-values.yaml`. See [Upgrades](https://cloudkeel.io/docs/operations/upgrades/).
