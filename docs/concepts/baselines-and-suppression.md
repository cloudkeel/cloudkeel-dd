---
title: "Baselines and suppression"
description: "The four mechanisms that keep a finding quiet - baselines, ignore rules, maintenance windows, manual suppression - and how each behaves when removed."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/concepts/baselines-and-suppression/](https://cloudkeel.io/docs/concepts/baselines-and-suppression/)**

Four different mechanisms can keep a finding quiet. They are not
interchangeable, they behave differently when you remove them, and picking the
wrong one is the usual cause of "I silenced this and it came back."

| Mechanism | Acts | Expires | Removing it reopens findings? |
|---|---|---|---|
| Baseline exclusions | Before scoring | No | n/a — re-evaluated each scan |
| Ignore rules | Before a finding is recorded, and on findings that already exist | No | **No** — see below |
| Maintenance windows | At the moment a finding is created | Yes, at the window's end | Yes, on expiry |
| Manual suppression | On one existing finding | Optional | Yes, on expiry |

## Baseline exclusions

Your cloud creates resources you never declared. Default VPC security groups,
service-linked roles, AKS node resource groups, GCP's `default-allow-*` firewall
rules — none of these are in your Terraform, and all of them are expected.

Cloudkeel-DD ships a catalog of **14 entries** covering the common cases:

| Cloud | Entries |
|---|---|
| AWS | 2 — service-linked IAM roles, default VPC security group |
| Azure | 4 — AKS managed node resource groups, Network Watcher, Backup, Databricks managed resource groups |
| GCP | 4 — default network firewall rules, three classes of Google-managed service agent |
| Kubernetes | 4 — `kubectl rollout restart`, the default `kubernetes` Service, the `kube-root-ca` ConfigMap, provider-managed namespaces |

A matched finding is still **recorded** — it is not hidden — but it is forced
not-serious, so it never alerts. You can disable any catalog entry for your own
workspace if you would rather see it.

**One caveat you should know about.** The AWS default-VPC security group entry
matches **by name only**. The payload AWS returns does not expose an `IsDefault`
flag, so a security group you created and named `default` is silently baselined
too. If you have one, rename it or disable that entry.

**This catalog is thin for a large estate.** GKE in particular generates
undeclared resources — node VMs, `gke-*` firewall rules — that the catalog does
not yet cover. Expect noise on your first GCP scan and tell us which patterns to
add.

## Ignore rules

An ignore rule stops a finding being recorded at all. A rule matches on any
combination of resource type, namespace, and a name pattern.

- The name pattern is a **glob**, not SQL — `?` and character classes work as
  they do in a shell.
- **A rule with no criteria at all matches nothing**, not everything. Creating
  one is rejected, and any that already exist are treated as inert.

Creating a rule also sweeps findings that **already exist** and matches them. That
sweep runs as a background job, not inside the request that saved the rule, so a
broad rule that matches hundreds of findings cannot time out halfway through.

### Deleting an ignore rule does not reopen what it silenced

This is deliberate, and it is the single behaviour most likely to surprise you.

Nothing in the scan path reopens a suppressed finding. Findings silenced by an
ignore rule are suppressed with **no expiry**, because the reason they are quiet
is the rule, and the rule does not expire — handing them to the expiry sweep
would reopen them, and the very next scan would silence them again.

**So delete in the right order:**

1. **Disable** the rule.
2. **Unsuppress** its findings — there is a bulk unsuppress-by-rule action for
   exactly this.
3. **Then delete** the rule.

Delete first and the link between rule and findings is severed. The findings stay
suppressed with nothing left to explain why.

→ [Undoing an over-broad rule](https://cloudkeel.io/docs/usage/suppression-rules/#undoing-an-over-broad-rule)
has the commands and the expected output.

### Recovering findings that were already stranded

If that already happened, there is a repair. Cloudkeel-DD can identify findings
that are suppressed, have no owning rule, no owning window, no human who
suppressed them, and no expiry — a state nothing else produces — and reopen them.

It is **manual on purpose**. You are shown the count and a sample before anything
changes, and the repair reopens findings **without re-arming notifications**:
these may have been silent for months, and a bookkeeping fix should not page
anyone. The next scan re-evaluates them and alerts honestly if they are still
real.

→ [Recovering findings stranded by a deleted rule](https://cloudkeel.io/docs/usage/suppression-rules/#recovering-findings-stranded-by-a-deleted-rule)
walks the count-then-recover flow.

## Maintenance windows

A window auto-suppresses findings raised during a planned change, matched on the
same resource-type / namespace / name-pattern criteria as ignore rules.

**A window only applies at the moment a finding is created.** It never suppresses
a finding that already existed when the window opened, and it never re-suppresses
one that reopened during the window. That second rule is what stops the next scan
from silently overriding a human who explicitly un-suppressed something
mid-window.

Suppressions created by a window carry the window's own end time as their expiry,
so they reopen on their own when it closes. If two active windows both match a
resource, the one ending **latest** wins.

Window times are evaluated in **UTC**.

→ [Schedule a maintenance window](https://cloudkeel.io/docs/usage/maintenance-windows/) has the steps,
and [Ending a window early](https://cloudkeel.io/docs/usage/maintenance-windows/#ending-a-window-early)
covers closing one ahead of time.

## Manual suppression

Suppressing one finding by hand requires a **non-empty reason** — enforced in the
state machine, not just the API schema — and takes an optional expiry. When the
expiry passes, a sweep running every 15 minutes reopens the finding and re-arms
its notification.

## Which one should I use?

| Situation | Reach for | How to do it |
|---|---|---|
| The cloud made it and always will | Baseline exclusion | Disable or enable catalog entries on the Policies page |
| A whole class of resource is noise forever | Ignore rule | [Silence a class of resource](https://cloudkeel.io/docs/usage/suppression-rules/) |
| Expected churn during a planned change | Maintenance window | [Schedule a window](https://cloudkeel.io/docs/usage/maintenance-windows/) |
| This one finding, for now, with a reason | Manual suppression | Suppress it from the finding's drawer |

## Next

- [The drift lifecycle](https://cloudkeel.io/docs/concepts/drift-lifecycle/) — scoring, attribution, and the seven states
- [Why Cloudkeel-DD scores drift instead of just reporting it](https://cloudkeel.io/docs/claims/reducing-noise/) — the reasoning behind all of this
- [Route findings to the right team](https://cloudkeel.io/docs/usage/ownership-routing/) — quieting is only half the problem
