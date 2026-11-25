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
one <h1>, canonical and og:url match, a BreadcrumbList. The AP hours-saved calculator: its example figures, a dash
(never NaN) on bad input, the disclaimer word for word. On every page (home included): JSON-LD parses, no we/our/us,
no size-reveal or gap phrases; on inner pages also no banned term and no product name at all (visible text, title,
meta and JSON-LD). /st-louis/ carries no street address. The sitemap lists every page and each answers 200 with a
matching canonical. Home: the revamp title, H1, tagline in the footer and the schema slogan, the nav labels, and the
four offer steps with their links. Off localhost: every src/worker.js REDIRECTS path (/about/ and /about -> /how-lumic-works/ among them) answers 301 to its page. Home's FAQPage covers exactly
the questions it shows.

Phase 5: the approved pricing lines appear word for word on /pricing/, home and /services/ with the "Book a call to talk
real pricing" button; each page with an "h1" in pages.json shows it; a page's FAQPage covers exactly the questions it
shows; /guardrails/ adds no new security claim; no JSON-LD carries a fixed price (minPrice only); the four new pages sit
in the footer and /st-louis/ links both of its children; /privacy/ is third person and names what the checklist stores.

Usage: python scripts/qa.py [base_url]      default http://localhost:8766  (serve public/, not the repo root)
Needs: playwright (uses the installed Google Chrome). Exit code 1 on any failure.
"""
import json
import re
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
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
            "sage-100": [r"/systems/sage-100/", r"\bSage 100\b"],
            "sage-intacct": [r"/systems/sage-intacct/", r"\bSage Intacct\b"]}  # own URL slug counts; a bare "Sage" still fails
# Pages that carry the general process only (Christian 2026-10-11, 9:33 PM CT): no client proof at all
NO_PROOF_PATHS = ("/systems/", "/industries/", "/services/payroll/", "/services/month-end-close/", "/ai-agent-skills/")  # Track 2: no results or proof numbers
# No proof, figure or client description on a /systems/ page (a product must never be tied to a client or a number)
import dashboard_count  # noqa: E402  (scripts/dashboard_count.py, the counted dashboards)
PROOF = [r"64 of 67", r"six weeks", r"\b13 agent roles\b", rf"\b(?:{'|'.join(dashboard_count.NUMBER_WORDS)}) (?:live )?dashboards", r"specialty manufacturer",
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
               r"\bfounder[- ]led\b", r"\bcoming soon\b", r"\bnext\b",
               # Christian 2026-11-25: show ability, never size (no client counts, no "first" deployments)
               r"\b(?:two|both|second|one|single|first|only) clients?\b", r"\bour first\b", r"\bfirst (?:managed|AP|client)\b",
               r"\bflagship client\b",
               # Round 3 (Christian's no-size rule, 2026-11-25): proof states ability, never age, firsts or counts
               r"\bfirst week\b", r"\bweek one\b", r"\bin its first\b", r"\bfirst (?:client|managed|deployment)s?\b",
               r"\b(?:one|two|three) clients?\b",
               r"\bsince (?:January|February|March|April|May|June|July|August|September|October|November|December|late|early|mid|20\d\d)\b",
               r"\bso far\b", r"(?<!up )\bto date\b", r"\bFounded\b", r"\bfoundingDate\b", r"\ba recent\b"]
HOME_OK = ["What happens next"]  # the home contact block's heading (live copy, unchanged); inner pages say "How to start"
# A service-area business: no street address anywhere on /st-louis/, including the schema
ADDRESS = [r"streetAddress", r"postalCode", r"\b6[23]\d{3}(?:-\d{4})?\b",
           r"\b\d{1,5}\s+(?:[NSEW]\.?\s+)?[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Parkway|Pkwy|Suite|Ste)\b"]
# Phase 5 (2026-10-12). Pricing lines are approved word for word (scripts/build_pages.py PRICE_*); each must appear on these
# paths exactly as written, and the CTA must read as approved and go to the booking page.
CAL = "https://cal.com/lumic/20-minute-call"
PRICING_CTA = "Book a call to talk real pricing"
PRICING_BLOCK_LINES = ["On-site work $1,500/day, credited toward phase one.", "Managed AI from $250 to $5,000 a month, depending on scope.",
                       "Monthly pricing covers running and supporting your agents. The build is a separate, one-time cost, priced in the written proposal.",
                       "Final pricing depends on your workflow and systems. These figures are starting points, not quotes."]
# Audit 2026-11-24 (P2-5): a page that shows the four steps carries their three lines and no separate pricing card
STEP_PRICE_LINES = ["Free consultation.", "On-site work $1,500/day, credited toward phase one.",
                    "Managed AI from $250 to $5,000 a month, depending on scope."]
PRICING_LINES = {"/": STEP_PRICE_LINES, "/services/": PRICING_BLOCK_LINES,
                 "/pricing/": ["Free consultation."] + PRICING_BLOCK_LINES,
                 # revamp 2026-11-24: the four offer steps (home, /how-lumic-works/) and the Managed AI page carry their lines too
                 "/how-lumic-works/": STEP_PRICE_LINES, "/ai-implementation/": STEP_PRICE_LINES, "/st-louis/": STEP_PRICE_LINES,
                 "/managed-ai/": PRICING_BLOCK_LINES[1:]}
# Christian 2026-11-25: one monthly range replaced the two monthly lines; neither old line may come back
OLD_PRICE_LINES = ["Managed agents from $1,000/month", "Full build-and-run from $2,500"]
# pages that carry the full pricing block (CTA + a link to /pricing/); the others only show their lines
PRICING_BLOCK_PATHS = ("/services/", "/pricing/", "/managed-ai/")
# the build is priced in the written proposal (Christian 2026-11-24); the old scoping sentence may not come back
OLD_PRICE_LINES_BUILD = ["scoped after the free consultation", "Scoped after the on-site day"]
# /guardrails/ collects only practices the site already states: no new security or control claims
GUARDRAILS_NEW_CLAIMS = [r"\bSOC ?2\b", r"encrypt", r"certif", r"\bISO\b", r"HIPAA", r"\bGDPR\b", r"penetration",
                         r"zero[- ]trust", r"compliant"]
# Revamp 2026-11-24 (CEO brief): home title, H1 (with its kicker), the brand tagline under it, the nav, the four offer steps
HOME_TITLE = "lumic | Custom AI implementation, St. Louis FDEs"
HOME_H1 = "Custom AI, built into your business and kept working."  # audit P2-2: the kicker moved out of the h1 into the eyebrow
TAGLINE = "AI, deployed into your business and kept working."
NAV_LABELS = ["Services", "Managed AI", "How lumic works", "Pricing", "St. Louis"]
STEP_LINKS = [CAL, "/ai-consulting/", "/ai-implementation/", "/managed-ai/"]
# A schema price is a starting price only (minPrice or "starting" wording); never a fixed "price" field
FIXED_PRICE_KEYS = ("price",)
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
    if "foundingDate" in html:
        fails.append(f"{where}: JSON-LD carries foundingDate (no-size rule)")
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


def ld_items(x):
    """Every (key, value) pair in a JSON-LD tree."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield k, v
            yield from ld_items(v)
    elif isinstance(x, list):
        for v in x:
            yield from ld_items(v)


def norm(s):
    return re.sub(r"[ \t]+", " ", (s or "").replace(" ", " ").replace("‑", "-")).strip()


def check_phase5(b):
    """Pricing copy word for word with its CTA, each page's H1, FAQPage = the questions shown, guardrails claim nothing new,
    no fixed schema price, the new pages in the footer and linked both ways with /st-louis/, privacy in third person."""
    fails = []
    pg = b.new_page(viewport={"width": 1440, "height": 900})

    def load(path):
        pg.goto(BASE + path, wait_until="load")
        return norm(pg.evaluate(OPEN_DETAILS_TEXT)), fetch(BASE + path)[1]

    for path, lines in PRICING_LINES.items():
        text, _ = load(path)
        fails += [f"{path}: pricing line missing or reworded: {l!r}" for l in lines if l not in text]
        fails += [f"{path}: retired pricing line {l!r}" for l in OLD_PRICE_LINES + OLD_PRICE_LINES_BUILD if l in text]
        if path not in PRICING_BLOCK_PATHS:
            continue
        ctas = pg.evaluate(f"[...document.querySelectorAll('a')].filter(a => a.textContent.trim() === {json.dumps(PRICING_CTA)}).map(a => a.href)")
        if not ctas:
            fails.append(f"{path}: no {PRICING_CTA!r} button")
        fails += [f"{path}: {PRICING_CTA!r} goes to {h}, want {CAL}" for h in ctas if h != CAL]
        if path != "/pricing/" and not pg.evaluate("!!document.querySelector('#pricing a[href=\"/pricing/\"]')"):
            fails.append(f"{path}: the pricing block does not link /pricing/")
    seen_ld = []
    for p in CFG["pages"]:
        if not (p.get("h1") or p.get("faq") or p["id"] in ("faq", "guardrails", "st-louis")):
            continue
        text, html = load(p["path"])
        if p.get("h1"):
            h1 = norm(pg.evaluate("document.querySelector('h1').textContent"))
            if h1 != p["h1"]:
                fails.append(f"{p['path']}: H1 {h1!r}, want {p['h1']!r}")
        faqld = [q["name"] for blk in ld_blocks(html) if isinstance(blk, dict) for g in blk.get("@graph", []) if g.get("@type") == "FAQPage"
                 for q in g["mainEntity"]]
        shown = [norm(x) for x in pg.evaluate("[...document.querySelectorAll('#faq .wl h3')].map(h => h.textContent)")]
        if (p.get("faq") or p["id"] == "faq") and (not faqld or faqld != shown):
            fails.append(f"{p['path']}: FAQPage JSON-LD {faqld} does not match the questions shown {shown}")
        if p["id"] == "guardrails":
            lds = "\n".join(s for blk in ld_blocks(html) if not isinstance(blk, str) for s in ld_strings(blk))
            for pat in GUARDRAILS_NEW_CLAIMS:
                for m in re.finditer(pat, text + "\n" + lds + "\n" + meta_text(html), re.I):
                    fails.append(f"/guardrails/: {m.group(0)!r} is not a practice the site already states")
        if p["id"] == "st-louis":
            for href in ("/st-louis/ai-consulting/", "/forward-deployed-engineers/"):
                if f'href="{href}"' not in html:
                    fails.append(f"/st-louis/: no link to {href}")
        if p["id"] == "st-louis-ai-consulting":
            for href in ["/st-louis/", "/how-lumic-works/", "/guardrails/", "/pricing/"] + [
                    x["path"] for x in CFG["pages"] if x.get("parent", {}).get("href") == "/services/"]:
                if f'href="{href}"' not in html:
                    fails.append(f"{p['path']}: no link to {href}")
    # no fixed price anywhere in the schema (home, every page, schema.jsonld): starting prices use minPrice
    for path in ["/"] + [p["path"] for p in CFG["pages"]]:
        html = fetch(BASE + path)[1]
        seen_ld += [(path, blk) for blk in ld_blocks(html) if isinstance(blk, dict)]
    try:
        seen_ld.append(("/schema.jsonld", json.loads(fetch(BASE + "/schema.jsonld")[1])))
    except Exception as e:
        fails.append(f"/schema.jsonld: {e}")
    for path, blk in seen_ld:
        fails += [f"{path}: JSON-LD has a fixed {k!r} {v!r} (use minPrice, a starting price)" for k, v in ld_items(blk) if k in FIXED_PRICE_KEYS]
    # the new pages are in the footer of every page (home checked here; inner pages share the same footer)
    home = fetch(BASE + "/")[1]
    foot = re.search(r"<footer>.*?</footer>", home, re.S)
    for href in ("/st-louis/ai-consulting/", "/forward-deployed-engineers/", "/guardrails/", "/pricing/",
                 "/ai-implementation/", "/managed-ai/", "/ai-consulting/", "/st-louis/metro-east/"):
        if not foot or f'href="{href}"' not in foot.group(0):
            fails.append(f"footer: no link to {href}")
    # /privacy/ (hand-written, outside pages.json): third person, and it names what the checklist form stores. It is exempt
    # from the product-name rule on purpose: a privacy page must name its processors accurately (e.g. Microsoft 365).
    text, html = load("/privacy/")
    for m in re.finditer(WE, text, re.I):
        fails.append(f"/privacy/: first-person word {m.group(0)!r}")
    for x in ("checklist form", "email address", "the page it was submitted from", "browser type"):
        if x not in text:
            fails.append(f"/privacy/: does not say the checklist form stores {x!r}")
    pg.close()
    return fails


# /resources/ap-hours-saved-calculator/ (2026-11-25): the browser calculator. The example numbers give the figures below, bad
# input shows a dash (never NaN), the disclaimer and the comparison label are word for word, and no lumic-result wording.
CALC_PATH = "/resources/ap-hours-saved-calculator/"
CALC_DEFAULTS = {"hours": "36.7", "hoursy": "440.0", "month": "$1,650", "year": "$19,800", "bill": "$8.25"}
CALC_LINES = ["These figures come only from the numbers entered. They are not a lumic result, a quote or a promise.",
              "Difference, from the numbers entered above.", "Example. Edit to match the work.",
              "Hours per month = (B × M + B × E × X) ÷ 60"]
CALC_BANNED = [r"hours lumic saves", r"lumic saves", r"you(?:'|’)ll save", r"industry average", r"on average"]


def check_calculator(b):
    fails = []
    if not any(p["path"] == CALC_PATH for p in CFG["pages"]):
        return [f"{CALC_PATH}: not in pages.json"]
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(BASE + CALC_PATH, wait_until="domcontentloaded")
    text = norm(pg.evaluate(OPEN_DETAILS_TEXT))
    fails += [f"{CALC_PATH}: missing {l!r}" for l in CALC_LINES if norm(l) not in text]
    for pat in CALC_BANNED:
        fails += [f"{CALC_PATH}: wording {m.group(0)!r}" for m in re.finditer(pat, text, re.I)]
    got = pg.evaluate("Object.fromEntries([...document.querySelectorAll('[data-o]')].map(e => [e.dataset.o, e.textContent.trim()]))")
    fails += [f"{CALC_PATH}: default {k} = {got.get(k)!r}, want {v!r}" for k, v in CALC_DEFAULTS.items() if got.get(k) != v]
    for bad in ("", "0", "-5", "abc", "1,2,3", "0x10", "1e3", "20%", "12.5"):
        pg.fill("#calc-b", bad)
        o = pg.evaluate("[...document.querySelectorAll('[data-o]')].map(e => e.textContent).join(' | ')")
        if "NaN" in o or "Infinity" in o or pg.text_content('[data-o="hours"]').strip() != "—":
            fails.append(f"{CALC_PATH}: bills {bad!r} shows {o[:120]!r} (want a dash, no NaN)")
    pg.fill("#calc-b", "200")
    pg.evaluate("document.getElementById('compare').open = true")
    for m2, want in (("4", "13.3 fewer hours a month"), ("12", "13.3 more hours a month"), ("8", "No difference in hours a month")):
        pg.fill("#calc-m2", m2)
        got = pg.text_content('[data-o="dhours"]').strip()
        if got != want:
            fails.append(f"{CALC_PATH}: comparison minutes {m2}: difference {got!r}, want {want!r}")
    if pg.evaluate("document.querySelectorAll('[aria-live]').length") != 1 or not pg.evaluate("!!document.querySelector('.sr-only[aria-live=\"polite\"][aria-atomic=\"true\"]')"):
        fails.append(f"{CALC_PATH}: want exactly one aria-live region, the visually hidden summary sentence")
    if pg.evaluate("[...document.querySelectorAll('.calc input')].some(i => !document.querySelector('label[for=\"' + i.id + '\"]') || parseFloat(getComputedStyle(i).fontSize) < 16)"):
        fails.append(f"{CALC_PATH}: an input without a visible label, or under 16px")
    pg.close()
    return fails


def check_pages(b):
    fails = check_phase5(b) + check_calculator(b)
    local = re.match(r"https?://(127\.0\.0\.1|localhost)", BASE) is not None
    # home: JSON-LD parses, voice and size rules, and its FAQPage covers exactly the questions it shows
    st, home = fetch(BASE + "/")
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(BASE + "/", wait_until="load")
    text = pg.evaluate(OPEN_DETAILS_TEXT)
    fails += content_checks("home", text, home, home=True)
    shown = pg.evaluate("[...document.querySelectorAll('#faq .wl h3')].map(h => h.textContent.trim())")
    # revamp 2026-11-24: the home hero, the nav and the four offer steps
    if f"<title>{HOME_TITLE}</title>" not in home:
        fails.append(f"home: title is not {HOME_TITLE!r}")
    h1 = norm(pg.evaluate("document.querySelector('h1').textContent"))
    if h1 != HOME_H1:
        fails.append(f"home: H1 {h1!r}, want {HOME_H1!r}")
    foot = pg.evaluate("document.querySelector('footer').innerText")
    if TAGLINE not in foot:
        fails.append(f"home: the tagline {TAGLINE!r} is not in the footer")
    orgs = [g for blk in ld_blocks(home) if isinstance(blk, dict) for g in blk.get("@graph", []) if g.get("@type") == "Organization"]
    if not orgs or orgs[0].get("slogan") != TAGLINE:
        fails.append("home: Organization slogan is not the tagline")
    if [n["label"] for n in CFG["nav"]] != NAV_LABELS:
        fails.append(f"pages.json nav {[n['label'] for n in CFG['nav']]}, want {NAV_LABELS}")
    navl = pg.evaluate("[...document.querySelectorAll('header.nav nav li a')].map(a => a.textContent.trim())")
    if navl != NAV_LABELS:
        fails.append(f"home nav {navl}, want {NAV_LABELS}")
    steps = pg.evaluate("[...document.querySelectorAll('#services .steps .step')].map(s => [s.querySelector('h3').textContent.trim(), (s.querySelector('a') || {}).getAttribute ? s.querySelector('a').getAttribute('href') : null])")
    if [x[1] for x in steps] != STEP_LINKS:
        fails.append(f"home: four steps {steps}, want links {STEP_LINKS}")
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
                if p["path"].startswith(NO_PROOF_PATHS):
                    body = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
                    for pat in PROOF:
                        for m in re.finditer(pat, ptext + " " + body, re.I):
                            fails.append(f"{where}: proof or client detail {m.group(0)!r} on a general-process page")
                    if re.search(r'href="/portfolio/#', html):
                        fails.append(f"{where}: links to a portfolio card (general-process pages link the portfolio page only)")
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
        print("note: the REDIRECTS 301s are not tested on a local server (the Worker serves it); run qa.py against the preview")
    else:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        op = urllib.request.build_opener(NoRedirect)
        # every entry in src/worker.js REDIRECTS (/about(/) included), with and without the trailing slash
        wjs = (Path(__file__).resolve().parent.parent / "src" / "worker.js").read_text(encoding="utf-8")
        redirects = dict(re.findall(r'"(/[a-z0-9/-]*)": "(/[a-z0-9/-]*/)"', re.search(r"const REDIRECTS = \{(.*?)\};", wjs, re.S).group(1)))
        if redirects.get("/about/") != "/how-lumic-works/" or redirects.get("/about") != "/how-lumic-works/":
            fails.append("src/worker.js: /about(/) no longer redirects to /how-lumic-works/")
        for path, want in sorted(redirects.items()):
            try:
                r = op.open(urllib.request.Request(BASE + path, headers={"User-Agent": UA}), timeout=20)
                code, loc = r.status, r.headers.get("Location")
            except urllib.error.HTTPError as e:
                code, loc = e.code, e.headers.get("Location")
            if code != 301 or not (loc or "").endswith(want):
                fails.append(f"{path}: {code} -> {loc} (want 301 -> {want})")
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
