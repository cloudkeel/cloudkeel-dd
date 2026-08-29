---
title: "Terraform Cloud / Enterprise setup"
description: "Connect a Terraform Cloud or Terraform Enterprise workspace as your desired-state source - the recommended first integration."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/terraform-cloud/](https://cloudkeel.io/docs/integrations/terraform-cloud/)**

This connects Cloudkeel-DD to your Terraform Cloud or Terraform Enterprise
workspaces. It's the **recommended first source** - what Cloudkeel-DD compares
live infrastructure against.

Cloudkeel-DD reads your workspaces. It does not run `plan`, run `apply`, or
replace your Terraform runner - it verifies what your runner believes.

## 1. Find your organization slug

It's in your workspace URL:

```
https://app.terraform.io/app/<organization>/workspaces/<workspace>
                               ^^^^^^^^^^^^^^
```

## 2. Create an API token

**Terraform Cloud -> Settings -> Tokens** - either a **user token** or a **team
token**. Copy it; it's shown once.

A team token scoped to just the workspaces you want read is the tighter option.
Read access is enough - Cloudkeel-DD never queues runs or modifies workspaces.

## 3. Connect it in Cloudkeel-DD

**Connect** -> **Terraform Cloud** (the default, marked Recommended):

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-terraform-cloud` |
| Address | `app.terraform.io` for Terraform Cloud. For Terraform Enterprise, your own hostname |
| Organization | The slug from step 1 |
| API token | From step 2 |
| Sync schedule | Manual, or every 15min / 30min / hourly / 6h / daily |

Click **Test connection** - it reports how many workspaces it found - then
**Save and start scanning**. A first scan starts automatically; results usually
appear within a minute or two.

## 4. Connect a live cloud credential too

On its own, this integration tells you what Terraform *reports*. Pair it with a
cross-check credential and Cloudkeel-DD independently re-verifies each resource
against the live cloud API, and finds resources no Terraform state knows about:

- **[Azure](https://cloudkeel.io/docs/integrations/azure-cross-check/)** - the recommended pairing
- **[AWS](https://cloudkeel.io/docs/integrations/aws-cross-check/)** · **[GCP](https://cloudkeel.io/docs/integrations/gcp-cross-check/)**

## What gets ingested

Cloudkeel-DD reads each workspace's `resource_drift` - Terraform's own record of
what changed outside Terraform - plus the declared resource set used for
unmanaged-resource detection.

Resources declared in **any** of your Terraform integrations count as managed,
not just the one being scanned. So a resource declared in workspace A won't be
falsely reported as unmanaged while scanning workspace B.

## Alternatives

- **No Terraform Cloud?** Keep raw `.tfstate` in cloud storage instead:
  [Azure Blob](https://cloudkeel.io/docs/integrations/azure-state/) ·
  [S3](https://cloudkeel.io/docs/integrations/aws-state/) · [GCS](https://cloudkeel.io/docs/integrations/gcp-state/).
- **Local plan file?** The `terraform_local` integration type reads a
  `terraform show -json` plan directly - no Terraform Cloud account needed.
- **GitOps instead of Terraform?** [Kubernetes/Helm](https://cloudkeel.io/docs/integrations/kubernetes/),
  Argo CD, and Flux are all supported sources.
