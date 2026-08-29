---
title: "Azure cross-check setup (live verification)"
description: "Create an Azure service principal with the built-in Reader role and connect it, then enable the subscriptions you want scanned."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/azure-cross-check/](https://cloudkeel.io/docs/integrations/azure-cross-check/)**

This connects Cloudkeel-DD to the live Azure API so it can **independently verify**
what Terraform claims, and find resources Terraform doesn't know about at all.

This is the credential that makes Cloudkeel-DD do its actual job. Without it,
Terraform-declared resources are still discovered and listed, but tagged
**"no live comparison available"** - Cloudkeel-DD won't pretend to have checked
something it couldn't reach.

It's a **read-only** credential. Cloudkeel-DD never modifies Azure resources.

## Why there's no custom role file here

AWS and GCP ship a least-privilege policy document in this folder
(`aws-iam-policy.json`, `gcp-iam-roles.json`) because those clouds need a custom
role built. **Azure doesn't** - the built-in **Reader** role is already exactly
what's needed: read everything, change nothing. So there's nothing to ship.

## 1. Create a service principal

One command creates the app registration, generates a secret, and assigns Reader
at your subscription:

```bash
az ad sp create-for-rbac \
  --name "d-detective" \
  --role Reader \
  --scopes /subscriptions/<your-subscription-id>
```

It prints the three values you need - **the password is shown once**:

```json
{
  "appId":    "...",   // -> Client ID
  "password": "...",   // -> Client secret
  "tenant":   "..."    // -> Tenant ID
}
```

<details>
<summary>Prefer the Azure Portal?</summary>

1. **Microsoft Entra ID -> App registrations -> New registration**. Name it
   (e.g. `d-detective`), leave the defaults, Register.
2. On the app's **Overview** page, copy the **Application (client) ID** and
   **Directory (tenant) ID**.
3. **Certificates & secrets -> New client secret**. Copy the secret's
   **Value** - not its Secret ID. Azure only shows it once.
4. Assign the role - see step 2 below.

</details>

## 2. Choose the role assignment scope

The command above scopes Reader to **one subscription**. That's the right default.

**Scanning several subscriptions?** Assign Reader once at the **management group**
level instead, and Cloudkeel-DD will discover every subscription underneath it:

```bash
az role assignment create \
  --assignee <appId> \
  --role Reader \
  --scope /providers/Microsoft.Management/managementGroups/<management-group-id>
```

One credential can span many subscriptions - you don't create one integration per
subscription. Each discovered subscription becomes a **scope** you enable
individually.

To add another individual subscription instead:

```bash
az role assignment create \
  --assignee <appId> \
  --role Reader \
  --scope /subscriptions/<another-subscription-id>
```

## 3. Connect it in Cloudkeel-DD

Settings -> **Cross-check integrations** -> **Azure**:

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-azure` |
| Tenant ID | `tenant` from step 1 |
| Client ID | `appId` from step 1 |
| Client secret | `password` from step 1 - the value, not the ID |

Click **Test connection**, then save.

## 4. Enable the subscriptions you want scanned

Open the **Scopes** panel on the integration and click **Discover**. Every
subscription your service principal can read appears as a scope.

Scopes are **opt-in**: a discovered subscription is never scanned until you
**Enable** it. You can also set each scope's **environment** (production,
staging, dev), which feeds the severity rules - drift in a dev subscription can
be gated differently from production.

Discovery re-runs automatically every 6 hours.

## What gets verified

**Field-level drift verification — 79 Azure resource types**, of which **68** are
cross-checked when the desired state comes from a Terraform plan and **77** from
raw `.tfstate`.

The [coverage page](https://cloudkeel.io/docs/claims/coverage/) lists every one of them with its
per-path status, and is generated at build time from the product's own type
registry — read the per-type detail there rather than from a list on this page.

The only types whose two paths differ:

- **`azurerm_role_assignment` and `azurerm_role_definition` are plan-path only.**
  The raw-state path has no ARM api-version entry for them, so they are tracked
  as inventory there.
- **Eleven types are raw-state-path only** — among them SQL databases, elastic
  pools, storage containers and shares, service bus queues and topics, and the
  Windows VM / function-app / web-app types. Connect a state source if those
  matter to you.

Azure is Cloudkeel-DD's deepest cross-check on the plan path. AWS covers security
groups only there and GCP covers all 59 of its types; see the coverage page for
the full matrix.

**Unmanaged-resource detection:** all 79 enumerated Azure types. Any of them
running in an enabled subscription that no connected Terraform state declares is
flagged.

Two limits to know before your first scan:

- **Key Vault keys are invisible to this cross-check.** They are data-plane
  objects that Resource Graph and ARM do not expose, so `azurerm_key_vault`
  compares vault-level posture instead — purge protection, RBAC mode, network
  access.
- **SQL TDE and backup retention are per-database child resources.**
  `azurerm_mssql_server` compares server-level posture instead — public network
  access and minimum TLS version.

## Notes

- **One Azure credential per workspace.** That credential spans many
  subscriptions via scopes. Connecting a second active Azure integration is
  rejected with a 409 - a second one would be silently ignored by every scan,
  so it fails loudly instead. Edit or deactivate the existing one.
- **Client secrets expire** (default 12-24 months, set by your tenant policy).
  When it does, scans fail and the integration shows the real Azure error in
  Inventory's **Last error**. Generate a new secret and update the integration -
  nothing else changes.
- **A failed scan never changes scope status.** Only a *successful* discovery can
  mark a scope as lost, so a broken credential can't make your subscriptions look
  deleted.
