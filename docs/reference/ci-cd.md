---
title: "Cloudkeel-DD CI/CD templates"
description: "Copy-paste GitHub Actions and GitLab CI templates for the pre-merge policy gate and the post-deploy scan trigger."
---

> Mirrored for search visibility. Canonical, always-current version: **[https://cloudkeel.io/docs/reference/ci-cd/](https://cloudkeel.io/docs/reference/ci-cd/)**

Copy-paste starting points for wiring Cloudkeel-DD into your pipeline. These
are not a published GitHub Action or GitLab CI/CD Component - copy the file
into your repo and adjust paths/branches to match your setup.

## What they do

1. **Policy check** (on every PR touching `terraform/`): runs `terraform
   plan`, extracts `resource_changes` via `terraform show -json`, and POSTs
   them to `POST /api/ci/policy-check`. If any enabled policy is violated,
   the job exits non-zero and fails the PR check.

   When the template's PR/MR context fields are present (`github_repo` +
   `github_commit_sha` + `github_pr_number` on GitHub, or `gitlab_project_id`
   + `gitlab_commit_sha` + `gitlab_mr_iid` on GitLab - both templates set
   these automatically from CI-provided variables), Cloudkeel-DD also posts
   the result back to the PR/MR itself: a commit status (pass/fail, shows up
   in the PR's checks list) plus a comment/note listing any violations, so a
   reviewer sees it inline without opening the CI job log. This uses each
   platform's Commit Status API specifically (not GitHub's Checks API, which
   is GitHub-App-only, and not GitLab's External Status Checks, which is a
   Premium/Ultimate-only feature) - both work with the same plain
   `GITHUB_PAT`/`GITLAB_PAT` token Cloudkeel-DD already uses for remediation.
   Posting failures (bad token, repo not found, rate limit) never fail the
   underlying policy check itself - `passed` in the response is always the
   real verdict; `github_posting`/`gitlab_posting` report separately whether
   the PR-side posting succeeded.
2. **Post-deploy scan trigger** (on merge to `main`): calls `POST
   /api/ci/trigger-scan` so Cloudkeel-DD picks up the change immediately
   instead of waiting for the next scheduled scan.

## Setup

1. In Cloudkeel-DD, go to **Settings -> CI/CD API keys** and create a key.
   Copy it immediately - it's only shown once.
2. Add two secrets/variables to your CI platform:
   - `DRIFT_DETECTIVE_API_URL` - your Cloudkeel-DD instance's base URL.
   - `DRIFT_DETECTIVE_API_KEY` - the key from step 1.
   - **GitLab:** mark both **Masked** but **NOT Protected**. The policy check
     runs on merge-request pipelines (the *feature* branch); a Protected
     variable is only exposed on protected branches, so it would be invisible
     and the job fails with `DRIFT_DETECTIVE_API_URL: parameter not set`.
   - **GitHub:** repository secrets are available to `pull_request` workflows
     from branches in the same repo; nothing extra to set.
3. Copy `github-actions/drift-policy-check.yml` into `.github/workflows/`,
   or `gitlab-ci/drift-policy-check.yml` into (or `include:`d from)
   `.gitlab-ci.yml`.
4. Adjust the `terraform/**` path filters and branch names if your repo
   layout differs from the default. The GitLab template runs on **merge-request
   pipelines** (via a `workflow:` block + a `merge_request_event` rule) - keep
   those, or a bare `changes:` rule produces an "empty/invalid pipeline" error
   on MRs.

## What's not included

- No auto-remediation from CI - opening a remediation PR/MR stays a manual,
  human-approved action inside Cloudkeel-DD.
- One API key can call any `/api/ci/*` endpoint for its tenant - there's no
  per-integration or per-endpoint scoping yet.
- PR/MR posting requires a real `GITHUB_PAT`/`GITLAB_PAT` configured on the
  Cloudkeel-DD backend (same token used for remediation) - without one, the
  policy check itself still works and returns the real result, but
  `github_posting`/`gitlab_posting` will report `success: false` with a
  clear "no token configured" error instead of posting anything.
