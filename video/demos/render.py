"""Render a lumic demo film (silent, made to loop on the site) from video/demos/<name>/demo.html.

The page exposes window.DURATION, window.seek(t) (deterministic), window.reelReady and window.POSTER (poster time).
Screens come from the demo dashboard's synthetic data (video/demos/capture.py); no live numbers.

Usage:
  python video/demos/render.py <name>                 MP4 + WebM + poster into video/demos/out/<name>/
  python video/demos/render.py <name> --at 3 5.9 12   one PNG per given time, for review
  python video/demos/render.py <name> --out public/video/demos   publish
Needs: playwright (uses the installed Google Chrome), ffmpeg on PATH.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
args = sys.argv[1:]
if not args or args[0].startswith("-") or any(a.startswith("-") and a not in {"--at", "--out"} for a in args):
    sys.exit(__doc__)
NAME = args[0]
SRC = HERE / NAME / "demo.html"
if not SRC.exists():
    sys.exit(f"no demo page: {SRC}")
OUT = Path(args[args.index("--out") + 1]).resolve() if "--out" in args else HERE / "out" / NAME
FPS, W, H = 30, 1920, 1080
STEM = f"lumic-demo-{NAME}"


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, a)], check=True)


def main():
    from playwright.sync_api import sync_playwright
    at = [float(x) for x in args[args.index("--at") + 1:] if not x.startswith("-")] if "--at" in args else None
    frames = Path(tempfile.gettempdir()) / f"lumic-demo-{NAME}-frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(SRC.as_uri() + "?render=1", wait_until="networkidle")
        pg.evaluate("window.reelReady")
        dur, poster = pg.evaluate("[window.DURATION, window.POSTER || 0]")
        times = at if at is not None else [i / FPS for i in range(int(dur * FPS))]
        for i, t in enumerate(times):
            pg.evaluate(f"window.seek({t})")
            pg.screenshot(path=str(frames / (f"t{t:05.2f}.png" if at is not None else f"{i:05d}.png")))
        if at is None:
            pg.evaluate(f"window.seek({poster})")
            pg.screenshot(path=str(frames / "poster.png"))
        b.close()
    OUT.mkdir(parents=True, exist_ok=True)
    if at is not None:
        for f in sorted(frames.glob("t*.png")):
            shutil.copy(f, OUT / f.name)
            print(OUT / f.name)
        return
    seq = ["-framerate", FPS, "-i", frames / "%05d.png"]
    ff(*seq, "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", OUT / f"{STEM}.mp4")
    ff(*seq, "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34", "-row-mt", "1", "-pix_fmt", "yuv420p", "-an", OUT / f"{STEM}.webm")
    ff("-i", frames / "poster.png", "-q:v", 3, OUT / f"{STEM}-poster.jpg")
    for f in sorted(OUT.glob(STEM + "*")):
        print(f"{f}  {f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
