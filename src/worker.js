// get-lumic.com: static assets, plus markdown for AI agents.
// A request that asks for text/markdown (Accept header) gets the markdown copy of the page: "/" -> /index.md.
// A markdown request for a missing page gets a short markdown 404. Everything else is the static site, unchanged.
const MD_PAGES = { "/": "/index.md", "/index.html": "/index.md" };
const NOT_FOUND_MD = `# Page not found

This page is not on get-lumic.com.

- Home: https://get-lumic.com/ (markdown: https://get-lumic.com/index.md)
- For AI agents: https://get-lumic.com/llms.txt
- Contact: hello@get-lumic.com
`;

function wantsMarkdown(req) {
  return /\btext\/markdown\b/i.test(req.headers.get("Accept") || "");
}

// Films: static assets answer a byte-range request with the whole file (200), and iPhone Safari will not play a video
// that way. So /video/* comes through here and a Range request gets 206 Partial Content with only the bytes asked for.
const RANGE = /^bytes=(\d*)-(\d*)$/;

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

async function serveVideo(req, env) {
  const range = req.headers.get("Range");
  const plain = new Headers(req.headers);
  plain.delete("Range");
  const res = await env.ASSETS.fetch(new Request(req.url, { method: "GET", headers: plain }));
  if (!res.ok) return res;
  const h = new Headers(res.headers);
  h.set("Accept-Ranges", "bytes");
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
    return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}`, "Accept-Ranges": "bytes" } });
  }
  h.set("Content-Range", `bytes ${start}-${end}/${size}`);
  h.set("Content-Length", String(end - start + 1));
  if (req.method === "HEAD") { drop(); return new Response(null, { status: 206, headers: h }); }
  const body = buf ? buf.subarray(start, end + 1) : sliceStream(res.body, start, end);
  return new Response(body, { status: 206, headers: h });
}

function withVary(res) {
  const r = new Response(res.body, res);
  r.headers.append("Vary", "Accept");
  return r;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/video/") && (req.method === "GET" || req.method === "HEAD")) return serveVideo(req, env);
    const md = wantsMarkdown(req);
    if (md && MD_PAGES[url.pathname]) {
      const res = await env.ASSETS.fetch(new Request(new URL(MD_PAGES[url.pathname], url), req));
      const r = new Response(res.body, res);
      r.headers.set("Content-Type", "text/markdown; charset=utf-8");
      r.headers.append("Vary", "Accept");
      return r;
    }
    const res = await env.ASSETS.fetch(req);
    if (md && res.status === 404) {
      return new Response(NOT_FOUND_MD, { status: 404, headers: { "Content-Type": "text/markdown; charset=utf-8", "Vary": "Accept" } });
    }
    if (MD_PAGES[url.pathname] || res.status === 404) return withVary(res);
    return res;
  },
};
