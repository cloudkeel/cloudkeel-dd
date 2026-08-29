---
title: "Release notes"
description: "Published Cloudkeel-DD releases, newest first - what changed, how many migrations each upgrade runs, and what to check before upgrading."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/release-notes/](https://cloudkeel.io/docs/claims/release-notes/)**

This is the changelog of record for public Cloudkeel-DD releases. Newest first.

## What "version" means here

Three things carry a version and they move independently. Every entry below is
the **published** version — the image tags on Docker Hub and the Helm chart in
the public OCI registry, which are published together from an already-tested
build.

| Track | Where it lives | Moves when |
|---|---|---|
| **Published** | Docker Hub images + OCI chart | A release is promoted. **This page tracks this one** |
| Chart in git | `Chart.yaml` | Someone bumps it, often *after* a publish |
| Deployed | Your cluster | You run `helm upgrade` |

A version bump in git does not publish, and publishing does not deploy. Read
your deployed version off the cluster (`helm list -n ddetective`), not off this
page.

---

## 0.3.0 — 2026-08-06

**The pilot timer starts enforcing. Read the first section before upgrading.**

### The install is now time-boxed

This is the first published chart that defaults
`config.licenseEnforcementEnabled` to `true`. An install scans for **30 days
from the moment its first workspace is created**, then stops *starting* new
scans.

It remains a **local date comparison** inside your own cluster. Nothing phones
home, there is no licence server, and an air-gapped install behaves identically.

**What stops:** new scans.
**What does not:** findings, history, connected integrations and login all keep
working, any scan already running finishes, and nothing is deleted.

**An upgrade cannot cut an existing install short.** The window is anchored on
whichever is later — your first workspace, or the first time this install ran a
version that enforces the timer — so a long-running install gets a full window
from the upgrade rather than expiring on the spot.

`config.licenseExpiresAt` sets an explicit date and overrides the 30 days;
`config.licenseEnforcementEnabled: false` returns the timer to reporting-only.
Both are documented under
[the pilot timer](https://cloudkeel.io/docs/configuration/helm-values/#the-pilot-timer).

### Coverage

- Field-level spec coverage expanded to **200 resource types** (79 Azure, 62
  AWS, 59 GCP), up from 22 in `0.2.1`. The [coverage page](https://cloudkeel.io/docs/claims/coverage/)
  is generated from the type registry shipped in this image.
- The live drift-proven bar did **not** move with it and is still three resource
  types: Azure NSG rules, AWS security-group rules, GCP firewall rules. Passing
  golden fixtures is not the same as a mapping confirmed against a live API, and
  we publish the two bars separately for that reason.

### Also in this release

- Credential-expiry tracking on integrations, so a state credential is flagged
  before it silently empties your managed set.
- A covering index for drift-events pagination, and an index on
  `observation(observed_at)`.
- Repair for suppressions stranded by a deleted ignore rule.

**Upgrade cost: moderate.** **5** Alembic migrations since `0.2.1` — verified by
diffing `alembic/versions/` between the two published images. Back up PostgreSQL
first, as with any schema step.

---

## 0.2.1 — 2026-07-29

**Drop-in patch. No migrations.**

- Tolerance for `PARTIAL` scan outcomes on the Kubernetes, ArgoCD and Flux scan
  paths, so one failing source no longer discards the rest of a scan's findings.
- A frontend fix carried over from the previous release.

**Upgrade cost: low.** **Zero** Alembic migrations since `0.2.0` — verified by
diffing `alembic/versions/` between the two published builds. A straight
`helm upgrade`.

---

## 0.2.0 — 2026-07-29

**The largest schema step shipped so far. Rehearse before upgrading.**

- Field-level cross-check generalised beyond its original hardcoded types, so
  shipped specs power the raw-state path. This is what took AWS raw-state
  coverage from security-groups-only to all six AWS types, and GCP to four.
- Severity and category corrections for AWS security groups and GCP firewall
  rules.
- Drift-events pagination, including the API change below.

**Upgrade cost: high.** **11** Alembic migrations since `0.1.6` — anyone coming
from that version runs all eleven in one go. Rehearse against a copy of your
data before running it over production rows. The migration Job runs
automatically as part of `helm upgrade`, so there is no separate step, and no
way to pause partway once it starts.

### Breaking: the drift-events list API returns an envelope

The list endpoint returns an object instead of a bare array, so a result count
can travel with the page:

```jsonc
// before
[ { "id": "...", "severity": "CRITICAL" }, ... ]

// now
{ "items": [ { "id": "...", "severity": "CRITICAL" }, ... ], "total": 2000 }
```

If you script against the API, the change is one `jq` path:

```bash
# before
curl -s -H "Authorization: Bearer $DD_API_KEY" \
  "$DD_URL/api/drift-events" | jq '.[]'

# now
curl -s -H "Authorization: Bearer $DD_API_KEY" \
  "$DD_URL/api/drift-events" | jq '.items[]'
```

The endpoint also accepts optional `limit` (max 200) and `offset`.
**Omitting `limit` returns every matching event, exactly as before** — existing
scripts keep the same row coverage and only need the `jq` path updated.

After upgrading, **hard-reload any open browser tab**. A tab loaded before the
upgrade runs the previous UI against the new response shape and will not render
the drift-events page until it reloads.

---

## 0.1.6 and earlier — pilot series

Per-release detail is not reconstructible for this series: these releases
predate any release tagging in the backend repository, so there is no commit
range to derive a changelog from. What the series established:

- Drift and unmanaged detection across Azure, AWS and GCP via read-only
  cross-check credentials.
- State sources: Terraform Cloud and Enterprise, plus raw `.tfstate` in Azure
  Blob, AWS S3 and GCP GCS.
- Kubernetes / Helm drift detection, with no GitOps tool required.
- Multi-scope discovery with explicit per-scope enablement.
- OPA policy checks with graceful degradation.
- Helm install with an automatic schema-migration Job and an immutable Fernet
  key for credential encryption.

For what a given version can actually do, the
[feature inventory](https://cloudkeel.io/docs/claims/feature-inventory/) is authoritative — every
capability is marked Shipped or Gap — and the
[coverage page](https://cloudkeel.io/docs/claims/coverage/) carries the per-type tables.

---

## Before any upgrade

1. **Back up PostgreSQL.** It holds integrations, encrypted credentials,
   resources and drift history.
2. **Reuse the same Fernet key and wrapped data key.** Changing either makes
   every stored credential undecryptable.
3. **Check the migration count** for the jump you are making. Zero is a drop-in;
   eleven is worth rehearsing.
4. **Pin both image tags.** Backend and frontend are separate builds with
   independent shas; one tag for both causes an `ImagePullBackOff`.

Full procedure: [Upgrades](https://cloudkeel.io/docs/operations/upgrades/).

> [!NOTE]
> **Maintaining this page**
>
> One section per published release, newest first, each stating its migration
> count and any breaking change. Migration counts are derivable by diffing
> `alembic/versions/` between the two published builds. Tagging releases in the
> backend repository would make future entries derivable rather than
> hand-assembled — the `0.1.6` gap above exists because no such tags were created.

