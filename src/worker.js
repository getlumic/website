// get-lumic.com: the static site, plus a thin layer for agents, films and headers.
// - Markdown for AI agents: a page with Accept: text/markdown, or "?mode=agent", returns its markdown copy (<path>index.md,
//   for the paths in MD_PAGES, which scripts/build_pages.py writes). A markdown request for a missing page gets a short
//   markdown 404.
// - Films: a byte-range request on /video/* gets 206 Partial Content (static assets return the whole file, and iPhone
//   Safari will not play a video that way).
// - Redirects: www.get-lumic.com -> get-lumic.com, /about(/) -> /how-lumic-works/, and the assets' own 307s (/index.html,
//   /privacy) become 301s.
// - Headers: HSTS everywhere, a Link header on pages (llms.txt and the markdown copy), a day of browser cache on films
//   and images (their file names are reused when a film is replaced, so not longer than that).
const APEX = "get-lumic.com";
// md-pages:start
const MD_PAGES = new Set(["/", "/services/", "/services/ap-automation/", "/services/cash-receipts-and-collections/", "/services/payroll/", "/services/month-end-close/", "/services/dashboards-and-reporting/", "/portfolio/", "/how-lumic-works/", "/guardrails/", "/pricing/", "/industries/manufacturing/", "/industries/distribution/", "/industries/service-firms/", "/st-louis/", "/st-louis/ai-consulting/", "/forward-deployed-engineers/", "/faq/", "/systems/", "/systems/quickbooks/", "/systems/netsuite/", "/systems/sage-100/", "/systems/sage-intacct/", "/resources/month-end-red-flags/"]);
// md-pages:end
const REDIRECTS = { "/about": "/how-lumic-works/", "/about/": "/how-lumic-works/" };
function mdFor(path) {
  if (path === "/index.html") return "/index.md";
  return MD_PAGES.has(path) ? path + "index.md" : null;
}
const NOT_FOUND_MD = `# Page not found

This page is not on get-lumic.com.

- Home: https://get-lumic.com/ (markdown: https://get-lumic.com/index.md)
- For AI agents: https://get-lumic.com/llms.txt
- Contact: hello@get-lumic.com
`;
const HSTS = "max-age=31536000";
const link = (md) => '</llms.txt>; rel="describedby"; type="text/plain"' + (md ? `, <${md}>; rel="alternate"; type="text/markdown"` : "");
const MEDIA_CACHE = "public, max-age=86400";

function wantsMarkdown(req, url) {
  return url.searchParams.get("mode") === "agent" || /\btext\/markdown\b/i.test(req.headers.get("Accept") || "");
}

function finish(res, extra) {
  const r = new Response(res.body, res);
  r.headers.set("Strict-Transport-Security", HSTS);
  for (const [k, v] of Object.entries(extra || {})) {
    if (k === "Vary") r.headers.append(k, v); else r.headers.set(k, v);
  }
  return r;
}

// Stream bytes [start, end] of body without buffering the whole film.
function sliceStream(body, start, end) {
  let pos = 0;
  const reader = body.getReader();
  return new ReadableStream({
    async pull(ctl) {
      for (;;) {
        const { done, value } = await reader.read();
        if (done) { ctl.close(); return; }
        const from = pos, to = pos + value.length - 1;
        pos += value.length;
        if (to < start) continue;
        if (from > end) { reader.cancel(); ctl.close(); return; }
        ctl.enqueue(value.subarray(Math.max(0, start - from), Math.min(value.length, end - from + 1)));
        if (to >= end) { reader.cancel(); ctl.close(); }
        return;
      }
    },
    cancel() { reader.cancel(); },
  });
}

const RANGE = /^bytes=(\d*)-(\d*)$/;

async function serveVideo(req, env) {
  const range = req.headers.get("Range");
  const plain = new Headers(req.headers);
  plain.delete("Range");
  const res = await env.ASSETS.fetch(new Request(req.url, { method: "GET", headers: plain }));
  if (!res.ok) return finish(res);
  const h = new Headers(res.headers);
  h.set("Accept-Ranges", "bytes");
  h.set("Cache-Control", MEDIA_CACHE);
  h.set("Strict-Transport-Security", HSTS);
  const m = range && RANGE.exec(range.trim());
  if (!m || (m[1] === "" && m[2] === "")) {
    return new Response(req.method === "HEAD" ? null : res.body, { status: 200, headers: h });
  }
  let size = Number(res.headers.get("Content-Length")), buf = null;
  if (!size) {  // no length on the asset response (chunked): read it once to learn the size
    buf = new Uint8Array(await res.arrayBuffer());
    size = buf.length;
  }
  let start, end;
  if (m[1] === "") { start = Math.max(0, size - Number(m[2])); end = size - 1; }       // bytes=-N: the last N bytes
  else { start = Number(m[1]); end = m[2] === "" ? size - 1 : Math.min(Number(m[2]), size - 1); }
  const drop = () => { if (!buf) res.body.cancel(); };
  if (start >= size || start > end) {
    drop();
    return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}`, "Accept-Ranges": "bytes", "Strict-Transport-Security": HSTS } });
  }
  h.set("Content-Range", `bytes ${start}-${end}/${size}`);
  h.set("Content-Length", String(end - start + 1));
  if (req.method === "HEAD") { drop(); return new Response(null, { status: 206, headers: h }); }
  const body = buf ? buf.subarray(start, end + 1) : sliceStream(res.body, start, end);
  return new Response(body, { status: 206, headers: h });
}


// Checklist email capture: POST /api/checklist (one email field plus a hidden honeypot). A valid email is stored in the
// LEADS KV namespace as {email, ts, page, ua}; a filled honeypot gets a normal-looking success and nothing is stored.
// JSON callers get {ok, pdf, page}; a plain form post (no JS) gets a 303 to the checklist page.
const CHECKLIST_PAGE = "/resources/month-end-red-flags/";
const CHECKLIST_PDF = "/resources/month-end-red-flags.pdf";
const EMAIL_RE = /^[^\s@<>()[\]\,;:"]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;

async function checklist(req, env, url) {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405, headers: { Allow: "POST", "Strict-Transport-Security": HSTS } });
  const json = /application\/json/i.test(req.headers.get("Content-Type") || "");
  let f = {};
  try {
    if (json) f = await req.json();
    else f = Object.fromEntries(await req.formData());
  } catch (e) { f = {}; }
  const ok = () => json
    ? new Response(JSON.stringify({ ok: true, pdf: CHECKLIST_PDF, page: CHECKLIST_PAGE }), { status: 200, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "Strict-Transport-Security": HSTS } })
    : new Response(null, { status: 303, headers: { Location: new URL(CHECKLIST_PAGE, url).toString(), "Strict-Transport-Security": HSTS } });
  if (String(f.website || "").trim()) return ok();                  // honeypot filled: a bot. Pretend success, store nothing.
  const email = String(f.email || "").trim().toLowerCase();
  if (email.length > 254 || !EMAIL_RE.test(email)) {
    return json
      ? new Response(JSON.stringify({ ok: false, error: "Enter a valid email address." }), { status: 400, headers: { "Content-Type": "application/json", "Strict-Transport-Security": HSTS } })
      : new Response("Enter a valid email address.", { status: 400, headers: { "Content-Type": "text/plain; charset=utf-8", "Strict-Transport-Security": HSTS } });
  }
  const ts = new Date().toISOString();
  const page = String(f.page || "").slice(0, 200);
  const ua = (req.headers.get("User-Agent") || "").slice(0, 300);
  if (env.LEADS) await env.LEADS.put(`lead:${ts}:${email}`, JSON.stringify({ email, ts, page, ua }));
  return ok();
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.hostname === "www." + APEX) {
      url.hostname = APEX;
      return new Response(null, { status: 301, headers: { Location: url.toString(), "Strict-Transport-Security": HSTS } });
    }
    if (url.pathname === "/api/checklist") return checklist(req, env, url);
    const get = req.method === "GET" || req.method === "HEAD";
    if (get && REDIRECTS[url.pathname]) {
      return new Response(null, { status: 301, headers: { Location: new URL(REDIRECTS[url.pathname] + url.search, url).toString(), "Strict-Transport-Security": HSTS } });
    }
    // Search engine ownership files: served at their exact .html path (the assets would redirect "x.html" to "x").
    if (get && /^\/google[0-9a-f]+\.html$/.test(url.pathname)) {
      const f = await env.ASSETS.fetch(new Request(new URL(url.pathname.replace(/\.html$/, ""), url), req));
      if (f.ok) return finish(f, { "Content-Type": "text/html; charset=utf-8" });
    }
    if (get && url.pathname.startsWith("/video/")) return serveVideo(req, env);

    const md = get && wantsMarkdown(req, url);
    const mdPath = mdFor(url.pathname);
    if (md && mdPath) {
      const res = await env.ASSETS.fetch(new Request(new URL(mdPath, url), req));
      if (res.ok) return finish(res, { "Content-Type": "text/markdown; charset=utf-8", "Vary": "Accept", "Link": link(mdPath) });
    }
    const res = await env.ASSETS.fetch(req);
    if (res.status === 307 || res.status === 302) {          // the assets' trailing-slash and /index.html redirects
      const loc = res.headers.get("Location");
      if (loc) return new Response(null, { status: 301, headers: { Location: new URL(loc, url).toString(), "Strict-Transport-Security": HSTS } });
    }
    if (md && res.status === 404) {
      return new Response(NOT_FOUND_MD, { status: 404, headers: { "Content-Type": "text/markdown; charset=utf-8", "Vary": "Accept", "Strict-Transport-Security": HSTS } });
    }
    const extra = {};
    if (mdPath || res.status === 404) extra.Vary = "Accept";
    if (/^text\/html/i.test(res.headers.get("Content-Type") || "")) extra.Link = link(mdPath);
    if (url.pathname.startsWith("/img/")) extra["Cache-Control"] = MEDIA_CACHE;
    return finish(res, extra);
  },
};
