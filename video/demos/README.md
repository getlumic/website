# Demo films

Short, silent, looping product videos for the site's "See it running" section (`#demo`). Each one shows a real lumic dashboard running on made-up data for a fictional company, moved by a camera written in code.

1. **Screens**: the dashboards run on any machine against a made-up data source, with no live data anywhere. cua-driver drives Chrome through them and saves each screen (1423x815). The kit that builds and runs that demo copy is private (it names the client's systems), so it lives in the playbook: `brand/demo-films/suite-demo/`. Screens are copied into `shots/<film>/`.
2. **Film**: `<film>/demo.html` sets `window.FILM` (screens, camera keys, cursor, clicks, highlight rings, captions, title and end card). `engine.js` draws it at 1920x1080, and `window.seek(t)` is deterministic.
3. **Render**: `python video/demos/render.py <film> [--at 3 5.9 12]` writes an MP4, a WebM and a poster into `out/<film>/`. Publish by copying them to `public/video/demos/`.
4. **Check**: `python scripts/qa.py http://localhost:8766` against `public/` served locally, then after deploy against https://get-lumic.com.

Films: `receivables`, `sales`, `purchasing`, `financial` (23 s each).

`capture_live.py` is the older fallback: it scrambles captures of a live dashboard in the browser. Use it only where a dashboard cannot run on made-up data.

`shots/`, `out/`, `_test/`, `_review/` and `.auth/` are git-ignored. Captures and sign-in sessions never go into this public repo.
