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

1. A **state source** (Terraform Cloud, or raw `.tfstate` in cloud storage)
   supplies the *desired* state.
2. A **cross-check credential** (a read-only Azure/AWS/GCP identity) lets
   Cloudkeel-DD read the *actual* live resources.

With only the state source, resources are discovered but tagged *"no live
comparison available"*: you get inventory, not drift. With only the credential,
there's nothing to compare against. **Connect both**, per cloud.

Kubernetes is the exception; one kubeconfig integration is self-contained:
desired = Helm's own stored release manifest, actual = a live read of the
Kubernetes API.

## What a scan does

1. **Ingest desired state**: parse the workspace / `.tfstate` / Helm release.
2. **Read actual state**: call the cloud or Kubernetes API for each resource,
   using the read-only credential and its enabled scopes.
3. **Diff**: per-resource, field by field, through type-specific normalizers
   that focus on security-relevant fields.
4. **Detect unmanaged**: anything live in an enabled scope that no state
   declares.
5. **Evaluate policy**: run the finding through the policy set (best-effort; a
   broken policy engine never fails the scan).
6. **Record**: open, refresh, or auto-resolve drift events with full history.

## Scopes

A **scope** is an account / subscription / project / cluster that a credential
can see. Live verification only runs against **enabled** scopes:

- **AWS and GCP** auto-enable the scope from the account ID / project ID you enter.
- **Azure** discovers your subscriptions and leaves each *disabled* until you opt
  in: a common "connected but no drift shows" cause. See
  [troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/).

## Does scanning cost anything on your cloud bill, or hit rate limits?

Every call a scan makes is a read-only, control-plane metadata call: Azure
Resource Graph, AWS's Cloud Control API (plus native EC2/IAM reads for a
handful of types it doesn't cover well), and GCP's Cloud Asset Inventory. None
of these are billed by their cloud provider - they're the same class of call
as `terraform plan`'s own refresh, not a data-plane operation like an object
download or a running workload.

**Discovering everything in a scope is close to flat cost, not
per-resource.** Each cloud's bulk listing call returns full resource
properties for many resources at once, paginated - a few calls cover
thousands of resources, not one call per resource.

**Field-level drift comparison for a state-declared resource does read that
resource individually**, one call per resource, so this part of a scan does
scale with how many resources your Terraform state or Helm release declares.
These calls are rate-limited **on Cloudkeel-DD's side first** - a
token-bucket limiter (10 requests/second by default, per credential per
scope) - so a scan paces itself well under what Azure/AWS/GCP's own quotas
allow, and every connector also recognizes a provider throttle response
(HTTP 429 / `Throttling`) and backs off and retries automatically rather than
failing the scan outright.

## By-design behaviours (not bugs)

- **Tag/label-only changes aren't flagged.** A changed cloud tag, GCP label, or
  Kubernetes label is low-signal; the normalizers focus on security-relevant
  fields (firewall/security-group rules, replica counts, images).
- **Adding a brand-new field the chart never declared isn't Kubernetes drift**:
  *changing a field the manifest owns* is. The API server defaults dozens of
  fields no chart declares; without this every resource would "drift" the moment
  it was created.
