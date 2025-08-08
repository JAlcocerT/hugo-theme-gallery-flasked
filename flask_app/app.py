from __future__ import annotations

import os
from pathlib import Path
from typing import List

from flask import Flask, abort, render_template, send_from_directory, url_for

# Resolve paths relative to repo root
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[1]
CONTENT_DIR = (REPO_ROOT / "exampleSite" / "content").resolve()

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}

app = Flask(
    __name__,
    template_folder=str(REPO_ROOT / "flask_app" / "templates"),
    static_folder=str(REPO_ROOT / "flask_app" / "static"),
)


def is_within_content(path: Path) -> bool:
    try:
        path.resolve().relative_to(CONTENT_DIR)
        return True
    except Exception:
        return False


def list_subdirs(path: Path) -> List[Path]:
    return sorted([p for p in path.iterdir() if p.is_dir()])


def list_images(path: Path) -> List[Path]:
    return sorted([p for p in path.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_IMAGE_EXTS])


@app.route("/")
def index():
    if not CONTENT_DIR.exists():
        abort(404, description=f"Content dir not found: {CONTENT_DIR}")
    subdirs = list_subdirs(CONTENT_DIR)
    # Expose relative paths from content root
    items = [p.relative_to(CONTENT_DIR) for p in subdirs]
    return render_template("index.html", content_root=str(CONTENT_DIR), items=items)


@app.route("/folder/<path:subpath>")
def view_folder(subpath: str):
    target = (CONTENT_DIR / subpath).resolve()
    if not is_within_content(target) or not target.exists() or not target.is_dir():
        abort(404)
    # List child directories and images in this folder
    subdirs = [p.relative_to(CONTENT_DIR) for p in list_subdirs(target)]
    images = [p.relative_to(CONTENT_DIR) for p in list_images(target)]
    return render_template(
        "folder.html",
        current_path=(target.relative_to(CONTENT_DIR)),
        subdirs=subdirs,
        images=images,
    )


@app.route("/content/<path:filepath>")
def serve_content(filepath: str):
    # Serve files from content directory safely
    target = (CONTENT_DIR / filepath).resolve()
    if not is_within_content(target) or not target.exists():
        abort(404)
    directory = target.parent
    filename = target.name
    return send_from_directory(directory, filename)


if __name__ == "__main__":
    # Enable debug auto-reload for convenience
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)), debug=True)
