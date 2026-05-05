"""Build public/og-image.png (1200x630) by rendering scripts/og-template.html.

The template embeds ~/projects/playbook/brand/logos/wordmark.svg as an <img>,
so the wordmark and indigo orb in the OG image are pixel-equivalent to the
canonical brand-kit asset (and therefore to every other surface that uses it).

Run: python3 scripts/build_og_image.py
First-time setup: pip install playwright && playwright install chromium
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "scripts" / "og-template.html"
OUT = ROOT / "public" / "og-image.png"

BRAND_WORDMARK = Path.home() / "projects" / "playbook" / "brand" / "logos" / "wordmark.svg"
PUBLIC_WORDMARK = ROOT / "public" / "wordmark.svg"
PUBLIC_TEMPLATE = ROOT / "public" / "_og-template.html"  # served path for /wordmark.svg to resolve


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "playwright is not installed.\n"
            "Run: pip install playwright && playwright install chromium"
        )

    if not BRAND_WORDMARK.exists():
        raise SystemExit(f"brand wordmark not found at {BRAND_WORDMARK}")

    # Sync the brand-kit wordmark into public/ so the template's <img src="/wordmark.svg">
    # resolves to the canonical asset on every render.
    shutil.copyfile(BRAND_WORDMARK, PUBLIC_WORDMARK)
    shutil.copyfile(TEMPLATE, PUBLIC_TEMPLATE)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 1200, "height": 630})
            page = context.new_page()
            # Serve via file:// from the public dir so /wordmark.svg resolves.
            page.goto(PUBLIC_TEMPLATE.as_uri())
            page.screenshot(path=str(OUT), full_page=False, omit_background=False)
            browser.close()
    finally:
        PUBLIC_TEMPLATE.unlink(missing_ok=True)

    print(f"wrote {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
