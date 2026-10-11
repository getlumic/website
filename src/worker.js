// get-lumic.com: the static site, plus a thin layer for agents, films and headers.
// - Markdown for AI agents: "/" with Accept: text/markdown, or "/?mode=agent", returns /index.md. A markdown request for a
//   missing page gets a short markdown 404.
// - Films: a byte-range request on /video/* gets 206 Partial Content (static assets return the whole file, and iPhone
//   Safari will not play a video that way).
// - Redirects: www.get-lumic.com -> get-lumic.com, and the assets' own 307s (/index.html, /privacy) become 301s.
// - Headers: HSTS everywhere, a Link header on pages (llms.txt and the markdown copy), a day of browser cache on films
//   and images (their file names are reused when a film is replaced, so not longer than that).
const APEX = "get-lumic.com";
const MD_PAGES = { "/": "/index.md", "/index.html": "/index.md" };
const NOT_FOUND_MD = `# Page not found

This page is not on get-lumic.com.

- Home: https://get-lumic.com/ (markdown: https://get-lumic.com/index.md)
- For AI agents: https://get-lumic.com/llms.txt
- Contact: hello@get-lumic.com
`;
const HSTS = "max-age=31536000";
const LINK = '</llms.txt>; rel="describedby"; type="text/plain", </index.md>; rel="alternate"; type="text/markdown"';
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

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.hostname === "www." + APEX) {
      url.hostname = APEX;
      return new Response(null, { status: 301, headers: { Location: url.toString(), "Strict-Transport-Security": HSTS } });
    }
    const get = req.method === "GET" || req.method === "HEAD";
    if (get && url.pathname.startsWith("/video/")) return serveVideo(req, env);

    const md = get && wantsMarkdown(req, url);
    if (md && MD_PAGES[url.pathname]) {
      const res = await env.ASSETS.fetch(new Request(new URL(MD_PAGES[url.pathname], url), req));
      return finish(res, { "Content-Type": "text/markdown; charset=utf-8", "Vary": "Accept", "Link": LINK });
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
    if (MD_PAGES[url.pathname] || res.status === 404) extra.Vary = "Accept";
    if (/^text\/html/i.test(res.headers.get("Content-Type") || "")) extra.Link = LINK;
    if (url.pathname.startsWith("/img/")) extra["Cache-Control"] = MEDIA_CACHE;
    return finish(res, extra);
  },
};
