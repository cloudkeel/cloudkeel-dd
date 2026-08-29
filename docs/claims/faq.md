---
title: "FAQ"
description: "Short answers on read-only access, what Cloudkeel-DD needs to run, how it differs from terraform plan, and what it does not do."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/faq/](https://cloudkeel.io/docs/claims/faq/)**

## Does Cloudkeel-DD change my infrastructure?

No. It is strictly **read-only** — it never creates, updates, or deletes cloud
resources and never runs `terraform apply`. It reports drift and gives you a
revert plan; acting on it is up to you. See the
[security model](https://cloudkeel.io/docs/claims/security-model/).

## Do I have to send my data to a SaaS?

No. Cloudkeel-DD runs in **your** Kubernetes cluster. All state and findings stay
in your PostgreSQL; outbound calls go only to the sources you connect.

## Does the install expire?

It scans for **30 days from the moment you create your first workspace**, then
stops *starting* new scans. That is a local date comparison inside your cluster
— nothing phones home, there is no licence server, and it behaves the same
air-gapped.

Nothing is deleted and nothing else changes: findings, history, connected
integrations and logins all keep working, and any scan already running finishes.
An upgrade can never cut an existing install short — the 30 days runs from
whichever is later, your first workspace or the first version you ran that
enforces the timer.

`config.licenseExpiresAt` extends the window and
`config.licenseEnforcementEnabled: false` returns it to reporting-only; both are
in [the pilot timer](https://cloudkeel.io/docs/configuration/helm-values/#the-pilot-timer). Ask us
and we extend it.

## Why do I need two integrations per cloud?

One supplies *desired* state (Terraform/state source), the other reads *actual*
state (a cloud cross-check credential). Drift is the diff between them, so you
need both. Kubernetes is the exception — one kubeconfig is self-contained.
See [how it works](https://cloudkeel.io/docs/claims/how-it-works/).

## I connected everything but no drift shows up.

Most often the **cross-check scope isn't enabled**. AWS/GCP auto-enable it;
**Azure** discovers subscriptions and leaves them disabled until you opt in.
Also confirm each discovered `.tfstate` is **Enabled**. See
[troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/).

## Why didn't a tag change show as drift?

By design. Tag/label-only changes are low-signal; the normalizers focus on
security-relevant fields (firewall/security-group rules, replica counts, images).

## Which resources get full field-level drift detection?

The field-level diff engine covers 200 resource types — 79 Azure, 62 AWS, 59 GCP
— each engine-verified via golden fixtures. Which ones are cross-checked against
your live cloud depends on your state source, not your cloud: raw `.tfstate`
reaches 198 of them, a Terraform plan reaches 128 (all GCP, 68 Azure, and AWS
security groups only). A much smaller subset — three types — is proven against
real cloud accounts, and we keep those two numbers apart.
Everything else is discovered and tracked as inventory, honestly labelled — never
assumed clean. See the [coverage page](https://cloudkeel.io/docs/claims/coverage/) for the full
tables; the [feature inventory](https://cloudkeel.io/docs/claims/feature-inventory/) marks each
capability Shipped or Gap.

## Does it work with EKS and GKE, not just AKS?

Yes — the Kubernetes integration talks to the Kubernetes API, so any distribution
works. EKS needs cluster API access enabled first (an access entry); see
[Kubernetes setup](https://cloudkeel.io/docs/integrations/kubernetes/).

## Do I need Argo CD or Flux?

No. The Kubernetes integration compares **Helm's own release record** against the
live API — it's built for plain `helm install`/`upgrade` with no GitOps tool. If
you *do* run Argo/Flux, use those instead.

## What happens if the policy engine (OPA) is down?

Nothing breaks. Policy evaluation is best-effort; a scan still detects drift and
unmanaged resources and records findings without policy tags.

## How do I rotate a credential?

Mint a fresh key for the same read-only identity and update the integration — no
downtime. Old keys can't be re-read, so always create new rather than reuse.
Steps in [troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/).

## Can I lose data on upgrade?

Upgrades run a schema migration before the app starts; back up PostgreSQL first
and keep the same Fernet key. See [Upgrades](https://cloudkeel.io/docs/operations/upgrades/) and
[Backup & restore](https://cloudkeel.io/docs/operations/backup-restore/).
