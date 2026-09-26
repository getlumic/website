"""Render video/reel/reel.html (picture) + video/reel/score.py (music) into public/video/ as MP4 + WebM + poster.

The reel page must expose:
  window.DURATION      -> length in seconds (40)
  window.seek(t)       -> draw the exact frame for time t (seconds); deterministic, no wall-clock timing
  window.reelReady     -> Promise that resolves once fonts/assets are loaded

Usage:
  python3 video/reel/render.py            # full render: frames + score, 30 fps
  python3 video/reel/render.py --stills   # one PNG per second into the frames dir, for review
  python3 video/reel/render.py --music    # rebuild the score only and re-mux it into the existing videos
Needs: playwright (uses the installed Google Chrome), numpy, ffmpeg on PATH.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "video" / "reel" / "reel.html"
SCORE = ROOT / "video" / "reel" / "score.py"
OUT = ROOT / "public" / "video"
FPS = 30
W, H = 1920, 1080
TMP = Path(tempfile.gettempdir())


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def build_score() -> Path:
    wav = TMP / "lumic-reel-score.wav"
    subprocess.run([sys.executable, str(SCORE), str(wav)], check=True)
    return wav


def encode(video_in: list, wav: Path) -> None:
    """video_in: ffmpeg input args for the picture (an image sequence or an existing file)."""
    ff(*video_in, "-i", wav, "-map", "0:v:0", "-map", "1:a:0",
       "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT / "lumic-reel.mp4")
    ff(*video_in, "-i", wav, "-map", "0:v:0", "-map", "1:a:0",
       "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34", "-row-mt", "1", "-pix_fmt", "yuv420p",
       "-c:a", "libopus", "-b:a", "128k", "-shortest", OUT / "lumic-reel.webm")


def remux(wav: Path) -> None:
    for name, acodec in (("lumic-reel.mp4", ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]),
                         ("lumic-reel.webm", ["-c:a", "libopus", "-b:a", "128k"])):
        src = OUT / name
        tmp = TMP / ("remux-" + name)
        ff("-i", src, "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", *acodec, "-shortest", tmp)
        shutil.move(tmp, src)


def main() -> None:
    if "--music" in sys.argv:
        remux(build_score())
        report()
        return

    from playwright.sync_api import sync_playwright

    stills = "--stills" in sys.argv
    frames = TMP / "lumic-reel-frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(SRC.as_uri() + "?render=1", wait_until="networkidle")
        page.evaluate("window.reelReady")
        duration = page.evaluate("window.DURATION")
        times = range(int(duration) + 1) if stills else range(int(duration * FPS))
        for i in times:
            t = i if stills else i / FPS
            page.evaluate(f"window.seek({min(t, duration - 1 / FPS)})")
            page.screenshot(path=str(frames / f"{i:05d}.png"))
        browser.close()

    if stills:
        print(f"stills in {frames}")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    encode(["-framerate", FPS, "-i", frames / "%05d.png"], build_score())
    ff("-i", frames / f"{int(duration * FPS) - 15:05d}.png", "-q:v", 3, OUT / "lumic-reel-poster.jpg")
    report()


def report() -> None:
    for f in sorted(OUT.iterdir()):
        print(f"{f.name}  {f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
