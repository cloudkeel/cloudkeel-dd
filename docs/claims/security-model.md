---
title: "Security model"
description: "What Cloudkeel-DD reads, what it never reads, how credentials are encrypted at rest, and why detection needs no write access."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/security-model/](https://cloudkeel.io/docs/claims/security-model/)**

Cloudkeel-DD is designed to be **safe to point at production**: it runs in your
cluster, reads with least-privilege credentials, and never writes to your cloud.

## Read-only, always

- **No writes to your cloud.** Cloudkeel-DD never creates, updates, or deletes
  cloud resources, and never runs `terraform apply`. Every connection guide uses
  a read-only credential.
- **No auto-remediation.** It produces a revert plan for drift; acting on it
  stays with you.
- The [least-privilege reference](https://cloudkeel.io/docs/claims/least-privilege/) lists the exact
  permissions each credential needs — all read/list/get, nothing mutating.

## What it reads

| Source | What it reads |
|---|---|
| Terraform Cloud / state bucket | Your `.tfstate` (desired resource config) |
| Cloud APIs (Azure/AWS/GCP) | Live resource configuration in **enabled scopes** |
| Kubernetes API | Helm release records + live workload specs |

## What it never reads or stores

- **Kubernetes `Secret` contents are excluded** from comparison entirely — secret
  values never land in a diff.
- It reads Helm's own **release** secrets only to learn desired state (the
  rendered manifest), and still never diffs `Secret` objects.
- It does not read your source code, CI logs, or anything outside the
  integrations you connect.

## Credential handling

- Connected credentials are **encrypted at rest** with your install's immutable
  [Fernet key](https://cloudkeel.io/docs/configuration/secrets/).
- Credentials are supplied by you and scoped narrowly (a bucket, a subscription,
  a cluster). Rotating them is a mint-new-key-then-update flow — see
  [troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/).

## Network & data residency

- All data — inventory, findings, encrypted credentials — stays in **your**
  PostgreSQL inside your cluster.
- Outbound calls go **only** to the endpoints you connect: your Terraform
  backend, your cloud, your clusters. The site and app make no third-party
  calls.
- The UI is reached via `kubectl port-forward` by default, or through your own
  ingress if you opt in — terminate TLS there in production.

## Application security

- All container images run as a **non-root** user.
- The API enforces authentication; sessions are signed with the JWT secret.
- Rate limiting protects the API (configurable).
- Policy evaluation (OPA) is **best-effort** — a broken or absent policy engine
  degrades gracefully and never fails a scan or exposes data.

## Tenancy

Each install serves your organization's tenant(s). Integrations, scopes,
resources, and findings are isolated per tenant.
