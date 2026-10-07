"""Capture screens of a REAL lumic dashboard for the demo films, with every number and name scrambled before it renders.

How it stays safe:
  * Every JSON response from the dashboard is rewritten in flight (Playwright route): money and quantities are scaled by one
    hidden factor (so totals still add up), ratios and day counts are nudged, and names, items, people, emails, phones,
    addresses, free-text notes and codes are replaced with consistent fakes. Requests going back to the server get the fake
    keys swapped back to the real ones, so drill-downs keep working.
  * HTML pages get the private term list applied (company names, user names), and the same terms are replaced in the DOM.
  * Before each screenshot a leak check scans the page text and every Chart.js label for any real value the run replaced.
    One hit stops the run and nothing is saved for that shot.
Real values never leave the browser: only scrambled PNGs and element boxes are written.

The shot list and the term list are PRIVATE (they name the client): keep them outside the public website repo, e.g.
  ~/projects/playbook/brand/demo-films/<film>.json        (shot list: base URL + steps)
  ~/.lumic-demo-terms.json                                 ({"Real Co. Name": "Northwind Supply Co.", "Jane Doe": "Alex Rivera"})

Run:
  python video/demos/capture_live.py <shotlist.json> [--terms FILE] [--login] [--out DIR] [--headed]
    --login   opens Chrome on the dashboard so a person signs in once; the session is kept in video/demos/.auth/ (gitignored)
Shot list:
  {"name": "receivables", "base": "http://host:5002", "viewport": [1440, 900],
   "hide": [".tour-invite"],                 CSS selectors hidden on every page
   "key_overrides": {"/api/overview:label": "segment"},   force a fake type for a JSON key, optionally only on one API path
   "nudge_percents": true,                   default: nudge every on-screen % and pts value (ratios survive the money scale)
   "steps": [{"goto": "/receivables"}, {"wait": 1500}, {"shot": "overview", "boxes": {"kpis": ".kpi-row"}},
             {"eval": "navigate('aging')"}, {"click": "text=Aging"}, {"dblclick": "tr[data-ck] >> nth=0"}, {"scroll": 400}]}
"""
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- fake vocabularies (generic; nothing real)
CO_A = ["Harbor", "Summit", "Northfield", "Bluestone", "Cedar", "Ironwood", "Lakeshore", "Redline", "Silverleaf", "Granite", "Westbrook",
        "Pinecrest", "Riverbend", "Oakridge", "Brightwater", "Fairview", "Kestrel", "Meridian", "Sterling", "Copperfield", "Highland",
        "Prairie", "Stonegate", "Clearwater", "Evergreen", "Foxhollow", "Maplewood", "Northstar", "Ridgeway", "Tidewater"]
CO_B = ["Supply", "Industries", "Distribution", "Partners", "Logistics", "Systems", "Products", "Group", "Trading", "Works",
        "Holdings", "Services", "Wholesale", "Electric", "Mechanical", "Contractors", "Outfitters", "Goods", "Solutions", "Brands"]
CO_C = ["Co.", "Inc.", "LLC", "Corp.", ""]
FIRST = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Quinn", "Reese", "Drew", "Parker", "Rowan", "Sam",
         "Blake", "Cameron", "Dana", "Emerson", "Hayden", "Kendall", "Logan", "Micah", "Noel", "Peyton", "Sasha", "Skyler"]
LAST = ["Rivera", "Bennett", "Hayes", "Coleman", "Foster", "Brooks", "Sullivan", "Price", "Reed", "Ellis", "Porter", "Hughes", "Myers",
        "Grant", "Wallace", "Ford", "Hart", "Dixon", "Lane", "Shaw", "Warren", "Holt", "Pierce", "Carver"]
PROD_A = ["Standard", "Heavy-Duty", "Compact", "Premium", "Utility", "Classic", "Pro", "Select", "Core", "Prime", "Flex", "Ultra"]
PROD_B = ["Carton", "Kit", "Bracket", "Liner", "Panel", "Fitting", "Coupling", "Spool", "Tray", "Cap", "Sleeve", "Clamp", "Insert",
          "Plate", "Cover", "Mount", "Seal Ring", "Spacer", "Housing", "Hinge"]
PROD_C = ["12 in", "24 in", "6 pk", "1 lb", "5 lb", "Case/24", "Small", "Large", "Type A", "Type B", "Gray", "Black", "Series 2", "XL"]
SEGMENTS = ["Retail", "Wholesale", "Industrial", "Healthcare", "Food & Beverage", "Automotive", "Construction", "E-Commerce",
            "Logistics", "Energy", "Hospitality", "Education", "Agriculture", "Government", "Utilities", "Telecom"]
NOTES = ["Followed up on the open balance; waiting on remittance detail.", "Confirmed the new ship-to address.",
         "Asked for an updated W-9.", "Promised payment by Friday.", "Sent the statement again by email.",
         "Price confirmed for the next order.", "Called about the short shipment; credit issued.", "Reviewed with the owner."]
STREETS = ["Main St", "Oak Ave", "Industrial Pkwy", "Commerce Dr", "Lake Rd", "Market St", "Park Blvd", "Mill Rd"]
CITIES = ["Springfield", "Fairview", "Riverton", "Greenville", "Madison", "Franklin", "Clinton", "Georgetown", "Salem", "Bristol"]

# ---------------------------------------------------------------- key classification (lowercased JSON keys)
K_KEEP_NUM = re.compile(r"(^|_)(year|yr|month|mo|day|dow|week|wk|quarter|qtr|period|idx|index|rank|page|pages|limit|offset|level|"
                        r"version|ver|sort|order|port|hour|minute|second|lat|lon|lng|seq|line|line_no|cur_month|compare_year|"
                        r"n_months|months|status|code|id)$|^id$|_id$")
K_RATIO = re.compile(r"pct|percent|ratio|rate|margin|share|yoy|growth|_pp$|score|dso|dpo|dio|turn|days|avg_|average|^avg|age")
K_PERSON = re.compile(r"contact|(^|_)rep($|_)|salesperson|salesman|user|buyer|approver|entered_by|created_by|updated_by|author|"
                      r"owner|employee|first_name|last_name|full_name|person|attention|attn|signer|by$")
K_EMAIL = re.compile(r"email|e_mail|mail$")
K_PHONE = re.compile(r"phone|fax|tel$|telephone|mobile|cell")
K_ADDR = re.compile(r"address|addr|street|line1|line2|city|zip|postal")
K_SEGMENT = re.compile(r"industry|segment|market|territory|region|category|class$|group$|channel|end_market")
K_PRODUCT = re.compile(r"item_desc|item_name|description|desc$|^desc|product|part_desc|material|sku_name|item_description")
K_COMPANY = re.compile(r"customer|cust|vendor|supplier|(^|_)name$|^name|company|shipto|ship_to|bill_to|payee|account_name|"
                       r"carrier|client|sold_to|bank")
K_CODE = re.compile(r"_key$|(^|_)code$|_no$|^no$|number|_num$|^num$|invoice|(^|_)po($|_)|check|sku|part$|^item$|item_code|itemcode|"
                    r"item_no|account$|acct|(^|_)gl($|_)|deposit|batch|ref$|reference|^key$|_ck$|^ck$|customerkey|vendorkey")
K_FREE = re.compile(r"note|notes|memo|comment|message|reason|body|remark|instructions")
DATEISH = re.compile(r"^\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}(-\d{2})?([ T]\d{1,2}:\d{2}(:\d{2})?)?|"
                     r"[A-Z][a-z]{2,8}\.? ?'?\d{2,4}|\d{1,2}:\d{2}( ?[AP]M)?|(Q[1-4]|H[12]) ?\d{2,4}|\d{4})\s*$")
MONEYISH = re.compile(r"(?<![\w/.-])(-?\$\s?-?[\d,]+(?:\.\d+)?|-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?![\w/-])")


def h(s, salt=""):
    return int(hashlib.sha256((salt + "|" + s).encode()).hexdigest()[:12], 16)


class Scrambler:
    def __init__(self, terms, seed):
        self.seed = seed
        rnd = random.Random(seed)
        self.K = rnd.uniform(0.52, 0.81)                      # one hidden scale for money and quantities
        self.terms = dict(terms)                              # real -> fake (private list: company, users)
        self.fwd = {}                                         # real string -> fake string (names, codes)
        self.rev = {}                                         # fake -> real (to send drill-down keys back)
        self.used = set()
        self.leak_strings = set(k for k in self.terms if len(k) >= 3)
        self.leak_numbers = set()
        self.path = ""                                        # URL path of the response being scrambled
        self.overrides = {}                                   # {"json_key": "segment" | "company" | "person" | "product" | "code" | "free"}
        self.mapkeys = False                                  # second pass: also rename dict keys that are real codes/names

    # ------------------------------------------------------------ string fakes
    def _unique(self, real, make):
        if real in self.fwd:
            return self.fwd[real]
        n = 0
        while True:
            fake = make(h(real, f"{self.seed}:{n}"))
            if n > 40:                                         # small vocabularies run out: number the fake
                fake = f"{fake} {n - 39}"
            if fake not in self.used and fake != real:
                break
            n += 1
        self.fwd[real], self.rev[fake] = fake, real
        self.used.add(fake)
        if len(real) >= 4 and not real.isdigit():
            self.leak_strings.add(real)
        return fake

    def company(self, s):
        return self._unique(s, lambda x: " ".join(w for w in (CO_A[x % len(CO_A)], CO_B[(x // 31) % len(CO_B)],
                                                                   CO_C[(x // 997) % len(CO_C)]) if w))

    def person(self, s):
        if "," in s:                                           # "Last, First"
            return self._unique(s, lambda x: f"{LAST[x % len(LAST)]}, {FIRST[(x // 29) % len(FIRST)]}")
        if len(s.split()) == 1 and len(s) <= 4:                # initials / user codes
            return self._unique(s, lambda x: "".join(chr(65 + (x >> (5 * i)) % 26) for i in range(len(s))))
        return self._unique(s, lambda x: f"{FIRST[x % len(FIRST)]} {LAST[(x // 29) % len(LAST)]}")

    def product(self, s):
        return self._unique(s, lambda x: f"{PROD_A[x % len(PROD_A)]} {PROD_B[(x // 13) % len(PROD_B)]} {PROD_C[(x // 263) % len(PROD_C)]}")

    def segment(self, s):
        return self._unique(s, lambda x: SEGMENTS[x % len(SEGMENTS)] + ("" if x % 7 else " Services"))

    def code(self, s):
        def make(x):
            r = random.Random(x)
            return "".join(str(r.randrange(10)) if c.isdigit() else (chr(65 + r.randrange(26)) if c.isupper() else
                           chr(97 + r.randrange(26)) if c.islower() else c) for c in s)
        return self._unique(s, make)

    def email(self, s):
        return self._unique(s, lambda x: f"{FIRST[x % len(FIRST)].lower()}.{LAST[(x // 29) % len(LAST)].lower()}@example.com")

    def phone(self, s):
        return self._unique(s, lambda x: f"555-01{x % 100:02d}")

    def address(self, s):
        return self._unique(s, lambda x: f"{100 + x % 8900} {STREETS[(x // 7) % len(STREETS)]}" if re.search(r"\d", s)
                            else CITIES[x % len(CITIES)])

    def free(self, s):
        return self._unique(s, lambda x: NOTES[x % len(NOTES)])

    # ------------------------------------------------------------ numbers
    def num(self, v, key):
        if isinstance(v, bool) or v is None:
            return v
        k = key.lower()
        if K_KEEP_NUM.search(k) or (isinstance(v, int) and 1900 <= v <= 2100):
            return v
        if K_RATIO.search(k):
            f = 1 + ((h(k, str(self.seed)) % 2400) / 10000 - 0.12)   # same nudge for the whole field: -12% .. +12%
            out = v * f
        else:
            out = v * self.K
            if abs(v) >= 1000:
                self.leak_numbers.add(abs(v))
        if isinstance(v, int):
            return int(round(out))
        decimals = len(repr(v).split(".")[1]) if "." in repr(v) and "e" not in repr(v) else 2
        return round(out, min(decimals, 4))

    def text_numbers(self, s):
        """Scale formatted amounts inside a string ("$31,886", "1,234.50"); dates are left alone."""
        if DATEISH.match(s):
            return s

        def rep(m):
            t = m.group(1)
            neg = t.startswith("-")
            core = t.lstrip("-").lstrip("$").strip().lstrip("-")
            try:
                val = float(core.replace(",", ""))
            except ValueError:
                return t
            if val >= 1000:
                self.leak_numbers.add(val)
            new = val * self.K
            dec = len(core.split(".")[1]) if "." in core else 0
            body = f"{new:,.{dec}f}"
            return ("-" if neg else "") + ("$" if "$" in t else "") + body
        return MONEYISH.sub(rep, s)

    def replace_known(self, s):
        for real in sorted(self.terms, key=len, reverse=True):
            s = re.sub(rf"(?<![A-Za-z]){re.escape(real)}(?![A-Za-z])", self.terms[real], s)
        for real in self.names():
            if real in s:
                s = s.replace(real, self.fwd[real])
        return s

    def names(self):
        """Real values safe to replace inside longer text: names with letters, never bare numbers or short codes."""
        return sorted((r for r in self.fwd if len(r) >= 4 and re.search(r"[A-Za-z]{2}", r)), key=len, reverse=True)

    # ------------------------------------------------------------ JSON walk
    def string(self, s, key):
        k = key.lower()
        kind = next((v for (path, kk), v in self.overrides.items() if kk == k and path in self.path), None)
        if kind and s not in self.terms and not DATEISH.match(s) and re.search(r"[A-Za-z]", s):
            return getattr(self, kind)(s)
        if not s.strip() or len(s) > 4000:
            return s
        if s in self.terms:
            return self.terms[s]
        if s in self.fwd:
            return self.fwd[s]
        if DATEISH.match(s):
            return s
        if K_EMAIL.search(k) and "@" in s:
            return self.email(s)
        if K_PHONE.search(k) and re.search(r"\d{3}", s):
            return self.phone(s)
        if K_ADDR.search(k):
            return self.address(s)
        if K_FREE.search(k) and len(s) > 12:
            return self.free(s)
        if K_CODE.search(k) and re.fullmatch(r"[\w\-./ #]{1,40}", s) and (re.search(r"\d", s) or re.fullmatch(r"[A-Z]{2,8}", s)):
            return self.code(s)
        if K_PERSON.search(k) and re.search(r"[A-Za-z]", s):
            return self.person(s)
        if K_SEGMENT.search(k) and re.search(r"[A-Za-z]", s):
            return self.segment(s)
        if K_PRODUCT.search(k) and re.search(r"[A-Za-z]", s):
            return self.product(s)
        if K_COMPANY.search(k) and re.search(r"[A-Za-z]", s):
            return self.company(s)
        if k == "label" or k.endswith("_label") or k == "labels":
            return s if not re.search(r"[A-Za-z]{3}", s) else self.replace_known(self.text_numbers(s))
        return self.replace_known(self.text_numbers(s))

    def walk(self, o, key=""):
        if isinstance(o, dict):
            return {(self.fwd.get(kk, kk) if self.mapkeys else kk): self.walk(v, kk) for kk, v in o.items()}
        if isinstance(o, list):
            return [self.walk(v, key) for v in o]
        if isinstance(o, str):
            return self.string(o, key)
        if isinstance(o, (int, float)):
            return self.num(o, key)
        return o

    def scramble_json(self, data):
        # two passes: the first learns every keyed name, the second also swaps those names where they appear un-keyed
        self.mapkeys = False
        self.walk(data)
        self.mapkeys = True
        return self.walk(data)

    def unscramble_url(self, url):
        """Swap fake values back to real ones, but only whole path segments and whole query values."""
        u = urlsplit(url)
        path = "/".join(quote(self.rev.get(unquote(seg), unquote(seg)), safe="@:+-._~!$&'()*,;=") for seg in u.path.split("/"))
        q = urlencode([(k, self.rev.get(v, v)) for k, v in parse_qsl(u.query, keep_blank_values=True)])
        return urlunsplit((u.scheme, u.netloc, path, q, u.fragment))

    def _unwalk(self, o):
        if isinstance(o, dict):
            return {self.rev.get(k, k): self._unwalk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [self._unwalk(v) for v in o]
        return self.rev.get(o, o) if isinstance(o, str) else o

    def unscramble_text(self, s):
        try:
            return json.dumps(self._unwalk(json.loads(s)))
        except ValueError:
            pairs = parse_qsl(s, keep_blank_values=True)
            return urlencode([(k, self.rev.get(v, v)) for k, v in pairs]) if pairs else s


# ---------------------------------------------------------------- browser side
PCT_JS = """(seed) => {
  const hash = s => { let x = seed >>> 0; for (const c of s) x = Math.imul(x ^ c.charCodeAt(0), 2654435761) >>> 0; return x; };
  const re = /(^|[^\d.,$])([-+−]?)(\d{1,3}(?:\.\d+)?)(\s?(?:%|pts?\b))/g;
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) {
    const t = n.nodeValue;
    if (!/%|pt/.test(t)) continue;
    const o = t.replace(re, (m, pre, sign, num, unit) => {
      const v = parseFloat(num); if (!v) return m;
      const f = 1 + ((hash(num + unit) % 3000) / 10000 - 0.15);            // -15% .. +15%, same for the same value
      const dec = (num.split('.')[1] || '').length;
      let nv = (v * f).toFixed(dec); if (parseFloat(nv) === v) nv = (v + Math.pow(10, -dec)).toFixed(dec);
      return pre + sign + nv + unit;
    });
    if (o !== t) n.nodeValue = o;
  }
}"""
DOM_JS = """(pairs) => {
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const order = pairs.sort((a, b) => b[0].length - a[0].length);
  for (let n; (n = w.nextNode());) {
    let t = n.nodeValue, o = t;
    for (const [r, f] of order) if (t.includes(r)) t = t.split(r).join(f);
    if (t !== o) n.nodeValue = t;
  }
  for (const el of document.querySelectorAll('input,textarea')) for (const [r, f] of order) if (el.value && el.value.includes(r)) el.value = el.value.split(r).join(f);
  document.title = order.reduce((s, [r, f]) => s.split(r).join(f), document.title);
}"""
TEXT_JS = """() => {
  const parts = [document.body.innerText, document.title];
  for (const el of document.querySelectorAll('input,textarea,select')) parts.push(el.value || '');
  for (const el of document.querySelectorAll('[title],[aria-label],[placeholder]'))
    parts.push(el.getAttribute('title') || '', el.getAttribute('aria-label') || '', el.getAttribute('placeholder') || '');
  const C = window.Chart;
  const charts = C ? (C.instances ? Object.values(C.instances) : []) : [];
  for (const ch of charts) {
    const d = ch.data || (ch.config && ch.config.data) || {};
    parts.push(...(d.labels || []).map(String));
    for (const ds of d.datasets || []) parts.push(String(ds.label || ''), ...(ds.data || []).map(v => typeof v === 'object' ? JSON.stringify(v) : String(v)));
  }
  return parts.join('\\n');
}"""


def leaks(text, sc):
    hits = [s for s in sc.leak_strings if s in text and s not in sc.used]   # a generic fake that equals a real label is not a leak
    for v in sc.leak_numbers:
        forms = {f"{v:,.2f}", f"{v:.2f}", f"{v:,.0f}", f"{v:.0f}"}
        for f in forms:   # whole-number match only: not inside a longer number, and cents must match
            digits = len(f.replace(",", "").split(".")[0])
            if (digits >= 5 or "." in f) and len(f.replace(",", "")) >= 5 and re.search(rf"(?<![\d,.]){re.escape(f)}(?![\d]|[.,]\d)", text):
                hits.append(f)
                break
    return sorted(set(hits))


def boxes(pg, sels):
    out = {}
    for name, sel in sels.items():
        loc = pg.locator(sel).first
        b = loc.bounding_box() if loc.count() else None
        if b:
            out[name] = [round(b["x"]), round(b["y"]), round(b["width"]), round(b["height"])]
        else:
            print(f"  no box for {name}: {sel}")
    return out


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        sys.exit(__doc__)
    cfg = json.loads(Path(a[0]).read_text(encoding="utf-8"))
    terms_path = Path(a[a.index("--terms") + 1]) if "--terms" in a else Path.home() / ".lumic-demo-terms.json"
    terms = json.loads(terms_path.read_text(encoding="utf-8")) if terms_path.exists() else {}
    if not terms:
        print(f"warning: no private term list at {terms_path}; company and user names in page HTML will not be replaced")
    name, base = cfg["name"], cfg["base"].rstrip("/")
    out = Path(a[a.index("--out") + 1]) if "--out" in a else HERE / "shots" / name
    out.mkdir(parents=True, exist_ok=True)
    auth = HERE / ".auth" / f"{name}.json"
    auth.parent.mkdir(exist_ok=True)
    (auth.parent / ".gitignore").write_text("*\n")
    W, H = cfg.get("viewport", [1440, 900])
    sc = Scrambler(terms, seed=cfg.get("seed", h(name) % 100000))
    # "key" applies everywhere; "/api/path:key" only to responses whose URL path contains /api/path
    sc.overrides = {(k.rsplit(":", 1)[0] if ":" in k else "", k.rsplit(":", 1)[-1].lower()): v
                    for k, v in cfg.get("key_overrides", {}).items()}

    with sync_playwright() as pw:
        if "--login" in a:
            b = pw.chromium.launch(channel="chrome", headless=False)
            ctx = b.new_context(viewport={"width": W, "height": H})
            pg = ctx.new_page()
            pg.goto(base + cfg["steps"][0].get("goto", "/"))
            input("Sign in in the Chrome window, then press Enter here... ")
            ctx.storage_state(path=str(auth))
            b.close()
            print(f"session saved to {auth}")

        b = pw.chromium.launch(channel="chrome", headless="--headed" not in a)
        ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=2,
                            storage_state=str(auth) if auth.exists() else None)

        def hdrs(resp, ctype=None):
            d = {k: v for k, v in resp.headers.items() if k.lower() not in ("content-length", "content-encoding")}
            if ctype:
                d["content-type"] = ctype
            return d

        def handle(route):
            req = route.request
            if not req.url.startswith(base):
                return route.continue_()
            url = sc.unscramble_url(req.url)
            body = req.post_data
            try:
                resp = route.fetch(url=url, post_data=sc.unscramble_text(body) if body else None)
            except Exception as e:                                    # noqa: BLE001
                print("  fetch failed:", req.url, e)
                return route.abort()
            ctype = resp.headers.get("content-type", "")
            if "json" in ctype:
                sc.path = urlsplit(url).path
                try:
                    data = resp.json()
                except Exception:                                     # noqa: BLE001
                    return route.fulfill(response=resp)
                return route.fulfill(response=resp, body=json.dumps(sc.scramble_json(data)),
                                     headers=hdrs(resp, "application/json"))
            if "html" in ctype or "javascript" in ctype:
                return route.fulfill(response=resp, body=sc.replace_known(resp.text()), headers=hdrs(resp))
            return route.fulfill(response=resp)

        ctx.route("**/*", handle)
        hide = ",".join(cfg.get("hide", []))
        res = {"_viewport": [W, H, 2]}
        for learn in (True, False):           # pass 1 learns every name on every page; pass 2 captures with all of them known
          pg = ctx.new_page()
          for i, st in enumerate(cfg["steps"]):
              if "goto" in st:
                  pg.goto(base + st["goto"], wait_until="networkidle")
                  if hide:
                      pg.add_style_tag(content=hide + "{display:none!important}")
              elif "eval" in st:
                  pg.evaluate(st["eval"])
              elif "click" in st:
                  pg.locator(st["click"]).first.click()
              elif "dblclick" in st:
                  pg.locator(st["dblclick"]).first.dblclick()
              elif "scroll" in st:
                  pg.mouse.wheel(0, st["scroll"])
              elif "wait" in st:
                  pg.wait_for_timeout(st["wait"])
              elif "shot" in st and learn:
                  pg.wait_for_load_state("networkidle")
                  pg.wait_for_timeout(st.get("settle", 1500))
              elif "shot" in st:
                  pg.wait_for_load_state("networkidle")
                  pg.wait_for_timeout(st.get("settle", 1500))
                  pairs = [[r, sc.terms[r]] for r in sc.terms] + [[r, sc.fwd[r]] for r in sc.names()]
                  pg.evaluate(DOM_JS, pairs)
                  if cfg.get("nudge_percents", True):
                      pg.evaluate(PCT_JS, sc.seed)
                  hits = leaks(pg.evaluate(TEXT_JS), sc)
                  if hits:
                      print(f"LEAK CHECK FAILED on shot '{st['shot']}' - real values still on the page (not saved):")
                      for x in hits[:25]:
                          print("   ", x if len(x) < 6 else x[:3] + "..." + f" ({len(x)} chars)")
                      b.close()
                      sys.exit(2)
                  pg.screenshot(path=str(out / f"{st['shot']}.png"), full_page=st.get("full", False))
                  res[st["shot"]] = boxes(pg, st.get("boxes", {}))
                  print(f"shot {st['shot']}: ok (leak check clean)")
              if "wait_after" in st:
                  pg.wait_for_timeout(st["wait_after"])
          pg.close()
        b.close()
    (out / "boxes.json").write_text(json.dumps(res, indent=1))
    print(f"scale factor hidden; {len(sc.fwd)} names/codes replaced; {len(sc.leak_numbers)} amounts scaled -> {out}")


if __name__ == "__main__":
    main()
