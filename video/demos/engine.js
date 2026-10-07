/* lumic demo-film engine. A film page sets window.FILM, loads this file, and gets a deterministic
   1920x1080 film: title card, a browser window with real dashboard screens moved by a code camera,
   a cursor with click ripples, highlight rings, captions and an end card. window.seek(t) draws time t.
   Screens: real lumic dashboards running on made-up data, captured with cua-driver (1423x815 CSS px). */
(function () {
  const F = window.FILM, SW = F.sw || 1423, SH = F.sh || 815;
  const css = `
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden;background:#f6f6fb}
body{font-family:"Instrument Sans",sans-serif;color:#0f172a;-webkit-font-smoothing:antialiased}
em{font-family:"Instrument Serif",serif;font-weight:400;font-style:italic;color:#5e5ce6;letter-spacing:-.005em}
.bg{position:absolute;inset:0;background:radial-gradient(ellipse 60% 55% at 50% 42%,rgba(94,92,230,.13),transparent 70%),#f6f6fb}
.dots{position:absolute;inset:0;background-image:radial-gradient(rgba(94,92,230,.16) 1.3px,transparent 1.5px);background-size:28px 28px;
  -webkit-mask-image:radial-gradient(ellipse 75% 70% at 50% 45%,#000 0%,transparent 75%)}
.title,.end{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.pill{display:inline-flex;align-items:center;gap:10px;font-size:20px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#5e5ce6;
  padding:10px 20px;border-radius:999px;background:#fff;box-shadow:0 0 0 1px rgba(94,92,230,.22)}
.pill i{width:8px;height:8px;border-radius:50%;background:#5e5ce6}
.title h1{margin-top:30px;font-size:96px;font-weight:500;letter-spacing:-.035em;line-height:1.04}
.win{position:absolute;left:${(1920 - SW) / 2}px;top:${(1080 - SH - 40) / 2 - 6}px;width:${SW}px;height:${SH + 40}px;border-radius:16px;overflow:hidden;background:#fff;
  box-shadow:0 0 0 1px rgba(15,23,42,.08),0 40px 90px -20px rgba(15,23,42,.28),0 12px 30px -10px rgba(94,92,230,.18)}
.bar{position:absolute;left:0;right:0;top:0;height:40px;background:#fbfbfd;border-bottom:1px solid #e9ebf2;display:flex;align-items:center;padding:0 18px}
.bar b{width:12px;height:12px;border-radius:50%;background:#e2e5ee;margin-right:8px}
.bar span{position:absolute;left:0;right:0;text-align:center;font-size:15px;color:#64748b;font-weight:500}
.bar .tag{position:absolute;right:16px;font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#5e5ce6;background:#eeedfd;padding:4px 10px;border-radius:999px}
.view{position:absolute;left:0;top:40px;width:${SW}px;height:${SH}px;overflow:hidden;background:#f8fafc}
.stage{position:absolute;left:0;top:0;width:${SW}px;height:${SH}px;transform-origin:0 0}
.stage img{position:absolute;left:0;top:0;width:${SW}px;height:${SH}px}
.ring{position:absolute;border-radius:10px;box-shadow:0 0 0 3px #5e5ce6,0 0 0 9px rgba(94,92,230,.18);opacity:0}
.cursor{position:absolute;left:0;top:0;width:34px;height:34px;opacity:0;filter:drop-shadow(0 3px 6px rgba(15,23,42,.35))}
.ripple{position:absolute;width:64px;height:64px;margin:-32px 0 0 -32px;border-radius:50%;border:3px solid #5e5ce6;opacity:0}
.cap{position:absolute;left:0;right:0;bottom:34px;display:flex;justify-content:center;pointer-events:none}
.cap div{display:inline-flex;align-items:center;gap:14px;background:rgba(15,23,42,.92);color:#fff;font-size:28px;font-weight:500;letter-spacing:-.01em;
  padding:16px 30px;border-radius:999px;box-shadow:0 18px 40px -12px rgba(15,23,42,.5);opacity:0}
.cap div i{width:10px;height:10px;border-radius:50%;background:#8b8af0;box-shadow:0 0 12px 2px rgba(139,138,240,.7)}
.end{opacity:0}
.end h2{font-size:92px;font-weight:500;letter-spacing:-.035em;line-height:1.05}
.end .wm{height:46px;margin-top:56px}
.end .url{margin-top:18px;font-size:20px;font-weight:600;letter-spacing:.2em;color:#64748b}`;
  document.head.insertAdjacentHTML("beforeend",
    '<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Instrument+Serif:ital@1&display=swap" rel="stylesheet">' +
    `<style>${css}</style>`);
  const base = F.base || `../shots/${F.name}/`;
  document.body.innerHTML = `
<div class="bg"></div><div class="dots"></div>
<div class="title" id="title"><div class="pill"><i></i>${F.kicker}</div><h1>${F.title}</h1></div>
<div class="win" id="win">
  <div class="bar"><b></b><b></b><b></b><span>${F.bar}</span><span class="tag" style="left:auto">Sample data</span></div>
  <div class="view">
    <div class="stage" id="stage">
      ${F.screens.map((s, i) => `<img id="s${i}" src="${base}${s.src}" alt="">`).join("")}
      ${(F.rings || []).map((r, i) => `<div class="ring" id="ring${i}" style="left:${r.x}px;top:${r.y}px;width:${r.w}px;height:${r.h}px"></div>`).join("")}
    </div>
    <div class="ripple" id="rip"></div>
    <svg class="cursor" id="cur" viewBox="0 0 24 24"><path d="M5 2.5v17.2l4.6-4.3 2.9 6.6 2.7-1.2-2.9-6.5H19z" fill="#0f172a" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>
  </div>
</div>
${F.captions.map((c, i) => `<div class="cap"><div id="cap${i}"><i></i>${c.text}</div></div>`).join("")}
<div class="end" id="end"><h2>${F.end}</h2><img class="wm" src="${F.wordmark || "../../../public/wordmark.svg"}" alt="lumic"><div class="url">GET-LUMIC.COM</div></div>`;

  const D = F.duration || 23;
  const $ = id => document.getElementById(id);
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const P = (t, a, b) => clamp((t - a) / (b - a), 0, 1);
  const io = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  const out = x => 1 - Math.pow(1 - x, 3);
  const fade = (t, a, b, c, d) => out(P(t, a, b)) * (1 - io(P(t, c, d)));
  function keyed(keys, t) {
    let i = 0;
    while (i < keys.length - 2 && t >= keys[i + 1][0]) i++;
    const a = keys[i], b = keys[i + 1], u = io(P(t, a[0], b[0]));
    return a.slice(1).map((v, k) => k === 2 && a.length === 4 ? Math.exp(Math.log(v) + (Math.log(b[k + 1]) - Math.log(v)) * u) : v + (b[k + 1] - v) * u);
  }
  function camera(t) {
    const [cx, cy, z] = keyed(F.cam, t);
    return { tx: clamp(SW / 2 - cx * z, SW - SW * z, 0), ty: clamp(SH / 2 - cy * z, SH - SH * z, 0), z };
  }
  const T = Object.assign({ titleOut: 2.0, winIn: 2.2, winOut: 19.0, endIn: 19.7 }, F.times || {});

  function draw(t) {
    $("title").style.opacity = fade(t, 0, .6, T.titleOut, T.titleOut + .6);
    $("title").style.transform = `translateY(${(1 - out(P(t, 0, .9))) * 24 - io(P(t, T.titleOut, T.titleOut + .7)) * 40}px)`;
    const wIn = out(P(t, T.winIn, T.winIn + 1)), wOut = io(P(t, T.winOut, T.winOut + 1));
    $("win").style.opacity = wIn * (1 - wOut);
    $("win").style.transform = `translateY(${(1 - wIn) * 70 + wOut * 40}px) scale(${(.94 + .06 * wIn) * (1 - .04 * wOut)})`;
    $("end").style.opacity = fade(t, T.endIn, T.endIn + .9, D - .7, D);
    $("end").style.transform = `translateY(${(1 - out(P(t, T.endIn, T.endIn + 1.1))) * 24}px)`;
    // screens: each fades (and optionally slides, to read as a scroll) in over the previous one
    F.screens.forEach((s, i) => {
      if (!i) return;
      const u = io(P(t, s.at, s.at + (s.dur || .4)));
      const el = $("s" + i);
      el.style.opacity = s.slide ? Math.min(1, u * 1.6) : u;
      el.style.transform = s.slide ? `translateY(${(1 - u) * s.slide}px)` : "";
      if (s.slide) $("s" + (i - 1)).style.transform = `translateY(${-u * s.slide}px)`;
    });
    const c = camera(t);
    $("stage").style.transform = `translate(${c.tx}px,${c.ty}px) scale(${c.z})`;
    (F.rings || []).forEach((r, i) => { $("ring" + i).style.opacity = fade(t, r.a, r.a + .4, r.b - .3, r.b); });
    const cur = F.cursor;
    if (cur) {
      const [x, y] = keyed(cur.keys, t), sx = c.tx + x * c.z, sy = c.ty + y * c.z;
      const clicks = F.clicks || [];
      const press = clicks.reduce((m, k) => Math.max(m, 1 - Math.abs(t - k - .05) / .12), 0);
      $("cur").style.opacity = fade(t, cur.show[0], cur.show[0] + .4, cur.show[1] - .4, cur.show[1]);
      $("cur").style.transform = `translate(${sx - 8}px,${sy - 5}px) scale(${1 - .14 * Math.max(0, press)})`;
      const last = clicks.filter(k => t >= k).pop(), rip = $("rip");
      if (last !== undefined && t - last < .55) {
        const u = (t - last) / .55;
        rip.style.opacity = (1 - u) * .9;
        rip.style.transform = `translate(${sx}px,${sy}px) scale(${.3 + out(u) * .9})`;
      } else rip.style.opacity = 0;
    }
    F.captions.forEach((cp, i) => {
      const v = fade(t, cp.a, cp.a + .45, cp.b - .35, cp.b);
      $("cap" + i).style.opacity = v;
      $("cap" + i).style.transform = `translateY(${(1 - v) * 14}px)`;
    });
  }
  window.DURATION = D;
  window.POSTER = F.poster || 6;
  window.seek = t => { draw(t); return document.fonts.ready; };
  window.reelReady = document.fonts.ready
    .then(() => Promise.all([...document.images].map(im => im.decode())))
    .then(() => { draw(0); return true; });
  if (!location.search.includes("render")) {
    const t0 = performance.now();
    window.reelReady.then(() => (function tick() { draw(((performance.now() - t0) / 1000) % D); requestAnimationFrame(tick); })());
  }
})();
