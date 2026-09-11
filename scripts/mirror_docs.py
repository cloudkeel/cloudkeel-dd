#!/usr/bin/env python3
"""Rebuild docs/ in this repo from ddetective-docs-website's Starlight source.

Recreated from scratch per MAINTAINING.md's documented steps (the original
script was never checked into this repo). Matches the established output
format exactly, verified against the mirror's own pre-existing converted
files before this rewrite.

Usage: python3 scripts/mirror_docs.py <path-to-ddetective-docs-website>/website/src/content/docs/docs
"""
import re
import sys
from pathlib import Path

SITE_ORIGIN = "https://cloudkeel.io"

# From website/src/consts.ts - the same values remark-site-vars.mjs resolves
# {{TOKEN}} against at build time on the live site.
SITE_VARS = {
    "APP_VERSION": "0.3.7",
    "CHART_VERSION": "0.3.7",
}

# Matches the same {{BARE_UPPER_SNAKE}} shape as remark-site-vars.mjs's TOKEN
# regex, so a real token here and there never drift apart.
TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

# Starlight aside type -> GitHub alert type. Not a 1:1 name match: Starlight's
# "danger" (most severe) maps to GitHub's most severe alert, [!CAUTION], and
# Starlight's "caution" maps to GitHub's next tier down, [!WARNING] - matches
# MAINTAINING.md's documented mapping and the mirror's own pre-existing
# converted output (checked against helm-values.md/secrets.md/gcp-cross-check.md
# before writing this).
ASIDE_TYPE_MAP = {
    "note": "NOTE",
    "tip": "TIP",
    "caution": "WARNING",
    "danger": "CAUTION",
}

# :::type[optional Title]\n...body...\n:::  (type is one of ASIDE_TYPE_MAP's keys)
ASIDE_RE = re.compile(
    r"^:::(note|tip|caution|danger)(?:\[(.*?)\])?\n(.*?)\n:::[ \t]*$",
    re.MULTILINE | re.DOTALL,
)

# Files under docs/ whose mirror copy is hand-written, not converted - never
# touch these. Path is relative to the source docs/ root, using the MIRROR's
# extension (the live source is .mdx; the mirror keeps its own .md).
HAND_WRITTEN = {"claims/coverage.md"}


def slug_for(rel_path: Path) -> str:
    """docs/configuration/helm-values.md -> configuration/helm-values ;
    docs/index.md -> '' (site root /docs/)."""
    parts = rel_path.with_suffix("").parts
    if parts[-1] == "index":
        parts = parts[:-1]
    return "/".join(parts)


def convert_asides(body: str) -> str:
    def repl(m: re.Match) -> str:
        starlight_type, title, inner = m.group(1), m.group(2), m.group(3)
        gh_type = ASIDE_TYPE_MAP[starlight_type]
        lines = [f"> [!{gh_type}]"]
        if title:
            lines.append(f"> **{title}**")
            lines.append(">")
        for line in inner.split("\n"):
            lines.append(f"> {line}" if line else ">")
        return "\n".join(lines)

    return ASIDE_RE.sub(repl, body)


def convert_file(src: Path, docs_root: Path) -> str:
    text = src.read_text(encoding="utf-8")

    # Split frontmatter (--- ... ---) from body. Every source file has one.
    fm_match = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.DOTALL)
    if not fm_match:
        raise ValueError(f"{src}: no frontmatter found")
    frontmatter, body = fm_match.group(1), fm_match.group(2)

    # {{TOKEN}} -> literal, same regex/vars as the live site's build step.
    def token_repl(m: re.Match) -> str:
        name = m.group(1)
        if name not in SITE_VARS:
            raise ValueError(f"{src}: unknown token {{{{{name}}}}} - add it to SITE_VARS")
        return SITE_VARS[name]

    body = TOKEN_RE.sub(token_repl, body)

    # Root-relative /docs/... links -> absolute, canonical-site links.
    body = body.replace("](/docs/", f"]({SITE_ORIGIN}/docs/")

    # Starlight asides -> GitHub alert blockquotes.
    body = convert_asides(body)

    rel = src.relative_to(docs_root)
    slug = slug_for(rel)
    url = f"{SITE_ORIGIN}/docs/{slug}/" if slug else f"{SITE_ORIGIN}/docs/"
    pointer = f"> Mirrored for search visibility. Canonical, always-current version: **[{url}]({url})**\n"

    return frontmatter + "\n" + pointer + "\n" + body.lstrip("\n")


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    docs_root = Path(sys.argv[1])
    out_root = Path(__file__).resolve().parent.parent / "docs"

    written, skipped = 0, 0
    for src in sorted(docs_root.rglob("*")):
        if not src.is_file() or src.suffix not in (".md", ".mdx"):
            continue
        rel = src.relative_to(docs_root)
        out_rel = rel.with_suffix(".md")
        if str(out_rel) in HAND_WRITTEN:
            print(f"skip (hand-written): {out_rel}")
            skipped += 1
            continue
        converted = convert_file(src, docs_root)
        out_path = out_root / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(converted, encoding="utf-8")
        print(f"wrote: {out_rel}")
        written += 1

    print(f"\n{written} file(s) written, {skipped} hand-written file(s) skipped")


if __name__ == "__main__":
    main()
