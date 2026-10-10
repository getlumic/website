"""Publish the narrated keynote films into the site.

The landing page has two film players and one link list (public/index.html):
  - the hero plays "Why lumic" (film: why), from public/video/demos/lumic-keynote-why.{webm,mp4} + -poster.jpg;
  - #demo plays the lumic overview (film: overview), from lumic-keynote-overview.*;
  - under the overview, "Watch each dashboard on its own" lists one link per dashboard film, in this order:
    Receivables, Sales, Purchasing, Payables, Financial, AI connector (films: receivables sales purchasing payables
    financial connector). Each link opens that film's mp4 (in a lightbox when JS runs).
The two players point at fixed file names, so publishing a new render of why or overview only copies its files.

For each film whose render is finished in video/keynote/out/<film>/ (lumic-keynote-<film>.mp4, .webm, -poster.jpg),
copy the three files into public/video/demos/ under the same names. Then rewrite the dashboard link list (between the
films:start / films:end markers) from the files in public/video/demos/: a dashboard film with all three keynote files
gets a link; one without gets no link (never an empty or "coming soon" entry). Re-running is safe.

Refuses a film (copies nothing for it) when a file is over 12 MB, was written in the last 60 seconds (render still
running), has no audio track or no duration, the lengths of its mp4 and webm disagree, or the mp4 is not fast-start.
Reports a player whose film files are missing from public/video/demos/ (the page would show a broken player).

Usage:  py -3.11 scripts/publish_keynote.py [film ...] [--dry-run] [--public DIR]
        films: why overview receivables sales purchasing payables financial connector (default: all)
        --public DIR  publish into another copy of public/ (for a test); default is this repo's public/
Exit code 1 if any film was refused or a player's files are missing. Then: QA the page, and deploy with
`npx wrangler deploy`.
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
# the two players on the page: (film, where it plays)
PLAYERS = [("why", "hero (#why-film)"), ("overview", "#demo (#overview-film)")]
# the dashboard films, in link order: (film, link label, description for screen readers; HTML-escaped)
SLOTS = [
    ("receivables", "Receivables",
     "The receivables dashboard: open balances, aging by customer, and a customer&rsquo;s contacts and notes."),
    ("sales", "Sales",
     "The sales dashboard: year-to-date sales, each customer month by month, and the trends page."),
    ("purchasing", "Purchasing",
     "The purchasing dashboard: POs to send, vendors to chase, and raw materials behind open orders."),
    ("payables", "Payables",
     "The payables dashboard: vendor invoices checked and waiting for a person to approve them."),
    ("financial", "Financial",
     "The financial dashboard: the income statement for two companies, and the postings behind one account."),
    ("connector", "AI connector",
     "The AI connector: an AI assistant answers questions from your ERP, email and files, and drafts entries for a "
     "person to approve."),
]
FILMS = [f for f, _ in PLAYERS] + [s[0] for s in SLOTS]
MAX_BYTES = 12_000_000
SETTLE_S = 60
PLAY_ICON = ('<span class="ic" aria-hidden="true"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 '
             '1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/></svg></span>')


def names(film, kind="keynote"):
    b = f"lumic-{kind}-{film}"
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


def check(film):
    """Return (sources dict, length_s) when the render is ready, (None, reason) to skip, or raise ValueError to refuse."""
    d = OUT / film
    src = {k: d / v for k, v in names(film).items()}
    missing = [p.name for p in src.values() if not p.is_file()]
    if missing:
        return None, "not rendered yet (" + ", ".join(missing) + " missing)"
    now = time.time()
    for p in src.values():
        n = p.stat().st_size
        if n == 0:
            raise ValueError(f"{p.name} is empty")
        if n > MAX_BYTES:
            raise ValueError(f"{p.name} is {n / 1e6:.1f} MB (limit {MAX_BYTES / 1e6:.0f} MB)")
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


def between(html, tag, inner):
    """Replace what sits between <!-- tag:start ... --> and <!-- tag:end -->."""
    m = re.search(r"(<!-- %s:start[^>]*-->)(.*?)([ \t]*<!-- %s:end -->)" % (tag, tag), html, re.S)
    if not m:
        raise SystemExit(f"index.html: markers '{tag}:start' / '{tag}:end' not found; page layout changed, update this script")
    return html[:m.start()] + m.group(1) + inner + m.group(3) + html[m.end():]


def sync_page(public, dry, pending=()):
    """Rewrite the dashboard film links from the films present in public/video/demos/; report the two players."""
    page = public / "index.html"
    html = page.read_text(encoding="utf-8")
    demos = public / "video" / "demos"

    def have(n):  # in public/video/demos, or about to be copied there (dry run)
        return (demos / n).is_file() or n in pending

    state = {f: all(have(n) for n in names(f).values()) for f in FILMS}
    for film, _ in PLAYERS:
        if f"/video/demos/{names(film)['mp4']}" not in html:
            raise SystemExit(f"index.html: the {film} player (/video/demos/{names(film)['mp4']}) not found; "
                             "page layout changed, update this script")
    links = ["\n"] + [
        f'            <li><a href="/video/demos/{names(film)["mp4"]}" data-film="{film}" data-desc="{desc}" '
        f'target="_blank" rel="noopener">{PLAY_ICON}{label}</a></li>\n'
        for film, label, desc in SLOTS if state[film]]
    html = between(html, "films", "".join(links))
    changed = html != page.read_text(encoding="utf-8")
    if changed and not dry:
        page.write_text(html, encoding="utf-8", newline="\n")
    return state, changed


def main():
    ap = argparse.ArgumentParser(description="Publish keynote films into public/video/demos and the page's film links.")
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
        print(f"  {film:12}" + (f" {info:.1f} s" if info else "") + ": " + "; ".join(done))
    state, changed = sync_page(public, a.dry_run, pending)
    print(f"index.html {'updated' if changed else 'unchanged'}" + (" (dry run, not written)" if a.dry_run and changed else ""))
    missing = 0
    for film, where in PLAYERS:
        ok = state[film]
        missing += not ok
        print(f"  {film:13} {where}: " + ("files present" if ok else "FILES MISSING in public/video/demos (broken player)"))
    for film, label, _ in SLOTS:
        print(f"  {label:13} " + ("linked under the overview film" if state[film] else "no link (no film yet)"))
    if refused:
        print(f"{refused} film(s) refused; nothing was copied for them.")
    print("next: serve public/ and run scripts/qa.py, then `npx wrangler deploy`")
    sys.exit(1 if refused or missing else 0)


if __name__ == "__main__":
    main()
