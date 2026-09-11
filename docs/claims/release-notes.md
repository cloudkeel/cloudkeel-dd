---
title: "Release notes"
description: "Published Cloudkeel-DD releases, newest first - what changed, how many migrations each upgrade runs, and what to check before upgrading."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/release-notes/](https://cloudkeel.io/docs/claims/release-notes/)**

This is the changelog of record for public Cloudkeel-DD releases. Newest first.

## What "version" means here

Three things carry a version and they move independently. Every entry below is
the **published** version: the image tags on Docker Hub and the Helm chart in
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

## 0.3.7 (2026-08-30)

**App-only bump: no chart template or `values.yaml` change.**

- **A permission error on one resource was silently dropping every resource
  ordered after it in that scan.** Fixed for AWS and Azure state scans; the
  fix also closed the equivalent gap on GCP and corrected a short-circuit
  cache that could wrongly skip a resource type in one subscription or
  project because a *different* one had already been denied on it.
- Fixed-coverage resource types no longer report `PARTIAL` when they shouldn't.
- AWS least-privilege IAM policy scoping corrected.
- GCP default-network resources suppressed from unmanaged findings.
- An integration's scope name is no longer exposed where it shouldn't be.
- ArgoCD / Flux unmanaged-resource resolution fixed.
- Frontend: "Kubernetes" was missing as an option in the drift-events Source
  filter, added. A type-coverage warning no longer claims it "was not
  permitted"; that wording only fits the separate attribution-gap kind.
- Frontend: owner-team autocomplete, a direct ownership link from the drift
  drawer, and bulk ownership assignment.

**Upgrade cost: low.** **Zero** Alembic migrations since `0.3.6`: verified by
diffing `alembic/versions/` between the two published images. A straight
`helm upgrade`.

---

## 0.3.6 (2026-08-29)

**The full fix for the cross-tenant remediation issue `0.3.5` only partly
closed, plus an AWS false-positive fix worth knowing about.**

### Security: the cross-tenant remediation gap is now fully closed

`0.3.5` shipped a narrower guardrail for an instance-wide GitHub/GitLab
remediation credential combined with an unvalidated target repository, which
could let one tenant's remediation action reach another tenant's connected
repo. This release replaces the guardrail with the real fix: every
remediation request now validates its target repository against the
requesting tenant's own connected integration.

### Also in this release

- AWS baseline-exclusion catalog reworked: service-linked IAM roles now match
  by name, and every VPC's auto-created "Main" route table is recognized:
  fewer false "unmanaged" findings on AWS estates.
- A registration race: two concurrent signups could both create a workspace.
  Now serialized.
- Drift Events / Reports tile misattribution fixed, along with a GCP
  subnetwork region collision that was inflating drift counts.
- A running scan's progress is now visible while it's still running,
  instead of only after it finishes.
- Attribution (the "who changed it" lookup) now skips a source once it's
  known to be denied, rather than re-asking on every resource. Two GCP read
  routes that were missing entirely (network, subnetwork) are added.
- AWS gets a real per-resource live cross-check on the Terraform-plan scan
  path, matching what Azure and GCP already had.
- `diff_field_rows` added to the drift-event API response; the frontend's
  client-side computation of the same thing retired.
- Standalone IAM-role and S3-bucket Terraform children now merge into the
  expected desired-state shape instead of reporting false drift.
- GCP key expiry and AWS key age now surfaced on integrations.

**Upgrade cost: low.** **2** Alembic migrations since `0.3.5`: verified by
diffing `alembic/versions/` between the two published images:
`a3f1c9d84e27` (GitHub/GitLab integration types) and `f5b8e2a71c93`
(`integrations.credential_created_at`).

---

## 0.3.5 (2026-08-28)

**Security-hardening release, plus a major frontend framework bump. Read the
security section before upgrading if you run this exposed to any untrusted
network.**

### Security: gaps closed, found via a security audit of the backend

- **A hardcoded JWT signing secret had no startup enforcement.** The backend
  now fails fast at import time if the secret is unset, is the documented
  placeholder, or is under 32 characters, the same guard the
  credential-encryption key already had.
- **The ArgoCD connector defaulted to TLS verification off**, and downgraded
  to plaintext HTTP unless a customer explicitly opted out. Now defaults to
  verified HTTPS; skipping verification is an explicit, documented opt-in for
  self-signed certs.
- **A cross-tenant remediation gap got a narrower guardrail here**: see the
  `0.3.6` entry above for the full fix.
- **A real Fernet encryption key was committed in this repo's tracked
  `.env.example`.** Fixed going forward; the repository's git history was not
  scrubbed, so an old real key may still be recoverable from it if you cloned
  before this date.
- **`/docs`, `/redoc` and `/openapi.json` exposed the full API schema to
  unauthenticated callers.** Both now require authentication.
- **No security headers were configured for the authenticated dashboard.**
  The frontend now sets `X-Frame-Options`, a Content-Security-Policy, HSTS,
  `X-Content-Type-Options` and `Referrer-Policy`.

### Also in this release

- **Connect more than one credential per cloud.** The block on a second
  active Azure, AWS or GCP integration is gone now that the scan pipeline
  fans out across every connected credential and attributes results and
  failures to the right one; previously a second credential was accepted
  by the API but silently never scanned.
- An owner can now reset a teammate's password directly from the UI. No
  email is sent (this product still sends none); the owner sets it and
  shares it themselves, the same posture the invite flow already has.
- Policy checks now also evaluate an already-clean managed resource, not
  only new drift. This closes a real gap: a Kubernetes `Service` quietly
  becoming internet-facing via a `LoadBalancer` type change could go
  unevaluated if the change didn't otherwise register as a drift event,
  which, for a chart that omits `spec.type` entirely, it didn't.
- A GCP asset type that no longer exists now degrades gracefully instead of
  failing the whole scope.
- A local Terraform plan could close a finding it shouldn't have, via a
  merged-union comparison. Fixed.
- Un-declaring an adopted resource is reversible again; undeclaring could
  previously strand it in a state no code path could recover.
- The ignore-rules preview now names each match's source and counts them.
- Frontend upgraded from Next.js 14 to 16.3.3, closing 21 known advisories on
  the old version.

**Upgrade cost: low.** **1** Alembic migration since `0.3.4`: verified by
diffing `alembic/versions/` between the two published images
(`b7d2e9c4a115_resources_workspace_source_index`).

---

## 0.3.4 (2026-08-20)

**The licensing epic: seats, scopes, and the pilot timer's most important
behavior change.**

> [!NOTE]
> **About 0.3.3**
>
> `0.3.3` was cut in git (closed registration by default) but **never
> published**; its chart and code changes are folded into this release
> instead. If you are upgrading from `0.3.2`, this section covers everything
> you get.

### The pilot timer converts to Free instead of stopping

Previously (`0.3.0`–`0.3.3`), an install's 30-day unmetered window ended by
stopping new scans. From this release, it settles onto the **Free ceiling**
instead: 1 enabled scope, 3 users, every feature, forever. Findings, history,
integrations and login all keep working; one scope keeps scanning on its
normal schedule; scopes past the ceiling are held back and say so on their
own row; nothing is deleted.

### Also in this release

- Signed licence-key format and an offline verifier: a licence key is
  checked entirely inside your cluster; nothing phones home.
- Per-scope and per-seat gates, both decided under a single lock to avoid a
  race at the boundary.
- New workspace registration closes itself after the first workspace is
  created (`config.allowOpenRegistration` in Helm values overrides this).
- The Settings → Licence page: tier, usage, cloud split, and key entry.
- A vendor-side licence-key-generation script.
- A licence refusal now reads as a plain sentence instead of a raw JSON blob.
- The pilot banner no longer claims scanning has stopped when it has not.

**Upgrade cost: low.** **2** Alembic migrations since `0.3.2`: verified by
diffing `alembic/versions/` between the two published images:
`a4f81c6b23d9` (one pending invite per tenant/email) and `c1f4a90bd275`
(install-metadata licence key).

---

## 0.3.2 (2026-08-16)

**Patch. One additive migration.**

- A denied IAM permission no longer looks identical to "no actor found" on a
  finding.
- Slack alerts for a widened security rule were silently dropping the message
  (Slack's `mrkdwn` was eating the asterisks); failed sends now log instead
  of vanishing.
- Adopting an unmanaged resource now closes the finding it makes unreachable;
  previously unclosable by any code path.
- Cross-source verification now counts AWS and GCP, not only Azure.
- Observation partitions trapped outside the create-ahead window now
  recover.
- The chart's own policy-check step loads the rendered ConfigMap into a real
  OPA instance instead of a stub.
- A rejected settings toggle is now surfaced instead of silently swallowed.

**Upgrade cost: low.** **1** Alembic migration since `0.3.1`: verified by
diffing `alembic/versions/` between the two published images
(`c9d3a71e4b52_capability_warnings_47`).

---

## 0.3.1 (2026-08-12)

**Republished after `0.3.0`'s images were deleted from Docker Hub: see the
warning on the `0.3.0` entry below.** Ships whatever had merged to `main` in
the six days between the two publishes, not a rebuild of the same code.

- The `Cloudkeel-DD` rename reached the running app itself: UI strings and
  prose, not just the marketing site.
- Findings and the Kubernetes dashboard now say which cluster they came
  from; AKS, EKS and GKE get their own dashboard card again instead of one
  shared card.
- Two stale coverage figures corrected: the frontend's landing page was
  stuck advertising 22 spec'd types after the registry had already reached
  200, and the backend's own least-privilege docs still said 6 AWS / 6 GCP
  specs instead of 62 / 59.
- The two heaviest routes stopped being prefetched from the nav, for load
  performance.

**Upgrade cost: low.** **Zero** Alembic migrations since `0.3.0`: verified
by diffing `alembic/versions/` between the two published images. A straight
`helm upgrade`.

---

## 0.3.0 (2026-08-06)

> [!WARNING]
> **This chart's images are gone from Docker Hub**
>
> `driftdetective/ddetective-backend:0.3.0` and `-frontend:0.3.0` were deleted
> on 2026-08-12, while the `0.3.0` chart itself stayed published. `helm install
> --version 0.3.0` still **succeeds** and then `ImagePullBackOff`s on every
> pod. Use `0.3.1` or later; see its entry above.

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
whichever is later (your first workspace, or the first time this install ran a
version that enforces the timer), so a long-running install gets a full window
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

**Upgrade cost: moderate.** **5** Alembic migrations since `0.2.1`: verified by
diffing `alembic/versions/` between the two published images. Back up PostgreSQL
first, as with any schema step.

---

## 0.2.1 (2026-07-29)

**Drop-in patch. No migrations.**

- Tolerance for `PARTIAL` scan outcomes on the Kubernetes, ArgoCD and Flux scan
  paths, so one failing source no longer discards the rest of a scan's findings.
- A frontend fix carried over from the previous release.

**Upgrade cost: low.** **Zero** Alembic migrations since `0.2.0`: verified by
diffing `alembic/versions/` between the two published builds. A straight
`helm upgrade`.

---

## 0.2.0 (2026-07-29)

**The largest schema step shipped so far. Rehearse before upgrading.**

- Field-level cross-check generalised beyond its original hardcoded types, so
  shipped specs power the raw-state path. This is what took AWS raw-state
  coverage from security-groups-only to all six AWS types, and GCP to four.
- Severity and category corrections for AWS security groups and GCP firewall
  rules.
- Drift-events pagination, including the API change below.

**Upgrade cost: high.** **11** Alembic migrations since `0.1.6`: anyone coming
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
**Omitting `limit` returns every matching event, exactly as before**: existing
scripts keep the same row coverage and only need the `jq` path updated.

After upgrading, **hard-reload any open browser tab**. A tab loaded before the
upgrade runs the previous UI against the new response shape and will not render
the drift-events page until it reloads.

---

## 0.1.6 and earlier (pilot series)

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
[feature inventory](https://cloudkeel.io/docs/claims/feature-inventory/) is authoritative: every
capability is marked Shipped or Gap, and the
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
> hand-assembled: the `0.1.6` gap above exists because no such tags were created.
