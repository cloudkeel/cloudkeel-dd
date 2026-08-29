---
title: "AWS cross-check setup (live verification)"
description: "Create a read-only AWS IAM policy and connect it, so Cloudkeel-DD can verify Terraform's claims against the live AWS API."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/aws-cross-check/](https://cloudkeel.io/docs/integrations/aws-cross-check/)**

This connects Cloudkeel-DD to the live AWS API so it can **independently verify**
what Terraform claims, and find resources Terraform doesn't know about at all.

It's a **read-only** credential - Cloudkeel-DD never modifies AWS resources. It's
also a **separate credential** from the bucket-scoped one used for
[raw `.tfstate` in S3](https://cloudkeel.io/docs/integrations/aws-state/); the two are independent and
safely coexist.

## 1. Create a narrow IAM user

AWS Console: **IAM -> Users -> Create user**. No console access needed - this is
an API-only credential.

## 2. Attach the read-only policy

Attach a policy using the exact document in
[`aws-iam-policy.json`](https://cloudkeel.io/docs/assets/aws-iam-policy.json). It grants only
`Describe`/`Get`/`List` calls, across the services Cloud Control dispatches to
for the 62 AWS types Cloudkeel-DD field-diffs.

> [!WARNING]
> **Re-attach this policy if you set it up before 2026-08-07**
>
> The published document used to grant reads for six services. AWS coverage grew
> to 62 resource types without it growing to match, so an older copy leaves most
> types reporting *"not verifiable"* — which reads as thin coverage rather than
> the permissions problem it is. Re-attaching is the whole fix; nothing else
> changes.


> [!WARNING]
> **Re-attach again if you set it up before 2026-08-28**
>
> The 2026-08-07 regeneration pulled each type's **read** permissions
> (`handlers.read.permissions` — used to fetch one resource by id) but missed its
> **list** permissions (`handlers.list.permissions` — used to enumerate which
> resources exist), wherever a type's Cloud Control handlers need different
> underlying actions for the two. Sixteen actions across appsync, athena, backup,
> cloudfront, CloudTrail, cognito-identity, cognito-idp, dynamodb, ecs,
> globalaccelerator, guardduty, kafka, lambda, ssm, states and transfer were
> missing as a result — `lambda:ListFunctions` most visibly, since Lambda had no
> enumeration permission at all under the previous document. Re-attaching is
> again the whole fix.


Plus `cloudformation:ListResources` and `cloudformation:GetResource` (their own
statement, `DDetectiveUniversalReader`). Despite the name these have nothing to
do with CloudFormation stacks - they are the IAM actions for the **Cloud
Control API**, which is how Cloudkeel-DD reads most AWS resource types.

> **Required, not optional - omit these and most types fail.** Without this
> statement every type read through Cloud Control returns
> `AccessDeniedException: ... not authorized to perform:
> cloudformation:ListResources`, and the scan reports them as *"not verifiable -
> not readable with this credential"*. That covers RDS instances, EIPs, EKS
> clusters, IAM roles and policies, KMS keys, load balancers, route tables, and
> S3 buckets. Security groups keep working, because they are the one documented
> exception that reads through `ec2:DescribeSecurityGroups` instead - which is
> why a policy missing this statement fails partially rather than completely.
>
> These actions are read-only, but they are scoped `resource/*` and so are
> broader than the per-service calls above. That breadth is what a single
> uniform read surface across every type costs.

Plus the underlying-service read actions (their own statement,
`DDetectiveUniversalReaderServices`). The Cloud Control API is only a dispatch
layer: `cloudformation:ListResources` lets Cloudkeel-DD *invoke* it, but each
resource type's handler then calls that service's **own** read API under the
same credential. Reading 62 types therefore means read actions across ~40
services — RDS, IAM, KMS, S3, DynamoDB, Lambda, CloudFront, EFS, Redshift,
OpenSearch and the rest.

This statement is **generated** from each type's declared permissions in the
CloudFormation registry (`aws cloudformation describe-type` →
`handlers.read.permissions` **and** `handlers.list.permissions` — reading one
resource by id and enumerating all of them are separate Cloud Control handlers
and can require different underlying actions), not hand-maintained. That is
why it grew: the hand-maintained version silently stopped matching coverage.

> **All metadata reads - no data-plane access.** The S3 actions are
> `GetBucket*` (bucket configuration: policy, encryption, versioning, tagging,
> and so on), never `s3:GetObject` - Cloudkeel-DD never reads object contents.
> Likewise nothing here reads secret values, Lambda code, or database rows.
>
> Keeping that true costs coverage on four types, and we chose the guarantee
> over the coverage. Their read handlers ask for permissions we deliberately
> **do not** grant:
>
> | Type | Withheld | Why |
> |---|---|---|
> | `aws_lambda_function` | `lambda:GetFunction` | Returns a pre-signed URL to download the function's code |
> | `aws_lambda_function`, `aws_cognito_user_pool`, `aws_sfn_state_machine` | `kms:Decrypt` | Data-plane: decrypts ciphertext |
> | `aws_cloudwatch_event_rule` | `iam:PassRole` | Not a read at all — it delegates a role |
>
> Those four field-diff on the attributes that *are* readable and report the
> rest as *"not verifiable"*. Grant the withheld actions yourself if you want
> full coverage on them and accept the trade — Cloudkeel-DD never asks for them.
> Wildcards in this statement are confined to `Describe*`/`List*`/`Get*` on
> services with no data-plane reach; S3, KMS, Lambda, SSM, Secrets Manager and
> Cognito stay enumerated action-by-action for exactly that reason.

Plus two **optional** actions, each its own statement so either can be
skipped independently:

- `cloudtrail:LookupEvents` (`DDetectiveActorAttributionOptional`) - lets
  Cloudkeel-DD look up *who* most recently changed a resource via CloudTrail,
  shown on drift findings as "Changed by". Skip it and that field just stays
  blank for AWS resources.
- `iam:ListAccessKeys` (`DDetectiveKeyAgeOptional`) - lets Cloudkeel-DD show
  how old this access key is on the integration list, as a rotation-hygiene
  nudge (AWS access keys have no expiry, unlike Azure's SAS or a GCP
  service-account key - this is age, not a deadline). Skip it and the
  integration list just shows no age for this credential.

Either way scanning works exactly the same.

Nothing that writes, and no `Action: "*"` — every wildcard is a read verb
(`Describe*`/`List*`/`Get*`) scoped to one service.

> [!WARNING]
> **This is a **managed** policy now, not an inline one**
>
> At 3,320 characters it no longer fits IAM's **2,048**-character limit for an
> inline user policy, so the old `aws iam put-user-policy` command fails with
> `LimitExceeded`. Managed policies allow 6,144, which this fits with room to
> grow. Create and attach it instead:


```bash
POLICY_ARN=$(aws iam create-policy \
  --policy-name DDetectiveReadOnly \
  --policy-document file://docs/aws-iam-policy.json \
  --query 'Policy.Arn' --output text)

aws iam attach-user-policy \
  --user-name ddetective-connector \
  --policy-arn "$POLICY_ARN"
```

Already have the old inline policy? Remove it after attaching the managed one,
so the account does not keep a stale grant around:

```bash
aws iam delete-user-policy \
  --user-name ddetective-connector \
  --policy-name DDetectiveReadOnly
```

## 3. Generate an access key pair

Same user -> **Security credentials** -> **Create access key**. Copy both values;
AWS shows the secret once.

## 4. Connect it in Cloudkeel-DD

Settings -> **Cross-check integrations** -> **AWS**:

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-aws` |
| Access key ID | From step 3 |
| Secret access key | From step 3 |
| Region | e.g. `us-east-1` |

Click **Test connection**, then save.

**The account is detected automatically.** On save, Cloudkeel-DD calls STS
`GetCallerIdentity` to learn the real AWS account ID and creates an enabled scope
for it - no manual account entry, no discovery step to run.

## What gets verified

**Field-level drift verification: security groups only** (`aws_security_group`,
including standalone `aws_security_group_rule` /
`aws_vpc_security_group_{ingress,egress}_rule` resources, merged into their
parent). Rules are canonicalized before comparison, so AWS's rule *coalescing*
and Terraform's separately-declared blocks don't register as false drift.

> [!WARNING]
> **Security-groups-only applies to the *plan* path, not to this credential**
>
> The one-type limit is a property of where the **desired** state comes from, not
> of what this credential can read. Point the same credential at a
> [raw `.tfstate` source in S3](https://cloudkeel.io/docs/integrations/aws-state/) and it field-diffs
> all **62** spec'd AWS types.
>
> 62 against 1 is the largest coverage asymmetry in the product. On AWS, connect a
> state bucket if you can.


**Unmanaged-resource detection: full**, across all **64** enumerated AWS types —
not just the ones the plan path cross-checks. Anything in that set running in
the account with no Terraform tracking is flagged. The
[coverage page](https://cloudkeel.io/docs/claims/coverage/) lists every enumerated and spec'd type,
generated at build time from the product's own type registry.

**Actor attribution (who changed it): via CloudTrail, wherever a finding has a
usable resource id.** If `cloudtrail:LookupEvents` is granted (see step 2),
drift and unmanaged-resource findings show who last modified the resource and
when, within the last 90 days (CloudTrail's own retention window for
`LookupEvents`) - unmanaged findings for any of the types above, live-diffed
drift for any type with a working normalizer, and security-group cross-check
findings. Best-effort: a missing permission, an old change, or an event
CloudTrail simply doesn't retain leaves this blank rather than failing the
scan.

For comparison: Azure carries the most spec'd types (79) and reaches 68 of them
on the plan path, where AWS reaches one. See
[Azure cross-check setup](https://cloudkeel.io/docs/integrations/azure-cross-check/).

## Notes

- **One AWS credential per workspace.** A second active AWS integration is
  rejected with a 409 - it would be silently ignored by every scan, so it fails
  loudly instead. Edit or deactivate the existing one.
- **One access key = one account.** AWS has no equivalent of Azure's
  multi-subscription model, so multi-account scanning (via AWS Organizations
  assume-role) is a [known gap](https://cloudkeel.io/docs/claims/feature-inventory/#known-gaps). One credential covers
  one account today.
- **Key rotation** is a manual action. When a key is rotated or revoked, scans
  fail and the real AWS error appears in Inventory's **Last error**; update the
  integration with the new key.
