---
title: "Why Cloudkeel-DD scores drift instead of just reporting it"
description: "Why every finding carries a severity and a seriousness verdict, and the controls that stop a drift tool becoming a firehose."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/reducing-noise/](https://cloudkeel.io/docs/claims/reducing-noise/)**

Most drift tools fail for the same reason: they report everything. A tag edit,
an autoscaler moving a replica count, a rotated certificate, and a security
group opened to `0.0.0.0/0` all arrive at the same volume. Within a month the
channel is muted, and the change that mattered scrolls past with the other four
hundred.

Cloudkeel-DD is built on the view that detection is the easy half. The product
is mostly the part that comes after: deciding which drift is worth a human's
attention, and giving you the controls to silence the rest permanently.

## The problem

A real cloud estate changes constantly for reasons nobody needs to hear about:

- Controllers and operators write status fields, annotations, and generation
  counters back onto resources you manage.
- Autoscalers change replica counts, and that is their job.
- Certificates rotate. Tokens refresh. Timestamps move.
- The same resource is described differently by Terraform and by the cloud API
  (a CIDR written two ways, a protocol written as `6` in one place and `tcp` in
  another, list ordering that carries no meaning).

If every one of those becomes a finding, the signal-to-noise ratio makes the
tool worthless no matter how good the detection is. So Cloudkeel-DD attacks
noise at four different layers, and it helps to know which layer you are
reaching for.

## Layer 1: normalization (nothing to configure)

Before anything is called drift, both sides of the comparison are normalized by
a declarative spec for that resource type. Protocol aliases, CIDR spellings,
list ordering, and singular/plural merges are absorbed here.

This layer exists so that differences which are not real differences never
become findings at all. There is no setting for it: if a resource type has a
spec, its known false-drift shapes are already handled. Field-level comparison
only happens for types that have one, which is why some resources are tracked
as inventory rather than diffed.

## Layer 2: severity and seriousness (automatic, tunable)

Every real drift is scored. Two separate things are happening, and they are
easy to confuse:

**Severity** answers *how bad is this change?* Findings are classified
harmless, risky, or critical. You can override the defaults for your own
environment with severity rules.

**Seriousness** answers *is this worth surfacing as a finding at all?* It is
the gate that decides whether something becomes a visible, notifiable event
rather than quiet inventory movement.

The practical effect is that an autoscaler moving a replica count and a
security group opening to the internet do not arrive looking the same.

## Layer 3: deliberate silencing (you configure this)

Three mechanisms, and picking the wrong one is the most common source of
confusion. The product used to make that worse by calling two of them a form of
"suppress" - the standing rule is now an **ignore rule**, and only the
per-finding action is still called **Suppress**. What is left to get right is
scope: one class of resource forever, one time range, or one finding.

| Mechanism | Silences | Scope | Ends when |
|---|---|---|---|
| **Ignore rule** | Matching open findings immediately, and future ones at scan time | Ongoing, matches by type/namespace/name pattern | You deactivate or delete the rule (already-silenced findings stay quiet until [bulk un-suppressed](https://cloudkeel.io/docs/usage/suppression-rules/#undoing-an-over-broad-rule)) |
| **Maintenance window** | New findings during a planned change | Time-boxed, matches the same way a rule does | Its `ends_at` passes, or you cancel it |
| **Suppressing one finding** | That single drift event | One event | Its expiry passes, or a human un-suppresses it |

The distinction that matters:

- An **ignore rule** is a standing decision: "we do not care about this
  class of resource, ever." Saving one silences the matching findings you
  already have and stops future ones from being raised. Use it for known,
  low-value noise.
- A **maintenance window** is a temporary decision: "we are deliberately
  changing things between these two times, do not page anyone about it."
  Findings raised inside the window are auto-silenced and expire on their own
  when the window closes.
- **Suppressing one finding** is a judgement about one specific event, not a
  pattern.

A deliberate design choice worth knowing: a maintenance window only silences
findings at the moment they are first raised. If you explicitly un-suppress
something during an active window, the next scan will not silently re-silence
it. Your explicit decision outranks the window.

> [!WARNING]
> **An ignore rule hides drift from every view**
>
> An ignore rule is not a filter on one screen. Matching resources stop
> producing findings everywhere, for everyone. That is the point, but it also
> means a too-broad rule can hide something you needed to see. Prefer the
> narrowest criteria that solves the problem, and always fill in the reason
> field so the next person understands the decision.


## Layer 4: routing (who hears about it)

Reducing volume is only half of it. The other half is that the remaining
findings should reach the people who own the resource, rather than a shared
channel everyone has learned to ignore.

Notification rules can filter by team, and match against a resource's
`owner_team`. See [Routing findings to the right team](https://cloudkeel.io/docs/usage/ownership-routing/).

## Choosing between them

- Noise from a whole class of resource, permanently → **ignore rule**
- Planned change, known start and end → **maintenance window**
- One finding you have judged and accepted → **suppress that finding**
- Right findings, wrong audience → **notification rules and ownership**
- Genuinely wrong classification → **severity rules**

## Related

- [Baselines and suppression](https://cloudkeel.io/docs/concepts/baselines-and-suppression/) - the four quieting mechanisms compared, and how each behaves when you remove it
- [The drift lifecycle](https://cloudkeel.io/docs/concepts/drift-lifecycle/) - where the severity gate sits in a scan
- [Create an ignore rule](https://cloudkeel.io/docs/usage/suppression-rules/)
- [Schedule a maintenance window](https://cloudkeel.io/docs/usage/maintenance-windows/)
- [Route findings to the right team](https://cloudkeel.io/docs/usage/ownership-routing/)
- [Glossary](https://cloudkeel.io/docs/reference/glossary/)
