"""QA for get-lumic.com before and after a deploy.

Checks, at widths 1440 / 1024 / 768 / 390 / 360: no horizontal page scroll, every in-page #link has a target,
no banned public term in the visible text, every <video> source and poster answers 200, no phone-only (4:5) film is
referenced, every dashboard film link answers 200, both 16:9 film players fit the screen. At 1440: the hero film
("Why lumic") autoplays muted and its Sound button restarts it from 0 with sound; the overview film in #demo autoplays
muted when scrolled to, takes the sound from the hero film, and never two films play with sound; "Watch each dashboard
on its own" opens and a film plays with sound in a lightbox that closes on Esc; "How the data flows" opens and the
flow chart lays out with its lines.

Every page in scripts/pages.json, at the same widths: no horizontal scroll, its declared film players fit (and autoplay
muted, take the sound, carry the sample-data note), in-page links have targets, internal links and media answer 200,
one <h1>, canonical and og:url match, a BreadcrumbList. On every page (home included): JSON-LD parses, no we/our/us,
no size-reveal or gap phrases; on inner pages also no banned term and no product name at all (visible text, title,
meta and JSON-LD). /st-louis/ carries no street address. The sitemap lists every page and each answers 200 with a
matching canonical. Off localhost: /about/ and /about answer 301 -> /how-lumic-works/. Home's FAQPage covers exactly
the questions it shows.

Usage: python scripts/qa.py [base_url]      default http://localhost:8766  (serve public/, not the repo root)
Needs: playwright (uses the installed Google Chrome). Exit code 1 on any failure.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8766").rstrip("/")
WIDTHS = [1440, 1024, 768, 390, 360]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"  # Cloudflare 403s the default urllib agent
# Public wording rules (playbook 03-positioning.md -> Public wording). Client and system names live in the private
# playbook (this repo is public): one regex per line in brand/site-banned-terms.txt.
BANNED = [r"Coming soon"]  # FDE is allowed since 2026-10-11 (positioning: FDEs for the back office)
_private = Path.home() / "projects" / "playbook" / "brand" / "site-banned-terms.txt"
if _private.exists():
    BANNED += [l.strip() for l in _private.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
else:
    print(f"note: {_private} not found; checking generic terms only")
# Product names (Christian 2026-10-11): allowed ONLY as whole list items inside the one [data-systems-list] element.
# Anywhere else on the page they fail, even where site-banned-terms.txt does not list them. Checked case-sensitively
# (so the plain word "ramp" is not a hit). Client and employer names stay banned everywhere, the list included.
PRODUCTS = ["QuickBooks Online", "QuickBooks Desktop", "NetSuite", "Sage Intacct", "Sage 100",
            "Microsoft Dynamics 365 Business Central", "Xero", "Acumatica", "Bill.com", "Ramp", "Expensify", "ADP",
            "Paychex", "Gusto", "Salesforce", "HubSpot", "Microsoft 365 / Outlook", "Excel", "Power BI", "SQL Server",
            "Google Workspace", "FileMaker", "Shopify"]
# What the list may show on the page: 15 of them plus the closing pill. All 23 stay in PRODUCT_PATTERNS, so a dropped
# name (Ramp, Gusto, Shopify ...) still fails anywhere on the page; Power BI survives only in Josh's bio (OUTSIDE_OK).
LIST_ITEMS = ["QuickBooks Online", "QuickBooks Desktop", "NetSuite", "Sage Intacct", "Sage 100",
              "Microsoft Dynamics 365 Business Central", "Xero", "Acumatica", "Bill.com", "ADP", "Paychex", "Salesforce",
              "HubSpot", "Microsoft 365 / Outlook", "Excel", "…and hundreds more."]
PRODUCT_PATTERNS = sorted({re.escape(x) for x in PRODUCTS} | {
    r"\bQuickBooks\b", r"\bSage\b", r"\bDynamics 365\b", r"\bBusiness Central\b", r"\bMicrosoft 365\b", r"\bOutlook\b"})
PRODUCT_PATTERNS = [p if p.startswith(r"\b") else rf"\b{p}\b" for p in PRODUCT_PATTERNS]
# Systems pages (pages.json "system": <family>): that family's names only, in the page text, title, meta and JSON-LD.
# Every other product name still fails there. Client and employer names stay banned everywhere.
FAMILIES = {"quickbooks": [r"/systems/quickbooks/", r"\bQuickBooks Online\b", r"\bQuickBooks Desktop\b", r"\bQuickBooks\b"],
            "netsuite": [r"/systems/netsuite/", r"\bNetSuite\b"],
            "sage-100": [r"/systems/sage-100/", r"\bSage 100\b"]}  # own URL slug counts; a bare "Sage" still fails
# No proof, figure or client description on a /systems/ page (a product must never be tied to a client or a number)
PROOF = [r"64 of 67", r"six weeks", r"\b13 agent roles\b", r"nine (?:live )?dashboards", r"specialty manufacturer",
         r"multi-company manufacturer", r"30 a day"]
# Copy that predates the list and stays as written (the flow chart's source tile; Josh's bio, kept verbatim)
OUTSIDE_OK = ["Excel and CSV files", "with Power BI and SQL by trade"]

# ---------- every page (scripts/pages.json), plus content rules that apply to home too ----------
CFG = json.loads((Path(__file__).resolve().parent / "pages.json").read_text(encoding="utf-8"))
SITE = "https://get-lumic.com"
# Voice: third person, lowercase "lumic". Case-insensitive whole words; the "US" country code in JSON-LD is dropped first.
WE = r"\b(?:we|our|us|ours|we['’]re|we['’]ve|we['’]ll)\b"
# Size reveals and gap admissions (public wording rules)
SIZE_REVEAL = [r"\bfirst client\b", r"\bso far\b", r"\bone of us\b", r"\bboth of us\b", r"\bChristian or Josh\b",
               r"\bspeak with a founder\b", r"\bteam of (?:\d+|two|three|four|five|six|seven|eight|nine|ten)\b",
               r"\bfounder[- ]led\b", r"\bcoming soon\b", r"\bnext\b"]
HOME_OK = ["What happens next"]  # the home contact block's heading (live copy, unchanged); inner pages say "How to start"
# A service-area business: no street address anywhere on /st-louis/, including the schema
ADDRESS = [r"streetAddress", r"postalCode", r"\b6[23]\d{3}(?:-\d{4})?\b",
           r"\b\d{1,5}\s+(?:[NSEW]\.?\s+)?[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Parkway|Pkwy|Suite|Ste)\b"]
OPEN_DETAILS_TEXT = """(() => { const c = [...document.querySelectorAll('details:not([open])')]; c.forEach(d => { d.open = true; });
    const t = document.body.innerText; c.forEach(d => { d.open = false; }); return t; })()"""


def fetch(url, method="GET"):
    r = urllib.request.urlopen(urllib.request.Request(url, method=method, headers={"User-Agent": UA}), timeout=20)
    return r.status, (r.read().decode("utf-8", "replace") if method == "GET" else "")


def ld_blocks(html):
    """Every JSON-LD block on a page, parsed (a parse error is returned as a string)."""
    out = []
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            out.append(json.loads(raw))
        except Exception as e:
            out.append(f"JSON-LD does not parse: {e}")
    return out


def ld_strings(x):
    if isinstance(x, dict):
        return [s for v in x.values() for s in ld_strings(v)]
    if isinstance(x, list):
        return [s for v in x for s in ld_strings(v)]
    return [x] if isinstance(x, str) and x != "US" else []


def meta_text(html):
    pats = [r"<title>(.*?)</title>", r'<meta name="description" content="(.*?)"', r'<meta property="og:[a-z_]+" content="(.*?)"',
            r'<meta name="twitter:[a-z]+" content="(.*?)"']
    return "\n".join(m for p in pats for m in re.findall(p, html, re.S))


def content_checks(where, text, html, home=False, allow=()):
    """Voice, size reveals, banned terms, product names (inner pages: none at all) on visible text, meta and JSON-LD."""
    fails = []
    blocks = ld_blocks(html)
    fails += [f"{where}: {b}" for b in blocks if isinstance(b, str)]
    lds = "\n".join(s for b in blocks if not isinstance(b, str) for s in ld_strings(b))
    meta = meta_text(html)
    for label, t in (("text", text), ("meta", meta), ("JSON-LD", lds)):
        for m in re.finditer(WE, t, re.I):
            fails.append(f"{where} {label}: first-person word {m.group(0)!r} (third person, 'lumic')")
        tt = t
        if home:
            for x in HOME_OK:
                tt = re.sub(re.escape(x), " ", tt, flags=re.I)  # innerText can be upper-cased by CSS
        for pat in SIZE_REVEAL:
            for m in re.finditer(pat, tt, re.I):
                fails.append(f"{where} {label}: size reveal or gap phrase {m.group(0)!r}")
        if not home:  # home's visible text gets the banned and product checks above, with its systems-list exception

            for pat in allow:  # a systems page's own product family
                t = re.sub(pat, " ", t)
            for pat in BANNED:
                for m in re.finditer(pat, t, re.I):
                    fails.append(f"{where} {label}: banned term {m.group(0)!r}")
            tp = t
            for x in OUTSIDE_OK:
                tp = tp.replace(x, " ")
            for pat in PRODUCT_PATTERNS:
                for m in re.finditer(pat, tp):
                    fails.append(f"{where} {label}: product name {m.group(0)!r} (product names only in a systems list, or a systems page's own family)")
    return fails


def check_pages(b):
    fails = []
    local = re.match(r"https?://(127\.0\.0\.1|localhost)", BASE) is not None
    # home: JSON-LD parses, voice and size rules, and its FAQPage covers exactly the questions it shows
    st, home = fetch(BASE + "/")
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(BASE + "/", wait_until="load")
    text = pg.evaluate(OPEN_DETAILS_TEXT)
    fails += content_checks("home", text, home, home=True)
    shown = pg.evaluate("[...document.querySelectorAll('#faq .wl h3')].map(h => h.textContent.trim())")
    pg.close()
    faqld = [q["name"] for blk in ld_blocks(home) if isinstance(blk, dict) for g in blk.get("@graph", []) if g.get("@type") == "FAQPage"
             for q in g["mainEntity"]]
    if faqld != shown:
        fails.append(f"home: FAQPage JSON-LD {faqld} does not match the questions shown {shown}")
    for p in CFG["pages"]:
        url, where = BASE + p["path"], p["path"]
        try:
            st, html = fetch(url)
        except Exception as e:
            fails.append(f"{where}: {e}")
            continue
        canon = re.search(r'<link rel="canonical" href="(.*?)"', html)
        if not canon or canon.group(1) != SITE + p["path"]:
            fails.append(f"{where}: canonical {canon and canon.group(1)!r}, want {SITE + p['path']!r}")
        if f'<meta property="og:url" content="{SITE + p["path"]}">' not in html:
            fails.append(f"{where}: og:url does not match the canonical")
        if f"<title>{p['title']}</title>" not in html.replace("&#x27;", "'").replace("&amp;", "&"):
            fails.append(f"{where}: title does not match pages.json")
        types = [g.get("@type") for blk in ld_blocks(html) if isinstance(blk, dict) for g in blk.get("@graph", [])]
        if "BreadcrumbList" not in types:
            fails.append(f"{where}: no BreadcrumbList JSON-LD")
        if p["id"] == "st-louis":
            for pat in ADDRESS:
                for m in re.finditer(pat, html):
                    fails.append(f"{where}: street address detail {m.group(0)!r} (service-area business: no street address)")
        for w in WIDTHS:
            pg = b.new_page(viewport={"width": w, "height": 900})
            pg.goto(url, wait_until="load")
            pg.wait_for_timeout(1200)
            sw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            if sw[0] > sw[1]:
                fails.append(f"{where} {w}px: horizontal scroll ({sw[0]} > {sw[1]})")
            fit = pg.evaluate("[...document.querySelectorAll('.fp')].map(f => { const r = f.getBoundingClientRect(); return [f.id, Math.round(r.left), Math.round(r.right), document.documentElement.clientWidth]; })")
            fails += [f"{where} {w}px: film {i} does not fit ({l}..{r} of {cw})" for i, l, r, cw in fit if l < 0 or r > cw]
            if sorted(x[0] for x in fit) != sorted(p["films"]):
                fails.append(f"{where} {w}px: film players {[x[0] for x in fit]}, pages.json declares {p['films']}")
            if w == 1440:
                bad = pg.evaluate("""[...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href'))
                    .filter(h => h.length > 1 && !document.getElementById(h.slice(1)))""")
                fails += [f"{where}: link without target: {h}" for h in sorted(set(bad))]
                if pg.evaluate("document.querySelectorAll('h1').length") != 1:
                    fails.append(f"{where}: not exactly one <h1>")
                nlist = pg.evaluate("document.querySelectorAll('[data-systems-list]').length")
                ptext = pg.evaluate(OPEN_DETAILS_TEXT)
                if p.get("systems_hub"):
                    if nlist != 1:
                        fails.append(f"{where}: systems hub needs exactly one [data-systems-list], found {nlist}")
                    items = pg.evaluate("[...document.querySelectorAll('[data-systems-list] li')].map(li => li.textContent.trim())")
                    fails += [f"{where}: systems list item {x!r} is not a listed product" for x in items if x not in PRODUCTS + LIST_ITEMS]
                    for x in items:  # listed names are fine inside the list; strip them before the page-wide checks
                        ptext = ptext.replace(x, " ")
                elif nlist:
                    fails.append(f"{where}: a [data-systems-list] outside home and the systems hub")
                if p["path"].startswith("/systems/"):
                    body = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
                    for pat in PROOF:
                        for m in re.finditer(pat, ptext + " " + body, re.I):
                            fails.append(f"{where}: proof or client detail {m.group(0)!r} on a systems page")
                    if re.search(r'href="/portfolio/#', html):
                        fails.append(f"{where}: links to a portfolio card (systems pages link the portfolio page only)")
                allow = [x for f in FAMILIES.values() for x in f] if p.get("systems_hub") else FAMILIES.get(p.get("system"), ())
                fails += content_checks(where, ptext, html, allow=allow)
                # internal links answer 200 (fragments dropped), media answers 200
                links = pg.evaluate("[...document.querySelectorAll('a[href^=\"/\"]')].map(a => a.href.split('#')[0])")
                media = pg.evaluate("[...document.querySelectorAll('video source, video[poster], img[src]')].map(e => e.src || e.poster)")
                for s in sorted(set(links + media)):
                    try:
                        code = urllib.request.urlopen(urllib.request.Request(s, method="HEAD", headers={"User-Agent": UA}), timeout=20).status
                    except Exception as e:
                        code = str(e)
                    if code != 200:
                        fails.append(f"{where}: {s}: {code}")
                # a declared film autoplays muted on screen; its Sound button gives it the one voice on the page
                for fid in p["films"]:
                    pg.evaluate(f"document.getElementById('{fid}').scrollIntoView({{block:'center'}})")
                    pg.wait_for_timeout(2500)
                    stt = pg.evaluate(f"(v => [v.readyState, v.paused, v.muted, v.currentTime])(document.querySelector('#{fid} video'))")
                    if stt[0] < 2 or stt[1] or not stt[2] or stt[3] <= 0:
                        fails.append(f"{where}: film {fid} did not autoplay muted ({stt})")
                    pg.click(f"#{fid} .snd")
                    pg.wait_for_timeout(400)
                    stt = pg.evaluate(f"(v => [v.paused, v.muted])(document.querySelector('#{fid} video'))")
                    if stt != [False, False]:
                        fails.append(f"{where}: film {fid} Sound button: paused/muted = {stt}")
                    note = pg.evaluate(f"(f => f && f.innerText)(document.getElementById('{fid}').closest('figure').querySelector('figcaption'))")
                    if not note or "Every figure is sample data." not in note:
                        fails.append(f"{where}: film {fid} has no 'Every figure is sample data.' note under it")
            pg.close()
    # sitemap: every URL answers 200 here and its page names itself as canonical
    try:
        sm = fetch(BASE + "/sitemap.xml")[1]
        locs = re.findall(r"<loc>(.*?)</loc>", sm)
        want = {SITE + "/"} | {SITE + p["path"] for p in CFG["pages"]}
        fails += [f"sitemap.xml: missing {u}" for u in sorted(want - set(locs))]
        for loc in locs:
            st, h = fetch(BASE + loc.replace(SITE, ""))
            c = re.search(r'<link rel="canonical" href="(.*?)"', h)
            if not c or c.group(1) != loc:
                fails.append(f"sitemap.xml: {loc} canonical is {c and c.group(1)!r}")
    except Exception as e:
        fails.append(f"sitemap.xml: {e}")
    # /about/ is a 301 to /how-lumic-works/ (the Worker does it; python's http.server cannot, so only off localhost)
    if local:
        print("note: /about/ 301 not tested on a local server (the Worker serves it); run qa.py against the preview")
    else:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        op = urllib.request.build_opener(NoRedirect)
        for path in ("/about/", "/about"):
            try:
                r = op.open(urllib.request.Request(BASE + path, headers={"User-Agent": UA}), timeout=20)
                code, loc = r.status, r.headers.get("Location")
            except urllib.error.HTTPError as e:
                code, loc = e.code, e.headers.get("Location")
            if code != 301 or not (loc or "").endswith("/how-lumic-works/"):
                fails.append(f"{path}: {code} -> {loc} (want 301 -> /how-lumic-works/)")
    return fails


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
                # One exception (Christian 2026-10-11): list items inside the single [data-systems-list] element may
                # be product names from PRODUCTS, and nothing else. The rest of that element (label, note) and the
                # rest of the page get the full banned list plus the product-name check.
                text, items, other, n_sys = pg.evaluate("""(() => {
                    // open every <details> for the check (closed ones hide their cards from innerText), then restore
                    const closed = [...document.querySelectorAll('details:not([open])')];
                    closed.forEach(d => { d.open = true; });
                    const els = [...document.querySelectorAll('[data-systems-list]')];
                    const lis = els.flatMap(e => [...e.querySelectorAll('li')]);
                    const items = lis.map(li => li.innerText.trim());
                    const hide = (xs, on) => xs.forEach(x => { if (on) { x.dataset.qaKeep = x.style.display; x.style.display = 'none'; }
                                                               else { x.style.display = x.dataset.qaKeep; delete x.dataset.qaKeep; } });
                    hide(lis, true);
                    const other = els.map(e => e.innerText).join('\\n');
                    hide(lis, false);
                    hide(els, true);
                    const rest = document.body.innerText;
                    hide(els, false);
                    closed.forEach(d => { d.open = false; });
                    return [rest, items, other, els.length];
                })()""")
                if n_sys > 1:
                    fails.append(f"{n_sys} [data-systems-list] elements (the product-name exception is for one section only)")
                fails += [f"systems list item not on the allowlist: {x!r}" for x in items if x not in LIST_ITEMS]
                for x in OUTSIDE_OK:
                    text = text.replace(x, " ")
                for where, t in (("on page", text), ("in the systems list label/note", other)):
                    for pat in BANNED:
                        for m in re.finditer(pat, t, re.I):
                            fails.append(f"banned term {where}: {m.group(0)!r}")
                    for pat in PRODUCT_PATTERNS:
                        for m in re.finditer(pat, t):
                            fails.append(f"product name {where} (allowed only in the systems list): {m.group(0)!r}")
                # client and employer names are caught inside the list items too (the systems exception is for products only)
                for pat in BANNED:
                    if re.search(pat, "Sage QuickBooks FileMaker", re.I):
                        continue
                    for m in re.finditer(pat, "\n".join(items), re.I):
                        fails.append(f"banned term in the systems list: {m.group(0)!r}")
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
        fails += check_pages(b)
        b.close()
    print("\n".join(fails) if fails else f"QA ok: {BASE} at {WIDTHS}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
