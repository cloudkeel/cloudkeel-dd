---
title: "Connecting integrations: checklist & troubleshooting"
description: "Every test-connection error mapped to its fix, why an integration reports no findings, and how a stuck scan self-heals."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/troubleshooting/](https://cloudkeel.io/docs/integrations/troubleshooting/)**

Every error in this guide is one a real connection run hit. Read the checklist
first; the table below maps each **Test connection** failure to its fix.

## The two-part model (why one credential is never enough)

Cloudkeel-DD compares **desired** state against **actual** state, so most clouds
need **two** integrations working together:

1. A **state source** (Terraform Cloud, or raw `.tfstate` in S3/GCS/Azure Blob) -
   the *desired* state.
2. A **cross-check credential** (AWS / GCP / Azure, read-only) - the *actual*
   live state.

With only the state source, resources are discovered but tagged **"no live
comparison available"**: you get inventory, not drift. With only the cross-check
credential, there's nothing to compare against. **Connect both**, per cloud.

Kubernetes is the exception - one kubeconfig integration is self-contained
(desired = Helm release record, actual = live API).

## Don't-skip checklist

- [ ] **State source connected** and each discovered `.tfstate` **Enabled** (they
      arrive `discovered`; nothing scans until you opt in).
- [ ] **Cross-check credential connected** for the same cloud.
- [ ] **Cross-check scope ENABLED.** A scope is what live verification runs
      against. **AWS and GCP auto-enable it** from the account ID / project ID you
      enter, so there's nothing to do. **Azure is different:** it *discovers* your
      subscriptions and leaves each **disabled** until you opt in (Settings -> the
      Azure integration -> enable the subscription). A disabled scope means the
      credential is connected but live verification and unmanaged detection never
      run - the most common "connected but no drift shows" cause on Azure.
- [ ] **Kubernetes: static token kubeconfig, not an exec-plugin one** (see
      [Kubernetes setup](https://cloudkeel.io/docs/integrations/kubernetes/)).
- [ ] **EKS: cluster API access enabled first** (access entry) - see the same guide.
- [ ] Bucket/object names typed exactly - copy-paste, don't retype.

## Test-connection error → fix

| Error you see | Cause | Fix |
|---|---|---|
| `NoSuchBucket: The specified bucket does not exist` | Bucket name typo (a dropped or duplicated character is easy to miss) | Copy the name from `aws s3 ls` / `gcloud storage ls` and paste it. Verify: `aws s3 ls s3://<bucket>` |
| `AccessDenied … not authorized to perform: s3:ListBucket` | The IAM policy grants `ListBucket` on the **wrong bucket ARN** (e.g. a stale bucket from an earlier setup) | Update the inline policy's `Resource` to the current bucket ARN (`arn:aws:s3:::<bucket>` for `ListBucket`, `…/*` for `GetObject`). See [`aws-s3-state-iam-policy.json`](https://cloudkeel.io/docs/assets/aws-s3-state-iam-policy.json) |
| GCS `403` / `does not have storage.objects.list access` | The service account isn't bound on the bucket (or is bound on a different one) | `gsutil iam ch serviceAccount:<sa-email>:roles/storage.objectViewer gs://<bucket>` |
| K8s `401 Unauthorized` (but `kubectl` works on your laptop) | You uploaded an **exec-plugin** kubeconfig; the `aws`/`gcloud`/`kubelogin` CLI it calls doesn't exist in Cloudkeel-DD's container | Build a **static token** kubeconfig from a ServiceAccount ([Kubernetes setup](https://cloudkeel.io/docs/integrations/kubernetes/) step 3) |
| K8s `You must be logged in to the server` when building the kubeconfig | EKS cluster in `CONFIG_MAP` mode / trusts only its creator - you can't even reach it to make the ServiceAccount | Enable API auth + add an access entry ([Kubernetes setup](https://cloudkeel.io/docs/integrations/kubernetes/) → *Prerequisite (EKS only)*) |
| `ResourceNotFoundException: The specified policyArn could not be found` (running `associate-access-policy`) | Wrong ARN form `arn:aws:eks:::…` | Use `arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy` (empty region, partition `aws`) |
| Connected fine, scan runs, **but no cloud drift ever appears** (Azure) | Discovered **subscription scope not enabled** (AWS/GCP auto-enable; Azure doesn't) | Enable the subscription on the Azure integration (see checklist) |

## Rotating a credential without downtime

Reader IAM keys / SA keys / SAS tokens created for an earlier setup can't be
re-read (the secret is shown only once). To reconnect, **mint a fresh key** for
the *same* least-privilege identity rather than making a new one:

```bash
aws iam create-access-key --user-name <reader-user>                 # AWS
gcloud iam service-accounts keys create key.json --iam-account <sa> # GCP
```

Update the integration with the new secret and Test connection. IAM/SA identities
cap the number of keys (AWS 2, GCP 10) - delete an unused one if you hit the limit.

## What "no drift" legitimately means

If everything is connected, scopes enabled, and a scan completes with **0 drift**,
that's a real result: nothing changed out-of-band. Two by-design behaviours that
are **not** bugs:

- **Tag/label-only changes aren't flagged.** A changed cloud tag, GCP label, or
  Kubernetes label is low-signal and intentionally ignored; the cross-check
  normalizers focus on security-relevant fields (firewall/security-group rules,
  replica counts, images, ...).
- **Adding a brand-new field the chart never declared isn't K8s drift** -
  *changing a field the manifest owns* is. See [Kubernetes setup](https://cloudkeel.io/docs/integrations/kubernetes/).

## Why an integration has no findings

The Inventory page reports a readiness state per integration. They are evaluated
in order and the first match wins, so the most actionable blocker is what you see:

| State | What it means | What to do |
|---|---|---|
| `scan_failed` | The last scan errored | Read **Last error** on the integration |
| `no_scopes_enabled` | Scopes were discovered, none enabled | Enable a subscription, account or project. A scan against zero enabled scopes is a no-op, which is why this outranks "never scanned" |
| `never_scanned` | Connected, no scan yet | Run a scan, or set a cadence |
| `scan_in_progress` | A scan is running now | Wait for it |
| `zero_resources_found` | The scan completed and found nothing | Check the state source actually contains resources of a supported type |
| `throttled` | The provider is rate-limiting reads | Wait; backoff is automatic |
| `cross_check_only` | This is a cloud credential, not a scan target | Connect a Terraform state source. This credential is consulted *during* a state scan and can never produce findings alone |
| `healthy` | Scanning and producing results | Nothing |

`cross_check_only` is the single most common dead end on a first install. An
Azure, AWS or GCP credential is a **cross-check helper**, never a scan target —
triggering a scan against one is rejected outright. Drift detection needs a
Terraform state source or a cluster to scan.

## A scan is stuck in pending

Only one scan runs per integration at a time; a second trigger reuses the
in-flight one rather than queueing a duplicate. If a worker dies mid-scan, its
scan can sit non-terminal and block that integration.

This self-heals. A scan that has not reached a terminal state within **one hour**
is marked failed on the next trigger, with an explanatory error message, and
scanning resumes. You do not need database access to clear it — but a scan that
reaches this state means a worker died, which is worth investigating.

## A type reports "not verifiable"

The resource was found, but Cloudkeel-DD could not read its live state, so it is
tracked as inventory instead of field-diffed. **The usual cause is a credential
missing that type's read permission, not missing coverage.**

Check that first — the credential files were regenerated on 2026-08-07 and older
copies grant far less than current coverage needs:

- **AWS.** The policy is now a *managed* policy (it outgrew IAM's 2,048-character
  inline limit). Re-create and attach it —
  [step 2](https://cloudkeel.io/docs/integrations/aws-cross-check/#2-attach-the-read-only-policy).
- **GCP, raw `.tfstate` only.** Re-apply the custom role with
  `gcloud iam roles update ... --file gcp-iam-roles.json` —
  [step 3](https://cloudkeel.io/docs/integrations/gcp-cross-check/#3-create-and-bind-the-read-only-custom-role).
  The Terraform Cloud path is unaffected, because it reads through Cloud Asset
  Inventory in bulk.

This degrades per type on purpose: one unreadable type must never discard the
rest of a scan's findings. The trade-off is that it looks like absent coverage,
so it is worth ruling out the credential before anything else.

Four AWS types stay partial **even with the current policy**, deliberately:
`aws_lambda_function`, `aws_cognito_user_pool`, `aws_sfn_state_machine` and
`aws_cloudwatch_event_rule`. Their read handlers ask for `lambda:GetFunction`,
`kms:Decrypt` or `iam:PassRole` — code download, data-plane decryption, and role
delegation. Cloudkeel-DD does not ask for those, so those types field-diff on
what is readable and report the rest.

If the credential is current and the type is not one of those four, then it
genuinely has no field-diff spec. The
[coverage page](https://cloudkeel.io/docs/claims/coverage/) is the authority on which types do.

## GCP: the whole scope returns nothing

The Cloud Asset API must be enabled on the project. If it is not, the failure is
**scope-level, not per-type** — one missing API means the entire GCP scope
returns no resources rather than degrading partially. The test-connection button
exercises exactly this call, so the problem surfaces at connection time rather
than at first scan.
