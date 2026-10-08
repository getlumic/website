"""QA for get-lumic.com before and after a deploy.

Checks, at widths 1440 / 1024 / 768 / 390 / 360: no horizontal page scroll, every in-page #link has a target,
no banned public term in the visible text, every <video> source and poster answers 200, no phone-only (4:5) film is
referenced, each film in the demo carousel loads and plays when its name is clicked with no second film playing or
unmuted, at phone widths the carousel shows its film count row and progress segments, the 40-second film opens
from the hero in a lightbox with sound and closes on Esc, and the AI connector film (once published) autoplays muted.

Usage: python scripts/qa.py [base_url]      default http://localhost:8766  (serve public/, not the repo root)
Needs: playwright (uses the installed Google Chrome). Exit code 1 on any failure.
"""
import re
import sys
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8766").rstrip("/")
WIDTHS = [1440, 1024, 768, 390, 360]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"  # Cloudflare 403s the default urllib agent
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
                srcs += pg.evaluate("[...document.querySelectorAll('video[data-poster]')].map(v => new URL(v.dataset.poster, location.href).href)")
                # phones play the same 16:9 films: no 4:5 phone cut may be referenced
                if pg.evaluate("document.documentElement.outerHTML.includes('-vertical')"):
                    fails.append("page references a phone-only (-vertical) film")
                # every carousel tab has its slide, in the same order
                tabs = pg.evaluate("[...document.querySelectorAll('#demo .car-tabs [data-film]')].map(t => t.dataset.film)")
                sl = pg.evaluate("[...document.querySelectorAll('#demo .car-slide')].map(s => s.dataset.film)")
                if tabs != sl:
                    fails.append(f"carousel tabs {tabs} do not match slides {sl}")
                for s in sorted(set(srcs)):
                    try:
                        code = urllib.request.urlopen(urllib.request.Request(s, method="HEAD", headers={"User-Agent": UA}), timeout=20).status
                    except Exception as e:
                        code = str(e)
                    if code != 200:
                        fails.append(f"media {s}: {code}")
                # demo carousel: the centre film plays on scroll, and each film loads and plays when its name is clicked
                active = "(v => [v.readyState, v.paused, v.currentTime, v.currentSrc])(document.querySelector('#demo .car-slide.is-active video'))"
                if pg.query_selector("#demo .car-slide video"):
                    pg.evaluate("document.getElementById('car').scrollIntoView({block:'center'})")
                    pg.wait_for_timeout(2500)
                    st = pg.evaluate(active)
                    if st[0] < 2 or st[2] <= 0:
                        fails.append(f"demo film did not play (readyState {st[0]}, paused {st[1]}, t {st[2]:.2f})")
                    for t in tabs[1:] + tabs[:1]:
                        pg.click(f'#demo .car-tabs [data-film="{t}"]')
                        pg.wait_for_timeout(1800)
                        st = pg.evaluate(active)
                        if st[0] < 2 or st[1] or st[2] <= 0 or t not in st[3]:
                            fails.append(f"demo film {t}: did not load and play (readyState {st[0]}, paused {st[1]}, t {st[2]:.2f}, {st[3]})")
                        n = pg.evaluate("[...document.querySelectorAll('#demo .car-slide video')].filter(v => !v.paused || !v.muted).length")
                        if n > 1:
                            fails.append(f"demo film {t}: {n} films playing or unmuted at once")
                else:
                    fails.append("demo carousel videos not found (#demo .car-slide video)")
                # the 40-second film opens from the hero in a lightbox, plays with sound, and Esc closes it
                pg.evaluate("window.scrollTo(0,0)")
                pg.click("#filmOpen")
                pg.wait_for_timeout(2500)
                lb = pg.evaluate("(v => [document.getElementById('film').open, !v.paused, v.muted])(document.getElementById('filmVideo'))")
                if lb != [True, True, False]:
                    fails.append(f"40-second film lightbox: open/playing/muted = {lb}")
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(400)
                if pg.evaluate("document.getElementById('film').open"):
                    fails.append("40-second film lightbox does not close on Esc")
                # the AI connector film (under the flow chart, once published) plays muted when scrolled to
                if pg.query_selector("#connector-film video"):
                    pg.evaluate("document.getElementById('connector-film').scrollIntoView({block:'center'})")
                    pg.wait_for_timeout(2500)
                    cf = pg.evaluate("(v => [v.readyState, v.paused, v.muted])(document.querySelector('#connector-film video'))")
                    if cf[0] < 2 or cf[1] or not cf[2]:
                        fails.append(f"AI connector film did not autoplay muted (readyState {cf[0]}, paused {cf[1]}, muted {cf[2]})")
            if w <= 390:
                # phones: the film count row and the progress segments show without any interaction
                mob = pg.evaluate("""(() => { const m = document.getElementById('carMob'), r = m && m.getBoundingClientRect();
                    const segs = [...document.querySelectorAll('#demo .car-tabs [role=tab]')].filter(b => b.getBoundingClientRect().width > 8);
                    return [!!m && getComputedStyle(m).display !== 'none' && r.height > 20, m ? m.innerText : '', segs.length,
                            document.querySelectorAll('#demo .car-slide').length]; })()""")
                if not mob[0] or "/" not in mob[1]:
                    fails.append(f"{w}px: carousel film count row not shown ({mob[1]!r})")
                if mob[2] != mob[3]:
                    fails.append(f"{w}px: {mob[2]} progress segments shown for {mob[3]} films")
            pg.close()
        b.close()
    print("\n".join(fails) if fails else f"QA ok: {BASE} at {WIDTHS}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
