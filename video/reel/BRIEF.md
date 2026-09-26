# lumic reel: 40-second motion-graphics showreel

The goal: a dynamic 40-second motion-graphics film about lumic. It should look like a top motion designer's showreel: bold, precise, and beautifully timed. It must stay in the NEW site theme (Quiet Tech, `public/index.html`): high tech yet calm, premium, never cluttered. It will be embedded on get-lumic.com under the hero.

## What lumic is (research summary; do not add claims)
- lumic designs, builds, and supports custom dashboards, AI agents, and workflow automation for manufacturers and distributors, on the ERP they already run. We stay on to keep it running (monthly retainer).
- Slogan (verbatim): **Custom dashboards + AI agents on the ERP your business already runs.**
- Proof in production: a complete reporting and automation suite for a $20M manufacturer and distributor with two operating companies. Six processes that were manual now run every day (live sales & margin, AR aging + statements, purchasing & POs, AP invoice agent, production & job-cost margin, consolidated financials). Do not name the client.
- AI agents prepare entries. They land **unposted**. A person approves and posts. Nothing posts on its own.
- AI connector (COMING SOON): connects any AI assistant that supports MCP (Claude, ChatGPT, and others) to Sage 100, reading correctly and preparing unposted entries. Sage 100 first, more ERP connectors coming soon. This is the ONLY place "Sage 100" may appear.
- Led by two finance-trained founders in St. Louis (a controller and a CFP®). Do not show names or photos in the reel.
- Site: get-lumic.com

## Theme (non-negotiable)
- Colors: purple, black, and white only. Indigo `#5e5ce6` / `#4845c2` / `#7a78f0` / wash `#eeedfd` / `#1f1d3a`. Near-black `#0f172a` / `#0e1525` / `#131b32` / `#18213a`. White `#ffffff`, bg `#f6f7fb` / `#eef1f8`, grays `#1e293b` / `#64748b` / `#94a3b8`, hairlines `#e2e8f0` / `#eef1f6`. Tints/transparency of these are fine. A tiny green `#16a34a` ▲ is allowed only as a data signal inside a dashboard card.
- Type: Instrument Sans (400–700) for everything, with Instrument Serif *italic* for accent words (the same pairing as the site). Google Fonts link: `https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@1&display=swap`.
- The wordmark: `lum` + dotless ı (U+0131) + `c`, system font stack (`-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif`), weight 700, letter-spacing -.025em, `#0f172a`. The indigo orb (`#5e5ce6`, soft glow) sits above the ı as its dot. On dark, the text is white and the orb is `#7a78f0`. **The orb is the hero of the film**: the single point of light (lumic = Latin *lumi*, light).
- Visual vocabulary from the site: white cards with hairline borders and soft long shadows, glass cards, thin indigo flow lines with travelling pulses, hairline orbit rings, tabular numbers, small uppercase kickers with a ring dot, "Illustration"-style sample data.

## Storyboard (40.0 s @ 30 fps, 1920×1080)
Use timings as a guide. Motion should flow continuously: match cuts, morphs, camera push/pull (scale/translate of a stage), masked text reveals, and staggered springs. Easing is mostly expo/cubic out with a few crisp snaps. No bounce-cartoon.

1. **0.0–3.0 · Light.** White frame. A single indigo point ignites and pulses once. A hairline ring expands from it, and a second, dotted ring follows. The orb glides and lands exactly as the dot of the `lumıc` wordmark as the letters rise in with a mask. Hold a beat.
2. **3.0–7.0 · The problem.** The wordmark lifts away. Kinetic type, word by word with masks: "Your ERP holds the data." Then: "Your team still does the work *by hand.*" (serif italic accent in indigo). Behind it, faint gray spreadsheet fragments drift in: cells, "Export.csv", copy-paste rows. Keep it restrained.
3. **7.0–11.0 · Order.** The scattered cells accelerate into a precise grid, snap, and the grid folds into a clean white dashboard card. An indigo flow line draws from a small "ERP" node into it.
4. **11.0–18.0 · Custom dashboards.** A kicker: "CUSTOM DASHBOARDS". The camera pushes into a dashboard composition. "Sales · month to date" counts up to **$1.28M** with ▲ 8.4%, a line chart draws with an indigo area fade, AR aging bars rise (Current / 30 / 60 / 90+, all indigo tints), and gross margin 34.2% ticks. Label the composition "Illustration" in tiny caps. End on a drill-down: one bar expands into a detail list.
5. **18.0–25.0 · AI agents.** Kicker: "AI AGENTS". An envelope glides in, opens, and an invoice slides out. An indigo scan line passes over it, and the fields (Vendor 01042 · INV-20931 · $4,860.00) lift off the paper and fly into a structured entry card. A status pill reads "Entry prepared · unposted". A cursor clicks **Approve**, a check draws, and a soft ring pulse. Line: "A person approves. *Nothing posts on its own.*"
6. **25.0–30.0 · Workflow automation.** Kicker: "WORKFLOW AUTOMATION". The camera pulls back to a node map on white: an ERP hub, with flow lines to "Statements sent", "POs created", and "Reports delivered". Pulses travel the lines on a rhythm, and each node ticks when the pulse arrives. Tabular timestamps tick.
7. **30.0–34.0 · We keep it running.** Transition to near-black (`#0e1525`) through an iris from the orb. Hairline orbit rings turn, and four checkpoints on the ring light in turn: "New reports", "Schema changes", "Data feeds", "New users". Big type: "We build it. *We keep it running.*"
8. **34.0–37.0 · AI connector.** Still on dark. "AI assistant" → "MCP" → "Sage 100" nodes connect with a pulse. A "Coming soon" pill appears, with the line "Connect any AI to Sage 100." and small text "More ERP connectors coming soon."
9. **37.0–40.0 · End card.** An iris back to white. The orb flies to center and becomes the dot of a large `lumıc` wordmark. The slogan fades up beneath (serif italic on "already runs."), then "get-lumic.com" in small tracking. The orb breathes once. The final 0.5 s holds still (it becomes the poster frame and the loop point).

## Craft notes
- Treat it like a showreel: varied rhythms, confident negative space, precise alignment, secondary motion (subtle parallax layers, shadow shifts, micro-overshoot on cards), motion blur hints via short trails on fast moves, and seamless transitions between scenes (no hard cuts to empty frames).
- Stay calm: one focal point at a time, generous white space, no neon, no gradients outside the palette, no shake.
- Text must be legible: at least 28px for lines, 18px for small labels at 1920×1080. Hold each line long enough to read.
- Music: original score synthesized in `video/reel/score.py` (no samples or licensed audio), locked to the picture's hit points; `render.py` muxes it in.

## Technical contract (the renderer depends on this)
- One file: `video/reel/reel.html`, 1920×1080 stage, inline CSS/JS, no external JS libraries (write your own tiny tween/easing helpers). Google Fonts is the only external resource.
- `window.DURATION = 40`. `window.seek(t)` must set every element's state purely as a function of `t` in seconds: deterministic, with no CSS animations/transitions, setTimeout, or Date/performance timing driving the visuals. `window.reelReady` is a Promise that resolves after `document.fonts.ready` and any image decode.
- Without `?render=1` in the URL, auto-play in real time with requestAnimationFrame (looping), so it can be previewed in a browser. With `?render=1`, do not auto-play.
- Render: `/private/tmp/claude-501/-Users-christian-Desktop-Lumic/42843ae8-5a65-4db6-a6e4-3aaaeeef5a66/scratchpad/venv/bin/python /Users/christian/projects/website/video/reel/render.py --stills` writes one PNG per second (00000–00040) to `$TMPDIR/lumic-reel-frames`. Review those, plus extra frames you seek to yourself (e.g. mid-transition), with the Read tool. Iterate until every second looks like a finished design frame.
- The full render (no flag) writes `public/video/lumic-reel.mp4`, `.webm`, and the poster. Run it once at the end and report the file sizes. The MP4 must stay under 20 MB.
