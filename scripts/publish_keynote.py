"""Publish the narrated keynote demo films into the site's demo carousel.

The carousel has six slots, in this order: Receivables, Sales, Purchasing, Payables, Financial, AI Connector
(films: receivables sales purchasing payables financial connector).

For each film whose render is finished in video/keynote/out/<film>/ (lumic-keynote-<film>.mp4, .webm, -poster.jpg),
copy the three files into public/video/demos/ under the same names. Then rewrite the carousel in public/index.html
from the files in public/video/demos/:
  - a film with its keynote files gets a slide and a tab, marked data-sound="1" (the slide shows the Sound button);
  - a film with only the older silent files (lumic-demo-<film>.*) keeps its silent film;
  - a film with neither gets no slide and no tab at all (never an empty or "coming soon" slot).
When the AI Connector film is live, the connector service card and the connector section link to it (#car-connector).
Every screen plays the same 16:9 film; there are no phone cuts. The page state follows the files, so re-running is safe.

Refuses a film (copies nothing for it) when a file is over 12 MB, was written in the last 60 seconds (render still
running), has no audio track or no duration, the lengths of its mp4 and webm disagree, or the mp4 is not fast-start.

Usage:  py -3.11 scripts/publish_keynote.py [film ...] [--dry-run] [--public DIR]
        films: receivables sales purchasing payables financial connector (default: all six)
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
# slot order on the page: (film, tab label, description for screen readers; HTML-escaped)
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
    ("connector", "AI Connector",
     "The AI connector: an AI assistant answers questions from your ERP, email and files, and drafts entries for a person to approve."),
]
FILMS = [s[0] for s in SLOTS]
MAX_BYTES = 12_000_000
SETTLE_S = 60
NOTE_SILENT = "Silent, 23 seconds each. Every figure is sample data."
NOTE_SOUND = "Every figure is sample data. Turn sound on for the narration."
CONNECTOR_OFF = ('href="#connector"', "See the connector &rarr;")
CONNECTOR_ON = ('href="#car-connector"', "Watch the AI Connector film &rarr;")
CONNECTOR_BTN = ('<a class="btn btn-p" href="#car-connector">Watch the AI Connector film <svg viewBox="0 0 16 16" '
                 'fill="currentColor" aria-hidden="true"><path d="M5 3.2v9.6a.6.6 0 0 0 .9.5l7.6-4.8a.6.6 0 0 0 0-1L5.9 2.7a.6.6 0 0 0-.9.5z"/></svg></a>')


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
    """Rewrite the carousel slides and tabs from the films present in public/video/demos/."""
    page = public / "index.html"
    html = page.read_text(encoding="utf-8")
    demos = public / "video" / "demos"

    def have(n):  # in public/video/demos, or about to be copied there (dry run)
        return (demos / n).is_file() or n in pending

    state = {}
    for film in FILMS:
        if all(have(n) for n in names(film).values()):
            state[film] = "keynote"
        elif all(have(n) for n in names(film, "demo").values()):
            state[film] = "demo"
        else:
            state[film] = None
    live = [s for s in SLOTS if state[s[0]]]
    if not live:
        raise SystemExit("no film files in public/video/demos; refusing to write an empty carousel")
    slides, tabs = ["\n"], ["\n"]
    for i, (film, label, desc) in enumerate(live):
        n = names(film, state[film])
        first = i == 0
        act = " is-active" if first else ""
        sound = ' data-sound="1"' if state[film] == "keynote" else ""
        hide = "" if first else ' aria-hidden="true"'
        sel, tix = ("true", "") if first else ("false", ' tabindex="-1"')
        slides.append(
            f'      <div class="car-slide{act}" id="car-{film}"{sound} data-film="{film}" role="tabpanel" '
            f'aria-labelledby="cart-{film}"{hide}>\n'
            f'        <div class="car-f"><video muted playsinline preload="none" data-poster="/video/demos/{n["poster"]}" aria-label="{desc}">\n'
            f'          <source src="/video/demos/{n["webm"]}" type="video/webm"><source src="/video/demos/{n["mp4"]}" type="video/mp4"></video></div>\n'
            f'      </div>\n')
        tabs.append(
            f'      <button type="button" role="tab" id="cart-{film}" aria-controls="car-{film}" '
            f'aria-selected="{sel}"{tix} data-film="{film}">'
            f'{label}<span class="bar" aria-hidden="true"><i></i></span></button>\n')
    html = between(html, "slides", "".join(slides))
    html = between(html, "tabs", "".join(tabs))
    # phone row: the name and count of the first film (the script keeps it current after that)
    html, n = re.subn(r'(<p class="lbl"[^>]*><b>)[^<]*(</b><span class="ct">)\d+ / \d+',
                      lambda m: f"{m.group(1)}{live[0][1]}{m.group(2)}1 / {len(live)}", html, count=1)
    if not n:
        raise SystemExit("index.html: phone film row (#carMob .lbl) not found")
    # the connector card and the connector section link to the AI Connector film once it is live
    on = state["connector"] is not None
    m = re.search(r'(<a class="offer3[^"]*" id="offer-connector" )href="[^"]*"(>.*?<span class="go">)[^<]*(</span>)', html, re.S)
    if not m:
        raise SystemExit("index.html: connector service card (#offer-connector) not found")
    href, go = CONNECTOR_ON if on else CONNECTOR_OFF
    html = html[:m.start()] + m.group(1) + href + m.group(2) + go + m.group(3) + html[m.end():]
    html = between(html, "connector-film", CONNECTOR_BTN if on else "")
    note = NOTE_SOUND if any(v == "keynote" for v in state.values()) else NOTE_SILENT
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
        print(f"  {film:12}" + (f" {info:.1f} s" if info else "") + ": " + "; ".join(done))
    state, note, changed = sync_page(public, a.dry_run, pending)
    print(f"index.html {'updated' if changed else 'unchanged'}" + (" (dry run, not written)" if a.dry_run and changed else ""))
    for film, label, _ in SLOTS:
        s = state[film]
        print(f"  {label:13} " + ("keynote, narrated (Sound button shown)" if s == "keynote"
                                   else "old silent film" if s == "demo" else "not on the page (no film yet)"))
    print("  connector card: " + ("links to the AI Connector film" if state["connector"] else "links to the connector section"))
    print(f"  note: {note}")
    if refused:
        print(f"{refused} film(s) refused; nothing was copied for them.")
    print("next: serve public/ and run scripts/qa.py, then `npx wrangler deploy`")
    sys.exit(1 if refused else 0)


if __name__ == "__main__":
    main()
