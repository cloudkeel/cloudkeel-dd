# Documentation

This is a **mirror** of [cloudkeel.io/docs](https://cloudkeel.io/docs) for
search visibility — the live site is canonical and updates first. Every page
here links back to its own live version. If something looks stale, trust the
link, not the page.

## Overview

- [What Cloudkeel-DD does](claims/what-it-does.md)
- [How drift detection works](claims/how-it-works.md)
- [Architecture](claims/architecture.md)

## Getting started

- [Pilot quickstart](getting-started/pilot.md)
- [Production installation](getting-started/production-install.md)
- [Where to go from here](getting-started/next-steps.md)

## Concepts

- [The drift lifecycle](concepts/drift-lifecycle.md)
- [Baselines and suppression](concepts/baselines-and-suppression.md)

## Connecting integrations

- [Connecting integrations (overview)](integrations/overview.md)
- [Checklist & troubleshooting](integrations/troubleshooting.md)
- [Terraform Cloud / Enterprise setup](integrations/terraform-cloud.md)
- [Azure cross-check setup (live verification)](integrations/azure-cross-check.md)
- [AWS cross-check setup (live verification)](integrations/aws-cross-check.md)
- [GCP cross-check setup (live verification)](integrations/gcp-cross-check.md)
- [Azure Terraform state setup](integrations/azure-state.md)
- [AWS Terraform state setup](integrations/aws-state.md)
- [GCP Terraform state setup](integrations/gcp-state.md)
- [Kubernetes / Helm setup](integrations/kubernetes.md)

## Using Cloudkeel-DD

- [Why Cloudkeel-DD scores drift instead of just reporting it](claims/reducing-noise.md)
- [How to act on a drift finding](usage/remediation.md)
- [How to silence a class of resource permanently](usage/suppression-rules.md)
- [How to silence drift during a planned change](usage/maintenance-windows.md)
- [How to route findings to the team that owns the resource](usage/ownership-routing.md)
- [How to bring an unmanaged resource under Terraform](usage/codify-unmanaged.md)
- [How to see who changed a resource](usage/who-changed-it.md)

## Configuration

- [Helm values reference](configuration/helm-values.md)
- [Secrets & the Fernet key](configuration/secrets.md)
- [Licensing](configuration/licensing.md)

## Security & compliance

- [Security model](claims/security-model.md)
- [Least-privilege credentials](claims/least-privilege.md)

## Operations

- [Upgrades](operations/upgrades.md)
- [Backup & restore](operations/backup-restore.md)
- [Monitoring & health](operations/monitoring.md)
- [Air-gapped installation](operations/offline.md)

## Reference

- [Feature inventory](claims/feature-inventory.md)
- [Coverage](claims/coverage.md)
- [Cloudkeel-DD CI/CD templates](reference/ci-cd.md)
- [Glossary](reference/glossary.md)

## Support

- [FAQ](claims/faq.md)
- [Release notes](claims/release-notes.md)

---

Something wrong or out of date? [Open an issue](../../../issues/new/choose)
(redact credentials/hostnames first — see [SUPPORT.md](../SUPPORT.md)), or
just use the live site linked at the top of every page.
