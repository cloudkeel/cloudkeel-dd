---
title: "How to act on a drift finding"
description: "The four things you can do with a finding - accept, revert, suppress, or open a remediation PR - and what each one actually produces."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/usage/remediation/](https://cloudkeel.io/docs/usage/remediation/)**

Detection is read-only. Nothing on this page changes your infrastructure:
Cloudkeel-DD never creates, updates or deletes a cloud resource, never runs
`terraform apply`, and has no auto-remediation path. Everything below either
records a decision or opens a pull request for a human to review.

## The four options

| You believe | Do this | What it does |
|---|---|---|
| Reality is right, the code is stale | **Accept** | Records the claim; you update your IaC |
| The code is right, reality is wrong | **Revert plan** | Generates a field-level plan for you to run |
| Neither — this is noise | **Suppress** | Silences it, with a required reason |
| You want a PR out of it | **Remediation PR** | Opens a real GitHub PR or GitLab MR |

Accept and revert are decisions. Only the remediation PR produces an artifact.

## Accept and revert do not close a finding

Both move it to **awaiting re-scan** (`pending_verification`), not to resolved.
A later scan decides:

- The drift is gone → the finding resolves.
- The drift is still there → it **reopens**, and reopening re-arms its
  notification. "The fix you claimed didn't hold" is the highest-signal thing
  this product says, so it is never silent.

You do not have to use either. Most drift is fixed by someone doing their normal
job, and when a re-scan finds it gone the finding resolves on its own, credited
as reconciled externally. The accept/revert detour exists for when you want the
claim on the record.

## The revert plan

Generated from the computed diff, in the opposite direction to a remediation PR:
it describes pushing *reality* back to the *declared* state.

Each step is one of three actions:

| Action | Meaning |
|---|---|
| `set` | The field changed; here is the declared value to restore |
| `remove` | Present live, absent from the declared state |
| `restore` | Present in the declared state, missing live |

It is structured data and suggestion text. **Nothing applies it** — review the
steps, run them yourself, then re-scan to confirm.

## Opening a remediation PR

Two different things share this button, and they produce **very different**
artifacts. Know which one you are getting.

### For drift on a managed resource

The PR adds a **JSON file** recording the desired state:

```
remediation/<resource_type>/<namespace>/<name>.json
```

with the last-known-good desired payload as its contents, and a body carrying
the drift category, severity, diff summary and the full field-level diff.

**This is a record, not a fix.** It is not HCL, and merging it does not
reconcile anything — it puts the desired state and the diff in front of
reviewers in your normal review workflow. The actual change to your Terraform is
still yours to write.

### For an unmanaged resource — Codify

The PR adds a **Terraform `import` block**:

```
codify/<resource_type>/<name>.tf
```

```hcl
import {
  to = aws_security_group.my_group
  id = "sg-0123456789abcdef0"
}
```

That is valid HCL, and it is an import block **only** — never a resource body.
Generate the body locally with Terraform 1.5+:

```bash
terraform plan -generate-config-out=generated.tf
```

Review the generated body before merging; defaults and computed attributes
usually need cleanup.

Codify needs the resource type to have a known identity mapping. If it does not,
the request is rejected with a clear message rather than guessing an import id.
See [Codify an unmanaged resource](https://cloudkeel.io/docs/usage/codify-unmanaged/) for the full
walkthrough.

## The approval gate

Whether a PR can open immediately depends on the finding's severity:

| Severity | Initial status | What is needed |
|---|---|---|
| `critical` | `pending` | A human must **approve** before a PR can open |
| everything else | `approved` | Nothing — it is ready to open |

Auto-approval is not auto-opening. **Opening the PR is always a separate,
explicit action**, at every severity. Nothing reaches your Git host because a
scan ran.

A remediation moves through `pending` → `approved` → `completed`, or to
`rejected` if you decline it, or `failed` if the Git host refuses the request —
in which case the error from the host is recorded on the action.

Approving something that is not `pending`, or trying to open a PR for something
not yet `approved`, is rejected rather than silently ignored.

## Prerequisites for PR creation

A Personal Access Token must be configured on the Cloudkeel-DD deployment:

| Provider | Setting |
|---|---|
| GitHub | `GITHUB_PAT` |
| GitLab | `GITLAB_PAT` |

Without one, PR creation fails with "No GitHub token configured". This is a
deployment-level setting, not per-tenant — see
[Secrets](https://cloudkeel.io/docs/configuration/secrets/).

You also supply a **target repository** on the request; it has no default, and
omitting it is rejected. The target branch defaults to `main`.

> [!NOTE]
> **This is the one place Cloudkeel-DD writes anything**
>
> Every other outbound call is a read. Opening a PR writes to *your* Git host,
> using *your* token, only when a human asks for it. It never touches your cloud.


## Verification

1. Open a finding and choose **Create remediation PR**.
2. If it is critical, approve it first.
3. Follow the returned URL to the PR or MR on your Git host.
4. Confirm the file path matches the table above — `remediation/…json` for
   drift, `codify/…tf` for an unmanaged resource.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "No GitHub token configured" | `GITHUB_PAT` / `GITLAB_PAT` not set on the deployment | Set it and restart; see [Secrets](https://cloudkeel.io/docs/configuration/secrets/) |
| "Remediation must be approved before opening a pull request" | The finding is critical and nobody approved it | Approve it first |
| "target_repo is required" | No repository given on the request | Supply the target repo |
| "No captured live payload to codify this resource from" | The unmanaged finding has no stored live snapshot | Re-scan so a snapshot is captured, then retry |
| Codify rejected for this type | No identity mapping for that resource type | Import it manually; Cloudkeel-DD will not guess an import id |
| PR opened but merging changed nothing | Expected for drift PRs — they add a JSON record, not HCL | Write the Terraform change yourself |
| Status is `failed` | The Git host refused the request | Read the recorded error; usually token scope or a wrong repo path |

## Related

- [The drift lifecycle](https://cloudkeel.io/docs/concepts/drift-lifecycle/) - where these actions sit in the seven states, and what re-arms a notification
- [Codify an unmanaged resource](https://cloudkeel.io/docs/usage/codify-unmanaged/) - the import-block flow in full
- [Baselines and suppression](https://cloudkeel.io/docs/concepts/baselines-and-suppression/) - when suppressing is the right answer instead
- [Security model](https://cloudkeel.io/docs/claims/security-model/) - why detection needs no write access
