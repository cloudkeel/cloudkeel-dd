---
title: "How to bring an unmanaged resource under Terraform"
description: "Turn an unmanaged resource into a Terraform import block and open a pull request that brings it under management."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/usage/codify-unmanaged/](https://cloudkeel.io/docs/usage/codify-unmanaged/)**

Turn a resource that exists in your cloud but is tracked by no Terraform
configuration into a pull request that adopts it. Cloudkeel-DD generates the
`import {}` block and opens the PR; you review and merge it.

This is how you burn down unmanaged resources rather than just counting them.

## Prerequisites

- An account with the **ADMIN** or **OWNER** role.
- An unmanaged-resource finding for a resource whose type is supported (see
  [Limits](#limits) below).
- Terraform **1.5 or newer** in the target repository - `import {}` blocks do
  not exist before 1.5.
- A GitHub or GitLab token configured on your deployment, if you want
  Cloudkeel-DD to open the PR for you. Without one you can still generate the
  patch and apply it by hand.

## Steps

The UI calls this action **remediation** - "codify" is the internal name for
what happens when the resource being remediated is unmanaged: instead of a diff
to revert, Cloudkeel-DD generates a Terraform `import {}` block to adopt it.

1. Open the resource behind the unmanaged finding (from the drift event, follow
   **View full diff & remediation →**, or open the resource directly).

2. On that finding, click **Create remediation PR**. You will be prompted for
   the provider (`github` or `gitlab`) and the target repository. Cloudkeel-DD
   builds the patch from the **live payload it captured during the scan**, not
   from a fresh read - so the block reflects the resource as it was when
   detected.

3. The generated block looks like this and contains nothing else:

    ```hcl
    import {
      to = aws_security_group.example
      id = "sg-0123456789abcdef0"
    }
    ```

4. What happens next depends on severity. A **critical** finding stops at
   *"Awaiting approval"* - use the **Approve** button to release it. Anything
   lower opens the pull request straight away. (No GitHub/GitLab token
   configured on the deployment? The create step fails; apply the block by hand
   instead.)

5. In the PR, run the step the body tells you to run:

    ```bash
    terraform plan -generate-config-out=generated.tf
    ```

    This is what produces the actual resource configuration. Cloudkeel-DD
    deliberately does not synthesise a resource body - see below.

6. Review the generated config, commit it alongside the import block, and merge.

7. Re-scan. The resource should now be tracked, and the unmanaged finding
   resolves.

## Why it only generates the import block

Generating a full resource body means guessing at every field, and a
confident-looking wrong body is worse than no body: it produces a plan that
quietly changes real infrastructure on the next apply.

`terraform plan -generate-config-out=` is Terraform's own supported path for
this, it uses the real provider schema, and it runs on your machine against
your state. So Cloudkeel-DD generates the part it can be certain about - the
import block and its id - and hands the rest to the tool that does it properly.

## Limits

- **Unsupported types fail explicitly.** If Cloudkeel-DD cannot construct a
  correct import id for a resource type, codify refuses rather than emitting a
  block that would import the wrong thing. You will see a "not supported"
  error naming the type.
- **A finding with no captured live payload cannot be codified.** You will get
  a 422. Re-scan to capture one.
- **`azurerm_role_assignment` has a cross-tenant caveat.** If the assigned
  principal belongs to a different Azure AD tenant, the generated import id can
  be wrong. Cloudkeel-DD has no signal for the principal's tenant, so the PR
  body carries the caveat and a human must check. Read it before merging.

## Verification

After merging and re-scanning, the resource should appear as managed rather
than unmanaged. Track the trend across your estate with the codify-progress
report:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/reports/codify-progress
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| 422 "no captured live payload" | The finding predates payload capture, or the scan did not store one | Re-scan, then retry |
| "not supported" for the type | No import-id strategy exists for that type | Import it by hand; the block is three lines |
| PR not created | No GitHub/GitLab token configured | Apply the patch manually, or ask an admin to configure one |
| `terraform plan` rejects `import` | Terraform older than 1.5 | Upgrade, or write an equivalent `terraform import` command |
| Plan wants to change the resource | The generated config does not match reality yet | Reconcile the generated config before merging - do not apply |

## Related

- [Act on a drift finding](https://cloudkeel.io/docs/usage/remediation/) - the four options, the approval gate, and what each PR actually contains
- [The drift lifecycle](https://cloudkeel.io/docs/concepts/drift-lifecycle/) - what happens to an unmanaged finding once the import PR merges
- [Why Cloudkeel-DD scores drift](https://cloudkeel.io/docs/claims/reducing-noise/)
- [Feature inventory](https://cloudkeel.io/docs/claims/feature-inventory/) - current type coverage
