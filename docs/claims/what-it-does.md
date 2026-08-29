---
title: "What Cloudkeel-DD does"
description: "The three things Cloudkeel-DD reports continuously: drift, unmanaged resources, and policy violations."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/claims/what-it-does/](https://cloudkeel.io/docs/claims/what-it-does/)**

Cloudkeel-DD answers one question continuously: **does your live infrastructure
still match what Terraform declared — and what's running that nobody declared?**

## The problem

Terraform tells you what *should* exist. It does not tell you what *actually*
exists right now. Between applies, infrastructure drifts:

- someone fixes an incident with a console click and never puts it back in code,
- a `kubectl scale` or `kubectl edit` changes a workload out of band,
- a resource is created by hand "just for a test" and never cleaned up,
- a security group or firewall rule is widened to unblock someone.

`terraform plan` can catch *some* of this, but only for resources already in
state, only when you run it, and it mutates nothing it doesn't own — so it never
sees **unmanaged** resources at all.

## What Cloudkeel-DD detects

| Signal | Meaning | Example |
|---|---|---|
| **Drift** | A managed resource's live config ≠ its declared config | Firewall `source_ranges` changed from `10.0.0.0/16` to `0.0.0.0/0` |
| **Unmanaged** | A live resource no state declares | A security group created by hand, absent from every `.tfstate` |
| **Policy violation** | Drift or a resource that breaks a rule | A container running as root; a public LoadBalancer with no exception |

Each finding carries a **field-level diff** (`old → new`), a severity, and a
category — not just "something changed."

## Who it's for

- **Platform / DevOps teams** who own Terraform and need to know when reality
  diverges from code.
- **Security & compliance** who need to catch unmanaged resources and
  world-open rules without waiting for the next apply.
- **Anyone doing GitOps-adjacent Kubernetes** with plain Helm (no Argo/Flux) who
  still wants drift detection on releases.

## What it does *not* do

Cloudkeel-DD is **read-only**. It never writes to your cloud, never reverts drift
for you, and never runs `terraform apply`. It tells you what changed and gives
you a revert plan; acting on it stays in your hands. See the
[security model](https://cloudkeel.io/docs/claims/security-model/).
