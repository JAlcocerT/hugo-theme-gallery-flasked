from __future__ import annotations

import os
from pathlib import Path
from typing import List

from flask import Flask, abort, render_template, send_from_directory, url_for, request, redirect
from werkzeug.utils import secure_filename
import re

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
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB max upload size
app.config["CONTENT_DIR"] = str(CONTENT_DIR)


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


def read_index_md(folder: Path) -> dict | None:
    """Read a folder's _index.md and extract simple fields and body.
    This does a minimal parse of YAML front matter for common scalar keys (title, description).
    """
    index_path = folder / "_index.md"
    if not index_path.exists():
        return None
    text = index_path.read_text(encoding="utf-8", errors="replace")
    title = None
    description = None
    body = text
    if text.lstrip().startswith("---"):
        # crude split of front matter and body
        parts = text.lstrip().split("---", 2)
        # parts: ['', '\nkey: val...\n', '\nbody...']
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            # extract simple key: value lines
            for line in fm_text.splitlines():
                m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*)\s*$", line)
                if not m:
                    continue
                k, v = m.group(1).lower(), m.group(2).strip()
                # strip quotes
                if v.startswith(('"', "'")) and v.endswith(('"', "'")) and len(v) >= 2:
                    v = v[1:-1]
                if k == "title":
                    title = v
                elif k == "description":
                    description = v
    return {"title": title, "description": description, "body": body.strip()}


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
    index_md = read_index_md(target)
    return render_template(
        "folder.html",
        current_path=(target.relative_to(CONTENT_DIR)),
        subdirs=subdirs,
        images=images,
        index_md=index_md,
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


@app.route("/folder/<path:subpath>/upload", methods=["POST"])
def upload_to_folder(subpath: str):
    """Handle image upload into a specific content subfolder."""
    target_dir = (CONTENT_DIR / subpath).resolve()
    if not is_within_content(target_dir) or not target_dir.exists() or not target_dir.is_dir():
        abort(404)

    if "file" not in request.files:
        abort(400, description="No file part in the request")
    file = request.files["file"]
    if not file or file.filename == "":
        abort(400, description="No selected file")

    filename = secure_filename(file.filename)
    if not filename:
        abort(400, description="Invalid filename")

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        abort(400, description=f"Unsupported file type: {ext}")

    save_path = (target_dir / filename)
    # Avoid overwriting existing files by adding a numeric suffix if needed
    if save_path.exists():
        stem = save_path.stem
        suffix = save_path.suffix
        i = 1
        while True:
            candidate = target_dir / f"{stem}-{i}{suffix}"
            if not candidate.exists():
                save_path = candidate
                break
            i += 1

    file.save(str(save_path))
    # Redirect back to the folder view
    return redirect(url_for("view_folder", subpath=subpath))


if __name__ == "__main__":
    # Enable debug auto-reload for convenience
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)), debug=True)
