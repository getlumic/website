"""QA for get-lumic.com before and after a deploy.

Checks, at widths 1440 / 1024 / 768 / 390 / 360: no horizontal page scroll, every in-page #link has a target,
no banned public term in the visible text, every <video> source and poster answers 200, no phone-only (4:5) film is
referenced, every dashboard film link answers 200, both 16:9 film players fit the screen. At 1440: the hero film
("Why lumic") autoplays muted and its Sound button restarts it from 0 with sound; the overview film in #demo autoplays
muted when scrolled to, takes the sound from the hero film, and never two films play with sound; "Watch each dashboard
on its own" opens and a film plays with sound in a lightbox that closes on Esc; "How the data flows" opens and the
flow chart lays out with its lines.

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
            pg.goto(BASE + "/", wait_until="load")  # not networkidle: the hero film streams, so the network never goes idle
            pg.wait_for_timeout(2000)
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
                # the dashboard film links (behind "Watch each tool on its own") open real files
                films = pg.evaluate("[...document.querySelectorAll('#films .pfilms a')].map(a => a.href)")
                if not films:
                    fails.append("no dashboard film links (#films .pfilms a)")
                srcs += films
                for s in sorted(set(srcs)):
                    try:
                        code = urllib.request.urlopen(urllib.request.Request(s, method="HEAD", headers={"User-Agent": UA}), timeout=20).status
                    except Exception as e:
                        code = str(e)
                    if code != 200:
                        fails.append(f"media {s}: {code}")
                # film players: [readyState, paused, muted, currentTime]
                def film(i):
                    return pg.evaluate(f"(v => [v.readyState, v.paused, v.muted, v.currentTime])(document.querySelector('#{i} video'))")
                def loud():
                    return pg.evaluate("[...document.querySelectorAll('video')].filter(v => !v.paused && !v.muted).length")
                # the "Why lumic" film in the hero autoplays muted
                pg.evaluate("window.scrollTo(0,0)")
                pg.wait_for_timeout(2500)
                st = film("why-film")
                if st[0] < 2 or st[1] or not st[2] or st[3] <= 0:
                    fails.append(f"hero film did not autoplay muted (readyState {st[0]}, paused {st[1]}, muted {st[2]}, t {st[3]:.2f})")
                # Sound on: the film starts again from 0 with sound
                before = st[3]
                pg.click("#why-film .snd")
                pg.wait_for_timeout(400)
                st = film("why-film")
                if st[1] or st[2] or st[3] > 1.5 or before <= st[3]:
                    fails.append(f"hero Sound button: paused {st[1]}, muted {st[2]}, t {before:.2f} -> {st[3]:.2f} (want playing, unmuted, back at 0)")
                if pg.get_attribute("#why-film .snd", "aria-pressed") != "true":
                    fails.append("hero Sound button not pressed after click")
                # the overview film in #demo autoplays muted when scrolled to; the hero film pauses off screen
                pg.evaluate("document.getElementById('overview-film').scrollIntoView({block:'center'})")
                pg.wait_for_timeout(2500)
                st = film("overview-film")
                if st[0] < 2 or st[1] or not st[2] or st[3] <= 0:
                    fails.append(f"overview film did not autoplay muted (readyState {st[0]}, paused {st[1]}, muted {st[2]}, t {st[3]:.2f})")
                if not film("why-film")[1]:
                    fails.append("hero film still plays when scrolled off screen")
                before = st[3]
                pg.click("#overview-film .snd")
                pg.wait_for_timeout(400)
                st = film("overview-film")
                if st[1] or st[2] or st[3] > 1.5 or before <= st[3]:
                    fails.append(f"overview Sound button: paused {st[1]}, muted {st[2]}, t {before:.2f} -> {st[3]:.2f} (want playing, unmuted, back at 0)")
                if not film("why-film")[2]:
                    fails.append("hero film kept its sound after the overview film took it (one voice at a time)")
                if loud() > 1:
                    fails.append(f"{loud()} films playing with sound at once")
                # "Watch each tool on its own": opens, and a film plays with sound in the lightbox; Esc closes it
                pg.click("#films > summary")
                pg.wait_for_timeout(300)
                if not pg.evaluate("document.getElementById('films').open"):
                    fails.append("'Watch each tool on its own' does not open")
                pg.click("#films .pfilms a >> nth=0")
                pg.wait_for_timeout(2500)
                lb = pg.evaluate("(v => [document.getElementById('film').open, !v.paused, v.muted, v.readyState])(document.getElementById('filmVideo'))")
                if lb[:3] != [True, True, False] or lb[3] < 2:
                    fails.append(f"dashboard film lightbox: open/playing/muted/readyState = {lb}")
                if loud() > 1:
                    fails.append(f"dashboard film lightbox: {loud()} films playing with sound at once")
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(400)
                if pg.evaluate("document.getElementById('film').open"):
                    fails.append("dashboard film lightbox does not close on Esc")
                # "How the data flows": opens, and the flow chart lays out with its lines
                pg.click("#sources > summary")
                pg.evaluate("document.getElementById('flow').scrollIntoView({block:'center'})")
                pg.wait_for_timeout(2500)
                fl = pg.evaluate("""[document.getElementById('sources').open, document.getElementById('flow').offsetHeight,
                    document.querySelectorAll('#flowLines path.fln[d]').length, document.getElementById('flow').classList.contains('in')]""")
                if not fl[0] or fl[1] < 200 or fl[2] < 12 or not fl[3]:
                    fails.append(f"'How the data flows': open {fl[0]}, height {fl[1]}, lines {fl[2]}, shown {fl[3]}")
                sw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
                if sw[0] > sw[1]:
                    fails.append(f"{w}px: horizontal scroll with the details open ({sw[0]} > {sw[1]})")
            # both 16:9 players fit the screen
            fit = pg.evaluate("[...document.querySelectorAll('.fp')].map(f => { const r = f.getBoundingClientRect(); return [f.id, Math.round(r.left), Math.round(r.right), document.documentElement.clientWidth]; })")
            fails += [f"{w}px: film {i} does not fit ({l}..{r} of {cw})" for i, l, r, cw in fit if l < 0 or r > cw]
            if len(fit) != 2:
                fails.append(f"{w}px: expected 2 film players (.fp), found {len(fit)}")
            pg.close()
        b.close()
    print("\n".join(fails) if fails else f"QA ok: {BASE} at {WIDTHS}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
