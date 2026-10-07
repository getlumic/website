"""QA for get-lumic.com before and after a deploy.

Checks, at widths 1440 / 1024 / 768 / 390 / 360: no horizontal page scroll, every in-page #link has a target,
no banned public term in the visible text, every <video> source answers 200, and the demo films load and play.

Usage: python scripts/qa.py [base_url]      default http://localhost:8766  (serve public/, not the repo root)
Needs: playwright (uses the installed Google Chrome). Exit code 1 on any failure.
"""
import re
import sys
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8766").rstrip("/")
WIDTHS = [1440, 1024, 768, 390, 360]
# Public wording rules (playbook 03-positioning.md -> Public wording). Client and system names live in the private
# playbook (this repo is public): one regex per line in brand/site-banned-terms.txt.
BANNED = [r"\bFDE\b", r"forward[- ]deployed", r"Coming soon"]
_private = Path.home() / "projects" / "playbook" / "brand" / "site-banned-terms.txt"
if _private.exists():
    BANNED += [l.strip() for l in _private.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
else:
    print(f"note: {_private} not found; checking generic terms only")


def main():
    from playwright.sync_api import sync_playwright
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        for w in WIDTHS:
            pg = b.new_page(viewport={"width": w, "height": 900})
            pg.goto(BASE + "/", wait_until="networkidle")
            sw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            if sw[0] > sw[1]:
                fails.append(f"{w}px: horizontal scroll ({sw[0]} > {sw[1]})")
            if w == 1440:
                bad = pg.evaluate("""[...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href'))
                    .filter(h => h.length > 1 && !document.getElementById(h.slice(1)))""")
                fails += [f"link without target: {h}" for h in sorted(set(bad))]
                text = pg.evaluate("document.body.innerText")
                for pat in BANNED:
                    for m in re.finditer(pat, text, re.I):
                        fails.append(f"banned term on page: {m.group(0)!r}")
                srcs = pg.evaluate("[...document.querySelectorAll('video source, video[poster]')].map(e => e.src || e.poster)")
                srcs += pg.evaluate("""[...document.querySelectorAll('.demo-tabs button')].flatMap(t => ['webm','mp4','poster.jpg']
                    .map(x => location.origin + '/video/demos/lumic-demo-' + t.dataset.film + (x === 'poster.jpg' ? '-poster.jpg' : '.' + x)))""")
                for s in sorted(set(srcs)):
                    try:
                        code = urllib.request.urlopen(urllib.request.Request(s, method="HEAD"), timeout=20).status
                    except Exception as e:
                        code = str(e)
                    if code != 200:
                        fails.append(f"media {s}: {code}")
                if pg.query_selector("#demoVideo"):
                    pg.evaluate("document.getElementById('demo').scrollIntoView()")
                    pg.wait_for_timeout(2500)
                    st = pg.evaluate("(v => [v.readyState, v.paused, v.currentTime])(document.getElementById('demoVideo'))")
                    if st[0] < 2 or st[2] <= 0:
                        fails.append(f"demo film did not play (readyState {st[0]}, paused {st[1]}, t {st[2]:.2f})")
                    for t in ["sales", "purchasing", "financial"]:
                        pg.click(f'.demo-tabs button[data-film="{t}"]')
                        pg.wait_for_timeout(1800)
                        st = pg.evaluate("(v => [v.readyState, v.currentSrc])(document.getElementById('demoVideo'))")
                        if st[0] < 2 or t not in st[1]:
                            fails.append(f"demo tab {t}: did not load ({st})")
            pg.close()
        b.close()
    print("\n".join(fails) if fails else f"QA ok: {BASE} at {WIDTHS}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
