---
title: "Azure Terraform state (raw `.tfstate`) setup"
description: "Connect raw .tfstate blobs in an Azure Storage container as a desired-state source, using a narrow read-and-list SAS token."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/integrations/azure-state/](https://cloudkeel.io/docs/integrations/azure-state/)**

This connects Cloudkeel-DD to raw `.tfstate` blobs sitting in an Azure Storage
container, so it can ingest Terraform state directly instead of going through
Terraform Cloud/Enterprise. It's a **separate, narrow credential** from the
Azure service principal used for live-resource cross-checking (Settings ->
Cross-check integrations -> Azure) - the two are independent and safely
coexist. No AAD app registration or RBAC role assignment is required for
this one; it's a plain SAS token.

## 1. Create a stored access policy on the container

In the Azure Portal: Storage account -> Containers -> your container ->
**Access policy** -> **Add policy**. Grant **Read** and **List** permissions
only, and set an expiry you're comfortable with (a year is reasonable — the
SAS below inherits this policy's expiry).

> [!WARNING]
> **An expired state credential is the one failure worth pre-empting**
>
> When Cloudkeel-DD cannot read your Terraform state, it cannot tell what is
> *managed*. It will not guess: unmanaged-resource detection is **withheld**
> tenant-wide until the read works again, and the scan completes `partial` with the
> 403 named against the state source.
>
> That is the safe direction — the alternative is worse. Before this behaviour
> existed, an expired SAS made the managed set look empty and every live resource
> read as unmanaged, so the product reported a customer's own Terraform-managed
> estate as undeclared, at high confidence.
>
> **So watch the expiry.** Cloudkeel-DD reads the `se=` parameter out of the SAS when
> you save it and shows the date on the integration row in Settings: called out once
> it has **expired**, and flagged when it expires **within 14 days**.
>
> Two limits to know:
>
> - **A SAS built on a stored access policy carries no `se=`** — the window lives
>   server-side, so Cloudkeel-DD has nothing to read and shows no expiry. If you
>   followed step 1, that is this SAS. Blank means *unknown*, never *safe*.
> - **Integrations saved before this shipped read as no-expiry until re-saved.**
>   Existing rows are not backfilled (deriving the date means decrypting every
>   stored secret inside a migration). Open the integration, re-enter the SAS, and
>   save to populate it.


## 2. Generate a SAS token under that policy

Easiest is the same container's **Shared access tokens** blade in the Portal:
pick the stored policy, generate, and copy the token.

From the CLI, sign the SAS with the **account key** - the simplest path, and it
works for anyone who can read the storage account key:

```bash
KEY=$(az storage account keys list --account-name <storage-account> --query "[0].value" -o tsv)
az storage container generate-sas --account-name <storage-account> \
  --name <container> --policy-name <policy> --account-key "$KEY" -o tsv
```

Copy the query-string portion (everything after any `?`) - that's what
Cloudkeel-DD needs, not the full blob URL.

> **Avoid the `--as-user` (user-delegation) variant unless you specifically
> need it.** A user-delegation SAS is authorized by *your* Azure RBAC, so it
> fails at scan time with `403 ... not authorized to perform this operation
> using this permission` unless you hold **Storage Blob Data Reader** on the
> account - even though the SAS string itself grants read+list. The account-key
> SAS above has no such dependency.

## 3. Connect it in Cloudkeel-DD

Settings -> **Terraform state sources** -> **+ Add storage source**:

| Field | Value |
|---|---|
| Integration name | Any label, e.g. `prod-tfstate` |
| Storage account | The storage account name (not the full URL) |
| Container | The container name |
| SAS token | The query string from step 2 |
| Path prefix (optional) | Restrict discovery to one folder, e.g. `envs/` |

Click **Test connection** to confirm Cloudkeel-DD can list `.tfstate` blobs,
then **Save and start scanning**. Discovered state files appear as
`discovered` - nothing is scanned until you explicitly **Enable** each one
(opt-in, same lifecycle as multi-scope subscription discovery).

## 4. Connect a live Azure credential too, for full drift detection

Without a live-resource Azure credential (Settings -> Cross-check
integrations -> Azure) covering the same subscription, resources parsed from
state are still discovered and shown in Inventory, but tagged **"no live
comparison available"** - there's nothing to diff them against, so no
clean/drift verdict is possible. Connect the Azure cross-check credential and
enable the matching subscription's scope to get real drift detection for
state-sourced resources.

Once a state file is discovered, its panel lists exactly which subscription
ids its resources reference (parsed straight out of the ARM ids already in
the state file) - a green badge means an `ENABLED` Cross-check scope already
covers it, grey means it doesn't yet. No guesswork about which subscription
to go connect.

## What gets ingested

Only `azurerm_*` resources are read from state today (Azure-first, matching
this project's existing multi-scope rollout order). Other providers' resources
in a mixed state file are counted but not persisted. Supported resource types
for live comparison: NSGs, route tables, load balancers, public IPs, and AKS
clusters (the same set the plan-JSON cross-check path supports).
