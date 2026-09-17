#!/usr/bin/env python3
"""Dick Wray Website -- Static Site Generator

Generates all HTML pages from Jinja2 templates and data files.
Run standalone or import build_site() from another module.
"""

import json
import os
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("ERROR: Jinja2 is required. Install with: pip install Jinja2")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# The admin-tool directory (where this script lives)
ADMIN_DIR = Path(__file__).resolve().parent

# The website root (parent of admin-tool)
SITE_DIR = ADMIN_DIR.parent

# Template directory
TEMPLATE_DIR = ADMIN_DIR / "templates" / "site"

# Data directory
DATA_DIR = SITE_DIR / "_data"

# Image directories
IMAGES_DIR = SITE_DIR / "assets" / "images"
COLLECTIONS_IMG_DIR = IMAGES_DIR / "collections"
BRANDING_DIR = IMAGES_DIR / "branding"

# ---------------------------------------------------------------------------
# Collection definitions
# ---------------------------------------------------------------------------

COLLECTIONS = [
    {
        "name": "Watercolors",
        "slug": "watercolors",
        "description": (
            "A selection of Dick Wray's vibrant watercolor works, showcasing "
            "his mastery of the medium and distinctive abstract expressionist style."
        ),
    },
    {
        "name": "Black & Whites",
        "slug": "black-and-whites",
        "description": (
            "Dick Wray's powerful black and white compositions, exploring "
            "contrast and form in abstract expressionism."
        ),
    },
    {
        "name": "Early Works",
        "slug": "early-works",
        "description": (
            "Early works from Dick Wray's formative years as an artist, "
            "showing the development of his distinctive style."
        ),
    },
    {
        "name": "Large Works",
        "slug": "large-works",
        "description": (
            "Dick Wray's monumental large-scale paintings, demonstrating "
            "his command of space and color on a grand scale."
        ),
    },
]

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

# Map of collection slugs to their homepage card image filenames
HOMEPAGE_CARD_MAP = {
    "watercolors": "watercolors-card",
    "black-and-whites": "black-and-whites-card",
    "early-works": "early-works-card",
    "large-works": "large-works-card",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def scan_images(directory: Path) -> list[str]:
    """Return sorted list of relative image paths (relative to SITE_DIR) in *directory*."""
    if not directory.is_dir():
        return []
    images = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            # Build a relative path from SITE_DIR
            rel = f.relative_to(SITE_DIR)
            # Use forward slashes for web paths
            images.append(str(rel).replace("\\", "/"))
    return images


def load_gallery(slug: str) -> list[dict] | None:
    """Load _data/galleries/<slug>.json (written by the web editor / admin tool).

    Returns a list of image dicts in display order, or None if the file
    doesn't exist (in which case the caller falls back to scanning the folder).
    Entries whose image file is missing on disk are skipped.
    """
    data = load_json(DATA_DIR / "galleries" / f"{slug}.json")
    if not isinstance(data, dict) or "images" not in data:
        return None
    images = []
    for entry in data.get("images") or []:
        if not isinstance(entry, dict):
            continue
        img = (entry.get("image") or "").strip().lstrip("/")
        if not img:
            continue
        if not (SITE_DIR / img).is_file():
            print(f"  (skipping missing image {img})")
            continue
        images.append({
            "path": img,
            "filename": Path(img).name,
            "title": entry.get("title", "") or "",
            "year": entry.get("year", "") or "",
            "medium": entry.get("medium", "") or "",
            "dimensions": entry.get("dimensions", "") or "",
            "notes": entry.get("notes", "") or "",
        })
    return images


def load_json(filepath: Path) -> any:
    """Load and return JSON data from *filepath*, or None if missing."""
    if not filepath.is_file():
        return None
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_json_list(filepath: Path) -> list:
    """Load a JSON file that may be an array or {items: [...]}. Returns a list."""
    data = load_json(filepath)
    if data is None:
        return []
    if isinstance(data, dict) and 'items' in data:
        return data['items']
    if isinstance(data, list):
        return data
    return []


def write_page(path: Path, content: str) -> None:
    """Write *content* to *path*, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_site() -> bool:
    """Build the entire static site.  Returns True on success, False on error."""
    try:
        return _build_site_impl()
    except Exception as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def _build_site_impl() -> bool:
    # ------------------------------------------------------------------
    # 1. Set up Jinja2
    # ------------------------------------------------------------------
    if not TEMPLATE_DIR.is_dir():
        print(f"ERROR: Template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return False

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # ------------------------------------------------------------------
    # 2. Load data
    # ------------------------------------------------------------------
    settings = load_json(DATA_DIR / "settings.json") or {
        "site_title": "Dick Wray | Abstract Expressionist Artist",
        "site_description": "Official website for abstract expressionist artist Dick Wray",
        "email": "contact@dickwray.com",
    }

    bio = load_json(DATA_DIR / "bio.json") or {}
    cv = load_json(DATA_DIR / "cv.json") or {}
    essays = load_json_list(DATA_DIR / "essays.json")
    interviews = load_json_list(DATA_DIR / "interviews.json")
    publications = load_json_list(DATA_DIR / "publications.json")
    image_metadata = load_json(DATA_DIR / "image_metadata.json") or {}

    # ------------------------------------------------------------------
    # 3. Scan images
    # ------------------------------------------------------------------
    splash_gallery = load_gallery("splash")
    if splash_gallery is not None:
        splash_images = [img["path"] for img in splash_gallery]
    else:
        splash_images = scan_images(COLLECTIONS_IMG_DIR / "splash")
    homepage_images = scan_images(COLLECTIONS_IMG_DIR / "homepage")

    # Build a lookup for homepage card images: slug -> relative path
    homepage_card_lookup: dict[str, str] = {}
    for img_path in homepage_images:
        fname_stem = Path(img_path).stem
        for slug, card_key in HOMEPAGE_CARD_MAP.items():
            if fname_stem == card_key:
                homepage_card_lookup[slug] = img_path

    # Choose an about-section image (first splash image or fallback)
    about_image = splash_images[0] if splash_images else "assets/images/branding/dickwray-logo_white.png"

    # ------------------------------------------------------------------
    # 4. Prepare collection data
    # ------------------------------------------------------------------
    collections_data = []
    for col in COLLECTIONS:
        card_image = homepage_card_lookup.get(
            col["slug"],
            f"assets/images/collections/homepage/{HOMEPAGE_CARD_MAP.get(col['slug'], col['slug'] + '-card')}.jpg",
        )
        # Prefer the gallery data file (editable on the web); fall back to
        # scanning the folder + image_metadata.json for older setups.
        gallery = load_gallery(col["slug"])
        if gallery is not None:
            col_images = [img["path"] for img in gallery]
            images_with_meta = gallery
        else:
            col_images = scan_images(COLLECTIONS_IMG_DIR / col["slug"])
            images_with_meta = []
        for img_path in (col_images if gallery is None else []):
            fname = Path(img_path).name
            meta_key = f"{col['slug']}/{fname}"
            meta = image_metadata.get(meta_key, {})
            images_with_meta.append({
                "path": img_path,
                "filename": fname,
                "title": meta.get("title", ""),
                "year": meta.get("year", ""),
                "medium": meta.get("medium", ""),
                "dimensions": meta.get("dimensions", ""),
                "notes": meta.get("notes", ""),
            })
        collections_data.append(
            {
                "name": col["name"],
                "slug": col["slug"],
                "description": col["description"],
                "images": col_images,
                "images_with_meta": images_with_meta,
                "card_image": card_image,
            }
        )

    # Common template context
    common_ctx = {
        "settings": settings,
        # Hide the Publications menu link until there is something to show
        "has_publications": bool(publications),
    }

    generated: list[str] = []

    # ------------------------------------------------------------------
    # 5. Render pages
    # ------------------------------------------------------------------

    # --- index.html ---
    tpl = env.get_template("index.html")
    html = tpl.render(
        **common_ctx,
        splash_images=splash_images,
        about_image=about_image,
        collections=collections_data,
        bio_paragraphs=bio.get("bio_paragraphs", []),
    )
    out = SITE_DIR / "index.html"
    write_page(out, html)
    generated.append("index.html")

    # --- cv.html ---
    tpl = env.get_template("cv.html")
    html = tpl.render(**common_ctx, cv=cv)
    write_page(SITE_DIR / "cv.html", html)
    generated.append("cv.html")

    # --- essays.html ---
    tpl = env.get_template("essays.html")
    html = tpl.render(**common_ctx, essays=essays)
    write_page(SITE_DIR / "essays.html", html)
    generated.append("essays.html")

    # --- interviews.html ---
    tpl = env.get_template("interviews.html")
    html = tpl.render(**common_ctx, interviews=interviews)
    write_page(SITE_DIR / "interviews.html", html)
    generated.append("interviews.html")

    # --- publications.html ---
    tpl = env.get_template("publications.html")
    html = tpl.render(**common_ctx, publications=publications)
    write_page(SITE_DIR / "publications.html", html)
    generated.append("publications.html")

    # --- Collection pages ---
    tpl = env.get_template("collection.html")
    for col in collections_data:
        html = tpl.render(**common_ctx, collection=col)
        filename = f"{col['slug']}.html"
        write_page(SITE_DIR / filename, html)
        generated.append(filename)

    # ------------------------------------------------------------------
    # 6. Report
    # ------------------------------------------------------------------
    print(f"Build complete. Generated {len(generated)} pages:")
    for name in generated:
        print(f"  -> {name}")

    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    success = build_site()
    sys.exit(0 if success else 1)
