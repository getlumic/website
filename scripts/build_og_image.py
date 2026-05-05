"""Build public/og-image.png (1200x630) — lumic wordmark + tagline.

Run: python3 scripts/build_og_image.py
Re-run any time the wordmark or tagline changes. Output is committed.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parents[1] / "public" / "og-image.png"

W, H = 1200, 630
BG       = (246, 247, 251)     # --bg
BG_2     = (238, 241, 248)     # --bg-2
PRIMARY  = (94, 92, 230)       # --primary  #5e5ce6
TEXT     = (15, 23, 42)        # --text-strong
MUTED    = (100, 116, 139)     # --muted

SFNS = "/System/Library/Fonts/SFNS.ttf"

def bold(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(SFNS, size)
    f.set_variation_by_name(b"Bold")
    return f

def regular(size: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(SFNS, size)
    f.set_variation_by_name(b"Regular")
    return f

def vertical_gradient(w: int, h: int, top: tuple, bot: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h), top)
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        r = round(top[0] + (bot[0] - top[0]) * t)
        g = round(top[1] + (bot[1] - top[1]) * t)
        b = round(top[2] + (bot[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img

def add_glow(img: Image.Image, cx: int, cy: int, diameter: int,
             color: tuple, intensity: int = 180) -> None:
    """Composite a soft circular glow onto an RGB image without square artifacts.
    Trick: blur an L-mode alpha mask separately from the solid-color overlay,
    so blurred RGBA-corner darkening can't bleed in."""
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    r = diameter // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=intensity)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=diameter * 0.5))
    overlay = Image.new("RGB", img.size, color)
    img.paste(overlay, (0, 0), mask)

def main() -> None:
    img = vertical_gradient(W, H, BG, BG_2)

    draw = ImageDraw.Draw(img)

    # ---------- Wordmark layout ----------
    wm_size = 280
    wm_font = bold(wm_size)
    parts = ["lum", "ı", "c"]
    widths = [draw.textlength(p, font=wm_font) for p in parts]
    spacing = -8
    total_w = sum(widths) + spacing * (len(parts) - 1)

    # Vertical centering by the ascender of the bold cap; visually balanced.
    bbox = wm_font.getbbox("lumic")
    cap_h = bbox[3] - bbox[1]
    wm_y = (H - cap_h) // 2 - 30 - bbox[1]

    x = (W - total_w) // 2
    starts = []
    for w in widths:
        starts.append(x)
        x += w + spacing

    # ---------- Compute i-dot location BEFORE drawing text ----------
    # Anchor to actual font metrics: top of `l`-ascender vs top of `u`-x-height,
    # so the dot sits proportionally above the lowercase letters regardless of
    # font weight / optical size choices.
    l_top = wm_font.getbbox("l")[1]      # y of `l` ascender top within text box
    u_top = wm_font.getbbox("u")[1]      # y of `u` x-height top within text box
    ascender_top_y = wm_y + l_top        # canvas y of `l` top
    xheight_top_y  = wm_y + u_top        # canvas y of `u` top
    cap_to_x = xheight_top_y - ascender_top_y   # vertical distance cap → x-height

    i_left = starts[1]
    i_w = widths[1]
    dot_cx = int(i_left + i_w / 2)

    # Dot sized as a fraction of the cap-to-x-height gap (proper i-dot proportion).
    dot_r = int(cap_to_x * 0.34)
    # Dot bottom edge sits just above x-height with a small breathing gap.
    gap = int(cap_to_x * 0.12)
    dot_cy = xheight_top_y - gap - dot_r

    # ---------- Soft ambient bloom behind the wordmark ----------
    add_glow(img, W // 2, H // 2, diameter=560, color=PRIMARY, intensity=70)
    # Localized warm halo under the dot
    add_glow(img, dot_cx, dot_cy, diameter=240, color=PRIMARY, intensity=130)

    # Re-create the draw context since we've pasted onto img
    draw = ImageDraw.Draw(img)

    # ---------- Draw wordmark on top of the bloom ----------
    for s, p in zip(starts, parts):
        draw.text((s, wm_y), p, font=wm_font, fill=TEXT)

    # ---------- Draw the indigo orb ----------
    draw.ellipse(
        (dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r),
        fill=PRIMARY,
    )

    # ---------- Tagline ----------
    tag_size = 44
    tag_font = regular(tag_size)
    tag = "Your business, in your hands."
    tag_w = draw.textlength(tag, font=tag_font)
    tag_y = wm_y + cap_h + 56
    draw.text(((W - tag_w) // 2, tag_y), tag, font=tag_font, fill=MUTED)

    # ---------- Footer URL ----------
    url_size = 22
    url_font = regular(url_size)
    url = "get-lumic.com"
    url_w = draw.textlength(url, font=url_font)
    draw.text(((W - url_w) // 2, H - 70), url, font=url_font, fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT}  ({OUT.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()