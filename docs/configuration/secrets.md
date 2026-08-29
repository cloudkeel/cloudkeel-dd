---
title: "Secrets & the Fernet key"
description: "The two secrets Cloudkeel-DD needs, why the Fernet key is immutable, and what happens if you lose it."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/configuration/secrets/](https://cloudkeel.io/docs/configuration/secrets/)**

Cloudkeel-DD needs two secrets. One is routine; one is **immutable and
load-bearing**.

## The Fernet key (immutable)

`secrets.fernetKey` encrypts every cloud credential you connect, at rest in the
database. It is a Fernet key (32-byte urlsafe base64).

> [!CAUTION]
> **Set it once, never change it**
>
> The Fernet key is **immutable for the life of the install**. If you lose or
> change it, every stored cloud credential becomes **undecryptable** — you'd
> have to reconnect every integration. Treat it like a root secret.


Generate it once, before first install:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Store it in your secret manager (Key Vault, Secrets Manager, Secret Manager,
Sealed Secrets, …) and pass the **same value** on every `helm upgrade`.

## The JWT secret

`secrets.jwtSecret` signs user session tokens. It is **not** immutable —
rotating it simply logs everyone out and is a safe way to invalidate all
sessions. Generate any long random string:

```bash
openssl rand -base64 48
```

## How to supply them

Never put real secret values in a committed `values.yaml`. Options, best first:

1. **External secret operator** (External Secrets, Sealed Secrets) syncing from
   your secret manager into the release's secret.
2. **`--set-file` / `--set`** from a CI secret store at deploy time (the value
   never lands in git).
3. A **pre-created Kubernetes Secret** the chart references.

## What's encrypted vs. what isn't

- **Encrypted with the Fernet key:** connected cloud credentials (access keys,
  SAS tokens, service-account keys, kubeconfig tokens).
- **Not secret:** discovered resource inventory, drift findings, diffs. These
  describe your infrastructure's shape, not its credentials.

Cloudkeel-DD **never** stores Kubernetes `Secret` *contents* in a diff — that
resource kind is excluded from comparison entirely. See the
[security model](https://cloudkeel.io/docs/claims/security-model/).
