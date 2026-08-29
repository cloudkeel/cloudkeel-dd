---
title: "GCP Terraform state (raw `.tfstate` in GCS) setup"
description: "Connect raw .tfstate objects in a GCS bucket as a desired-state source, using a bucket-scoped read-only service account."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/gcp-state/](https://cloudkeel.io/docs/integrations/gcp-state/)**

This connects Cloudkeel-DD to raw `.tfstate` objects sitting in a GCS bucket,
so it can ingest Terraform state directly instead of going through Terraform
Cloud/Enterprise. It's a **separate, narrow credential** from the GCP service
account used for live-resource cross-checking (Settings -> Cross-check
integrations -> GCP) - the two are independent and safely coexist. This one
uses a storage-only OAuth scope (`devstorage.read_only`), narrower than the
live-resource credential's project-wide `cloud-platform` scope.

## 1. Create a dedicated service account

In the GCP Console: IAM & Admin -> Service Accounts -> **Create service
account**. No roles needed at creation time - grant access at the bucket
level in the next step instead of project-wide.

## 2. Grant it read-only access to just one bucket

Cloud Storage -> your bucket -> **Permissions** -> **Grant access** -> add
the service account with role `Storage Object Viewer`
(`roles/storage.objectViewer`), or bind the narrower custom role in
`docs/gcp-gcs-state-iam-roles.json` (just `storage.objects.get` +
`storage.objects.list`) instead. Either way, grant it at the **bucket**
level, not the project level:

```
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET_NAME \
  --member="serviceAccount:YOUR_SA_EMAIL" \
  --role="roles/storage.objectViewer"
```

## 3. Generate a JSON key

Same service account -> **Keys** -> **Add key** -> **Create new key** ->
JSON. Download it - this is the `service_account_json` Cloudkeel-DD needs.

## 4. Connect it in Cloudkeel-DD

Settings -> **Terraform state sources** -> **+ Add storage source** -> GCP:

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-tfstate` |
| Bucket | The GCS bucket name |
| Prefix (optional) | Restrict discovery to one folder, e.g. `envs/` |
| Project ID | The GCP project id the bucket lives in |
| Service account JSON | Upload or paste the key file from step 3 |

Click **Test connection** to confirm Cloudkeel-DD can list `.tfstate` objects,
then **Save and start scanning**. Discovered state files appear as
`discovered` - nothing is scanned until you explicitly **Enable** each one
(opt-in, same lifecycle as multi-scope project discovery).

## 5. Connect a live GCP credential too, for drift detection

Without a live-resource GCP credential (Settings -> Cross-check integrations
-> GCP) connected, resources parsed from state are still discovered and shown
in Inventory, but tagged **"no live comparison available"**. Connect the GCP
cross-check credential (for the same project) to get real drift detection on
the state-diffable types described below.

## What gets ingested

Only `google_*` resources are read from state today. Other providers'
resources in a mixed state file are counted but not persisted.

**Live-diffed from raw state — all 59 GCP types.** GCP has no per-path gap:
every spec'd type is reachable from raw `.tfstate` exactly as it is from a
Terraform plan, so choosing a state source costs you no GCP coverage. The
[coverage page](https://cloudkeel.io/docs/claims/coverage/) lists all 59, generated from the
product's own type registry.

A `google_*` type with no field-diff spec is enumerated for unmanaged detection
but never field-diffed — it stays inventory-only, labelled with the reason. An
unverified field mapping risks confident-looking false drift, which is worse
than an honest "not yet diffed."
