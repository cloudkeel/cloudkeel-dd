---
title: "Cloudkeel-DD documentation"
description: "Self-hosted configuration-drift detection for Terraform and Kubernetes teams. Install it, connect a cloud, and read your first finding."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/](https://cloudkeel.io/docs/)**

Cloudkeel-DD is self-hosted configuration-drift detection for teams who run
Terraform or Kubernetes on Azure, AWS, or GCP. It compares the state you
declared against the state that is actually running, and reports three things:
resources that no longer match your code, resources no state declares at all,
and resources that break a policy you enabled. It runs inside your own cluster,
reads with read-only credentials, and never writes to your cloud.

## Where to start

- **[Pilot quickstart](https://cloudkeel.io/docs/getting-started/pilot/)** — install on your own
  cluster and read your first drift finding.
- **[Connecting integrations](https://cloudkeel.io/docs/integrations/overview/)** — the
  desired-vs-actual model, then per-cloud setup with the exact read-only
  permissions each one needs.
- **[The drift lifecycle](https://cloudkeel.io/docs/concepts/drift-lifecycle/)** — how a finding is
  scored, attributed, and resolved.
- **[Coverage](https://cloudkeel.io/docs/claims/coverage/)** — exactly which resource types are
  checked field-by-field, and which are tracked as inventory.

## Reference

- **[Act on a drift finding](https://cloudkeel.io/docs/usage/remediation/)** — accept, revert, suppress, or open a remediation PR
- **[Baselines and suppression](https://cloudkeel.io/docs/concepts/baselines-and-suppression/)** — the four ways a finding goes quiet
- **[Security model](https://cloudkeel.io/docs/claims/security-model/)** — what is read, what is never read, and where credentials live
- **[Feature inventory](https://cloudkeel.io/docs/claims/feature-inventory/)** — every capability, marked shipped or gap
- **[Troubleshooting](https://cloudkeel.io/docs/integrations/troubleshooting/)** — why an integration has no findings
- **[Glossary](https://cloudkeel.io/docs/reference/glossary/)** — drift, unmanaged, scope, inventory, spec
