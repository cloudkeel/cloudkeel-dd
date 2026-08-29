---
title: "How to silence drift during a planned change"
description: "Schedule a window so drift from planned work is auto-silenced, and understand why it only applies to newly raised findings."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/usage/maintenance-windows/](https://cloudkeel.io/docs/usage/maintenance-windows/)**

Schedule a window around planned work so the drift it produces does not page
anyone. Findings raised inside the window are auto-silenced and expire on their
own when it closes - you do not have to remember to turn anything back on.

For noise you want gone permanently, use an
[ignore rule](https://cloudkeel.io/docs/usage/suppression-rules/) instead.

## Prerequisites

- An account with the **ADMIN** or **OWNER** role.
- Start and end times for the work.

## Steps

1. Open **Settings → Maintenance windows**.

2. Name the window after the work, not the date: `Q3 network migration`.

3. Set **starts_at** and **ends_at**. Both are required and `ends_at` must be
   after `starts_at`.

> [!NOTE]
> **Windows are date-ranged, not recurring**
>
> There is no "every Saturday 02:00-04:00" schedule. Each window is one
> explicit time range. For recurring work, create a window per occurrence.


4. Set at least one match criterion - the same three fields an ignore rule
   uses, matched the same way:

    | Field | Matches |
    |---|---|
    | `resource_type` | Exact resource type |
    | `namespace` | Exact namespace |
    | `name_pattern` | Glob against the resource name |

    As with rules, criteria combine with AND, and a window with no criteria is
    rejected rather than treated as "match everything".

5. Fill in the **reason** - it is copied onto every suppression the window
   creates, so whoever reviews those findings later can see why they were
   silenced.

6. Click **Add window**.

## What actually happens

While the window is open, a new finding that matches its criteria is
immediately marked suppressed, with an expiry equal to the window's `ends_at`.
When that time passes, the normal expiry sweep reopens the finding if it is
still real - so nothing is lost, it is only deferred.

Two behaviours worth knowing:

- **Only new findings are caught.** A finding that already existed before the
  window opened is not retroactively silenced.
- **Your explicit decisions win.** If you un-suppress a finding while the
  window is still open, later scans will not silently re-suppress it.

## Verification

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/maintenance-windows
```

The window should be listed with `is_active: true`. Trigger a scan during the
window and confirm matching findings arrive already suppressed rather than open.

## Ending a window early

Set the window inactive (**PATCH** with `is_active: false`, or toggle it in the
UI). New findings stop being auto-suppressed immediately.

Suppressions the window already created keep their original expiry - they are
an audit record of a decision that was made, so cancelling the window does not
retroactively rewrite them. Un-suppress those findings individually if you need
them back sooner.

> [!NOTE]
> **Windows cannot be edited after creation**
>
> Criteria and times are fixed once a window exists, and there is no hard
> delete. A window's scope changing underneath suppressions it already
> created would make those records untrustworthy. Cancel it and create a new
> one instead.


## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Findings still arriving open | Window not active yet, or criteria do not match | Check `starts_at` has passed and the resource actually matches |
| Findings reopened too early | Expiry equals `ends_at`; the sweep runs periodically after that | Expected - extend by creating a new window |
| Existing findings not silenced | Windows only catch newly-raised findings | Suppress those individually |
| 403 on create | Viewer role | Ask an admin |

## Related

- [Baselines and suppression](https://cloudkeel.io/docs/concepts/baselines-and-suppression/) - why a window only applies to findings raised while it is open
- [Why Cloudkeel-DD scores drift](https://cloudkeel.io/docs/claims/reducing-noise/)
- [Create an ignore rule](https://cloudkeel.io/docs/usage/suppression-rules/)
