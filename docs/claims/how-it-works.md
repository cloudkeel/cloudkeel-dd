---
title: "How drift detection works"
description: "How a scan compares declared desired state against a live read of your cloud, and what it does with the difference."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/how-it-works/](https://cloudkeel.io/docs/claims/how-it-works/)**

Cloudkeel-DD compares **desired state** against **actual state** on every scan.

```
desired (what you declared)          actual (what's really running)
─────────────────────────────        ──────────────────────────────
Terraform Cloud workspace      ┐
raw .tfstate in S3/GCS/Blob    ├──►   live cloud read (Azure/AWS/GCP APIs)
Helm release record (k8s)      ┘      live Kubernetes API read
                     │                          │
                     └──────────►  diff  ◄──────┘
                                     │
                          drift · unmanaged · policy
```

## The two halves

Most clouds need **two** integrations working together:

1. A **state source** — Terraform Cloud, or raw `.tfstate` in cloud storage —
   supplies the *desired* state.
2. A **cross-check credential** — a read-only Azure/AWS/GCP identity — lets
   Cloudkeel-DD read the *actual* live resources.

With only the state source, resources are discovered but tagged *"no live
comparison available"*: you get inventory, not drift. With only the credential,
there's nothing to compare against. **Connect both**, per cloud.

Kubernetes is the exception — one kubeconfig integration is self-contained:
desired = Helm's own stored release manifest, actual = a live read of the
Kubernetes API.

## What a scan does

1. **Ingest desired state** — parse the workspace / `.tfstate` / Helm release.
2. **Read actual state** — call the cloud or Kubernetes API for each resource,
   using the read-only credential and its enabled scopes.
3. **Diff** — per-resource, field by field, through type-specific normalizers
   that focus on security-relevant fields.
4. **Detect unmanaged** — anything live in an enabled scope that no state
   declares.
5. **Evaluate policy** — run the finding through the policy set (best-effort; a
   broken policy engine never fails the scan).
6. **Record** — open, refresh, or auto-resolve drift events with full history.

## Scopes

A **scope** is an account / subscription / project / cluster that a credential
can see. Live verification only runs against **enabled** scopes:

- **AWS and GCP** auto-enable the scope from the account ID / project ID you enter.
- **Azure** discovers your subscriptions and leaves each *disabled* until you opt
  in — a common "connected but no drift shows" cause. See
  [troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/).

## By-design behaviours (not bugs)

- **Tag/label-only changes aren't flagged.** A changed cloud tag, GCP label, or
  Kubernetes label is low-signal; the normalizers focus on security-relevant
  fields (firewall/security-group rules, replica counts, images).
- **Adding a brand-new field the chart never declared isn't Kubernetes drift** —
  *changing a field the manifest owns* is. The API server defaults dozens of
  fields no chart declares; without this every resource would "drift" the moment
  it was created.
