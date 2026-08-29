---
title: "Where to go from here"
description: "What to set up after your first drift finding: scheduling, severity rules, notifications, and the CI/CD policy gate."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/getting-started/next-steps/](https://cloudkeel.io/docs/getting-started/next-steps/)**

You've run the [pilot](https://cloudkeel.io/docs/getting-started/pilot/) and read your first finding. This is what to
reach for next, and what the pilot deliberately leaves out.

## Broaden coverage

- **[Connect Kubernetes](https://cloudkeel.io/docs/integrations/kubernetes/)** — Helm release drift on
  AKS / EKS / GKE. One kubeconfig integration is self-contained (no separate
  cross-check credential needed).
- **[Connect AWS](https://cloudkeel.io/docs/integrations/aws-cross-check/)** (security groups) and
  **[GCP](https://cloudkeel.io/docs/integrations/gcp-cross-check/)** (firewall rules) — the same
  independent cross-check, other clouds.
- **[CI/CD gates](https://cloudkeel.io/docs/reference/ci-cd/)** — block drift pre-merge with a policy
  gate, and trigger a scan right after a deploy.

## Tune the signal

- **[Why drift is scored, not just reported](https://cloudkeel.io/docs/claims/reducing-noise/)** — the
  severity model that keeps the feed actionable.
- **Route findings to a team** — Slack or webhook, filtered by severity, category,
  and owner. See [ownership routing](https://cloudkeel.io/docs/usage/ownership-routing/) and
  **Settings → Notification rules**.
- **Silence known noise** — [ignore rules](https://cloudkeel.io/docs/usage/suppression-rules/) for
  a class of resource, [maintenance windows](https://cloudkeel.io/docs/usage/maintenance-windows/) for a
  planned change.

## Act on findings

- **[Bring an unmanaged resource under Terraform](https://cloudkeel.io/docs/usage/codify-unmanaged/)** —
  generate the import block for something running in no state file.
- **[See who changed a resource](https://cloudkeel.io/docs/usage/who-changed-it/)** — attribution from
  the cloud's own activity log.

## What this pilot does not include

- **No SSO/SAML** — email/password with role-based access control today.
- **No billing** — nothing to pay, nothing to configure.
- **TLS is your call** — the chart takes a TLS secret; it doesn't provision certs.
  A stable hostname/TLS is the [production installation](https://cloudkeel.io/docs/getting-started/production-install/) path.
- **Cloudkeel-DD never writes to your cloud** — remediation is a PR you review and
  merge yourself. Read-only credentials are enough, everywhere.
