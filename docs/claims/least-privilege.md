---
title: "Least-privilege credentials"
description: "The exact read-only credential each connector needs, per provider, with copy-pasteable IAM policies and role definitions."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/least-privilege/](https://cloudkeel.io/docs/claims/least-privilege/)**

Cloudkeel-DD never writes to your cloud, so **read-only credentials are always
enough**. This page collects the exact policy documents; each connection guide
walks through creating the credential.

## Reference policies

| File | Purpose |
|---|---|
| [`aws-iam-policy.json`](https://cloudkeel.io/docs/assets/aws-iam-policy.json) | AWS cross-check (live-resource read) |
| [`aws-s3-state-iam-policy.json`](https://cloudkeel.io/docs/assets/aws-s3-state-iam-policy.json) | AWS raw-state bucket read |
| [`gcp-iam-roles.json`](https://cloudkeel.io/docs/assets/gcp-iam-roles.json) | GCP cross-check custom role |
| [`gcp-iam-roles-attribution.json`](https://cloudkeel.io/docs/assets/gcp-iam-roles-attribution.json) | GCP cross-check, optional actor attribution |
| [`gcp-iam-roles-credential-expiry.json`](https://cloudkeel.io/docs/assets/gcp-iam-roles-credential-expiry.json) | GCP cross-check, optional credential-expiry visibility |
| [`gcp-gcs-state-iam-roles.json`](https://cloudkeel.io/docs/assets/gcp-gcs-state-iam-roles.json) | GCP raw-state bucket role |

Azure has no custom-role document on purpose — it uses the **built-in Reader
role**. See [Azure cross-check setup](https://cloudkeel.io/docs/integrations/azure-cross-check/).

## Principles

- **Scope to the resource, not `*`.** State-bucket policies name the one bucket;
  cloud cross-check roles are read-only across the account/subscription/project
  you enable.
- **Separate credentials for separate jobs.** The bucket-scoped state reader is a
  *different* credential from the live-resource cross-check reader; they coexist
  safely and can be rotated independently.
- **Kubernetes uses a read-only ServiceAccount** with `get/list/watch` and a
  static token kubeconfig — no exec-plugin, no admin. See
  [Kubernetes setup](https://cloudkeel.io/docs/integrations/kubernetes/).

## Per-provider summary

| Provider | Cross-check credential | Raw state credential |
|---|---|---|
| **Azure** | Built-in **Reader** on the subscriptions you enable. No custom role — Reader already covers Resource Graph, ARM reads, and the Activity Log used for attribution. [Setup](https://cloudkeel.io/docs/integrations/azure-cross-check/) | A narrow, time-boxed **SAS** on the state container |
| **AWS** | The read-only actions in `aws-iam-policy.json` — `cloudformation:ListResources`/`GetResource` for Cloud Control, plus the per-service describes it needs. `cloudtrail:LookupEvents` and `iam:ListAccessKeys` are separate, **optional** statements — attribution and access-key-age visibility respectively; neither is required for scanning. [Setup](https://cloudkeel.io/docs/integrations/aws-cross-check/) | `s3:ListBucket` on the bucket + `s3:GetObject` on its contents |
| **GCP** | The custom role in `gcp-iam-roles.json` — `cloudasset.assets.listResource` for bulk listing, plus a `.get` permission per type that supports single reads. Two **optional** second roles add extras without changing scanning: `gcp-iam-roles-attribution.json` (`logging.logEntries.list`) for attribution, and `gcp-iam-roles-credential-expiry.json` (`iam.serviceAccountKeys.get`) so the integration list can show this key's own expiry. [Setup](https://cloudkeel.io/docs/integrations/gcp-cross-check/) | `storage.objects.get` + `storage.objects.list` on the one bucket |
| **Kubernetes** | A ServiceAccount with `get`/`list`/`watch` on six kinds, plus `get`/`list` on namespaces and `list` on secrets to read Helm's release records. [Setup](https://cloudkeel.io/docs/integrations/kubernetes/) | n/a — Helm's own records are the desired state |

Two notes on the GCP role, because both cause silent failures:

- `.list` without `.get` passes the test-connection check and then fails at
  cross-check time. The shipped role includes both.
- The Cloud Asset API must be enabled on the project. If it is not, the whole
  scope returns nothing rather than degrading per-type.

## Both cloud credential files were regenerated on 2026-08-07

They were written when the engine field-diffed 22 resource types and were never
grown as coverage reached 200. **Re-apply them if you set yours up earlier** —
[AWS](https://cloudkeel.io/docs/integrations/aws-cross-check/), [GCP](https://cloudkeel.io/docs/integrations/gcp-cross-check/).

Under-granting fails quietly by design: a permission error on one type becomes a
per-type *"not verifiable"* note rather than a failed scan, so one gap can never
sink a whole source. The cost is that an under-scoped credential looks like thin
coverage instead of a permissions problem. If a type you expect to be
field-diffed shows *"not verifiable"*, check the credential before concluding
Cloudkeel-DD does not cover it — see
[troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/#a-type-reports-not-verifiable).

Neither file is hand-maintained any more. The AWS policy is generated from each
type's `handlers.read.permissions` **and** `handlers.list.permissions` in the
CloudFormation registry — reading one resource by id and enumerating all of
them are separate Cloud Control handlers, and the 2026-08-07 regeneration
covered only the former, missing list-only actions (`lambda:ListFunctions`
most visibly) until 2026-08-28. The GCP role is generated from the connector's
own read routes. Generating from a registry keeps the file from silently
falling behind added coverage the way the original hand-maintained version
did; it does not by itself guarantee every generation pass captures every
handler a type needs.

## Rotation

Reader keys can't be re-read after creation, so rotate by **minting a fresh key**
for the same identity and updating the integration — no downtime. Full steps in
[troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/).
