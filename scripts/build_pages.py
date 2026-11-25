"""Build the inner pages of get-lumic.com from scripts/pages.json and src/pages/.

For each page in pages.json: stamps the shared head (title, meta, canonical, Open Graph, JSON-LD), header, breadcrumb,
contact block and footer around src/pages/<id>.html and writes public/<path>/index.html. Extra JSON-LD nodes for a
page come from src/pages/<id>.jsonld (a JSON list; the string "@AREA" becomes the area served). A page's own questions
come from its pages.json "faq" list: {{page_faq}} shows them and the same list writes the page's FAQPage.

Also, in place:
- public/index.html: the header, footer, FAQ (list and FAQPage JSON-LD), the pricing section and the four steps between their markers.
- Every "<n> live dashboards" (home, the pages, llms.txt): the count from scripts/dashboard_count.py, as a word. The rest of the home
  page stays hand-edited.
- public/sitemap.xml: home, every page, privacy; lastmod is each source file's last commit date (today if uncommitted).
- src/worker.js: the list of paths that have a markdown copy (between the md-pages markers).

Run it after any change to a page, the nav, the footer or the FAQ, then build_markdown.py:

    py -3.11 scripts/build_pages.py && py -3.11 scripts/build_markdown.py
"""
import datetime, html, io, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB, SRC = ROOT / "public", ROOT / "src" / "pages"
SITE = "https://get-lumic.com"
CFG = json.loads(io.open(ROOT / "scripts" / "pages.json", encoding="utf-8").read())
import sys; sys.path.insert(0, str(ROOT / "scripts"))
import dashboard_count  # the live dashboard count, counted from the code (scripts/dashboard_count.py)
_DASH = re.compile(r"\b(" + "|".join(sorted(dashboard_count.NUMBER_WORDS, key=len, reverse=True)) + r")( live dashboards)\b", re.I)


def dashboards(text):
    """Every "<number word> live dashboards" gets the counted number, keeping the capital letter of the sentence."""
    return _DASH.sub(lambda m: (dashboard_count.WORD.capitalize() if m.group(1)[0].isupper() else dashboard_count.WORD) + m.group(2), text)
CAL = "https://cal.com/lumic/20-minute-call"
# Google Fonts: loaded without blocking render (a preload that turns into the stylesheet once it arrives; noscript fallback).
FONTS = "https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@1&display=swap"
FONTS_LINKS = (f'<link rel="preload" as="style" href="{FONTS}" onload="this.onload=null;this.rel=\'stylesheet\'">\n'
               f'<noscript><link rel="stylesheet" href="{FONTS}"></noscript>')

CK = ('<span class="ck" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" '
      'stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 8.5l3 3 6-7"/></svg></span>')
AR = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
      'stroke-linejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')
ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')
BOOK = f'<a class="btn btn-p" href="{CAL}" target="_blank" rel="noopener">Book a call\n          {ARROW}</a>'
# Pricing (Christian 2026-10-12, via the Phase 5 brief): the lines are approved word for word; do not reword them.
BOOK_PRICING = f'<a class="btn btn-p" href="{CAL}" target="_blank" rel="noopener">Book a call to talk real pricing\n          {ARROW}</a>'
PRICE_ONSITE = "On-site work $1,500/day, credited toward phase one."
PRICE_AGENTS = "Managed AI from $250 to $5,000 a month, depending on scope."  # Christian 2026-11-25: one range, floor $250
PRICE_BUILD = ("Monthly pricing covers running and supporting your agents. The build is a separate, one-time cost, "
               "scoped after the free consultation.")
PRICE_FINAL = "Final pricing depends on your workflow and systems. These figures are starting points, not quotes."
# The short pricing block on home and the Services hub (the same card and ledger as the offers above it); links /pricing/.
PRICING_BLOCK = f"""<article class="keep rv" id="pricing">
      <div>
        <span class="tag">Pricing</span>
        <h3>Free consultation.</h3>
        <p>{PRICE_ONSITE}</p>
        <p>{PRICE_AGENTS}</p>
        <p>{PRICE_BUILD}</p>
        <p>{PRICE_FINAL}</p>
        <div class="cta">
          {BOOK_PRICING}
          <a class="btn btn-g" href="/pricing/">See pricing {ARROW}</a>
        </div>
      </div>
      <ul class="ledger" aria-label="Pricing at a glance">
        <li class="hd"><span>At a glance</span></li>
        <li><span>Consultation</span><span class="st">Free</span></li>
        <li><span>On-site work</span><span class="st">$1,500/day</span></li>
        <li><span>The build</span><span class="st">One-time, scoped</span></li>
        <li><span>Running and support</span><span class="st">Monthly</span></li>
      </ul>
    </article>"""
# The four steps (revamp 2026-11-24): the same wording on home (between its steps markers) and /how-lumic-works/
# ({{four_steps}}). Each step links its own page and carries its approved pricing line word for word. Reuses .steps
# (.s4: four columns on wide screens).
_STEP_LINK = 'style="margin-top:14px"'
FOUR_STEPS = f"""<ol class="steps s4 rv">
      <li class="track" aria-hidden="true"><i></i></li>
      <li class="step"><span class="n" aria-hidden="true">01</span><h3>Free consultation.</h3><p>A 20&#8209;minute call. You walk the team through the work your people do by hand.</p><a class="founder-link" {_STEP_LINK} href="{CAL}" target="_blank" rel="noopener">Book a call →</a></li>
      <li class="step"><span class="n" aria-hidden="true">02</span><h3>On-site day and written proposal.</h3><p>lumic&rsquo;s FDEs work beside your team where the work happens, map where AI fits, and write a proposal: what to build, the timeline, and the cost.</p><p style="margin-top:10px"><strong>{PRICE_ONSITE}</strong></p><a class="founder-link" {_STEP_LINK} href="/ai-consulting/">AI consulting →</a></li>
      <li class="step"><span class="n" aria-hidden="true">03</span><h3>Build.</h3><p>The team builds the agents, automations and dashboards inside your systems and sets up the approval step. Your team tests them on real work before they go live.</p><p style="margin-top:10px"><strong>Scoped after the on-site day.</strong> {PRICE_BUILD} {PRICE_FINAL}</p><a class="founder-link" {_STEP_LINK} href="/ai-implementation/">AI implementation →</a></li>
      <li class="step"><span class="n" aria-hidden="true">04</span><h3>Managed AI.</h3><p>lumic watches it, tests it every month, fixes what breaks, and upgrades it as AI improves. A person on your team approves what matters.</p><p style="margin-top:10px"><strong>{PRICE_AGENTS}</strong></p><a class="founder-link" {_STEP_LINK} href="/managed-ai/">Managed AI →</a></li>
    </ol>"""
# The pricing block as its own section (home, and the service / industry / system pages before the checklist).
PRICING_SECTION = f"""<!-- ============ PRICING ============ -->
<section id="plans" aria-label="Pricing">
  <div class="wrap">
    <div class="thread" aria-hidden="true"><i></i></div>
    {PRICING_BLOCK}
  </div>
</section>"""


def checklist(path):
    """The free-checklist form section (the same markup on home, the industry pages and month-end close)."""
    return f"""<!-- ============ CHECKLIST ============ -->
<section id="checklist" aria-labelledby="checklist-h">
  <div class="wrap">
    <div class="runs rv" data-checklist>
      <p class="runs-l">Free checklist</p>
      <h2 id="checklist-h">Month-End Red Flags Service Firms Usually Miss</h2>
      <p class="lead">Ten month-end mistakes in AP, billing, payroll and the close, on one page. Enter an email and the checklist downloads right away.</p>
      <form class="ck-form cta" method="post" action="/api/checklist" novalidate style="margin-top:20px;flex-wrap:wrap">
        <input type="hidden" name="page" value="{path}">
        <input type="email" name="email" required autocomplete="email" inputmode="email" aria-label="Email address" placeholder="you@company.com" style="font:inherit;font-size:16px;padding:12px 16px;border:1px solid rgba(14,21,37,.16);border-radius:999px;min-width:0;flex:1 1 240px;max-width:360px;background:#fff;color:inherit">
        <input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0">
        <button class="btn btn-p" type="submit">Get the checklist</button>
      </form>
      <p class="pfilms-note" data-ck-msg role="status" aria-live="polite">One email field. No spam, no trackers.</p>
    </div>
  </div>
</section>"""


BRAND = 'lum<span class="idot">&#305;<span class="idot-dot"></span></span>c'
SND = ('<button class="snd" type="button" aria-label="Sound" aria-pressed="false" title="Turn sound on"><svg class="off" viewBox="0 0 24 24" '
       'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5L6.5 9H3.5v6h3l4.5 4z"/>'
       '<path d="M16 9.5l5 5M21 9.5l-5 5"/></svg><svg class="on" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
       'stroke-linejoin="round" aria-hidden="true"><path d="M11 5L6.5 9H3.5v6h3l4.5 4z"/><path d="M15.5 9a4 4 0 0 1 0 6M18.5 6.5a7.5 7.5 0 0 1 0 11"/></svg></button>')
PLAY = ('<span class="fp-pp" aria-hidden="true"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/>'
        '</svg></span>')
# The overview film from the home page (#demo), reused (same files), with its sample-data note under the player. Its
# poster and its two sources (with their ?v= content versions) are read from the home page's player, which
# scripts/publish_keynote.py keeps current, so a new film render reaches the inner pages on the next build.
def overview_media():
    h = io.open(PUB / "index.html", encoding="utf-8").read()
    m = re.search(r'<div class="fp" id="overview-film"[^>]*>\s*<video [^>]*?data-poster="([^"]+)"[^>]*>\s*'
                  r'<source src="([^"]+)" type="video/webm"><source src="([^"]+)" type="video/mp4">', h)
    assert m, "index.html: the overview player (#overview-film) not found"
    return m.groups()


OV_POSTER, OV_WEBM, OV_MP4 = overview_media()
OVERVIEW_ALT = ("The lumic overview: AI reads a vendor bill, matches it to its purchase orders and flags a price difference for approval. "
                "It drafts a purchase order, sends a statement, and answers a question with a drafted follow-up. Then live sales, cash and margin, "
                "all from one set of data.")
FILM_OVERVIEW = f"""<figure class="hero-fig">
        <div class="orbit" aria-hidden="true">
          <svg viewBox="0 0 400 400" fill="none">
            <g class="ring r1"><circle cx="200" cy="200" r="150" stroke="rgba(94,92,230,.22)" stroke-width=".8"/><circle cx="350" cy="200" r="2.6" fill="#7a78f0"/></g>
            <g class="ring r2"><circle cx="200" cy="200" r="104" stroke="rgba(94,92,230,.2)" stroke-width=".8" stroke-dasharray="1 4"/><circle cx="200" cy="96" r="2" fill="#5e5ce6"/></g>
          </svg>
          <span class="orb"></span>
        </div>
      <div class="fp" id="overview-film" data-voice="overview">
        <video muted playsinline preload="none" poster="{OV_POSTER}" aria-label="{OVERVIEW_ALT}">
          <source src="{OV_WEBM}" type="video/webm"><source src="{OV_MP4}" type="video/mp4"></video>
        {PLAY}
        {SND}
      </div>
      <figcaption class="fp-cap"><b>See it running.</b> Every figure is sample data. Turn sound on for the narration.</figcaption>
    </figure>"""
AREA = [{"@type": "City", "name": "St. Louis, Missouri"}] + [
    {"@type": "AdministrativeArea", "name": n} for n in (
        "St. Louis County, Missouri", "St. Charles County, Missouri", "Jefferson County, Missouri", "Franklin County, Missouri",
        "Madison County, Illinois", "St. Clair County, Illinois")]


def esc(s):
    return html.escape(s, quote=True)


def nav(current, home=False):
    items = []
    for n in CFG["nav"]:
        cls = ' class="nav-opt"' if n.get("opt") else ""
        cur = ' aria-current="page"' if n["href"] == current else ""
        items.append(f'        <li{cls}><a href="{n["href"]}"{cur}>{esc(n["label"])}</a></li>')
    return (f'<header class="nav">\n  <div class="wrap nav-in">\n'
            f'    <a class="brand" href="{"#top" if home else "/"}" aria-label="lumic home">{BRAND}</a>\n'
            f'    <nav aria-label="Primary">\n      <ul>\n' + "\n".join(items) + '\n      </ul>\n    </nav>\n'
            f'    <a class="btn btn-p" href="{CAL}" target="_blank" rel="noopener">Book a call {ARROW}</a>\n  </div>\n</header>')


def footer(home=False):
    items = []
    for n in CFG["footer"]:
        ext = ' target="_blank" rel="noopener"' if n["href"].startswith("http") else ""
        items.append(f'          <li><a href="{n["href"]}"{ext}>{esc(n["label"])}</a></li>')
    return (f'<footer>\n  <div class="wrap">\n    <div class="f-top">\n      <div>\n'
            f'        <a class="brand" href="{"#top" if home else "/"}" aria-label="lumic home">{BRAND}</a>\n'
            f'        <p>AI, deployed into your business and kept working.</p>\n      </div>\n'
            f'      <nav aria-label="Footer">\n        <ul class="f-links">\n' + "\n".join(items) + '\n        </ul>\n      </nav>\n    </div>\n'
            f'    <p class="f-bot">© 2026 lumic · Founded May 2026 · <a href="/st-louis/">Serving Greater St. Louis, Missouri and Illinois</a> · <a href="/privacy/">Privacy</a></p>\n'
            f'  </div>\n</footer>')


# The home page's contact block; on inner pages the side heading reads "How to start".
CONTACT = f"""<!-- ============ CONTACT ============ -->
<section class="contact" id="contact" aria-labelledby="contact-h" style="padding-top:clamp(40px,5vw,64px);padding-bottom:clamp(56px,6vw,88px)">
  <div class="wrap">
    <div class="thread d3" aria-hidden="true" style="top:calc(-1 * clamp(40px,5vw,64px) + 8px);height:calc(2 * clamp(40px,5vw,64px) - 16px)"><i></i></div>
    <div class="cc rv">
      <div class="cc-l">
        <h2 id="contact-h">Based in St.&nbsp;Louis. Start with a <em class="s">conversation.</em></h2>
        <div class="cc-act">
          <a class="btn btn-p" href="{CAL}" target="_blank" rel="noopener">Book a call {ARROW}</a>
          <span class="or">or write to lumic</span>
          <a class="ce-mail" href="mailto:hello@get-lumic.com?subject=lumic%20intro%20call">hello@get-lumic.com {ARROW}</a>
        </div>
      </div>
      <div class="cc-r">
        <div class="who">
          <div class="faces"><img src="/img/founders/christian.jpg" alt="Christian Gonzenbach" width="56" height="56" loading="lazy" decoding="async"><img src="/img/founders/josh.jpg" alt="Joshua Wittenauer" width="56" height="56" loading="lazy" decoding="async"></div>
          <p>Every engagement is led by <b>a senior FDE</b>, on site.</p>
        </div>
        <div>
          <div class="kicker">How to start</div>
          <ol class="nx">
            <li><span class="n">1</span><div><b>A 20&#8209;minute call.</b><span>You walk the team through the work your people do by hand.</span></div></li>
            <li><span class="n">2</span><div><b>A written proposal.</b><span>What lumic would build, the timeline, and the cost.</span></div></li>
            <li><span class="n">3</span><div><b>An on-site visit.</b><span>lumic&rsquo;s FDEs meet your team where the work happens and confirm the plan. They come on site across Greater St.&nbsp;Louis and travel for the right fit.</span></div></li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</section>"""


def faq_items(items, indent="            "):
    out = []
    for f in items:
        a = f.get("html") or esc(f["a"])
        out.append(f'{indent}<li>{CK}<div><h3>{esc(f["q"])}</h3><p>{a}</p></div></li>')
    return "\n".join(out)


def faq_ld(items, at):
    return {"@type": "FAQPage", "@id": at, "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in items]}


def trail(p):
    """The levels between Home and the page: optional "ancestors" (a list, from the top level down), then the optional "parent"."""
    return list(p.get("ancestors", [])) + ([p["parent"]] if p.get("parent") else [])


def crumbs(p):
    # middle levels, e.g. "parent": {"label": "Services", "href": "/services/"}; "ancestors" adds levels above the parent
    mid = "".join(f'<li><a href="{x["href"]}">{esc(x["label"])}</a></li>' for x in trail(p))
    return (f'<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>{mid}'
            f'<li aria-current="page">{esc(p["crumb"])}</li></ol></nav>')


def page_ld(p):
    url = SITE + p["path"]
    graph = [
        {"@type": p["type"], "@id": url + "#webpage", "url": url, "name": p["title"], "description": p["description"],
         "inLanguage": "en", "about": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"},
         "breadcrumb": {"@id": url + "#breadcrumb"}},
        {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(
                [("Home", SITE + "/")] + [(x["label"], SITE + x["href"]) for x in trail(p)]
                + [(p["crumb"], url)])]},
    ]
    extra = SRC / f'{p["id"]}.jsonld'
    if extra.exists():
        graph += json.loads(io.open(extra, encoding="utf-8").read())
    if p["id"] == "faq":
        graph.append(faq_ld(CFG["faq"], url + "#faq"))
    if p.get("faq"):  # a page's own questions (pages.json "faq"), shown by {{page_faq}} and marked up from the same list
        graph.append(faq_ld(p["faq"], url + "#faq"))
    if p["id"] == "portfolio":  # one Service per card, read from the cards themselves (no Review or rating markup)
        src = io.open(SRC / "portfolio.html", encoding="utf-8").read()
        cards = re.findall(r'<article class="pf"[^>]*>.*?<h3>(.*?)</h3>\s*<p>(.*?)</p>', src, re.S)
        plain = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
        graph[0]["mainEntity"] = {"@id": url + "#items"}
        graph.append({"@type": "ItemList", "@id": url + "#items", "numberOfItems": len(cards), "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {"@type": "Service", "name": plain(n), "description": plain(d),
                                                             "provider": {"@id": SITE + "/#org"}}}
            for i, (n, d) in enumerate(cards)]})

    def fill(x):
        if x == "@AREA":
            return AREA
        if isinstance(x, dict):
            return {k: fill(v) for k, v in x.items()}
        if isinstance(x, list):
            return [fill(v) for v in x]
        return x
    return {"@context": "https://schema.org", "@graph": fill(graph)}


def films_list():
    """The tool films list from the home page (between its films markers), reused as is."""
    h = io.open(PUB / "index.html", encoding="utf-8").read()
    m = re.search(r"<!-- films:start.*?-->\n(.*?)\n\s*<!-- films:end -->", h, re.S)
    return m.group(1) if m else ""


def build_page(p):
    url = SITE + p["path"]
    body = io.open(SRC / f'{p["id"]}.html', encoding="utf-8").read().rstrip()
    for k, v in {"{{crumbs}}": crumbs(p), "{{ck}}": CK, "{{lck}}": CK, "{{ar}}": AR, "{{book}}": BOOK,
                 "{{book_pricing}}": BOOK_PRICING, "{{pricing_block}}": PRICING_BLOCK, "{{pricing_section}}": PRICING_SECTION, "{{checklist}}": checklist(p["path"]), "{{price_onsite}}": PRICE_ONSITE,
                 "{{price_build}}": PRICE_BUILD, "{{price_agents}}": PRICE_AGENTS, "{{four_steps}}": FOUR_STEPS, "{{price_final}}": PRICE_FINAL, "{{arrow}}": ARROW,
                 "{{film_overview}}": FILM_OVERVIEW, "{{films_list}}": films_list(), "{{faq_items}}": faq_items(CFG["faq"], "        "),
                 "{{page_faq}}": faq_items(p.get("faq", []), "        ")}.items():
        body = body.replace(k, v)
    assert "{{" not in body, f'{p["id"]}: unfilled token {re.search(r"{{.*?}}", body).group(0)}'
    body = dashboards(body)
    t, d = esc(p["title"]), esc(p["description"])
    ld = json.dumps(page_ld(p), ensure_ascii=False, separators=(",", ":"))
    doc = f"""<!DOCTYPE html>
<!-- get-lumic.com: written by scripts/build_pages.py from src/pages/{p["id"]}.html and scripts/pages.json. Edit those, not this file. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="alternate" type="text/markdown" href="{p["path"]}index.md" title="{esc(p["crumb"])}, as markdown">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#ffffff">

<meta property="og:type" content="website">
<meta property="og:site_name" content="lumic">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{SITE}/og-image.png">
<script type="application/ld+json">{ld}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{FONTS_LINKS}
<link rel="stylesheet" href="/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

{nav(p["path"])}

<main id="main">
{body}

{CONTACT}
</main>

{footer()}

<script src="/site.js"></script>
</body>
</html>
"""
    out = PUB / p["path"].strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="\n").write(doc)
    return out


def stamp(text, name, new, comment=("<!-- ", " -->")):
    a, b = f"{comment[0]}{name}:start{comment[1]}", f"{comment[0]}{name}:end{comment[1]}"
    pat = re.compile(re.escape(a) + r".*?" + re.escape(b), re.S)
    assert len(pat.findall(text)) == 1, f"marker {name} not found exactly once"
    return pat.sub(lambda m: f"{a}\n{new}\n{b}", text)


def build_home():
    f = PUB / "index.html"
    h = io.open(f, encoding="utf-8").read()
    h = stamp(h, "nav", nav("/", home=True))
    h = stamp(h, "footer", footer(home=True))
    home_faq = [x for x in CFG["faq"] if x.get("home")]
    h = stamp(h, "faq", faq_items(home_faq))
    h = stamp(h, "pricing", PRICING_SECTION)
    h = stamp(h, "steps", "    " + FOUR_STEPS)
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', h, re.S)
    ld = json.loads(m.group(2))
    ld["@graph"] = [faq_ld(home_faq, SITE + "/#faq") if g.get("@type") == "FAQPage" else g for g in ld["@graph"]]
    h = h[:m.start(2)] + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + h[m.end(2):]
    h = dashboards(h)
    io.open(f, "w", encoding="utf-8", newline="\n").write(h)
    llms = PUB / "llms.txt"
    text = dashboards(io.open(llms, encoding="utf-8").read())  # read it before the write opens (and empties) the file
    io.open(llms, "w", encoding="utf-8", newline="\n").write(text)


def lastmod(*files):
    dates = []
    for f in files:
        rel = str(Path(f).relative_to(ROOT)).replace("\\", "/")
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", rel], capture_output=True, text=True).stdout.strip()
        d = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%cs", "--", rel], capture_output=True, text=True).stdout.strip()
        dates.append(datetime.date.today().isoformat() if dirty or not d else d)
    return max(dates)


def build_sitemap():
    urls = [("/", lastmod(PUB / "index.html"))]
    urls += [(p["path"], lastmod(SRC / f'{p["id"]}.html', ROOT / "scripts" / "pages.json")) for p in CFG["pages"]]
    urls += [("/privacy/", lastmod(PUB / "privacy" / "index.html"))]
    body = "".join(f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{d}</lastmod>\n  </url>\n" for u, d in urls)
    io.open(PUB / "sitemap.xml", "w", encoding="utf-8", newline="\n").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n')


def build_worker():
    f = ROOT / "src" / "worker.js"
    w = io.open(f, encoding="utf-8").read()
    paths = ["/"] + [p["path"] for p in CFG["pages"]]
    w = stamp(w, "md-pages", "const MD_PAGES = new Set(" + json.dumps(paths) + ");", ("// ", ""))
    io.open(f, "w", encoding="utf-8", newline="\n").write(w)


def main():
    for p in CFG["pages"]:
        print("wrote", build_page(p).relative_to(ROOT))
    build_home()
    build_sitemap()
    build_worker()
    print("home nav/footer/faq, sitemap.xml, worker md-pages stamped")


if __name__ == "__main__":
    main()
