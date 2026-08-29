---
title: "The drift lifecycle"
description: "What happens to a finding from the moment it is detected: the severity gate, actor attribution, the seven states it can occupy, and what re-arms a notification."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/concepts/drift-lifecycle/](https://cloudkeel.io/docs/concepts/drift-lifecycle/)**

A finding is not a log line. It is a record with a lifecycle, and understanding
that lifecycle is what makes the difference between acting on this tool and
muting it.

Each scan runs the same four steps against every resource it can see: **detect**
the difference, **score** it, **attribute** it to whoever made the change, then
**record** it against any finding that already exists.

## 1. Detect

A scan compares a desired state against an actual state.

- **Desired** — a Terraform Cloud workspace, a raw `.tfstate` file, or, for
  Kubernetes, Helm's own stored release manifest.
- **Actual** — a live read of the cloud provider or Kubernetes API.

The comparison runs field by field through a type-specific spec. A type with no
spec is never diffed against a guess: it is annotated
`live_comparison: unavailable` with a reason and counted as inventory. There is
deliberately no fallback raw diff, because an unverified field mapping produces
confident-looking false drift.

Two things are ignored by design:

- **Tag and label-only changes.** Low signal, high volume.
- **Fields the desired state never declared.** The Kubernetes API server defaults
  dozens of fields no chart mentions. Changing a field the manifest owns is
  drift; a field appearing that it never owned is not.

## 2. Score — the severity gate

Every finding is scored against your own rule set. A rule matches on three
optional fields — resource type, environment, and property category — and
produces two things: a **severity** (`harmless`, `risky`, `critical`) and a
boolean **is-serious**.

**The most specific match wins.** Specificity is simply how many of the three
fields the rule pins down. Ties break by priority, then by which rule was created
most recently — so a newer rule you wrote beats an older one at equal
specificity.

Every workspace starts with four editable rules:

| Rule | Matches | Result |
|---|---|---|
| Security-sensitive changes are always serious | any type, any environment, `security` category | `critical`, serious |
| Tag-only drift in staging is not serious | `staging`, `metadata` category | `harmless`, not serious |
| Tag-only drift in development is not serious | `development`, `metadata` category | `harmless`, not serious |
| Everything else defaults to serious | everything | `risky`, serious |

Two behaviours worth knowing:

- **Not-serious findings are still recorded.** They are auto-closed rather than
  discarded, so they appear in history and reports but never alert. You can
  promote one back to open at any time.
- **If no rule matches at all, the finding is scored `risky` and serious.** A
  workspace that deleted every rule fails toward visible, never toward silent.

Findings matched by the baseline registry are forced not-serious regardless of
severity — see [Baselines and suppression](https://cloudkeel.io/docs/concepts/baselines-and-suppression/).

→ Severity rules are edited on the Policies page. If findings are reaching the
wrong people rather than being wrongly scored, the fix is
[ownership routing](https://cloudkeel.io/docs/usage/ownership-routing/), not the severity gate.

## 3. Attribute

Cloudkeel-DD then asks the cloud's own audit log who last wrote to the resource,
and stamps that on the finding.

| Cloud | Source |
|---|---|
| Azure | Activity Log |
| AWS | CloudTrail `LookupEvents` |
| GCP | Cloud Audit Logs |

This is **best-effort and bounded**. Every lookup uses a **72-hour lookback** and
reads at most **5 pages** of results. A missing permission, an API error, or a
change older than the window all produce the same outcome: the field stays blank
and the scan continues. Attribution never fails a scan.

On AWS, CloudTrail's own 90-day retention is a further ceiling.

If attribution matters to you, grant the optional per-cloud read permission —
`cloudtrail:LookupEvents`, `logging.logEntries.list`, or Azure's built-in Reader,
which already includes it.

→ [How to see who changed a resource](https://cloudkeel.io/docs/usage/who-changed-it/) has the exact
grant per cloud, and a symptom table for when the field stays blank.

## 4. Record — the seven states

A finding is a lifecycle entity, not a per-scan row. A re-scan of still-drifted
infrastructure refreshes the finding in place rather than raising a duplicate.

| State | Meaning |
|---|---|
| `open` | Live and unacknowledged |
| `in_progress` | Someone acknowledged it |
| `suppressed` | Deliberately silenced, with a reason |
| `pending_verification` | Someone claimed a fix; awaiting a confirming scan |
| `resolved` | The drift is gone. Terminal |
| `false_positive` | This was never real drift. Terminal |
| `auto_closed` | Scored not-serious. Recorded, never alerted |

The transitions that surprise people:

- **Accept and revert do not close a finding.** They move it to
  `pending_verification`. It becomes `resolved` only when a later scan confirms
  the drift is actually gone, and bounces back to `open` if it is not.
- **Most findings never pass through `pending_verification` at all.** Drift
  usually gets fixed by someone doing their normal job, not by clicking in this
  app first. When a re-scan finds the drift simply gone, the finding resolves
  directly and is credited as reconciled externally.
- **`resolved` and `false_positive` are terminal.** If the same resource drifts
  again later, that is a new finding, not a reopening of the old one.
- **Suppressing requires a reason.** This is enforced in the state machine
  itself, not only in the API schema, so no internal path can bypass it.

Every transition appends a row to an append-only history table. There is no
update or delete path for it.

## What re-arms a notification

A finding that has already been announced will not be announced again unless one
of exactly three things happens:

1. **It is created** in the open state.
2. **It reopens or is promoted** — from auto-closed, suppressed, or
   pending_verification back to open.
3. **Its severity escalates** on a later scan.

Acknowledging and then un-acknowledging a finding deliberately does *not* re-arm
it: you are acting on an alert you are already looking at, not receiving new
information.

Reopening is the highest-signal thing this product says — it means the fix you
claimed did not hold — so it is armed even though the finding was announced
during its previous open spell.

One deliberate exception: reopening findings through orphan recovery does not
re-arm them, because that repairs bookkeeping rather than reporting news. See
[Recovering findings that were already stranded](https://cloudkeel.io/docs/concepts/baselines-and-suppression/#recovering-findings-that-were-already-stranded).

## Acting on a finding

Where each state transition comes from, in task terms:

| You want to | Do this |
|---|---|
| Stop a class of finding being raised at all | [Silence a class of resource](https://cloudkeel.io/docs/usage/suppression-rules/) |
| Silence expected churn during planned work | [Schedule a maintenance window](https://cloudkeel.io/docs/usage/maintenance-windows/) |
| Find out who made the change | [See who changed a resource](https://cloudkeel.io/docs/usage/who-changed-it/) |
| Get the finding to the team that owns it | [Route findings by owning team](https://cloudkeel.io/docs/usage/ownership-routing/) |
| Bring an unmanaged resource under Terraform | [Codify it into an import PR](https://cloudkeel.io/docs/usage/codify-unmanaged/) |
| Accept it, revert it, or open a remediation PR | [Act on a drift finding](https://cloudkeel.io/docs/usage/remediation/) |

## Next

- [Baselines and suppression](https://cloudkeel.io/docs/concepts/baselines-and-suppression/) — the four ways a finding goes quiet
- [Why Cloudkeel-DD scores drift instead of just reporting it](https://cloudkeel.io/docs/claims/reducing-noise/) — why the severity gate exists
- [Coverage](https://cloudkeel.io/docs/claims/coverage/) — which resource types reach this pipeline at all
