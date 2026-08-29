# Security policy

Cloudkeel-DD runs with **read-only** access to your cloud accounts by design,
and this repo carries no application source — but if you find a vulnerability
in the software itself (the images, the chart, the API, or the frontend),
please report it privately rather than filing a public issue.

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.**

Email **hello@cloudkeel.io** with:

- A description of the issue and its potential impact
- Steps to reproduce, or a proof of concept if you have one
- The chart/image version you tested against (`helm list -n ddetective` /
  `kubectl get deploy -n ddetective -o wide`)

<!-- MAINTAINERS: consider a dedicated security@cloudkeel.io alias once
     someone owns triaging it — don't publish it here until it actually
     exists and is monitored (same rule this project already applies to
     every published contact address: no mailbox, no claim). -->

We'll acknowledge reports and work with you on a disclosure timeline. Please
give us a reasonable window to ship a fix before any public disclosure.

## Scope

In scope: the Cloudkeel-DD Helm chart, container images, API, and frontend as
published to the public Docker Hub / OCI registry. Not in scope: your own
cluster configuration, third-party integrations you've connected, or
infrastructure you manage outside of Cloudkeel-DD.
