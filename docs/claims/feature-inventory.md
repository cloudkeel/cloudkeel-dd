---
title: "Feature inventory"
description: "Everything Cloudkeel-DD ships today, area by area, with the honest gaps listed at the end."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/feature-inventory/](https://cloudkeel.io/docs/claims/feature-inventory/)**

Configuration-drift detection for Azure, AWS, GCP, Terraform, Kubernetes, ArgoCD,
and Flux — with policy-as-code enforcement and CI/CD integration.

Every capability below is **shipped** and running in the reference deployment.
Coverage is stated honestly: capabilities that aren't fully field-diffed are
tracked as **inventory** and clearly labelled, and the [Known gaps](#known-gaps)
at the end are stated plainly, not hidden. Where a coverage claim uses the word
*verified*, it means one of two bars — **engine-verified** (passes golden-fixture
tests) or **proven against a real cloud account** (exercised end-to-end against
live infrastructure). See the [coverage page](https://cloudkeel.io/docs/claims/coverage/) for the
per-type tables.

## Connectors & data sources

How Cloudkeel-DD learns what's actually running.

| Feature | Description | Status |
|---|---|---|
| ArgoCD connector | Live managed-resource state via the ArgoCD API. | Shipped |
| Terraform Cloud / Enterprise connector | Pulls declared state and Terraform's own drift report directly from the Terraform Cloud / Enterprise API. | Shipped |
| Terraform local-state connector | Reads a local `terraform show -json` plan file directly — no Terraform Cloud account needed. | Shipped |
| Azure Resource Manager connector | Reads AKS, load balancers, NSGs, public IPs, route tables and more, for cross-check and unmanaged-resource detection. | Shipped |
| AWS connector | Reads security groups, load balancers, EIPs, route tables, EKS clusters, IAM roles/policies, S3, KMS, and RDS via the AWS Cloud Control API — read-only. | Shipped |
| GCP connector | Reads GKE clusters, firewall rules, load balancers, Compute instances, Cloud SQL, IAM, service accounts, GCS, and KMS via Cloud Asset Inventory — read-only. | Shipped |
| Flux connector | HelmRelease / Kustomization drift via the Kubernetes API. | Shipped |
| Kubernetes / Helm direct connector | Drift detection for clusters with no GitOps tool at all — compares Helm's stored release manifest ("desired") against a live API read ("actual"), ignoring API-server-defaulted fields. Uses a read-only ServiceAccount kubeconfig; works across AKS, EKS, and GKE, each cluster scoped independently. | Shipped |
| Per-integration sync schedule | Set each integration to manual, or one of five cadences in the UI — every 15 minutes, 30 minutes, hourly, 6 hours, or daily. A scheduler checks every minute and triggers due scans through the same path as a manual run. Only one scan per integration runs at a time — a second trigger reuses the in-flight scan rather than queueing a duplicate. | Shipped |

## Drift detection engine

Turning raw state into a signal worth acting on.

| Feature | Description | Status |
|---|---|---|
| Diff engine + severity classifier | Every drift is scored harmless / risky / critical. | Shipped |
| Declarative normalizer engine | Field-level drift rules are **data, not code**: each resource type is a reviewable YAML spec run by a pure engine, with a semantics library that absorbs schema-shape, protocol, CIDR, port, and ordering noise so none of it registers as false drift. Every spec ships golden fixtures, and a CI gate blocks any change that would produce phantom drift. Adding a type is a spec + fixtures — no code. | Shipped |
| Azure ↔ Terraform cross-check | Terraform's self-reported state is independently re-verified against live Azure. **79 Azure types are engine-verified (golden fixtures)**; the plan path cross-checks 68, the raw-state path 77 (role assignments and role definitions have no ARM api-version entry). A far smaller subset — **NSG rules** — is **live drift-proven against a real Azure subscription**. | Shipped |
| GCP ↔ Terraform cross-check | Same independent re-verification on GCP. **59 GCP types are engine-verified (golden fixtures)**; both paths cross-check all 59 — GCP is the only cloud with no per-path gap. A far smaller subset — **firewall rules** — is **live drift-proven against a real GCP project**: a 2026-07-25 run detected an added port on a managed rule at field level, plus an unmanaged rule. | Shipped |
| AWS ↔ Terraform cross-check | Same on AWS, with real false-drift protection: security-group rules are canonicalized so AWS's rule coalescing and Terraform's separately-declared blocks never register as a difference, and protocol aliases are normalized. **62 AWS types are engine-verified (golden fixtures)**; the raw-state path cross-checks all 62, the plan path exactly **one** — `aws_security_group`. That 62-against-1 gap is the largest coverage asymmetry in the product. A far smaller subset — **security-group rules** — is **live drift-proven against a real AWS account**: a 2026-07-25 run detected an added `0.0.0.0/0` SSH ingress rule at field level, plus an unmanaged security group. | Shipped |
| Unmanaged-resource detection (cloud) | Flags live resources with zero Terraform tracking, across the enumerated high-value types on Azure, AWS, and GCP (see the [coverage page](https://cloudkeel.io/docs/claims/coverage/) for the exact set). Requires a connected Terraform state source to define what "managed" means — a cloud credential on its own produces no findings. | Shipped |
| Unmanaged-resource detection (Kubernetes) | Lists every object of the six supported kinds and flags the ones no tool claims. Ownership is read from each object's own metadata — Helm's `app.kubernetes.io/managed-by` label and `meta.helm.sh/release-name` annotation, or ArgoCD's tracking-id annotation and instance labels — so it needs no Terraform state source, no GitOps-tool credentials and no CRD access, and it catches operator-created objects. An object whose ownership metadata has been stripped reads as unmanaged. | Shipped |
| Out-of-band change detection (Kubernetes) | Reports which tool last wrote a Kubernetes object when that is not the tool managing it — a hand-run `kubectl` against a Helm-managed workload, for example. Read from `metadata.managedFields`, which the API server maintains itself, so it needs no allowlist of deployment tools. Shown on the finding as "changed outside your pipeline", with the tools named. | Shipped |
| Unmanaged detection aggregates across all a tenant's Terraform integrations | A resource declared in *any* of a tenant's Terraform configs counts as managed — not just the one integration being scanned — and an open unmanaged finding auto-resolves once the resource becomes Terraform-managed. | Shipped |
| Changed-by attribution | Who last touched a resource — wired into the event pipeline on **all three clouds**: Azure Activity Log, AWS CloudTrail, and GCP Cloud Audit Logs. Best-effort and bounded: a **72-hour lookback** and a **5-page cap** per query, each behind an optional per-cloud read permission. A miss leaves the field blank and never fails a scan. See [Who changed it](https://cloudkeel.io/docs/usage/who-changed-it/). | Shipped |
| Duplicate-event prevention | A re-scan of still-drifted infra refreshes the existing event in place (and auto-resolves it when the drift is gone) instead of piling up duplicates. | Shipped |
| Human-readable diff summaries | Plain-English descriptions of what changed, not raw field dumps. | Shipped |
| Multi-source correlation | The Terraform-vs-live cross-check result is surfaced on the drift-event drawer and as a Reports stat — real cross-source agreement/disagreement, not just multiple sources in one dashboard. | Shipped |
| Seriousness gate | Every drift is evaluated against a per-tenant, editable rule set (resource type × environment × category → severity, most-specific match wins). Not-serious drift is still recorded for history/reports but auto-closed and never alerted. Seeded with sensible defaults, editable from the Policies page. | Shipped |
| Rule edits reach findings that already exist | Editing a severity, ignore or baseline rule — or shipping a new normalizer spec — re-scores findings whose configuration has not changed since they were raised. Previously a stored verdict was only revisited when the resource's own config next moved, which for stable infrastructure could be never. Each scan records the scoring inputs it used, so a re-score is triggered by the inputs changing rather than by anyone remembering to bump a version. | Shipped |

## Policy-as-code

Real OPA/Rego evaluation, not a rules-engine mockup.

| Feature | Description | Status |
|---|---|---|
| Four built-in policies | Critical drift needs an owner · no open ingress from anywhere · no public exposure without exception · containers must not run as root. | Shipped |
| Policy evaluation on every scan | A dedicated OPA sidecar evaluates every drifted resource as it's found. | Shipped |
| Per-tenant policy toggle | Turn any policy on or off from the Policies page. | Shipped |
| Violations surfaced in the UI | A badge on Drift Events, full detail in the drawer, plus a dedicated Policies page. | Shipped |

## Drift lifecycle & resolution

What happens to a drift event after it's detected — a real state machine, not a single "resolved" checkbox.

| Feature | Description | Status |
|---|---|---|
| Accept | Marks live reality as correct — the team is expected to update their IaC/GitOps source to match. Detection stays read-only; this only records the claim. | Shipped |
| Revert plan | Generates a suggested, field-level plan for pushing reality back to the desired state, built from the computed diff. Never applied automatically — review and run it yourself. | Shipped |
| Suppress with reason + expiry | Suppressing requires a reason (enforced server-side) and supports an optional expiry; a scheduled task auto-reopens expired suppressions. | Shipped |
| Promote | Manually reopens an auto-closed (not-serious) event — "actually, this does matter." Restricted to auto-closed events. | Shipped |
| Re-scan verification | Accept/revert claims move an event to "awaiting re-scan" — it only becomes Resolved once the next scan of that resource confirms the drift is gone, and bounces back to Open if it isn't. | Shipped |
| Append-only event history | Every status change is recorded as its own immutable row — no update/delete path exists, enforced structurally. | Shipped |

## Remediation

Turning a detected drift into a fix.

| Feature | Description | Status |
|---|---|---|
| GitHub PR-based remediation | Opens a real pull request with the reconciling patch. | Shipped |
| GitLab MR-based remediation | Same flow, opens a merge request instead. | Shipped |
| Approval gate for critical severity | A human must approve before a critical-severity PR/MR opens. | Shipped |
| Codify (unmanaged → Terraform `import{}` PR) | Turns an unmanaged resource into a Terraform `import{}` block and opens a GitHub PR / GitLab MR to bring it under management. | Shipped |

## CI/CD integration

Shift-left — catching drift before it merges, not just after.

| Feature | Description | Status |
|---|---|---|
| API key authentication | Tenant-scoped machine credentials for CI pipelines. | Shipped |
| Pre-merge policy gate | CI submits a Terraform plan; the same OPA policies check it before merge. | Shipped |
| Post-deploy scan trigger | CI kicks off an immediate scan right after a deploy. | Shipped |
| GitHub Actions + GitLab CI templates | Real, runnable copy-paste pipeline configs, not just documented endpoints. | Shipped |
| PR/MR status + comment posting | A commit status and a violations comment posted back to the PR/MR itself, not just the CI job log. | Shipped |

## Dashboard & reporting

Where a team actually spends its time.

| Feature | Description | Status |
|---|---|---|
| Drift Events | Stats strip, quick filters, platform boxes, row-click drawer. | Shipped |
| Inventory | Every integration and resource, with edit / delete / sync-now. | Shipped |
| Reports | Summary, weekly trends, MTTR, ownership gaps, CSV export, date-range filters. | Shipped |
| Resource detail | Full expected-vs-actual diff plus remediation actions. | Shipped |
| Connect / onboarding | Guided multi-provider setup with test-before-save and live connection status. | Shipped |

## Notifications & suppression

Controlling the signal-to-noise ratio.

| Feature | Description | Status |
|---|---|---|
| Slack / webhook notification rules | Route findings to Slack or a generic webhook, filtered by severity, category, and owning team. | Shipped |
| Test-notification sending | A real send-and-verify, not a fake green check. | Shipped |
| Ignore rules | Silence known-noisy patterns, with a live preview of what a rule would match. | Shipped |
| Maintenance windows | Auto-suppress drift events raised during a scheduled change window (e.g. a planned deploy), so expected churn doesn't alert. | Shipped |
| Drift-resolved announcements | When a finding resolves, the same channels that were told about it are told it is fixed — so a quiet channel means "nothing is wrong", not "the integration broke". | Shipped |
| Per-destination delivery ledger | Every notification attempt is recorded per destination, so "was Slack actually told?" is an answerable question rather than an inference from the absence of an error. | Shipped |

## Multi-tenancy, auth & identity

The foundation everything else sits on.

| Feature | Description | Status |
|---|---|---|
| Tenant & user registration, JWT login | Standard email/password auth, scoped per tenant. | Shipped |
| Per-tenant data isolation | Every query scoped to the caller's tenant. | Shipped |
| Role-based access control | Owner / admin / viewer roles, enforced on every mutating endpoint — not just hidden buttons. | Shipped |
| Team invites via shareable link | Working signup links (no email infrastructure needed) to bring a teammate into an existing workspace. | Shipped |
| Credentials encrypted at rest | Integration secrets (tokens, kubeconfigs) are encrypted transparently at the data layer. | Shipped |
| Audit log | Who did what, when — login, integration, drift-event, remediation, policy, user, and API-key actions, with IP address; admin+ visible, 365-day auto-purge. | Shipped |
| Rate limiting | Per-tenant and stricter per-IP limits on auth endpoints; fails open if the rate-limit store is briefly unreachable. | Shipped |
| Designed visual identity | A designed theme system with a custom logo and an original icon set for every connector. | Shipped |

## Observability & operations

Running this in production, not just on a laptop.

| Feature | Description | Status |
|---|---|---|
| Deep health check | `/health/detailed` round-trips Postgres, Redis, and OPA for real — a readiness probe distinct from the cheap `/health` liveness probe. | Shipped |
| Structured JSON logging | Every log line is structured JSON, in both the API and worker processes. | Shipped |
| Scheduled data retention | A daily job purges snapshots (90 days), resolved/false-positive drift events (365 days), and audit logs (365 days). | Shipped |
| Integration health signals | A real last-error surfaces in Inventory and the Reports healthy/failed counts — written on a scan or cross-check failure, and cleared on recovery. | Shipped |
| Partial-failure scan semantics | One cross-check cloud failing mid-scan (revoked credential, throttle) no longer discards the scan's other findings — the scan finishes `PARTIAL` with results kept and the failing integration flagged. | Shipped |
| One active credential per cloud, per tenant | Exactly one active cross-check credential per cloud is scanned; creating or re-activating a duplicate is rejected loudly rather than silently ignored. (That credential can span many subscriptions via scopes.) | Shipped |
| Multi-scope: one Azure credential, many subscriptions | Connect one Azure service principal once; Cloudkeel-DD discovers its subscriptions into an opt-in list and scans each **enabled** one independently, with per-subscription failure isolation and 6-hourly re-discovery. | Shipped |
| Multi-scope discovery for AWS / GCP | Multi-account (AWS Organizations) / multi-project (GCP) discovery under one credential is not built yet. The common case — one credential, one account/project — works on all three clouds. | Gap |
| AWS / GCP account & project scope self-service | Connecting or updating an AWS or GCP cross-check credential auto-creates a real account/project scope (AWS via `GetCallerIdentity`, GCP from the supplied project id), so a state file goes straight to live comparison. | Shipped |
| Raw `.tfstate` ingestion (Azure Blob) | Register an Azure Storage container via a narrow, read+list SAS token (separate from the live-resource credential), auto-discover `.tfstate` blobs (opt-in per file), and diff each `azurerm_*` resource against a live read by resource ID. Resources whose subscription has no connected credential are tracked as honest inventory. Not yet in the onboarding wizard. | Shipped |
| Raw `.tfstate` ingestion (AWS S3) | The same, for an S3 bucket via a bucket-scoped IAM credential. Field-diffs **all 62 spec'd AWS types**, against the plan path's one — this is by far the broader AWS path, and the one to prefer. `aws_eip` and `aws_route_table` are enumerated for unmanaged detection but have no spec, so they stay inventory. Not yet in the onboarding wizard. | Shipped |
| Raw `.tfstate` ingestion (GCP GCS) | The same, for a GCS bucket via a bucket-scoped service account. Field-diffs **all 59 spec'd GCP types** — the same set the plan path reaches, so a state source costs no GCP coverage. Other types are tracked as honest inventory. Not yet in the onboarding wizard. | Shipped |

## Deployment & packaging

Shipping it to a customer's cluster, not just running it on a laptop.

| Feature | Description | Status |
|---|---|---|
| Production container images | Multi-stage, non-root images published publicly on Docker Hub; the backend image serves API, worker, and beat (by command), and the frontend is a real production build. | Shipped |
| Helm chart for Kubernetes | One chart deploys the whole product (backend / worker / beat / frontend / OPA), a per-release database migration Job, bundled single-replica PostgreSQL + Redis (or bring your own), and one Ingress routing `/` to the frontend and `/api` same-origin to the backend. Verified end-to-end on a real AKS cluster. | Shipped |

## Known gaps

Stated plainly, not hidden.

- **No billing or monetization.** No plans, entitlements, or payment integration.
- **No SSO/SAML.** Standard email/password + JWT only.
- **CI/CD API key is not per-endpoint scoped.** One tenant-scoped API key can call any `/api/ci/*` endpoint for its tenant; there's no per-endpoint permission scoping yet.
- **Multi-scope is Azure-complete; AWS/GCP discovery is still pending.** Multiple Azure subscriptions per tenant work end-to-end; AWS accounts and GCP projects run as one scope each until multi-account/multi-project discovery lands.
- **Raw `.tfstate` ingestion has three v1 limitations.** (1) A resource seen via both a plan-JSON integration and a raw-state integration is tracked twice (no cross-source merge yet). (2) It's connectable from Settings only, not the onboarding wizard. (3) Credentials don't auto-refresh — an expired token surfaces as a per-file error, and rotation is a manual action.
- **Live field-level cross-check is narrower than the connectors, and is path-dependent.** The engine ships 200 golden-fixture-verified specs (79 Azure / 62 AWS / 59 GCP), but which are cross-checked depends on where the desired state comes from: the Terraform plan path covers 68 Azure, 59 GCP and AWS security groups only; the raw-state path covers 77 Azure, 62 AWS and 59 GCP. Everything else discovered is tracked as honest inventory. See the [coverage page](https://cloudkeel.io/docs/claims/coverage/). A type with no spec is reported as **unchecked** rather than silently skipped, so the narrowness is visible in the product instead of looking like a clean result. A malformed spec costs only its own type's precision — it can no longer stop a scan.
- **Real-cloud proof is far narrower than engine verification, and the gap widened in 2026.** All 200 specs pass golden fixtures; the subset with drift injected into a live account and detected field-level is **three cloud resource types**: **Azure** NSG rules, **AWS** security-group rules, **GCP** firewall rules — plus Kubernetes drift across real AKS, EKS and GKE clusters. The engine bar grew 9.1× without the proof bar moving at all, so the ratio is now 200 to 3. Treat that as the honest boundary — a spec passing golden fixtures is not the same as a mapping confirmed against a live API.
- **Email and PagerDuty notification channels are not implemented.** The data model accepts those channel names, but only Slack and generic webhook have a payload builder — every delivery is an HTTP POST to the rule's own webhook URL. Selecting an unimplemented channel does not deliver anything.
- **Maintenance windows only apply at the moment a finding is created.** A window never suppresses a finding that already exists, and never re-suppresses one that reopened during the window — so a human's explicit un-suppress is never silently overridden.
- **Out-of-band Kubernetes detection has two limits.** (1) It annotates a finding that already exists rather than raising its own, because a resource can carry only one active finding at a time — so it is not separately countable or filterable, and a workload that was hand-edited but is otherwise clean shows nothing. (2) A hand-edit that only ADDS a field the Helm chart never declared (an annotation, a label, an extra env var) produces no drift and therefore nothing to annotate — the scan deliberately ignores fields the chart never mentioned, otherwise every server-side default would look like drift. In short: it reports hand-edits that also changed something the chart declares. Note this is a *different mechanism* from Kubernetes unmanaged detection, which does visit objects created entirely by hand — see the [coverage page](https://cloudkeel.io/docs/claims/coverage/).
- **Kubernetes unmanaged detection trusts object metadata.** Ownership is read from the labels and annotations Helm and ArgoCD stamp on what they create. An object whose ownership metadata has been stripped reads as unmanaged. That is arguably the honest answer — nothing on the object claims it — but it is a real source of false positives in clusters that rewrite labels.
- **The Reports "top clusters by drift" widget is inactive.** It relies on a cluster grouping that isn't populated yet, so it renders empty.
