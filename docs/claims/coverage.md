---
title: "Coverage"
description: "What Cloudkeel-DD detects, per cloud and resource type."
---

> Mirrored for search visibility. This page's full breakdown table is
> **generated at build time** from the product's own type registry, so it
> cannot be reproduced statically here without risking going stale. For the
> live, always-current, per-type breakdown: **[https://cloudkeel.io/docs/claims/coverage/](https://cloudkeel.io/docs/claims/coverage/)**

Cloudkeel-DD is honest about coverage: capabilities are marked **Shipped** or
**Gap**, and every discovered resource type that isn't field-diffed is tracked
as **inventory** — clearly labelled, never silently assumed clean.

## The three bars, never blurred together

- **Real-cloud drift-proven** — drift injected into a live account and
  detected field-level. **3 types**: Azure NSG rules, AWS security-group
  rules, GCP firewall rules. This is the only bar we state as proven on a
  live account.
- **Engine-verified** — passes golden-fixture tests, not yet proven on a live
  account. **200 spec'd types**: Azure 79, AWS 62, GCP 59.
- Everything else discovered is **inventory-level** today.

## Coverage is path-dependent, not just cloud-dependent

Which of the 200 spec'd types are actually cross-checked against your live
cloud depends on **where your desired state comes from**, not only on which
cloud it is — Terraform Cloud/Enterprise (or a local plan file) reaches a
different subset than raw `.tfstate` in S3/GCS/Azure Blob. AWS in particular
is materially narrower on the plan path. The live page above has the exact
per-path, per-type table, regenerated on every build — that's the version to
cite, not this summary.

Scans are **point-in-time**, never continuous.
