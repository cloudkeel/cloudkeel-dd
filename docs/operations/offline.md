---
title: "Air-gapped installation"
description: "Running Cloudkeel-DD with no internet access: the five images to mirror, pulling the chart from the public OCI registry, and pointing the install at your own registry."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/operations/offline/](https://cloudkeel.io/docs/operations/offline/)**

Cloudkeel-DD needs no internet access to run. We operate no endpoints of our own,
so there is no telemetry, no analytics and no licence server to punch a hole for.
The only outbound calls it makes are the read-only ones to the endpoints **you**
connect — your Terraform state backend, your cloud APIs, your Kubernetes
clusters — plus any notification webhook or Git host you configure yourself.

What an air-gapped install does need is the container images and the chart,
mirrored inside your network before you start.

> [!NOTE]
> **The pilot timer runs offline too — plan for it at install time**
>
> From chart `0.3.0` an install scans for 30 days from its first workspace and
> then stops *starting* new scans. That is a **local date comparison**, not a
> callout: being air-gapped neither triggers it early nor exempts you from it, and
> there is still nothing to punch a hole for.
>
> Set `config.licenseExpiresAt` to an agreed date when you install and the window
> follows it, with no connectivity needed then or later. Either way nothing is
> deleted when a window closes — findings, history, integrations and login keep
> working. See [the pilot timer](https://cloudkeel.io/docs/configuration/helm-values/#the-pilot-timer).


## Images to mirror

Five, all pulled at install time.

| Image | Used by | Always pulled? |
|---|---|---|
| `driftdetective/ddetective-backend` | API, worker, beat, the schema-migration Job, and the wait-for-database init containers | Yes |
| `driftdetective/ddetective-frontend` | The UI | Yes |
| `openpolicyagent/opa:1.18.2` | Policy evaluation | Yes — deployed unconditionally |
| `postgres:16` | Bundled database | Only when `postgresql.enabled` (default `true`) |
| `redis:7` | Bundled broker and rate-limit store | Only when `redis.enabled` (default `true`) |

**One image covers five workloads.** The API, worker and beat are the same
backend image run with different commands, and both the migration Job and the
wait-for-database init containers use it too. Mirror it once.

**Pin the tags.** `images.backend.tag` and `images.frontend.tag` default to the
chart's `appVersion` when left empty. Set them explicitly for an air-gapped
mirror, so a chart upgrade cannot ask for a tag you have not copied in.

If you point `postgresql.enabled` and `redis.enabled` at external managed
instances instead, those two images drop off the list.

## Pull the chart

The chart lives in the same public OCI registry as the images. Pull it to a file
on a connected machine:

```bash
helm pull oci://registry-1.docker.io/driftdetective/d-detective --version <version>
```

That writes `d-detective-<version>.tgz`. Carry it in with the images and install
from the local file rather than from the registry.

## Point the install at your registry

```yaml
imagePullSecrets:
  - name: my-registry-creds

images:
  backend:
    repository: registry.internal/mirror/ddetective-backend
    tag: "<appVersion>"
  frontend:
    repository: registry.internal/mirror/ddetective-frontend
    tag: "<appVersion>"

opa:
  image: registry.internal/mirror/opa:1.18.2

postgresql:
  image: registry.internal/mirror/postgres:16

redis:
  image: registry.internal/mirror/redis:7
```

```bash
helm install dd ./d-detective-<version>.tgz -f airgap-values.yaml \
  --namespace ddetective --create-namespace
```

The required secrets are unchanged — see [secrets](https://cloudkeel.io/docs/configuration/secrets/).
The Fernet key is immutable after first install.

## What still has to be reachable

Nothing of ours. But Cloudkeel-DD can only scan what the cluster can reach: your
Terraform state backend, the cloud API endpoints for each connected credential,
and the API server of each connected Kubernetes cluster. If a scope is not
reachable from inside the air gap, it cannot be scanned — that is a network
constraint on your side, not an internet requirement on ours.

## These docs, offline

The documentation site loads nothing from a third party: no script, stylesheet,
image or font comes from an external host, and every absolute URL in the built
site is its own canonical link. Fonts are self-hosted. So the same static files
the public site serves can be served inside the air gap with no external access.

Ask us and we will supply the built bundle.
