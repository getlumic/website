# Demo films

Short, silent, looping product videos for the site's demo section. Each one shows a real lumic dashboard, moved by a camera written in code.

1. **Capture**: `capture_live.py <shotlist.json> --terms <terms.json> [--login] [--out DIR]` drives the real dashboard in Chrome. Before the page renders, it scrambles every number and name in the dashboard's data: money is scaled by one hidden factor, ratios are nudged, and names, items and codes are replaced with made-up ones. A leak check runs before each screenshot. Shot lists and term lists name the client, so they live in the private playbook, never in this repo.
2. **Film**: `<film>/demo.html` places the captured screens in a browser-window frame on the site background. It adds camera moves, a cursor, clicks, captions and an end card. `window.seek(t)` is deterministic.
3. **Render**: `python video/demos/render.py <film> [--at 3 5.9 12]` writes an MP4, a WebM and a poster into `out/<film>/`. Use `--out public/video/demos` to publish.

`shots/`, `out/`, `_test/` and `.auth/` are git-ignored. Captures and sign-in sessions never go into this public repo.
