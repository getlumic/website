"""Build the markdown copies of the site for AI agents: public/index.md and public/llms-full.txt.

Reads public/index.html (the <main> copy and the FAQ in its JSON-LD) and public/llms.txt, so the markdown always says
what the page says. Run it after every copy change, before deploy:

    py -3.11 scripts/build_markdown.py
"""
import io, json, re
from html.parser import HTMLParser
from pathlib import Path

PUB = Path(__file__).resolve().parent.parent / "public"
SITE = "https://get-lumic.com"
SKIP = {"script", "style", "svg", "video", "button", "dialog", "noscript", "img"}
VOID = {"br", "img", "source", "input", "meta", "link", "hr"}
HEAD = {"h1": "# ", "h2": "## ", "h3": "### ", "summary": "### "}
BLOCK = {"h1", "h2", "h3", "p", "li", "summary", "figcaption", "blockquote", "cite", "tr", "div", "article", "section", "ul", "ol", "table"}


class MD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.buf, self.skip, self.stack, self.cells, self.href, self.inmain = [], "", 0, [], None, None, False

    def flush(self, prefix=""):
        t = re.sub(r"\s+", " ", self.buf).strip()
        t = re.sub(r"\s+([.,;:!?])", r"\1", t)
        self.buf = ""
        if t:
            self.out.append(prefix + t)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.inmain = True
        if not self.inmain or tag in VOID:
            return
        hidden = a.get("aria-hidden") == "true" or tag in SKIP or a.get("class", "").split()[:1] in (["n"], ["flow-hub"])
        self.stack.append((tag, hidden))
        if hidden:
            self.skip += 1
            return
        if self.skip:
            return
        if tag in BLOCK:
            self.flush()
        if tag == "tr":
            self.cells = []
        if tag == "a":
            href = a.get("href", "")
            self.href = (SITE + href) if href.startswith("/") else (None if href.startswith("#") else href)
            if self.href:
                self.buf += " ["
        if tag in ("span", "small"):
            self.buf += " — " if tag == "small" else " "

    def handle_endtag(self, tag):
        if tag == "main":
            self.flush()
            self.inmain = False
            return
        if not self.inmain or tag in VOID or not self.stack:
            return
        # close up to the matching tag (the page is well formed; this only guards against stray ends)
        while self.stack:
            t, hidden = self.stack.pop()
            if hidden:
                self.skip -= 1
            elif not self.skip:
                self._end(t)
            if t == tag:
                break

    def _end(self, tag):
        if tag in ("td", "th"):
            self.cells.append(re.sub(r"\s+", " ", self.buf).strip())
            self.buf = ""
        elif tag == "tr":
            cells = [c for c in (self.cells or []) if c]
            if cells:
                self.out.append("- " + " → ".join(cells))
            self.cells = None
        elif tag == "a" and self.href:
            self.buf += f"]({self.href})"
            self.href = None
        elif tag in HEAD:
            self.flush(HEAD[tag])
        elif tag == "li":
            self.flush("- ")
        elif tag in ("blockquote", "cite"):
            self.flush("> ")
        elif tag in BLOCK:
            self.flush()
        elif tag == "span":
            self.buf += " "

    def handle_data(self, d):
        if self.inmain and not self.skip:
            self.buf += d


def main():
    html = io.open(PUB / "index.html", encoding="utf-8").read()
    title = re.search(r"<title>(.*?)</title>", html).group(1)
    desc = re.search(r'<meta name="description" content="(.*?)">', html).group(1)
    p = MD()
    p.feed(html)
    lines, prev = [], None
    for l in p.out:
        if l == prev:
            continue
        islist = l.startswith(("- ", "> "))
        if lines and lines[-1] != "" and (l.startswith("#") or not islist):
            lines.append("")  # a heading or a paragraph after a list starts a new block
        l = re.sub(r"\s+\]", "]", l)
        lines.append(l)
        if l.startswith(("# ", "## ", "### ")) or not l.startswith(("- ", "> ")):
            lines.append("")
        prev = l
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
    faq = next(g for g in ld["@graph"] if g["@type"] == "FAQPage")
    faq_md = "\n\n".join(f"### {q['name']}\n\n{q['acceptedAnswer']['text']}" for q in faq["mainEntity"])
    foot = re.search(r'<p class="f-bot">(.*?)</p>', html, re.S).group(1)
    foot = re.sub(r"<[^>]+>", "", foot).replace("·", "|").strip()
    import datetime
    front = (f"---\ntitle: \"{title}\"\ndescription: \"{desc}\"\ncanonical: {SITE}/\n"
             f"last_updated: {datetime.date.today().isoformat()}\n---\n\n")
    page = (front + f"# {title}\n\n> {desc}\n\nSource: {SITE}/ | Contact: hello@get-lumic.com\n\n{body}\n\n## Questions\n\n{faq_md}\n\n"
            f"---\n\n{foot}\n")
    io.open(PUB / "index.md", "w", encoding="utf-8", newline="\n").write(page)
    llms = io.open(PUB / "llms.txt", encoding="utf-8").read().strip()
    full = f"{llms}\n\n---\n\n# Full site copy\n\n{page}"
    io.open(PUB / "llms-full.txt", "w", encoding="utf-8", newline="\n").write(full)
    print("index.md", len(page), "chars; llms-full.txt", len(full), "chars")

    # the page's JSON-LD as its own file, and the two discovery files that point at real files only
    io.open(PUB / "schema.jsonld", "w", encoding="utf-8", newline="\n").write(json.dumps(ld, ensure_ascii=False, indent=1) + "\n")
    io.open(PUB / "schemamap.xml", "w", encoding="utf-8", newline="\n").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url contentType="structuredData/schema.org"><loc>{SITE}/schema.jsonld</loc></url>\n</urlset>\n')
    # ARD catalog (agenticresourcediscovery.org): urn:air:<domain>:<namespace>:<name> identifiers, one url each.
    # Only documents we really publish; no API or MCP server is claimed.
    q = ["what does lumic do", "who leads lumic", "does lumic work outside St. Louis"]
    U = "urn:air:get-lumic.com:docs:"
    catalog = {"specVersion": "0.91", "entries": [
        {"identifier": U + "llms", "displayName": "lumic for AI agents", "type": "text/plain", "url": f"{SITE}/llms.txt", "representativeQueries": q},
        {"identifier": U + "llms-full", "displayName": "Full site copy", "type": "text/plain", "url": f"{SITE}/llms-full.txt", "representativeQueries": q},
        {"identifier": U + "home-markdown", "displayName": "Home page as markdown", "type": "text/markdown", "url": f"{SITE}/index.md", "representativeQueries": q},
        {"identifier": U + "schema", "displayName": "Organization, service and FAQ (schema.org)", "type": "application/ld+json", "url": f"{SITE}/schema.jsonld",
         "representativeQueries": ["what areas does lumic serve", "how much does lumic cost"]},
        {"identifier": U + "sitemap", "displayName": "Sitemap", "type": "application/xml", "url": f"{SITE}/sitemap.xml", "representativeQueries": ["list the pages on get-lumic.com"]},
    ]}
    (PUB / ".well-known").mkdir(exist_ok=True)
    for name in ("ard.json", "ai-catalog.json"):  # canonical path, plus the legacy one
        io.open(PUB / ".well-known" / name, "w", encoding="utf-8", newline="\n").write(json.dumps(catalog, indent=1) + "\n")
    for e in catalog["entries"]:  # list only files that exist
        assert (PUB / e["url"].replace(SITE + "/", "")).exists(), e["url"]


if __name__ == "__main__":
    main()
