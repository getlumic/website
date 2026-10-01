<!-- Canonical instructions for ANY AI agent. CLAUDE.md beside it is a one-line `@AGENTS.md` stub — edit THIS file, never that one. -->

# website — lumic marketing site

Source for [get-lumic.com](https://get-lumic.com) — "AI, deployed into your business and
kept working." Static site served from `public/`, deployed on
Cloudflare Workers.

## Global / lumic doctrine
This repo is part of lumic — read `~/projects/playbook/AGENTS.md` first (auto-imported for Claude via the partner's global file; other agents read it directly).

Public copy is **operator-formal** ("Built by operators"), never casual-conversational —
`01-brand.md`. Brand assets are canonical in the playbook's `brand/` directory; the
favicon, wordmark, and OG image here derive from those, so change the playbook first.
Marketing message and channel doctrine: `11-marketing.md`.

## Layout
- `public/` — the deployed site: `index.html`, `favicon.svg`, `wordmark.svg`,
  `og-image.png`, `apple-touch-icon.png`, `img/`, `christian/` + `christian.vcf`
  (contact card).
- `scripts/` — `build_og_image.py` + `og-template.html`, which regenerate `og-image.png`.
- `wrangler.jsonc` — Cloudflare Workers config.

## Deploy
```
npx wrangler deploy
```
