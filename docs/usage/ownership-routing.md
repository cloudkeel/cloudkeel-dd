---
title: "How to route findings to the team that owns the resource"
description: "Set a resource's owning team and route its findings to the channel that team actually reads."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/usage/ownership-routing/](https://cloudkeel.io/docs/usage/ownership-routing/)**

Reducing the number of findings only helps if the ones that survive reach
someone who can act. This guide sets a resource's owning team and routes
notifications by it, so findings stop landing in a shared channel everyone has
learned to ignore.

## Prerequisites

- An account with the **ADMIN** or **OWNER** role.
- At least one scan completed, so the resources exist in inventory.

## Steps

### 1. Tag resources with an owning team

Set `owner_team` on the resource. Three related fields are available and can be
set independently:

| Field | Purpose |
|---|---|
| `owner_team` | The team notification rules route on |
| `service_name` | The service the resource belongs to |
| `business_unit` | Wider organisational grouping |
| `cost_center` | Chargeback / showback grouping |

**In the UI** (per resource): open **Inventory**, click the resource to open
its drawer, and use **Edit** in the ownership section. It has fields for
**Owner team**, **Service**, **Business unit**, and **Cost center**; set what
you need and **Save**. The Inventory table also shows each resource's owner
team and lets you filter by it, so you can see at a glance what is still
unowned.

**Via the API** (for scripting ownership across many resources at once):

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"owner_team": "platform", "service_name": "checkout"}' \
  https://<your-d-detective-host>/api/resources/<resource-id>
```

Omitting a field leaves it unchanged. To find resource ids:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/resources
```

That listing returns `owner_team`, `service_name`, `business_unit`, and
`cost_center` so you can audit which resources are still unowned.

> [!NOTE]
> **Set it yourself - there is no auto-derivation yet**
>
> Whether you use the UI or the API, ownership is set by hand. Cloudkeel-DD
> does not currently derive `owner_team` from cloud tags, Kubernetes
> namespace labels, or Terraform workspace metadata. For a large estate,
> script the PATCH calls from whatever your existing source of ownership
> truth is rather than editing each resource in the drawer.


> [!WARNING]
> **There is no way to clear a field back to empty via the API**
>
> Passing `null` in a PATCH means "leave unchanged", not "clear". To blank a
> field over the API, send an empty string.


### 2. Route notifications by team

Create a notification rule with a team filter matching the `owner_team` value
you set. Findings on resources owned by that team are routed to that rule's
destination; others are not.

Open **Settings → Notification rules**, fill in **Team** (the form marks it
optional - it is the team filter), and click **Add rule**.

## Verification

1. Set `owner_team` on a resource you can deliberately drift.
2. Create a notification rule filtered to that team.
3. Trigger drift on the resource and run a scan.
4. Confirm the notification arrives via that rule.

To confirm the ownership stuck:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://<your-d-detective-host>/api/resources | \
  python3 -c "import json,sys; [print(r['name'], '->', r.get('owner_team')) for r in json.load(sys.stdin)]"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Team-filtered rule never fires | `owner_team` is empty on the resources | It is manual - PATCH the resources first |
| PATCH returns 403 | Viewer role | Ask an admin |
| Field will not clear | `null` means "unchanged" | Send an empty string instead |
| Ownership lost after re-scan | Should not happen; ownership is resource metadata, not scan output | Confirm you are looking at the same resource id |

## Related

- [The drift lifecycle](https://cloudkeel.io/docs/concepts/drift-lifecycle/) - the severity gate that decides what reaches a channel in the first place
- [Why Cloudkeel-DD scores drift](https://cloudkeel.io/docs/claims/reducing-noise/) - routing as the fourth noise layer
- [Who changed it](https://cloudkeel.io/docs/usage/who-changed-it/) - attribution, which answers a different question
