---
title: "Glossary"
description: "Definitions for drift, unmanaged resource, scope, desired and actual state, inventory, spec, and severity."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/reference/glossary/](https://cloudkeel.io/docs/reference/glossary/)**

**Actual state** — the live configuration of a resource, read from the cloud or
Kubernetes API at scan time.

**Cross-check credential** — a read-only cloud identity (Azure Reader, an AWS/GCP
reader) that lets Cloudkeel-DD read *actual* state and detect unmanaged resources.

**Desired state** — what you declared: a Terraform Cloud workspace, a raw
`.tfstate`, or a Helm release's rendered manifest.

**Drift** — a managed resource whose actual state no longer matches its desired
state, expressed as a field-level diff.

**Drift event** — a recorded drift finding with a status (`open`, `resolved`,
`suppressed`, …), severity, category, and history.

**Fernet key** — the immutable symmetric key that encrypts stored cloud
credentials at rest. See [Secrets](https://cloudkeel.io/docs/configuration/secrets/).

**Ignore rule** — a pattern that permanently silences a *class* of resource:
existing open findings immediately, future findings at scan time. Managed in
**Settings → Ignore rules**; the API path matches (`/api/ignore-rules`). Older
material calls this a *suppression rule* — same thing, previous name. Not to be
confused with a per-finding *suppression*.

**Integration** — a connected source: a state source, a cross-check credential,
or a Kubernetes cluster.

**Managed resource** — a resource that appears in a Terraform state (or Helm
release); the opposite of *unmanaged*.

**Normalizer** — the per-resource-type logic that compares desired vs. actual on
security-relevant fields, ignoring low-signal noise (tags, server-defaulted
fields).

**Policy violation** — a finding that breaks a rule (e.g. a world-open rule, a
root container), evaluated by the policy engine.

**Scan** — one pass of ingest → live read → diff → detect → record, per
integration.

**Scope** — an account / subscription / project / cluster a credential can see.
Live verification runs only against **enabled** scopes.

**State source** — a desired-state integration: Terraform Cloud, or raw
`.tfstate` in S3 / GCS / Azure Blob.

**Suppression** — one finding deliberately silenced, recorded as its own row
with a reason. Created three ways: the **Suppress** action in a finding's
drawer (that one finding only), an **ignore rule** sweeping matching
findings, or a **maintenance window** expiring drift during a planned change.
[Which to reach for](https://cloudkeel.io/docs/claims/reducing-noise/).

**Unmanaged resource** — a live resource that no connected state declares.
