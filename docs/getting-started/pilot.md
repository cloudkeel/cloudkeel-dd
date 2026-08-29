---
title: "Pilot quickstart"
description: "Install Cloudkeel-DD with Helm, connect a Terraform source and a read-only cloud credential, and read your first drift finding."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/getting-started/pilot/](https://cloudkeel.io/docs/getting-started/pilot/)**

One goal: get Cloudkeel-DD reading your own infrastructure and show you your
**first real drift finding**. Everything here is on the path to that moment;
anything else is linked, not inlined.

## What you'll have at the end

Cloudkeel-DD running in your cluster, reading your Terraform state, independently
verifying it against live Azure, and showing you what drifted, what nobody
declared, and what violates policy — from **read-only** credentials, without
ever writing to your cloud.

Our own measured run, on a cold single-node AKS cluster, took **15 minutes** from
`helm install` to the first finding. **Budget an hour for your first**: the
workload comes up in under two minutes, but gathering a cloud credential depends
on your org's access, not on Cloudkeel-DD.

> [!NOTE]
> **The measured breakdown (cold AKS, one Standard_D2s_v3 node)**
>
> | Phase | Time |
> |---|---|
> | `helm install` returns | instant (creates resources, doesn't block) |
> | Image pull | dominant factor — 273 MB total, scales with your network |
> | Migration Job completes | 55s (exact, from the Job's own status) |
> | All 7 workloads Running | within 90s |
>
> On a cluster that already has the images cached, the pull disappears and
> you're left with roughly the migration time.


## Prerequisites

Get all of these in hand before you start — the cloud credential is the long pole.

| You need | Verify it |
|---|---|
| A Kubernetes cluster (1.24+) you can create namespaces in | `kubectl auth can-i create namespace` → `yes` |
| Helm 3 | `helm version --short` → `v3.x` |
| A Terraform state source — Terraform Cloud/Enterprise **or** raw `.tfstate` in cloud storage | you can reach the TFC UI, or list the state bucket |
| One **read-only** cloud credential to verify against — the Azure happy path is inlined in [step 4](#4-connect-azure-the-credential-that-does-the-work) | `az account show` → your subscription |

You do **not** need: a cloud account for Cloudkeel-DD itself, an agent on your
nodes, an Ingress controller (the frontend proxies `/api` itself), or any change
to how you run Terraform. The chart and images are public on Docker Hub — no repo
access, no pull secret.

> [!WARNING]
> **Azure app registrations may need approval**
>
> Step 4 creates an Azure service principal, which needs permission to create
> an app registration and assign a role. In locked-down tenants that can need a
> ticket — **start that request first**, it's your critical path.


## 1. Install

Generate the three secrets, then install straight from Docker Hub. The generation
commands sit directly above the install so it's one copy-paste:

```bash
# Needs Python 3 with the `cryptography` package (pip install cryptography).
# No Python locally? See the Docker variant below.
FERNET=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
DATAKEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet(b'$FERNET').encrypt(Fernet.generate_key()).decode())")
JWT=$(openssl rand -base64 48)

helm install dd oci://registry-1.docker.io/driftdetective/d-detective --version 0.3.6 \
  --namespace ddetective --create-namespace \
  --set secrets.fernetKey="$FERNET" \
  --set secrets.dataKeyWrapped="$DATAKEY" \
  --set secrets.jwtSecret="$JWT" \
  --set postgresql.auth.password="$(openssl rand -hex 16)"
```

> [!WARNING]
> **Save `$FERNET` and `$DATAKEY` before continuing**
>
> Together they encrypt every cloud credential you're about to enter. If either
> is lost or changes, those credentials become undecryptable and every
> integration must be re-entered. Both must stay identical across upgrades.


> [!NOTE]
> **This install scans for 30 days, then keeps going on the Free limits**
>
> From chart `0.3.0`, a self-serve install runs unmetered for **30 days from the
> moment you create your first workspace**. There is no form, no account and no
> call to install it — the window is on duration, not on access, and nothing
> phones home to check it.
>
> From chart `0.3.4`, what happens next is that the install moves to the **Free
> limits** and carries on scanning within them. Scopes beyond the limit stop
> getting new scans and say so on their own row; everything within it keeps
> running on its normal schedule.
>
> Nothing is taken away either way: findings, history, connected integrations and
> login all keep working, any scan already running finishes, and nothing is
> deleted. See [the pilot timer](https://cloudkeel.io/docs/configuration/helm-values/#the-pilot-timer)
> for the values that extend the window, or
> [Licensing](https://cloudkeel.io/docs/configuration/licensing/) for raising the limits with a key.
>
> *On charts before `0.3.4` the window ending stopped new scans from starting
> instead.*


> [!NOTE]
> **No Python locally? Generate the secrets with the backend image**
>
> Needs Docker running; it pulls a one-off copy of the public image.
> ```bash
> IMG=driftdetective/ddetective-backend:0.3.6
> FERNET=$(docker run --rm $IMG python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
> DATAKEY=$(docker run --rm $IMG python -c "from cryptography.fernet import Fernet; print(Fernet(b'$FERNET').encrypt(Fernet.generate_key()).decode())")
> JWT=$(openssl rand -base64 48)
> ```


**You should see** all seven workloads reach Running within ~90 seconds:

```bash
kubectl -n ddetective get pods -w
```

> [!NOTE]
> **Reinstalling later?**
>
> `helm uninstall dd` keeps the bundled Postgres data (its PVC survives), so a
> fresh reinstall reuses the old database *including its old password* and the
> migration fails with `password authentication failed`. For a clean reinstall,
> delete the PVC too: `kubectl delete pvc data-dd-d-detective-postgres-0 -n ddetective`.


Want a stable hostname/TLS for a longer-lived pilot, or a managed database?
That's the [production installation](https://cloudkeel.io/docs/getting-started/production-install/) path; the default
here needs neither.

## 2. Open the app and register

```bash
kubectl -n ddetective port-forward svc/dd-frontend 3000:3000
```

Open `http://localhost:3000` and choose **Need a tenant? Register**. The first
account you create owns the workspace.

**You should see** the empty dashboard. There is no seeded demo login in a real
deployment — that exists only in the local dev stack.

## 3. Connect Terraform (your desired state)

Cloudkeel-DD needs to know what *should* exist. Point it at Terraform Cloud (the
default, marked **Recommended**).

1. **Organization slug** — it's in your workspace URL:
   `https://app.terraform.io/app/`**`<organization>`**`/workspaces/...`
2. **API token** — Terraform Cloud → **Settings → Tokens** → create a user or
   team token. Read access is enough; Cloudkeel-DD never queues runs. Copy it —
   it's shown once.

In Cloudkeel-DD: **Connect → Terraform Cloud**, enter `app.terraform.io`, the org
slug, and the token. Click **Test connection**, then **Save and start scanning**.

**You should see** the connection test report how many workspaces it found, then
a first scan start automatically.

> [!NOTE]
> **Keeping raw `.tfstate` instead of Terraform Cloud?**
>
> Register it under **Settings → Terraform state sources** and skip this step:
> [Azure Blob](https://cloudkeel.io/docs/integrations/azure-state/) ·
> [S3](https://cloudkeel.io/docs/integrations/aws-state/) · [GCS](https://cloudkeel.io/docs/integrations/gcp-state/).


## 4. Connect Azure (the credential that does the work)

At this point Cloudkeel-DD can see what Terraform *claims*. It cannot yet check
whether reality agrees. The Azure cross-check credential is what makes it do its
actual job. It's **read-only** — the built-in **Reader** role, nothing custom.

One command creates the app registration, generates a secret, and assigns Reader.
The first line fills in your subscription ID so there's nothing to hand-edit:

```bash
SUB=$(az account show --query id -o tsv)
az ad sp create-for-rbac --name "d-detective" --role Reader --scopes "/subscriptions/$SUB"
```

It prints three values — **the password is shown once**:

```json
{ "appId": "...",      // → Client ID
  "password": "...",   // → Client secret (copy now)
  "tenant": "..." }    // → Tenant ID
```

In Cloudkeel-DD: **Settings → Cross-check integrations → Azure**, enter the Tenant
ID, Client ID, and Client secret, then click **Test connection**. Once the test
passes, that same button becomes **Save and start scanning** - click it. Scanning
several subscriptions? Assign Reader at the management-group level instead — see
[Azure cross-check setup](https://cloudkeel.io/docs/integrations/azure-cross-check/#2-choose-the-role-assignment-scope).

**You should see** a green connection test.

> [!NOTE]
> **Using AWS or GCP instead?**
>
> Same idea, one credential: [AWS cross-check](https://cloudkeel.io/docs/integrations/aws-cross-check/)
> (security groups) · [GCP cross-check](https://cloudkeel.io/docs/integrations/gcp-cross-check/)
> (firewall rules). AWS and GCP auto-enable their scope, so you can skip step 5.


## 5. Enable the subscription scope

> [!WARNING]
> **This is the #1 reason drift never shows on Azure**
>
> Azure **discovers** your subscriptions and leaves each one **disabled** until
> you opt in. A connected credential with no enabled scope runs no verification
> at all. (AWS and GCP auto-enable from the account/project ID — Azure doesn't.)


Open the **Scopes** panel on the Azure integration, click **Discover**, then
**Enable** the subscription you want scanned.

**You should see** the subscription flip from `discovered` to `enabled`. If a
scan later shows no cloud drift, re-check this first — see the
[don't-skip checklist](https://cloudkeel.io/docs/integrations/troubleshooting/#dont-skip-checklist).

## 6. Run your first scan

**Drift Events → Scan now** (or wait for the schedule). Results usually appear
within a minute or two.

## 7. Read your first finding

A drift event is not just "something changed" — it's the exact field, scored:

```
! DRIFT   critical   network-security-group   nsg/web-nsg
  ingress rule "allow-https":
      expected (Terraform):  source = 10.0.0.0/16     ← internal only
      actual   (live Azure): source = 0.0.0.0/0       ← open to the internet
```

Read it left to right:

- **Severity** (`critical`) — from your per-tenant severity rules. Drift in a dev
  scope can be scored lower than the same change in production.
- **Category** (`network-security-group`) — the resource type that drifted.
- **The field diff** — the one property that changed, expected vs. actual, so you
  know exactly what to fix, not just that the resource is dirty.

Alongside drift, the same scan surfaces **unmanaged resources** (running in Azure,
in no Terraform state — most teams find something here on the first scan) and
**policy violations** (OPA-evaluated, e.g. open ingress from anywhere).

Then decide, per event: **Accept** (reality is right — update your IaC),
**Suppress** (known noise; requires a reason, supports an expiry), **Revert plan**
(a suggested plan to push reality back), or **Create remediation PR** (a real,
human-approved GitHub/GitLab PR). Accept and revert don't close the event
immediately — it becomes *awaiting re-scan* and only resolves when a later scan
confirms the drift is gone.

> [!NOTE]
> **A clean first scan is a valid result**
>
> Zero drift means Terraform and reality genuinely agree — not a failure. See
> [what "no drift" legitimately means](https://cloudkeel.io/docs/integrations/troubleshooting/#what-no-drift-legitimately-means).


## Next steps

You have real findings. [**Where to go from here**](https://cloudkeel.io/docs/getting-started/next-steps/) covers
connecting more clouds and Kubernetes, routing findings to a team, CI/CD gates,
tuning noise, and what this pilot deliberately leaves out.

Hitting an error at any step? The
[connection troubleshooting guide](https://cloudkeel.io/docs/integrations/troubleshooting/) maps every
**Test connection** failure to its fix.
