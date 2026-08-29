---
title: "How to see who changed a resource"
description: "Show who last modified a drifted resource, the per-cloud permission it needs, and the lookback limits that leave it blank."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/usage/who-changed-it/](https://cloudkeel.io/docs/usage/who-changed-it/)**

Show the person or service principal that most recently modified a drifted
resource, and when. This turns "something changed" into "someone changed this,
here is who to ask".

Attribution is **optional and best-effort**. It requires one extra read-only
permission per cloud, and it degrades quietly rather than failing a scan.

## Prerequisites

- The cross-check integration for the cloud already connected
  ([AWS](https://cloudkeel.io/docs/integrations/aws-cross-check/) ·
  [GCP](https://cloudkeel.io/docs/integrations/gcp-cross-check/) ·
  [Azure](https://cloudkeel.io/docs/integrations/azure-cross-check/)).
- Permission to modify that integration's credential policy or role.

## Steps

### AWS

Add `cloudtrail:LookupEvents` to the connector's IAM policy. It ships as its
own statement, `DDetectiveActorAttributionOptional`, in
[`aws-iam-policy.json`](https://cloudkeel.io/docs/assets/aws-iam-policy.json) - if you attached that
document as-is, you already have it.

### GCP

Create and bind the separate attribution role from
[`gcp-iam-roles-attribution.json`](https://cloudkeel.io/docs/assets/gcp-iam-roles-attribution.json),
which grants read access to the Admin Activity audit log:

```bash
gcloud iam roles create DDetectiveActorAttributionOptional \
  --project <your-project-id> \
  --file docs/gcp-iam-roles-attribution.json

gcloud projects add-iam-policy-binding <your-project-id> \
  --member "serviceAccount:ddetective-connector@<your-project-id>.iam.gserviceaccount.com" \
  --role "projects/<your-project-id>/roles/DDetectiveActorAttributionOptional"
```

### Azure

Azure attribution reads the Activity Log. Grant the connector service principal
read access to it on the subscription.

## Verification

1. Change a tracked resource outside Terraform, deliberately.
2. Run a scan.
3. Open the resulting finding. It should show a **Changed by** value and a
   timestamp.

If the field is blank, work through the table below - a blank field is the
documented degraded state, not an error.

## What you get, and what you do not

- **Covered:** drift findings and unmanaged-resource findings, wherever the
  finding carries a resource id the audit log can be queried by.
- **The lookback is 72 hours.** Every query asks the audit log for writes in the
  last 72 hours only. A change older than that shows blank even when the log
  still holds it. This is the most common reason the field is empty on a
  long-standing drift.
- **At most 5 pages are read per lookup.** On a resource with very high write
  volume the relevant entry can fall outside those pages. The cap bounds the
  worst case rather than letting one noisy resource stall a scan.
- **AWS retention is 90 days.** `LookupEvents` only returns events inside
  CloudTrail's own retention window — a ceiling above the 72-hour lookback, not
  instead of it.
- **Best-effort by design.** A missing permission, an event the audit log did
  not retain, or a change made through a path the log does not record leaves
  the field blank. It never fails the scan, and it never guesses.

> [!NOTE]
> **Blank is not the same as 'nobody'**
>
> An empty "Changed by" means Cloudkeel-DD could not attribute the change, not
> that no one made it. Do not read it as evidence of anything.


## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Always blank, AWS | `cloudtrail:LookupEvents` not granted | Re-attach the policy including the optional statement |
| Always blank, GCP | Attribution role not created or not bound | Run both commands above; binding without creating is a common miss |
| Blank for older findings only | The change is outside the 72-hour lookback | Expected; nothing to fix |
| Blank for some resource types | The finding has no resource id usable as an audit-log key | Expected; coverage is per-finding, not per-type |
| Shows a service principal, not a person | The change was made by automation | Correct - trace it via the principal's own pipeline |

## Related

- [The drift lifecycle](https://cloudkeel.io/docs/concepts/drift-lifecycle/) - where attribution sits in a scan, and the bounds that leave the field blank
- [Route findings to the right team](https://cloudkeel.io/docs/usage/ownership-routing/) - who *owns* it, a different question from who *changed* it
- [Least-privilege credentials](https://cloudkeel.io/docs/claims/least-privilege/)
