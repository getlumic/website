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

function withVary(res) {
  const r = new Response(res.body, res);
  r.headers.append("Vary", "Accept");
  return r;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
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
