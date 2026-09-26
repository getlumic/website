"""Derive reel-vertical.html (1080x1920, Instagram Stories) from reel.html (1920x1080).
Same timeline, same engine; scenes re-composed for a tall screen. Every replacement is asserted,
so a change to reel.html that breaks the mapping fails loudly instead of rendering a wrong frame.
Usage: python3 video/reel/make_vertical.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = (HERE / "reel.html").read_text()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, f"expected {count}x, found {n}: {old[:90]!r}"
    s = s.replace(old, new)


# ---------------------------------------------------------------- CSS
rep("lumic reel. 1920x1080, 40 s.", "lumic reel, VERTICAL cut for Instagram Stories. 1080x1920, 40 s. Generated from reel.html by make_vertical.py; edit reel.html, then re-run.")
rep("#stage{position:absolute;left:0;top:0;width:1920px;height:1080px;", "#stage{position:absolute;left:0;top:0;width:1080px;height:1920px;")
rep(".layer{position:absolute;left:0;top:0;width:1920px;height:1080px}", ".layer{position:absolute;left:0;top:0;width:1080px;height:1920px}\n#zoomer{position:absolute;left:0;top:0;width:831px;height:1477px;zoom:1.3}")
rep("#dots{position:absolute;left:-60px;top:-60px;width:2040px;height:1200px;", "#dots{position:absolute;left:-60px;top:-60px;width:1200px;height:2040px;")
rep(".ln.center{left:0;width:1920px;text-align:center}", ".ln.center{left:0;width:1080px;text-align:center}")
rep(".h{font-size:76px;", ".h{font-size:84px;")
rep(".hx{font-size:84px;", ".hx{font-size:80px;")
rep(".sub{font-size:30px;", ".sub{font-size:32px;")
rep(".kick{font-size:21px;", ".kick{font-size:23px;")
rep("#ddots{position:absolute;left:0;top:0;width:1920px;height:1080px;", "#ddots{position:absolute;left:0;top:0;width:1080px;height:1920px;")
rep("radial-gradient(60% 60% at 60% 50%,#000 10%,transparent 75%);mask-image:radial-gradient(60% 60% at 60% 50%,#000 10%,transparent 75%)}",
    "radial-gradient(70% 50% at 50% 60%,#000 10%,transparent 75%);mask-image:radial-gradient(70% 50% at 50% 60%,#000 10%,transparent 75%)}")

# ---------------------------------------------------------------- camera + zoomed composition space (design px x 1.3)
rep('<div id="cam" class="layer">\n', '<div id="cam" class="layer">\n    <div id="zoomer">\n')
rep("      </div>\n    </div>\n\n    <!-- text (outside the camera so type stays rock-steady) -->",
    "      </div>\n    </div>\n    </div>\n\n    <!-- text (outside the camera so type stays rock-steady) -->")

# scene 4 (design coords inside the zoomer)
rep('<path id="drillP" d="M1643,771 V818 H1402"', '<path id="drillP" d="M661,1201 V1226 H442"')
rep('<circle id="drillD" cx="1643" cy="771"', '<circle id="drillD" cx="661" cy="1201"')
rep('<div id="cardC" class="card" style="left:930px;top:648px;', '<div id="cardC" class="card" style="left:40px;top:1010px;')
rep('<div id="cardB" class="card" style="left:1440px;top:470px;', '<div id="cardB" class="card" style="left:455px;top:900px;')
rep('<div id="panel" class="card" style="left:900px;top:652px;width:500px;', '<div id="panel" class="card" style="left:30px;top:1030px;width:410px;')
rep('.row .nm{font-size:20px;color:var(--ink);font-weight:500;width:150px}', '.row .nm{font-size:20px;color:var(--ink);font-weight:500;width:118px}')
rep('<span class="rb" style="width:150px">', '<span class="rb" style="width:112px">')
rep('<span class="rb" style="width:97px">', '<span class="rb" style="width:72px">')
rep('<span class="rb" style="width:51px">', '<span class="rb" style="width:38px">')
rep('<div id="cap4" class="cap" style="left:1580px;top:900px">', '<div id="cap4" class="cap" style="left:604px;top:1244px">')
# scene 5
rep('<div id="cap5" class="cap" style="left:1586px;top:742px">', '<div id="cap5" class="cap" style="left:632px;top:1194px">')
rep('<div id="entry" class="card" style="left:1330px;top:290px;', '<div id="entry" class="card" style="left:372px;top:760px;')
# scene 6: hub on top-left, three nodes stacked right, elbow flows from the hub's bottom
rep('<path id="fp0" d="M690,650 C930,650 960,481 1200,481"', '<path id="fp0" d="M205,770 C205,849 290,849 380,849"')
rep('<path id="fp1" d="M690,650 C930,650 960,651 1200,651"', '<path id="fp1" d="M205,770 C205,979 290,979 380,979"')
rep('<path id="fp2" d="M690,650 C930,650 960,821 1200,821"', '<path id="fp2" d="M205,770 C205,1109 290,1109 380,1109"')
rep('<div class="node" id="n0" style="left:1200px;top:432px">', '<div class="node" id="n0" style="left:380px;top:800px">')
rep('<div class="node" id="n1" style="left:1200px;top:602px">', '<div class="node" id="n1" style="left:380px;top:930px">')
rep('<div class="node" id="n2" style="left:1200px;top:772px">', '<div class="node" id="n2" style="left:380px;top:1060px">')

# ---------------------------------------------------------------- text blocks (top third, re-broken for a tall screen)
a = s.index('    <div id="x2" class="layer">')
b = s.index('    <!-- end card -->')
s = s[:a] + '''    <div id="x2" class="layer">
      <div class="ln hx" id="t2a" style="left:64px;top:440px">Your ERP holds the data.</div>
      <div class="ln hx" id="t2b" style="left:64px;top:560px">Your team still does</div>
      <div class="ln hx" id="t2c" style="left:64px;top:648px">the work <em>by hand.</em></div>
    </div>
    <div id="x4" class="layer">
      <span class="kdot" id="kd4" style="left:64px;top:336px"></span><div class="ln kick" id="k4" style="left:94px;top:330px">Custom dashboards</div>
      <div class="ln h" id="t4a" style="left:64px;top:380px">Live numbers,</div>
      <div class="ln h" id="t4b" style="left:64px;top:470px">read straight from</div>
      <div class="ln h" id="t4c" style="left:64px;top:560px"><em>your ERP.</em></div>
      <div class="ln sub" id="t4s" style="left:64px;top:690px;width:900px">Sales, margin, cash, AR, and inventory, built around the questions an owner asks.</div>
    </div>
    <div id="x5" class="layer">
      <span class="kdot" id="kd5" style="left:64px;top:336px"></span><div class="ln kick" id="k5" style="left:94px;top:330px">AI agents</div>
      <div class="ln h" id="t5a" style="left:64px;top:380px">Invoices in.</div>
      <div class="ln h" id="t5b" style="left:64px;top:470px">Entries prepared.</div>
      <div class="ln h" id="t5c" style="left:64px;top:560px"><em>You approve.</em></div>
      <div class="ln sub" id="t5s" style="left:64px;top:690px;width:900px">Every entry lands unposted. Nothing posts on its own.</div>
    </div>
    <div id="x6" class="layer">
      <span class="kdot" id="kd6" style="left:64px;top:336px"></span><div class="ln kick" id="k6" style="left:94px;top:330px">Workflow automation</div>
      <div class="ln h" id="t6a" style="left:64px;top:380px">The manual steps,</div>
      <div class="ln h" id="t6b" style="left:64px;top:470px"><em>replaced.</em></div>
      <div class="ln sub" id="t6s" style="left:64px;top:600px;width:920px">Statements sent, POs created, reports delivered on schedule.</div>
    </div>

''' + s[b:]

# end card: wordmark, three-line slogan, URL
rep('''      <div class="ln center" id="t9a" style="top:600px;font-size:44px;letter-spacing:-.015em;color:var(--text);font-weight:400">Custom dashboards + AI agents on the ERP your business <em>already runs.</em></div>
      <div class="ln center" id="t9b" style="top:696px;font-size:21px;letter-spacing:.2em;color:var(--mut);font-weight:600">GET-LUMIC.COM</div>''',
    '''      <div class="ln center" id="t9a" style="top:1000px;font-size:50px;letter-spacing:-.015em;color:var(--text);font-weight:400">Custom dashboards + AI agents</div>
      <div class="ln center" id="t9c" style="top:1066px;font-size:50px;letter-spacing:-.015em;color:var(--text);font-weight:400">on the ERP your business</div>
      <div class="ln center" id="t9e" style="top:1132px;font-size:50px;letter-spacing:-.015em;color:var(--text);font-weight:400"><em>already runs.</em></div>
      <div class="ln center" id="t9b" style="top:1262px;font-size:23px;letter-spacing:.2em;color:var(--mut);font-weight:600">GET-LUMIC.COM</div>''')

rep('<svg id="rs" class="abs" width="1920" height="1080" viewBox="0 0 1920 1080">', '<svg id="rs" class="abs" width="1080" height="1920" viewBox="0 0 1080 1920">')
rep('<circle id="r1" cx="960" cy="540"', '<circle id="r1" cx="540" cy="960"')
rep('<circle id="r2" cx="960" cy="540"', '<circle id="r2" cx="540" cy="960"')
rep('<div class="wmk dark" id="wmD" style="font-size:36px">', '<div class="wmk dark" id="wmD" style="font-size:44px">')

# ---------------------------------------------------------------- dark scene 7: rings below the text
rep('<svg id="rings" class="abs" width="1920" height="1080" viewBox="0 0 1920 1080">', '<svg id="rings" class="abs" width="1080" height="1920" viewBox="0 0 1080 1920">')
rep('<circle cx="1380" cy="540" r="380"', '<circle cx="540" cy="1180" r="410"')
rep('<circle id="rgD" cx="1380" cy="540" r="306"', '<circle id="rgD" cx="540" cy="1180" r="330"')
rep('<circle cx="1380" cy="540" r="232"', '<circle cx="540" cy="1180" r="250"')
rep('<span class="kdot dk" id="kd7" style="left:150px;top:297px"></span><div class="ln kick dkick" id="k7" style="left:180px;top:292px">',
    '<span class="kdot dk" id="kd7" style="left:64px;top:336px"></span><div class="ln kick dkick" id="k7" style="left:94px;top:330px">')
rep('<div class="ln h dkl" id="t7a" style="left:150px;top:336px">', '<div class="ln h dkl" id="t7a" style="left:64px;top:380px">')
rep('<div class="ln h dkl" id="t7b" style="left:150px;top:418px">', '<div class="ln h dkl" id="t7b" style="left:64px;top:470px">')
rep('<div class="ln sub dsub" id="t7s" style="left:150px;top:560px;width:620px">', '<div class="ln sub dsub" id="t7s" style="left:64px;top:600px;width:900px">')

# ---------------------------------------------------------------- dark scene 8: the connector as a vertical chain
rep('<svg id="conn" class="abs" width="1920" height="1080" viewBox="0 0 1920 1080">', '<svg id="conn" class="abs" width="1080" height="1920" viewBox="0 0 1080 1920">')
rep('<line id="cln0" x1="755" y1="560" x2="870" y2="560"', '<line id="cln0" x1="540" y1="1024" x2="540" y2="1119"')
rep('<line id="cln1" x1="1050" y1="560" x2="1165" y2="560"', '<line id="cln1" x1="540" y1="1181" x2="540" y2="1276"')
rep('<div class="dpill" id="soon" style="left:0;top:214px">', '<div class="dpill" id="soon" style="left:0;top:548px">')
rep('<div class="ln center dkl" id="t8a" style="top:272px;font-size:74px;letter-spacing:-.028em">Connect any AI to <em>your ERP and workflows.</em></div>',
    '<div class="ln center dkl" id="t8a" style="top:618px;font-size:84px;letter-spacing:-.028em">Connect any AI to</div>\n      <div class="ln center dkl" id="t8c" style="top:708px;font-size:84px;letter-spacing:-.028em"><em>your ERP and workflows.</em></div>')
rep('<div class="dcard" id="dcA" style="left:405px;top:498px">', '<div class="dcard" id="dcA" style="left:365px;top:898px">')
rep('<div class="dcard" id="dcS" style="left:1165px;top:498px">', '<div class="dcard" id="dcS" style="left:365px;top:1278px">')
rep('<div class="dtag" id="dtag" style="left:0;top:648px">', '<div class="dtag" id="dtag" style="left:0;top:1428px">')
rep('<div class="ln center dsub" id="t8b" style="top:760px;font-size:23px;font-weight:400">', '<div class="ln center dsub" id="t8b" style="top:1510px;font-size:26px;font-weight:400">')
rep('<svg id="irisR" class="abs" width="1920" height="1080" viewBox="0 0 1920 1080">', '<svg id="irisR" class="abs" width="1080" height="1920" viewBox="0 0 1080 1920">')

# ---------------------------------------------------------------- JS: layout constants
rep("const GRID = { w: 150, h: 54, gap: 8, cols: 6, rows: 4 };", "const ZOOM = 1.3;                                 // composition space: design px x 1.3 = screen px\nconst GRID = { w: 118, h: 44, gap: 6, cols: 6, rows: 4 };")
rep("GRID.left = 960 - (GRID.cols * GRID.w + (GRID.cols - 1) * GRID.gap) / 2;", "GRID.left = 415.5 - (GRID.cols * GRID.w + (GRID.cols - 1) * GRID.gap) / 2;")
rep("GRID.top = 540 - (GRID.rows * GRID.h + (GRID.rows - 1) * GRID.gap) / 2;", "GRID.top = 885 - (GRID.rows * GRID.h + (GRID.rows - 1) * GRID.gap) / 2;")
rep("const CC = { x: 460, y: 290, w: 1000, h: 520 };  // card at center (scene 3)", "const CC = { x: 35.5, y: 665, w: 760, h: 440 };   // card at center (scene 3)")
rep("const CA = { x: 880, y: 200, w: 640, h: 400 };   // card A (scene 4)", "const CA = { x: 60, y: 640, w: 640, h: 400 };     // card A (scene 4)")
a = s.index("const FR = [")
b = s.index("];", a) + 2
s = s[:a] + """const FR = [
  { x: 470, y: 610, d: 1.0, r: -3, k: 'grid', v: [['Q3', '4,210', '3,982'], ['Q4', '5,006', '4,410']] },
  { x: 40, y: 640, d: .75, r: 2.5, k: 'chip', v: 'Export_0925.csv' },
  { x: 380, y: 722, d: 1.15, r: 1.5, k: 'fx', v: '=VLOOKUP(B2,Sheet3!A:F,4,0)' },
  { x: 60, y: 745, d: .9, r: -4, k: 'err', v: '#REF!' },
  { x: 170, y: 832, d: .8, r: -1.5, k: 'hdr', v: ['A', 'B', 'C', 'D', 'E'] },
  { x: 500, y: 872, d: 1.1, r: 3, k: 'chip', v: 'AR_aging_final_v3.xlsx' },
  { x: 60, y: 952, d: 1.2, r: -2.5, k: 'grid', v: [['Net 30', '12,480', '—'], ['Net 60', '8,215', 'N/A']] },
  { x: 640, y: 992, d: .85, r: 2, k: 'keys', v: ['Ctrl', 'C'] },
  { x: 430, y: 1062, d: .9, r: 2.5, k: 'chip', v: 'Invoice_4471.pdf' },
  { x: 80, y: 1112, d: 1.05, r: -3, k: 'fx', v: '=SUM(C2:C48)' },
  { x: 720, y: 1120, d: .7, r: -2, k: 'err', v: 'N/A' },
  { x: 300, y: 1180, d: .95, r: 1, k: 'keys', v: ['Ctrl', 'V'] },
  { x: 540, y: 1192, d: .8, r: 3, k: 'chip', v: 'PO_log_2026.xlsx' },
  { x: 40, y: 1236, d: .7, r: -2, k: 'grid', v: [['Jan', '41,200', '38,900']] }
];""" + s[b:]
rep("CELLS.map((c, i) => [i, Math.hypot(c.gx - 900, c.gy - 520)])", "CELLS.map((c, i) => [i, Math.hypot(c.gx - 415, c.gy - 885)])")
rep("const x = 1380 + 232 * Math.cos(a * Math.PI / 180), y = 540 + 232 * Math.sin(a * Math.PI / 180);", "const x = 540 + 250 * Math.cos(a * Math.PI / 180), y = 1180 + 250 * Math.sin(a * Math.PI / 180);")

# text line registry (new ids for the re-broken lines)
rep("line('k6', 25.45, 99, .04); line('t6a', 25.55, 99); line('t6s', 26.15, 99, .02, .9);",
    "line('k6', 25.45, 99, .04); line('t6a', 25.55, 99); line('t6b', 25.7, 99, .06, 1.05); line('t6s', 26.15, 99, .02, .9);")
rep("line('t8a', 34.35, 36.15, .05); line('t8b', 35.45, 36.2, .02, .9);",
    "line('t8a', 34.35, 36.15, .05); line('t8c', 34.5, 36.18, .05, 1.05); line('t8b', 35.45, 36.2, .02, .9);")
rep("line('t9a', 38.45, 99, .026, .95); line('t9b', 38.95, 99, .01, .8);",
    "line('t9a', 38.4, 99, .03, .95); line('t9c', 38.52, 99, .03, .95); line('t9e', 38.64, 99, .05, .9); line('t9b', 38.95, 99, .01, .8);")

# measure(): scene 1 centre, end lockup, bug
rep("WM.x0 = 960 - WM.w / 2; WM.y0 = 626 - WM.h / 2;", "WM.x0 = 540 - WM.w / 2; WM.y0 = 1046 - WM.h / 2;")
rep("WE.x0 = 960 - r1.w / 2; WE.y0 = 462 - r1.h / 2;", "WE.x0 = 540 - r1.w / 2; WE.y0 = 820 - r1.h / 2;")
rep("WE.ox = 960 - WE.dot.x; WE.oy = 560 - WE.dot.y;", "WE.ox = 540 - WE.dot.x; WE.oy = 1150 - WE.dot.y;")
rep("WM.bx = 96; WM.by = 46; WM.bs = 36 / 200;", "WM.bx = 64; WM.by = 168; WM.bs = 44 / 200;")

# orb
rep("const sx = 960, sy = 540, ex = WM.dot.x, ey = WM.dot.y;", "const sx = 540, sy = 960, ex = WM.dot.x, ey = WM.dot.y;")
rep("return { x: 960, y: 560, s: lerp(base, WE.dot.w / 48, g), o: 1, c,", "return { x: 540, y: 1150, s: lerp(base, WE.dot.w / 48, g), o: 1, c,")

# scene 1
rep("const fl = $('flare'); const fw = 1000 * tw(t, .03, .6, E.outExpo);", "const fl = $('flare'); const fw = 820 * tw(t, .03, .6, E.outExpo);")
rep("fl.style.width = f2(fw) + 'px'; tr(fl, 960 - fw / 2, 540);", "fl.style.width = f2(fw) + 'px'; tr(fl, 540 - fw / 2, 960);")
# scene 3 ripple centre
rep("const d = Math.hypot(c.gx + GRID.w / 2 - 960, c.gy + GRID.h / 2 - 540);", "const d = Math.hypot(c.gx + GRID.w / 2 - 415, c.gy + GRID.h / 2 - 885);")
# scene 5
rep("const ENV = { x: 930 + 600 * (1 - ar), y: 690 + sink + 110 * ex, r: 9 * (1 - ar) };", "const ENV = { x: 50 + 560 * (1 - ar), y: 1010 + sink + 110 * ex, r: 9 * (1 - ar) };")
rep("const PX = 940, PY = 250;", "const PX = 40, PY = 630;")
rep("box(en, lerp(1330, 360, mv), lerp(290, 590, mv), lerp(440, 330, mv), lerp(420, 120, mv));", "box(en, lerp(372, 40, mv), lerp(760, 650, mv), lerp(440, 330, mv), lerp(420, 120, mv));")
rep("el.style.fontSize = f2(lerp(fsS, fsE, pp)) + 'px';", "el.style.fontSize = f2(lerp(fsS, fsE, pp) * ZOOM) + 'px';")
rep("const x = lerp(1640, tx, m), y = lerp(930, ty, m) + 30 * Math.sin(Math.PI * m);", "const x = lerp(980, tx, m), y = lerp(1700, ty, m) + 30 * Math.sin(Math.PI * m);")
# scene 6
rep("const cx = 1200 + 440 - 22 - 16, cy = [481, 651, 821][i];", "const cx = 380 + 440 - 22 - 16, cy = [849, 979, 1109][i];")
rep("hr.setAttribute('cx', 410); hr.setAttribute('cy', 650);", "hr.setAttribute('cx', 90); hr.setAttribute('cy', 710);")
# dark: irises open on the hub and close on the MCP orb
rep("R = 2300 * p; cx = 410; cy = 650;", "R = 2300 * p; cx = 108; cy = 918;")
rep("R = 2300 * (1 - p); cx = 960; cy = 560;", "R = 2300 * (1 - p); cx = 540; cy = 1150;")
rep("tr(gl, lerp(1380, 960, gp), lerp(540, 560, gp));", "tr(gl, 540, lerp(1180, 1150, gp));")
# scene 7 rings
rep("rg.setAttribute('transform', `translate(1380 540) scale(${s.toFixed(4)}) translate(-1380 -540)`);", "rg.setAttribute('transform', `translate(540 1180) scale(${s.toFixed(4)}) translate(-540 -1180)`);")
rep("$('rgD').setAttribute('transform', `rotate(${(t * 7).toFixed(2)} 1380 540)`);", "$('rgD').setAttribute('transform', `rotate(${(t * 7).toFixed(2)} 540 1180)`);")
rep("const pt = a => [1380 + 232 * Math.cos(a * Math.PI / 180), 540 + 232 * Math.sin(a * Math.PI / 180)];", "const pt = a => [540 + 250 * Math.cos(a * Math.PI / 180), 1180 + 250 * Math.sin(a * Math.PI / 180)];")
rep("const base = [[1380, 540 - 232 - 22], [1380 + 232 + 26, 540], [1380, 540 + 232 + 22], [1380 - 232 - 26, 540]][i];",
    "const base = [[540, 1180 - 250 - 22], [540 + 250 + 26, 1180], [540, 1180 + 250 + 22], [540 - 250 - 26, 1180]][i];")
# scene 8: vertical chain
rep("tr(soon, 960 - sw / 2, 0, Math.max(0, lerp(.85, 1, sIn)));", "tr(soon, 540 - sw / 2, 0, Math.max(0, lerp(.85, 1, sIn)));")
rep("tr(A, -50 * (1 - aIn), 0, 1 - .04 * out);", "tr(A, 0, -40 * (1 - aIn), 1 - .04 * out);")
rep("tr(S, 50 * (1 - bIn), 0, 1 - .04 * out);", "tr(S, 0, 40 * (1 - bIn), 1 - .04 * out);")
rep("l0.setAttribute('x2', f2(lerp(755, 870, d0))); l1.setAttribute('x2', f2(lerp(1050, 1165, d1)));", "l0.setAttribute('y2', f2(lerp(1024, 1119, d0))); l1.setAttribute('y2', f2(lerp(1181, 1276, d1)));")
rep("const px = p => lerp(755, 1165, p);", "const px = p => lerp(1024, 1276, p);")
rep("[$('cp'), $('cpg')].forEach(c => { c.setAttribute('cx', f2(px(pp))); c.setAttribute('cy', 560);", "[$('cp'), $('cpg')].forEach(c => { c.setAttribute('cx', 540); c.setAttribute('cy', f2(px(pp)));")
rep("c.setAttribute('cx', f2(px(clamp(pp - (k + 1) * .012)))); c.setAttribute('cy', 560);", "c.setAttribute('cx', 540); c.setAttribute('cy', f2(px(clamp(pp - (k + 1) * .012))));")
rep("tr(tg, 1340 - tgw / 2,", "tr(tg, 540 - tgw / 2,")
# dark orb path
rep("let x = 410, y = 650, w = 44, h = 44, rad = 22, bg = '#7a78f0', txt = 0, s = 1;", "let x = 108, y = 918, w = 44, h = 44, rad = 22, bg = '#7a78f0', txt = 0, s = 1;")
rep("x = lerp(410, 1380, g1); y = lerp(650, 540, g1) - 120 * Math.sin(Math.PI * g1);", "x = lerp(108, 540, g1); y = lerp(918, 1180, g1) - 120 * Math.sin(Math.PI * g1);")
rep("x = lerp(x, 960, g2); y = lerp(y, 560, g2) - 60 * Math.sin(Math.PI * g2);", "x = lerp(x, 540, g2); y = lerp(y, 1150, g2) - 30 * Math.sin(Math.PI * g2);")
# camera: gentler pushes, centred on the lower compositions
rep("s = 1 + .035 * E.ioSine(P(t, 10.6, 16.8)) - .035 * E.ioCubic(P(t, 16.8, 17.45)); ox = 1330; oy = 520;", "s = 1 + .02 * E.ioSine(P(t, 10.6, 16.8)) - .02 * E.ioCubic(P(t, 16.8, 17.45)); ox = 540; oy = 1100;")
rep("s = 1 + .03 * E.ioSine(P(t, 17.7, 24.3)) - .03 * E.ioCubic(P(t, 24.3, 25.3)); ox = 1300; oy = 480;", "s = 1 + .02 * E.ioSine(P(t, 17.7, 24.3)) - .02 * E.ioCubic(P(t, 24.3, 25.3)); ox = 540; oy = 1100;")
rep("s = 1 + .025 * E.ioSine(P(t, 25.4, 30.0)); ox = 900; oy = 650;", "s = 1 + .02 * E.ioSine(P(t, 25.4, 30.0)); ox = 540; oy = 1150;")
# preview fit
rep("K = Math.min(innerWidth / 1920, innerHeight / 1080);", "K = Math.min(innerWidth / 1080, innerHeight / 1920);")
rep("stage.style.transform = `translate(${(innerWidth - 1920 * K) / 2}px,${(innerHeight - 1080 * K) / 2}px) scale(${K})`;",
    "stage.style.transform = `translate(${(innerWidth - 1080 * K) / 2}px,${(innerHeight - 1920 * K) / 2}px) scale(${K})`;")

(HERE / "reel-vertical.html").write_text(s)
print("wrote", HERE / "reel-vertical.html")
