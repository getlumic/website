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
  The same date is the dateModified of each page's WebPage (and Article) node, and of home's WebPage node.
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
PRICE_BUILD_LINE = "The build is a separate, one-time cost, priced in the written proposal."  # the approved build line on its own
PRICE_BUILD = "Monthly pricing covers running and supporting your agents. " + PRICE_BUILD_LINE  # Christian 2026-11-24: the build is priced in the proposal, after the on-site day
PRICE_FINAL = "Final pricing depends on your workflow and systems. These figures are starting points, not quotes."
# What the monthly fee covers: one list, the same on /managed-ai/ and /pricing/ ({{fee_covers}}), and one sentence for the
# Managed AI price card and llms.txt ({{fee_covers_line}}).
FEE_ROWS = [("Monitoring", "Ongoing", "monitoring"), ("Testing", "Monthly", "monthly tests"), ("Fixes", "Included", "fixes"),
            ("Upgrades as tools improve", "Included", "upgrades as tools improve"),
            ("Releases", "At night", "releases at night"),  # releases ship at night when there is a change (not "nightly")
            ("Support desk", "Included", "the support desk"), ("AI usage for the agreed scope", "Included", "the AI usage the agents need for the agreed scope"), ("A summary of its work", "Monthly", "a monthly summary of its work"),
            ("Human approval", "Built in", "human approval")]
FEE_COVERS_LINE = "Includes " + ", ".join(x[2] for x in FEE_ROWS[:-1]) + " and " + FEE_ROWS[-1][2] + "."
FEE_COVERS_SHORT = "Includes monitoring, monthly tests, fixes and upgrades."  # the /pricing/ card; the ledger below it is hidden on phones, so the sentence must stand alone
FEE_COVERS = ('<ul class="ledger" aria-label="Covered for each managed agent">\n'
              '        <li class="hd"><span>Each managed agent</span><span class="st">Covered</span></li>\n'
              + "\n".join(f'        <li><span>{a}</span><span class="st">{b}</span></li>' for a, b, _ in FEE_ROWS) + "\n      </ul>")
# The short pricing block on home and the Services hub (the same card and ledger as the offers above it); links /pricing/.
PRICING_BLOCK = f"""<article class="keep rv" id="pricing">
      <div>
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
        <li><span>The build</span><span class="st">One-time, in the proposal</span></li>
        <li><span>Running and support</span><span class="st">Monthly</span></li>
      </ul>
    </article>"""
# The four steps (revamp 2026-11-24): the same wording on home (between its steps markers) and /how-lumic-works/
# ({{four_steps}}). Each step links its own page and carries its approved pricing line word for word. Reuses .steps
# (.s4: four columns on wide screens).
_STEP_LINK = 'style="margin-top:14px"'
FOUR_STEPS = f"""<ol class="steps s4 rv">
      <li class="track" aria-hidden="true"><i></i></li>
      <li class="step"><span class="n" aria-hidden="true">01</span><h3>Free consultation.</h3><p>A 20&#8209;minute call.<span class="ph-x"> You walk the team through the work your people do by hand.</span></p><a class="founder-link" {_STEP_LINK} href="{CAL}" target="_blank" rel="noopener">Book a call →</a></li>
      <li class="step"><span class="n" aria-hidden="true">02</span><h3>On-site day and written proposal.</h3><p>lumic&rsquo;s FDEs work beside your team where the work happens and write a proposal.<span class="ph-x"> They map where AI fits; the proposal says what to build, the timeline, and the cost.</span></p><p style="margin-top:10px"><strong>{PRICE_ONSITE}</strong></p><a class="founder-link" {_STEP_LINK} href="/ai-consulting/">AI consulting →</a></li>
      <li class="step"><span class="n" aria-hidden="true">03</span><h3>Build.</h3><p>The team builds the agents, automations and dashboards inside your systems and sets up the approval step.<span class="ph-x"> Your team tests them on real work before they go live. lumic runs the job for you on a dedicated computer, or packages it for the AI assistant your team already uses.</span></p><p style="margin-top:10px"><strong>Priced in the written proposal.</strong></p><a class="founder-link" {_STEP_LINK} href="/ai-implementation/">AI implementation →</a></li>
      <li class="step"><span class="n" aria-hidden="true">04</span><h3>Managed AI.</h3><p>lumic watches it, tests it every month, fixes what breaks, and upgrades it as AI improves. A person on your team approves what matters.</p><p style="margin-top:10px"><strong>{PRICE_AGENTS}</strong></p><a class="founder-link" {_STEP_LINK} href="/managed-ai/">Managed AI →</a></li>
    </ol>"""
# The same four steps with their price lines taken out, for a page that shows the prices in one other place
# (/how-lumic-works/: its "lumic at a glance" block carries all four price lines). {{four_steps_plain}}
FOUR_STEPS_PLAIN = re.sub(r'<p style="margin-top:10px"><strong>.*?</strong></p>', "", FOUR_STEPS)
assert FOUR_STEPS_PLAIN.count("$") == 0 and FOUR_STEPS_PLAIN.count('class="step"') == 4


def glance_items():
    """The "lumic at a glance" facts (pages.json "glance"): all of them open llms.txt (scripts/build_markdown.py); the ones
    marked "page" show on /how-lumic-works/ ({{at_a_glance}}) as a <dl>, two by two from 960px (site.css .glance)."""
    return "\n".join(f'      <div><dt>{esc(g["q"])}</dt><dd>{curly(g.get("html") or esc(g["a"]))}</dd></div>'
                     for g in CFG["glance"] if g.get("page"))


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
            f'    <p class="f-bot"><span>© 2026 lumic</span><a href="/st-louis/">Serving Greater St. Louis, Missouri and Illinois</a><a href="/privacy/">Privacy</a></p>\n'
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
          <p class="cc-k">How to start</p>
          <ol class="nx">
            <li><span class="n">1</span><div><b>A 20&#8209;minute call.</b><span>You walk the team through the work your people do by hand.</span></div></li>
            <li><span class="n">2</span><div><b>An on-site day.</b><span>lumic&rsquo;s FDEs work beside your team where the work happens. They come on site across Greater St.&nbsp;Louis and travel for the right fit.</span></div></li>
            <li><span class="n">3</span><div><b>A written proposal.</b><span>What lumic would build, the timeline, and the cost.</span></div></li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</section>"""


def curly(s):
    """Straight apostrophes in FAQ copy become typographic ones (attribute quotes are double quotes, so untouched)."""
    return s.replace("&#x27;", "\u2019").replace("'", "\u2019")


def faq_items(items, indent="            "):
    # Questions carry no tick icon (a tick reads as "done"); li.q drops the icon column
    out = []
    for f in items:
        a = curly(f.get("html") or esc(f["a"]))
        out.append(f'{indent}<li class="q"><div><h3>{esc(curly(f["q"]))}</h3><p>{a}</p></div></li>')
    return "\n".join(out)


def faq_ld(items, at):
    return {"@type": "FAQPage", "@id": at, "mainEntity": [
        {"@type": "Question", "name": curly(f["q"]), "acceptedAnswer": {"@type": "Answer", "text": curly(f["a"])}} for f in items]}


# One "Related" list per page (at most 4 links, placed last, before the contact block): {{related /a/ /b/ ...}}
LABELS = {"/services/": "Services", "/ai-implementation/": "AI implementation", "/managed-ai/": "Managed AI",
          "/ai-consulting/": "AI consulting", "/ai-agent-skills/": "AI agent skills", "/pricing/": "Pricing",
          "/how-lumic-works/": "How lumic works", "/guardrails/": "Guardrails", "/portfolio/": "Portfolio",
          "/systems/": "Systems lumic works with", "/faq/": "Common questions", "/st-louis/": "St.\u00a0Louis",
          "/st-louis/ai-consulting/": "AI consulting in St.\u00a0Louis", "/st-louis/metro-east/": "Metro East",
          "/forward-deployed-engineers/": "Forward Deployed Engineers",
          "/forward-deployed-engineers/small-business/": "FDEs for small and mid-size businesses",
          "/services/ap-automation/": "AP automation", "/services/cash-receipts-and-collections/": "Cash receipts and collections",
          "/services/payroll/": "Payroll", "/services/month-end-close/": "Month-end close",
          "/services/dashboards-and-reporting/": "Dashboards and reporting",
          "/services/order-desk-and-customer-service/": "Order desk and customer service",
          "/industries/manufacturing/": "Manufacturing", "/industries/distribution/": "Distribution",
          "/industries/service-firms/": "Service firms",
          "/resources/how-to-implement-ai-in-a-small-business/": "How to implement AI in a small business",
          "/resources/ai-agent-for-accounting/": "AI agents for accounting",
          "/resources/how-to-choose-an-ai-implementation-partner/": "How to choose an AI implementation partner",
          "/systems/sage-100/": "Sage 100", "/systems/sage-100/ap-automation/": "Sage 100 AP automation"}


def related(hrefs):
    assert 1 <= len(hrefs) <= 4, f"related: {len(hrefs)} links (at most 4)"
    items = "".join(f'<li><a class="more-link" href="{h}">{esc(LABELS[h])} {ARROW}</a></li>' for h in hrefs)
    return (f'<!-- ============ RELATED ============ -->\n<section class="related-s" aria-labelledby="related-h">\n  <div class="wrap">\n'
            f'    <h2 class="related-h" id="related-h">Related</h2>\n    <ul class="links">{items}</ul>\n  </div>\n</section>')


def trail(p):
    """The levels between Home and the page: optional "ancestors" (a list, from the top level down), then the optional "parent"."""
    return list(p.get("ancestors", [])) + ([p["parent"]] if p.get("parent") else [])


def crumbs(p):
    # middle levels, e.g. "parent": {"label": "Services", "href": "/services/"}; "ancestors" adds levels above the parent
    mid = "".join(f'<li><a href="{x["href"]}">{esc(x["label"])}</a></li>' for x in trail(p))
    return (f'<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>{mid}'
            f'<li aria-current="page">{esc(p["crumb"])}</li></ol></nav>')


def page_lastmod(p):
    """The date a page last changed: the sitemap's lastmod and the JSON-LD dateModified, from the same git dates."""
    return lastmod(SRC / f'{p["id"]}.html', ROOT / "scripts" / "pages.json")


# lumic is based in St. Louis and can work with businesses anywhere in the United States (the owner, 2026-11-25): a Service
# node's "@AREA" is the country first, then the local areas; the local pages (/st-louis/...) keep the local list only.
AREA_US = [{"@type": "Country", "name": "United States"}] + AREA


def page_ld(p):
    url = SITE + p["path"]
    modified = page_lastmod(p)
    graph = [
        {"@type": p["type"], "@id": url + "#webpage", "url": url, "name": p["title"], "description": p["description"],
         "inLanguage": "en", "about": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"},
         "breadcrumb": {"@id": url + "#breadcrumb"}, "dateModified": modified},
        {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(
                [("Home", SITE + "/")] + [(x["label"], SITE + x["href"]) for x in trail(p)]
                + [(p["crumb"], url)])]},
    ]
    extra = SRC / f'{p["id"]}.jsonld'
    if extra.exists():
        graph += json.loads(io.open(extra, encoding="utf-8").read())
        for g in graph:  # an Article carries the same build-stamped date as its page (never hand-typed)
            if g.get("@type") == "Article":
                g["dateModified"] = modified
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
            return AREA if p["path"].startswith("/st-louis/") else AREA_US
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


def arrows(text):
    """One arrow on every link (audit P3-3): a text arrow at the end of a link becomes the SVG arrow."""
    return text.replace('<span aria-hidden="true">→</span>', ARROW).replace(' →</a>', f' {ARROW}</a>')


def build_page(p):
    url = SITE + p["path"]
    body = io.open(SRC / f'{p["id"]}.html', encoding="utf-8").read().rstrip()
    for k, v in {"{{crumbs}}": crumbs(p), "{{ck}}": CK, "{{lck}}": CK, "{{ar}}": AR, "{{book}}": BOOK,
                 "{{book_pricing}}": BOOK_PRICING, "{{pricing_block}}": PRICING_BLOCK, "{{pricing_section}}": PRICING_SECTION, "{{checklist}}": checklist(p["path"]), "{{price_onsite}}": PRICE_ONSITE,
                 "{{price_build}}": PRICE_BUILD, "{{price_agents}}": PRICE_AGENTS, "{{four_steps}}": FOUR_STEPS, "{{four_steps_plain}}": FOUR_STEPS_PLAIN, "{{at_a_glance}}": glance_items(), "{{price_build_line}}": PRICE_BUILD_LINE, "{{fee_covers}}": FEE_COVERS, "{{fee_covers_line}}": FEE_COVERS_LINE, "{{fee_covers_short}}": FEE_COVERS_SHORT, "{{price_final}}": PRICE_FINAL, "{{arrow}}": ARROW,
                 "{{film_overview}}": FILM_OVERVIEW, "{{films_list}}": films_list(), "{{faq_items}}": faq_items(CFG["faq"], "        "),
                 "{{page_faq}}": faq_items(p.get("faq", []), "        ")}.items():
        body = body.replace(k, v)
    body = re.sub(r"\{\{related ([^}]+)\}\}", lambda m: related(m.group(1).split()), body)
    assert "{{" not in body, f'{p["id"]}: unfilled token {re.search(r"{{.*?}}", body).group(0)}'
    body = arrows(dashboards(body))
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
    modified = lastmod(f)  # before the write below, so a rebuild with no change keeps the committed date
    h = io.open(f, encoding="utf-8").read()
    h = stamp(h, "nav", nav("/", home=True))
    h = stamp(h, "footer", footer(home=True))
    home_faq = [x for x in CFG["faq"] if x.get("home")]
    h = stamp(h, "faq", faq_items(home_faq))
    h = stamp(h, "pricing", "")  # the four steps on home carry the price lines; no separate pricing card (audit P2-5)
    h = stamp(h, "steps", "    " + FOUR_STEPS)
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', h, re.S)
    ld = json.loads(m.group(2))
    ld["@graph"] = [faq_ld(home_faq, SITE + "/#faq") if g.get("@type") == "FAQPage" else g for g in ld["@graph"]]
    title = html.unescape(re.search(r"<title>(.*?)</title>", h).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', h).group(1))
    webpage = {"@type": "WebPage", "@id": SITE + "/#webpage", "url": SITE + "/", "name": title, "description": desc, "inLanguage": "en",
               "about": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"}, "dateModified": modified}
    ld["@graph"] = [g for g in ld["@graph"] if g.get("@id") != webpage["@id"]] + [webpage]
    h = h[:m.start(2)] + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + h[m.end(2):]
    h = arrows(dashboards(h))
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
    urls += [(p["path"], page_lastmod(p)) for p in CFG["pages"]]
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
