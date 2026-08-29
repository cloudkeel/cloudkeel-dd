---
title: "How to silence a class of resource permanently"
description: "Silence a whole class of resource with an ignore rule, preview what it matches, and remove it without stranding findings."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/usage/suppression-rules/](https://cloudkeel.io/docs/usage/suppression-rules/)**

Stop a whole category of resource from generating drift findings, for good.
Use this for known, low-value noise: a namespace full of scratch workloads, a
resource type your team deliberately manages outside Terraform, a naming
pattern that always churns.

For a *planned, time-boxed* change, use a
[maintenance window](https://cloudkeel.io/docs/usage/maintenance-windows/) instead - it expires on its own.

> [!WARNING]
> **This is not the per-finding Suppress button**
>
> Two different features, two different words. An **ignore rule** (this page,
> found under **Settings → Ignore rules**) is a pattern that silences a *class*
> of resource, now and in the future. The **Suppress** action in a finding's
> drawer silences *that one finding* and nothing else - it creates no rule
> and will not touch the next finding like it. If you clicked Suppress in the
> drawer and expected the whole category to go quiet, this page is the feature
> you wanted. [Which silencing mechanism to reach
> for](https://cloudkeel.io/docs/claims/reducing-noise/) compares all three.
>
> If you are looking for "suppression rules", that was the old name for ignore
> rules - the product calls them ignore rules everywhere now.


## Prerequisites

- An account with the **ADMIN** or **OWNER** role. Viewers can see rules but
  cannot create or change them.
- At least one integration connected and one scan completed, so you can see the
  findings you want to silence.

## Steps

1. Open **Settings → Ignore rules**. If you have no rules yet, the section shows
   an empty state - click **Create a rule** to get the form.

2. Give the rule a **name** that says what it silences, not what it is. `Scratch
   namespaces - no drift tracking` is useful in six months; `rule 3` is not.

3. Fill in at least one match criterion. All three are optional individually,
   but **at least one is required**:

    | Field | Matches | Example |
    |---|---|---|
    | `resource_type` | Exact resource type | `aws_security_group` |
    | `namespace` | Exact namespace (Kubernetes) | `scratch` |
    | `name_pattern` | Glob against the resource name | `tmp-*` |

    Criteria combine with AND. A rule with `resource_type` and `namespace` set
    matches only resources that satisfy both.

> [!WARNING]
> **Empty criteria matches nothing, not everything**
>
> A rule with no criteria set is rejected. This is deliberate: the
> failure mode of "empty means match everything" would silence an entire
> estate by accident.


4. Fill in the **reason**. The form marks it optional and will save without it -
   do it anyway. This is the field that makes the rule reviewable later, and it
   is the difference between a rule someone can safely delete and one nobody
   dares touch.

5. Before saving, check the **preview**: it shows how many resources the
   criteria match, a sample of their names, and - the number that matters -
   how many *currently open findings* saving the rule will silence
   immediately. If the preview says it matches far more than you intended,
   narrow the criteria before saving, not after.

6. Click **Add rule**. The rule takes effect **immediately**: open findings that match are
   silenced in bulk the moment the rule is created (they move to
   `suppressed`, each recording which rule silenced it), and future scans
   stop raising new findings for matching resources. Editing a rule's
   criteria or re-activating a disabled rule triggers the same immediate
   sweep.

## Verification

Check the findings list: matching findings that were open now show
`suppressed`, and each one's history records the rule that silenced it.
After the next scan, confirm no new findings appear for matching resources.

To confirm the rule itself exists and is active:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/ignore-rules
```

Each rule returns with `is_active`. The UI and the API use the same word: the
Settings surface is **Ignore rules** and the path is `/api/ignore-rules`.

## Turning a rule off

Toggle the rule inactive rather than deleting it, if you might want it back.
An inactive rule stops matching immediately but keeps its name and reason as a
record of the decision.

Deleting is permanent, and matching resources will start generating findings
again on the next scan. **Neither deleting nor deactivating reopens the
findings the rule already silenced** - they stay `suppressed`, each still
naming the rule as the reason. That is deliberate: silencing was an explicit
decision, and un-silencing hundreds of findings should be one too. To undo it,
use the endpoint below.

## Undoing an over-broad rule

If a rule silenced more than you intended, reopen everything it suppressed in
one call:

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/ignore-rules/<rule-id>/unsuppress
```

The response says what happened:

```json
{"reopened": 42, "suppressions_cleared": 42}
```

`suppressions_cleared` is how many of the rule's suppressions were withdrawn;
`reopened` is how many findings actually came back to `open`. The two can
differ - a finding that was *also* suppressed manually (or has since been
resolved) keeps its other state rather than being forced open.

This deliberately does **not** deactivate the rule: reopened findings would
just be silenced again on the next scan while the rule still matches them.
Deactivate or edit the rule first, then unsuppress.

> [!WARNING]
> **Delete the rule last, not first**
>
> `unsuppress` needs the rule to still exist — it takes the rule's id, and returns
> `404` once the rule is gone. Delete first and the findings it silenced are left
> with no rule to unsuppress them through. Always work in this order:
>
> **1. deactivate → 2. unsuppress → 3. delete.**
>
> If you already deleted one, the next section is the way back.


## Recovering findings stranded by a deleted rule

Findings silenced by a rule that no longer exists stay `suppressed` with nothing
pointing at them. Nothing reopens them automatically — not the next scan, not the
suppression-expiry sweep — so without this they are invisible indefinitely.

First, ask how many there are. This is **read-only and available to any role**,
because "have I lost findings?" is a question anyone looking at the board should
be able to answer:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/ignore-rules/orphaned-suppressions
```

```json
{
  "count": 12,
  "sample": [
    {
      "drift_event_id": "8f3c...",
      "resource": "azurerm_network_security_group/ddsandbox-nsg",
      "severity": "risky",
      "reason": "Silenced by ignore rule: noisy NSG tags",
      "suppressed_at": "2026-07-14T09:12:44Z"
    }
  ]
}
```

The `sample` (up to 5, newest first) is there so you can see **what** you are
about to reopen before reopening it. The one real risk of recovery is bringing
back something you wanted quiet.

Then repair it. This one is **admin-only**:

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/ignore-rules/recover-orphaned-suppressions
```

```json
{"reopened": 12, "suppressions_cleared": 12}
```

The two counts read the same way as `unsuppress` above: `suppressions_cleared` is
how many stranded suppressions were withdrawn, `reopened` is how many findings
actually returned to `open`. A finding that was *also* suppressed manually, or
has since been resolved, keeps its other state.

**Recovery never notifies.** A reopened finding may be months old, and paging
someone about it at 3am would make the repair worse than the problem. The next
scan re-evaluates it honestly, and alerts from that point on as normal.

### Why this is a button and not automatic

Reopening on delete would be the obvious design, and it was rejected. Silencing
is an explicit decision; reversing it for hundreds of findings at once, as a side
effect of a cleanup, would turn every rule deletion into a delayed alert storm.
So the count is always available and the repair is always yours to trigger.

The steady state here is zero. If the count is non-zero, someone deleted a rule
out of order — worth knowing on its own.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Rule saved but existing findings still show `open` | The immediate sweep runs in the background and normally lands within seconds; if findings stay open, the rule's criteria may not match them (criteria AND together) | Check the rule's preview against one of the still-open findings; loosen the non-matching criterion |
| Rule matches nothing | `name_pattern` is a glob, not a regex | Use `tmp-*`, not `^tmp-.*$` |
| Rule matches far more than intended | Only one criterion set, and it was broad | Narrow the criteria, then `POST /api/ignore-rules/<id>/unsuppress` to reopen what it already silenced |
| Deleted the rule but findings stayed quiet | Deleting never reopens what a rule already silenced | Use `POST /api/ignore-rules/<id>/unsuppress` *before* deleting. Already deleted it? [Recover the stranded findings](#recovering-findings-stranded-by-a-deleted-rule) |
| `404` from `unsuppress` | The rule id no longer exists — it returns `404` rather than a green `{"reopened": 0}`, so this cannot be mistaken for success | [Recover the stranded findings](#recovering-findings-stranded-by-a-deleted-rule) |
| 403 on create | Viewer role | Ask an admin, or have your role changed |

## Related

- [Baselines and suppression](https://cloudkeel.io/docs/concepts/baselines-and-suppression/) - how ignore rules differ from windows, baselines and manual suppression, and why deleting a rule strands findings
- [Why Cloudkeel-DD scores drift](https://cloudkeel.io/docs/claims/reducing-noise/) - which silencing mechanism to reach for
- [Schedule a maintenance window](https://cloudkeel.io/docs/usage/maintenance-windows/) - the time-boxed alternative
