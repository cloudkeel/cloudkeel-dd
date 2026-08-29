---
title: "GCP cross-check setup (live verification)"
description: "Create the read-only GCP custom role, bind it to a service account, and connect it for live verification of Terraform state."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/gcp-cross-check/](https://cloudkeel.io/docs/integrations/gcp-cross-check/)**

This connects Cloudkeel-DD to the live GCP APIs so it can **independently verify**
what Terraform claims, and find resources Terraform doesn't know about at all.

It's a **read-only** credential - Cloudkeel-DD never modifies GCP resources. It's
also a **separate credential** from the bucket-scoped one used for
[raw `.tfstate` in GCS](https://cloudkeel.io/docs/integrations/gcp-state/); the two are independent and
safely coexist.

## 1. Enable the Cloud Asset API

Cloudkeel-DD reads your GCP inventory through **Cloud Asset Inventory** - one
query returns every asset type at once. The API must be enabled on the project
before any scan can work, and enabling it is separate from granting
permissions.

```bash
gcloud services enable cloudasset.googleapis.com --project <your-project-id>
```

> **Skip this and the whole GCP scope fails, not just one type.** Without it,
> scans report *"Cloud Asset API has not been used in project `<number>` before
> or it is disabled"*. Unlike AWS - where each resource type is listed
> separately and fails independently - Cloud Asset Inventory is a single query
> covering all types, so there is no per-type boundary to degrade on. One
> missing API means the entire GCP scope returns nothing.
>
> Enabling takes a few minutes to propagate. If a scan run immediately
> afterwards still fails, wait and retry before changing anything else.

## 2. Create a service account

GCP Console: **IAM & Admin -> Service Accounts -> Create service account**. No
roles at creation time - the next step grants exactly what's needed.

```bash
gcloud iam service-accounts create ddetective-connector \
  --project <your-project-id> \
  --display-name "Cloudkeel-DD read-only connector"
```

## 3. Create and bind the read-only custom role

Use the exact role definition in [`gcp-iam-roles.json`](https://cloudkeel.io/docs/assets/gcp-iam-roles.json) —
65 read-only permissions: Cloud Asset Inventory listing, plus a `.get` for every
GCP type Cloudkeel-DD field-diffs. Nothing that writes.

> [!WARNING]
> **Already created this role? It grew from 16 permissions to 63**
>
> The role carried `.get` on nine resource kinds while GCP coverage grew to 59
> types. **Which path you use decides whether that affected you:**
>
> - **Terraform Cloud / plan path — unaffected.** It reads through Cloud Asset
>   Inventory in bulk, which `cloudasset.assets.listResource` alone covers.
> - **Raw `.tfstate` in GCS — affected.** That path reads each resource through
>   its own REST `GET`, so a type whose `.get` is missing came back
>   *"not verifiable"* instead of field-diffed.
>
> Re-applying the whole file is the fix, and is safe when permissions are already
> present:
>
> ```bash
> gcloud iam roles update DDetectiveReadOnly --project <your-project-id> \
>   --file gcp-iam-roles.json
> ```
>
> `.list` alone passes the **Test connection** check and only fails later, during
> a scan — which is why this went unnoticed for so long.


> [!WARNING]
> **Re-apply again if you created this role before 2026-08-28**
>
> Two permissions were added: `compute.networks.get` and
> `compute.subnetworks.get`. The connector's raw-`.tfstate` read path had no
> route to fetch either type at all until this same day, so the role was never
> generated with them - re-applying the whole file adds exactly these two.
> Without them, a Terraform-managed `google_compute_network` or
> `google_compute_subnetwork` field-diffs everywhere else but this one, and
> fails with a permission-denied error naming the missing action rather than
> the generic *"not verifiable."*


```bash
gcloud iam roles create DDetectiveReadOnly \
  --project <your-project-id> \
  --file gcp-iam-roles.json

gcloud projects add-iam-policy-binding <your-project-id> \
  --member "serviceAccount:ddetective-connector@<your-project-id>.iam.gserviceaccount.com" \
  --role "projects/<your-project-id>/roles/DDetectiveReadOnly"
```

Prefer a predefined role? `roles/viewer` also works, but it's far broader than
needed - the custom role is the least-privilege option.

**Optional: actor attribution.** To also let Cloudkeel-DD show *who* most
recently changed a resource (via Cloud Audit Logs' Admin Activity log),
create and bind the separate
[`gcp-iam-roles-attribution.json`](https://cloudkeel.io/docs/assets/gcp-iam-roles-attribution.json)
role too:

```bash
gcloud iam roles create DDetectiveActorAttributionOptional \
  --project <your-project-id> \
  --file docs/gcp-iam-roles-attribution.json

gcloud projects add-iam-policy-binding <your-project-id> \
  --member "serviceAccount:ddetective-connector@<your-project-id>.iam.gserviceaccount.com" \
  --role "projects/<your-project-id>/roles/DDetectiveActorAttributionOptional"
```

Skip it and scanning still works exactly the same; the "changed by" field
just stays blank for GCP resources.

**Optional: credential-expiry visibility.** To let Cloudkeel-DD show when this
service account key itself stops working (only meaningful if your
organization enforces a key-lifetime policy - otherwise there is nothing to
show), create and bind
[`gcp-iam-roles-credential-expiry.json`](https://cloudkeel.io/docs/assets/gcp-iam-roles-credential-expiry.json)
too:

```bash
gcloud iam roles create DDetectiveKeyExpiryOptional \
  --project <your-project-id> \
  --file docs/gcp-iam-roles-credential-expiry.json

gcloud projects add-iam-policy-binding <your-project-id> \
  --member "serviceAccount:ddetective-connector@<your-project-id>.iam.gserviceaccount.com" \
  --role "projects/<your-project-id>/roles/DDetectiveKeyExpiryOptional"
```

Skip it and scanning still works exactly the same; the integration list just
shows no expiry date for this credential, the same as it does today.

## 4. Generate a JSON key

```bash
gcloud iam service-accounts keys create ddetective-key.json \
  --iam-account ddetective-connector@<your-project-id>.iam.gserviceaccount.com
```

Same in the Console: the service account -> **Keys -> Add key -> Create new key
-> JSON**.

## 5. Connect it in Cloudkeel-DD

Settings -> **Cross-check integrations** -> **GCP**:

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-gcp` |
| Project ID | Your project ID (Console -> project selector) |
| Service account JSON key | The file from step 4 |

Click **Test connection**, then save.

**The project scope is created immediately** from the Project ID you entered - no
discovery step to run, no manual scope setup.

## What gets verified

**Field-level drift verification — all 59 GCP resource types.** GCP is the only
cloud with no per-path gap: every spec'd type is cross-checked whether the
desired state comes from a Terraform plan or from raw `.tfstate` in GCS.

The [coverage page](https://cloudkeel.io/docs/claims/coverage/) lists all 59 with their per-path
status, generated at build time from the product's own type registry — read the
per-type detail there rather than from a list on this page.

A `google_*` type with no spec is never field-diffed. It is tracked as
**inventory**, labelled "no live-fetch normalizer for this type yet", rather
than shipping an unverified field mapping that risks false drift.

**Unmanaged-resource detection: full**, across all 59 enumerated types. Anything
in that set running in the project with no Terraform tracking is flagged.

**Actor attribution (who changed it): via Cloud Audit Logs, wherever a finding
has a usable resource id.** If the optional `DDetectiveActorAttributionOptional`
role is bound (see step 3), drift and unmanaged-resource findings show who last
modified the resource and when. Best-effort: a missing permission, an old
change, or an entry the Admin Activity log simply doesn't retain leaves this
blank rather than failing the scan.

> Expect findings on your first scan. Every GCP project's default network ships
> with implicit `default-allow-*` firewall rules that no Terraform config
> declares - those are genuinely unmanaged, and Cloudkeel-DD says so.

For comparison: Azure carries the most spec'd types (79), but GCP is the only
cloud where every one of them is reachable on both desired-state paths. See
[Azure cross-check setup](https://cloudkeel.io/docs/integrations/azure-cross-check/) and the
[coverage page](https://cloudkeel.io/docs/claims/coverage/).

## Notes

- **One GCP credential per workspace.** A second active GCP integration is
  rejected with a 409 - it would be silently ignored by every scan, so it fails
  loudly instead. Edit or deactivate the existing one.
- **One credential = one project.** Multi-project scanning (via Cloud Resource
  Manager discovery) is a [known gap](https://cloudkeel.io/docs/claims/feature-inventory/#known-gaps).
- **Key rotation** is a manual action. When a key is revoked or deleted, scans
  fail and the real GCP error appears in Inventory's **Last error**; update the
  integration with a new key.
