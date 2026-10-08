"""Publish the narrated keynote demo films into the site's demo carousel.

For each film whose render is finished in video/keynote/out/<film>/ (lumic-keynote-<film>.mp4, .webm, -poster.jpg),
copy the three files into public/video/demos/ under the same keynote names, then point that carousel slide in
public/index.html at them and mark it data-sound="1" (the slide shows the Sound button). A film that is not rendered
yet keeps its old silent film. The page state follows the files in public/video/demos/, so re-running is safe.

The 4:5 phone cut (lumic-keynote-<film>-vertical.mp4, -vertical.webm, -vertical-poster.jpg) is copied too when it is
there, and written onto the slide's <video> as data-v-mp4 / data-v-webm / data-v-poster; the page picks it on phones
(width <= 640 px). A film without a phone cut shows its 16:9 film on phones.

Refuses a film (copies nothing for it) when a file is over 12 MB (8 MB for the phone cut), was written in the last
60 seconds (render still running), has no audio track or no duration, the lengths of its files disagree, or an mp4 is
not fast-start. A refused phone cut does not block the 16:9 film; phones then get the 16:9 film.

Usage:  py -3.11 scripts/publish_keynote.py [film ...] [--dry-run] [--public DIR]
        films: receivables sales purchasing financial (default: all four)
        --public DIR  publish into another copy of public/ (for a test); default is this repo's public/
Exit code 1 if any film was refused. Then: QA the page, and deploy with `npx wrangler deploy`.
"""
import argparse
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "video" / "keynote" / "out"
FILMS = ["receivables", "sales", "purchasing", "financial"]
MAX_BYTES = 12_000_000
MAX_BYTES_VERTICAL = 8_000_000
SETTLE_S = 60
NOTE_SILENT = "Silent, 23 seconds each. Every figure is sample data."
NOTE_SOUND = "Every figure is sample data. Turn sound on for the narration."


def names(film, vertical=False):
    b = f"lumic-keynote-{film}" + ("-vertical" if vertical else "")
    return {"mp4": f"{b}.mp4", "webm": f"{b}.webm", "poster": f"{b}-poster.jpg"}


def probe(path):
    """(duration_s or None, has_audio) from ffprobe; None if ffprobe is not installed."""
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    r = subprocess.run([exe, "-v", "error", "-show_entries", "stream=codec_type:format=duration", "-of", "compact", str(path)],
                       capture_output=True, text=True)
    m = re.search(r"duration=([\d.]+)", r.stdout)
    return (float(m.group(1)) if m else None, "codec_type=audio" in r.stdout)


def mp4_faststart(path):
    """True when the moov box comes before mdat (the browser can start playing before the whole file arrives)."""
    with open(path, "rb") as f:
        pos, size = 0, os.path.getsize(path)
        while pos < size:
            f.seek(pos)
            h = f.read(8)
            if len(h) < 8:
                return False
            n, kind = struct.unpack(">I4s", h)
            if n == 1:
                n = struct.unpack(">Q", f.read(8))[0]
            if kind == b"moov":
                return True
            if kind == b"mdat" or n < 8:
                return False
            pos += n
    return False


def check(film, vertical=False, length=None):
    """Return (sources dict, length_s) when the render is ready, (None, reason) to skip, or raise ValueError to refuse.
    length: the 16:9 film's length in seconds; the phone cut must match it."""
    d = OUT / film
    src = {k: d / v for k, v in names(film, vertical).items()}
    limit = MAX_BYTES_VERTICAL if vertical else MAX_BYTES
    missing = [p.name for p in src.values() if not p.is_file()]
    if missing:
        if vertical:
            return None, "no phone cut yet (" + ", ".join(missing) + " missing); phones get the 16:9 film"
        return None, "not rendered yet (" + ", ".join(missing) + " missing); keeps the old silent film"
    now = time.time()
    for k, p in src.items():
        n = p.stat().st_size
        if n == 0:
            raise ValueError(f"{p.name} is empty")
        if n > limit:
            raise ValueError(f"{p.name} is {n / 1e6:.1f} MB (limit {limit / 1e6:.0f} MB)")
        age = now - p.stat().st_mtime
        if age < SETTLE_S:
            raise ValueError(f"{p.name} was written {age:.0f} s ago; the render may still be running. Try again in a minute")
    with open(src["poster"], "rb") as f:
        if f.read(3) != b"\xff\xd8\xff":
            raise ValueError(f"{src['poster'].name} is not a JPEG")
    if not mp4_faststart(src["mp4"]):
        raise ValueError(f"{src['mp4'].name} is not fast-start (moov after mdat); re-mux with -movflags +faststart")
    pm, pw = probe(src["mp4"]), probe(src["webm"])
    if pm is None:
        print(f"  note: ffprobe not found; audio and length checks skipped for {film}")
    else:
        for (dur, audio), p in ((pm, src["mp4"]), (pw, src["webm"])):
            if not audio:
                raise ValueError(f"{p.name} has no audio track")
            if dur is None:
                raise ValueError(f"{p.name} has no duration (file incomplete?)")
        if abs(pm[0] - pw[0]) > 0.5:
            raise ValueError(f"{src['mp4'].name} is {pm[0]:.1f} s but the webm is {pw[0]:.1f} s; one of them is incomplete")
        if length is not None and abs(pm[0] - length) > 0.5:
            raise ValueError(f"{src['mp4'].name} is {pm[0]:.1f} s but the 16:9 film is {length:.1f} s; not the same timeline")
    return src, (pm[0] if pm else None)


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy(src, dst, dry):
    if dst.is_file() and dst.stat().st_size == src.stat().st_size and sha1(dst) == sha1(src):
        return "unchanged"
    if dry:
        return "would copy"
    tmp = dst.with_name(dst.name + ".part")
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)
    return "copied"


def sync_page(public, dry, pending=()):
    """Point each carousel slide at its keynote film when all three keynote files are in public/video/demos/."""
    page = public / "index.html"
    html = page.read_text(encoding="utf-8")
    demos = public / "video" / "demos"
    state = {}

    def have(n):  # in public/video/demos, or about to be copied there (dry run)
        return (demos / n).is_file() or n in pending

    for film in FILMS:
        keynote = all(have(n) for n in names(film).values())
        vertical = keynote and all(have(n) for n in names(film, True).values())
        state[film] = (keynote, vertical)
        m = re.search(r'(<div class="car-slide[^"]*" id="car-%s")([^>]*>)(.*?</video>)' % film, html, re.S)
        if not m:
            raise SystemExit(f"index.html: carousel slide #car-{film} not found; page layout changed, update this script")
        attrs = m.group(2).replace(' data-sound="1"', "")
        if keynote:
            attrs = ' data-sound="1"' + attrs
        body = re.sub(r' data-v-(?:mp4|webm|poster)="[^"]*"', "", m.group(3))
        body = re.sub(r"/video/demos/lumic-(?:demo|keynote)-%s\b" % film,
                      f"/video/demos/lumic-{'keynote' if keynote else 'demo'}-{film}", body)
        if vertical:
            v = names(film, True)
            extra = "".join(f' data-v-{k}="/video/demos/{v[k]}"' for k in ("mp4", "webm", "poster"))
            body, n = re.subn(r"<video\b", "<video" + extra, body, count=1)
            if not n:
                raise SystemExit(f"index.html: no <video> in slide #car-{film}")
        html = html[:m.start()] + m.group(1) + attrs + body + html[m.end():]
    note = NOTE_SOUND if any(k for k, _ in state.values()) else NOTE_SILENT
    html, n = re.subn(r'(<p class="demo-note">).*?(</p>)', lambda m: m.group(1) + note + m.group(2), html, count=1)
    if not n:
        raise SystemExit("index.html: demo-note paragraph not found")
    changed = html != page.read_text(encoding="utf-8")
    if changed and not dry:
        page.write_text(html, encoding="utf-8", newline="\n")
    return state, note, changed


def main():
    ap = argparse.ArgumentParser(description="Publish keynote demo films into public/video/demos and the carousel.")
    ap.add_argument("films", nargs="*", metavar="film", help="any of: " + " ".join(FILMS))
    ap.add_argument("--dry-run", action="store_true", help="check and report, change nothing")
    ap.add_argument("--public", default=str(ROOT / "public"), help="the public/ folder to publish into")
    a = ap.parse_args()
    bad = [f for f in a.films if f not in FILMS]
    if bad:
        ap.error("unknown film: " + ", ".join(bad) + " (choose from " + ", ".join(FILMS) + ")")
    films = a.films or FILMS
    public = Path(a.public).resolve()
    demos = public / "video" / "demos"
    if not (public / "index.html").is_file() or not demos.is_dir():
        raise SystemExit(f"{public} does not look like the site's public/ folder")
    refused, pending = 0, set()
    print(f"publish keynote films -> {demos}" + ("  (dry run)" if a.dry_run else ""))
    for film in films:
        try:
            src, info = check(film)
        except ValueError as e:
            refused += 1
            print(f"  {film:12} REFUSED: {e}")
            continue
        if src is None:
            print(f"  {film:12} {info}")
            continue
        done = [f"{p.name} ({p.stat().st_size / 1e6:.1f} MB) {copy(p, demos / p.name, a.dry_run)}" for p in src.values()]
        pending |= {p.name for p in src.values()}
        print(f"  {film:12} 16:9" + (f" {info:.1f} s" if info else "") + ": " + "; ".join(done))
        try:
            vsrc, vinfo = check(film, vertical=True, length=info)
        except ValueError as e:
            refused += 1
            print(f"  {'':12} phone cut REFUSED: {e}; phones get the 16:9 film")
            continue
        if vsrc is None:
            print(f"  {'':12} {vinfo}")
            continue
        done = [f"{p.name} ({p.stat().st_size / 1e6:.1f} MB) {copy(p, demos / p.name, a.dry_run)}" for p in vsrc.values()]
        pending |= {p.name for p in vsrc.values()}
        print(f"  {'':12} phone 4:5: " + "; ".join(done))
    state, note, changed = sync_page(public, a.dry_run, pending)
    print(f"index.html {'updated' if changed else 'unchanged'}" + (" (dry run, not written)" if a.dry_run and changed else ""))
    for film in FILMS:
        k, v = state[film]
        print(f"  {film:12} " + (("keynote, narrated (Sound button shown); phones: " + ("4:5 cut" if v else "16:9 film"))
                                 if k else "old silent film"))
    print(f"  note: {note}")
    if refused:
        print(f"{refused} film(s) refused; nothing was copied for them.")
    print("next: serve public/ and run scripts/qa.py, then `npx wrangler deploy`")
    sys.exit(1 if refused else 0)


if __name__ == "__main__":
    main()
