---
title: "AWS Terraform state (raw `.tfstate` in S3) setup"
description: "Connect raw .tfstate objects in an S3 bucket as a desired-state source, using a bucket-scoped read-only IAM credential."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/aws-state/](https://cloudkeel.io/docs/integrations/aws-state/)**

This connects Cloudkeel-DD to raw `.tfstate` objects sitting in an S3 bucket,
so it can ingest Terraform state directly instead of going through Terraform
Cloud/Enterprise. It's a **separate, narrow credential** from the AWS
access keys used for live-resource cross-checking (Settings -> Cross-check
integrations -> AWS) - the two are independent and safely coexist.

## 1. Create a narrow IAM user

In the AWS Console: IAM -> Users -> **Create user**. No console access
needed - this is an API-only credential.

## 2. Attach a bucket-scoped policy

Attach an inline policy scoped to just the bucket holding your state files -
see `docs/aws-s3-state-iam-policy.json` for the exact document (replace
`REPLACE_WITH_YOUR_BUCKET_NAME` with your bucket's name). It grants only
`s3:ListBucket` (on the bucket) and `s3:GetObject` (on objects inside it) -
nothing else, and scoped to that one bucket, not `"Resource": "*"`. If you
only want Cloudkeel-DD to discover state files under one folder, add an
`s3:prefix` condition to the `ListBucket` statement:

```json
"Condition": { "StringLike": { "s3:prefix": ["envs/*"] } }
```

## 3. Generate an access key pair

Same IAM user -> **Security credentials** -> **Create access key**. Copy
both the access key ID and secret access key - AWS only shows the secret once.

## 4. Connect it in Cloudkeel-DD

Settings -> **Terraform state sources** -> **+ Add storage source** -> AWS:

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-tfstate` |
| Bucket | The S3 bucket name |
| Prefix (optional) | Restrict discovery to one folder, e.g. `envs/` |
| Region | The bucket's region, e.g. `us-east-1` |
| Access key ID | From step 3 |
| Secret access key | From step 3 |

Click **Test connection** to confirm Cloudkeel-DD can list `.tfstate` objects,
then **Save and start scanning**. Discovered state files appear as
`discovered` - nothing is scanned until you explicitly **Enable** each one
(opt-in, same lifecycle as multi-scope account discovery).

## 5. Connect a live AWS credential too, for security-group drift detection

Without a live-resource AWS credential (Settings -> Cross-check integrations
-> AWS) connected, resources parsed from state are still discovered and shown
in Inventory, but tagged **"no live comparison available"**. Connect the AWS
cross-check credential to get real drift detection for state-sourced security
groups.

## What gets ingested

Only `aws_*` resources are read from state today. Other providers' resources
in a mixed state file are counted but not persisted.

**Live-diffed from raw state — all 62 AWS types.** The
[coverage page](https://cloudkeel.io/docs/claims/coverage/) lists every one of them, generated at
build time from the product's own type registry.

`aws_security_group` includes standalone `aws_security_group_rule` /
`aws_vpc_security_group_{ingress,egress}_rule` resources, merged into their
parent.

> [!TIP]
> **This is the path that matters most on AWS**
>
> A state source is **dramatically** broader than the Terraform Cloud path, which
> cross-checks `aws_security_group` and nothing else — 62 types against 1. If AWS
> is your centre of gravity, connect a state bucket rather than relying on
> Terraform Cloud alone. It is the single largest coverage asymmetry in the
> product.


A raw-state resource is live-diffed when it has a spec **and** its ARN maps to a
Cloud Control type; anything else is tracked as inventory with the reason
`no live-diff spec for <type> yet`. Two enumerated AWS types have no field-diff
spec and stay inventory-only: `aws_eip` and `aws_route_table`. An unverified
field mapping risks confident-looking false drift, which is worse than an honest
"not yet diffed."
