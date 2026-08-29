# Getting support

## Before opening an issue

1. Check **[the docs](https://cloudkeel.io/docs)** — especially the
   [FAQ](https://cloudkeel.io/docs/claims/faq) and the getting-started /
   configuration sections.
2. Confirm which version you're running: `helm list -n ddetective` (chart
   version) and `kubectl get deploy -n ddetective -o wide` (image tags).

## Opening an issue

Use **[the bug report template](../../issues/new?template=bug_report.md)** for
something broken, or **[the support request
template](../../issues/new?template=support_request.md)** for "how do I…" /
"is this expected…" questions.

Please include:

- Chart and image versions (see above)
- What you expected vs. what happened
- Relevant logs (`kubectl logs -n ddetective deploy/dd-backend`, etc.)

**Redact before you paste.** Logs, `values.yaml`, and error output can contain
credentials, connection strings, internal hostnames, or tokens. Replace them
with placeholders (`<redacted>`) before including them in a public issue.

## Response expectations

This is a small team and there's no formal SLA yet — we read every issue and
prioritize by impact. For anything urgent affecting a production install,
say so in the issue and include the version and impact clearly.

## Found a security vulnerability?

**Don't file it here.** See [SECURITY.md](SECURITY.md) for a private
reporting channel.
