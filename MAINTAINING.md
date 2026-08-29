# Publishing a release here

This repo mirrors what's already live on the public registry — it never
originates a release. Whenever `ddetective-release` promotes a new chart
version to `oci://registry-1.docker.io/driftdetective/d-detective`, mirror it
here in this order.

## 1. Confirm the version is actually installable

```bash
helm show chart oci://registry-1.docker.io/driftdetective/d-detective --version <v>
```

If this fails, the version was never published (see `0.3.3` in README) —
don't create a release for it. If the chart shows but every pod would
`ImagePullBackOff` (images deleted after the fact, as with `0.3.0`), also
don't create a release — add it to the README's version-notes callout
instead.

## 2. Get real image digests

Don't trust the Docker Hub tags UI (it serves a stale cache). Use the
registry v2 API:

```bash
for repo in ddetective-backend ddetective-frontend; do
  TOKEN=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:driftdetective/$repo:pull" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
  curl -sI -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.index.v1+json" \
    "https://registry-1.docker.io/v2/driftdetective/$repo/manifests/<v>" | grep -i docker-content-digest
done
```

## 3. Write release notes from the real changelog

Pull the actual chart-bump commit message from `ddetective-helm` (private
workspace) — `git log --format="%H %s" -- d-detective/Chart.yaml`, find the
commit that set `version: <v>`, and use its full message as the source. Don't
summarize from memory or from another doc; that's how the workspace's
coverage numbers went stale in the past.

Include: what changed since the previous version, and the digests from step 2.

## 4. Create the GitHub Release

```bash
gh release create <v> --repo cloudkeel/cloudkeel-dd \
  --title "Cloudkeel-DD <v>" --notes-file <notes>.md
```

Create releases in ascending version order so the highest one lands as
"Latest" by default.

## 5. Refresh `values.yaml`

```bash
helm show values oci://registry-1.docker.io/driftdetective/d-detective --version <v> 2>/dev/null \
  | sed '/^Pulled:/d; /^Digest:/d' > values.yaml
```

Then update the provenance header at the top of `values.yaml` (version number
and the `helm show values ...` command it documents) to match `<v>`.

## 6. Check the pricing table still matches the live page

The README's Pricing section is a hand-copied summary of
`ddetective-docs-website/website/src/pages/pricing.astro` (private workspace)
— it is **not** generated, so a pricing change there does not propagate here
automatically. Diff the tiers (price, scope/user counts, support level) in
that file against the README table on every release, not just when you
remember pricing changed — the workspace's own coverage numbers have gone
stale this same way more than once.

## 7. Update the README quickstart

Bump the `--version <v>` in the `helm install` block to the new version. The
`values.yaml` pointer paragraph itself is version-agnostic and doesn't need
editing.

## 8. Lint before pushing

This repo has no CI wired up yet, so run the check by hand against the
private workspace's `scripts/claims-lint.py` before pushing anything
customer-facing (README, release notes, anything under `docs/`):

```bash
python3 -c "
import importlib.util, glob
spec = importlib.util.spec_from_file_location('claims_lint', '<path-to-workspace>/scripts/claims-lint.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
total = 0
for f in glob.glob('**/*.md', recursive=True):
    text = open(f, encoding='utf-8').read()
    findings = m.scan_text(f, text)
    total += len(findings)
    m.report(findings)
print(f'{total} violation(s)')
"
```

## 9. Commit and push

One commit is fine: `values.yaml` + README version bump + (if applicable) the
version-notes callout update and the pricing table.

---

# Refreshing the `docs/` mirror

`docs/` in this repo is a converted copy of
`ddetective-docs-website/website/src/content/docs/docs/` (private workspace,
the Starlight source) — for search visibility only. The live site at
[cloudkeel.io/docs](https://cloudkeel.io/docs) is canonical and always
updates first. This mirror does **not** auto-refresh; re-run it whenever the
upstream docs change meaningfully (new pages, a rewritten section, or a
version bump that changes inline command examples).

## What the conversion does, and why

Plain `.md` files on GitHub don't get Starlight's build step, so a straight
`cp` would ship broken syntax. The conversion:

1. Resolves `{{CHART_VERSION}}` / `{{APP_VERSION}}` template vars to literal
   values (Starlight's `remark-site-vars` plugin does this at build time on
   the live site; GitHub has no build step to do it here).
2. Rewrites root-relative `/docs/...` links to absolute
   `https://cloudkeel.io/docs/...` links — this mirror's file layout isn't
   guaranteed to line up with live-site slugs 1:1, and the live site is
   canonical anyway.
3. Converts Starlight `:::note[Title]` / `:::tip` / `:::caution` / `:::danger`
   asides to GitHub's native `> [!NOTE]` / `> [!TIP]` / `> [!WARNING]` /
   `> [!CAUTION]` alert blockquotes, which GitHub renders as colored callouts
   on plain `.md`. There is no Starlight-aside equivalent outside the site.
4. Inserts a one-line canonical-URL pointer right after each page's
   frontmatter — a reader can land on any one of these files directly from a
   search engine without ever seeing `docs/README.md`.

**One file is hand-written, not converted:** `docs/claims/coverage.md`. The
live Coverage page's breakdown table is generated at build time from the
product's own type registry (`coverage.json`); reproducing the per-type table
here would create a fourth stale copy of exactly the numbers this workspace
has already had to sweep more than once. The mirrored page carries only the
guardrail-level summary (3 real-cloud-proven / 200 spec'd) plus a link to the
live, generated table — don't add the detailed table back here.

## Re-running it

The conversion script isn't checked into this repo (it's a one-off tool, not
a build dependency). Recreate it from this file's git history
(`MAINTAINING.md`'s own log, commit that first added `docs/`), or rewrite it
from scratch following the four steps above — it's under 100 lines of
Python. After running it:

1. Re-verify no leftover Starlight-only syntax:
   `grep -rn ":::" docs/` should show only false positives (e.g. AWS ARNs
   like `arn:aws:s3:::bucket`), never a real aside marker.
   `grep -rn "{{" docs/` and `grep -rEn '\]\(/docs/' docs/` should both be
   empty.
2. Re-check `docs/claims/coverage.md` by hand if coverage numbers changed —
   it's hand-written, so it won't pick up a registry change automatically.
3. Update `docs/README.md`'s index if pages were added, removed, or
   retitled — it mirrors `astro.config.mjs`'s sidebar structure (private
   workspace) and isn't generated either.
4. Lint (step 8 above) before pushing.
