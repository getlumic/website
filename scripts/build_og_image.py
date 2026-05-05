"""Build public/og-image.png (1200x630) by rendering scripts/og-template.html.

The template uses the same .brand markup and CSS as the live site header, so
the wordmark and indigo orb in the OG image are pixel-equivalent to what
visitors see at the top of get-lumic.com.

Run: python3 scripts/build_og_image.py
First-time setup: pip install playwright && playwright install chromium
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "scripts" / "og-template.html"
OUT = ROOT / "public" / "og-image.png"


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "playwright is not installed.\n"
            "Run: pip install playwright && playwright install chromium"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        page.goto(TEMPLATE.as_uri())
        page.screenshot(path=str(OUT), full_page=False, omit_background=False)
        browser.close()

    print(f"wrote {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
