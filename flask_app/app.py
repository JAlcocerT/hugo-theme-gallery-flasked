from __future__ import annotations

import os
from pathlib import Path
from typing import List

from flask import Flask, abort, render_template, send_from_directory, url_for, request, redirect
from werkzeug.utils import secure_filename
import re
from datetime import datetime
import subprocess

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


def get_index_md_path(folder: Path) -> Path:
    return folder / "_index.md"


def read_raw_index_md(folder: Path) -> str:
    p = get_index_md_path(folder)
    if not p.exists():
        return "---\ntitle: \ndescription: \n---\n\n"  # minimal starter
    return p.read_text(encoding="utf-8", errors="replace")


def write_raw_index_md(folder: Path, content: str) -> None:
    p = get_index_md_path(folder)
    # backup existing
    if p.exists():
        bak = p.with_suffix(p.suffix + ".bak")
        try:
            bak.write_text(p.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        except Exception:
            pass
    p.write_text(content, encoding="utf-8")

# --- Leaf bundle index.md helpers ---
def get_leaf_md_path(folder: Path) -> Path:
    return folder / "index.md"


def read_leaf_md(folder: Path) -> dict | None:
    """Parse folder's index.md (leaf bundle) similarly to _index.md."""
    p = get_leaf_md_path(folder)
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    # reuse the same crude parser
    title = None
    description = None
    body = text
    if text.lstrip().startswith("---"):
        parts = text.lstrip().split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            for line in fm_text.splitlines():
                m = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*)\s*$", line)
                if not m:
                    continue
                k, v = m.group(1).lower(), m.group(2).strip()
                if v.startswith(('"', "'")) and v.endswith(('"', "'")) and len(v) >= 2:
                    v = v[1:-1]
                if k == "title":
                    title = v
                elif k == "description":
                    description = v
    return {"title": title, "description": description, "body": body.strip()}


def read_raw_leaf_md(folder: Path) -> str:
    p = get_leaf_md_path(folder)
    if not p.exists():
        return "---\ntitle: \ndescription: \n---\n\n"  # starter
    return p.read_text(encoding="utf-8", errors="replace")


def write_raw_leaf_md(folder: Path, content: str) -> None:
    p = get_leaf_md_path(folder)
    if p.exists():
        bak = p.with_suffix(p.suffix + ".bak")
        try:
            bak.write_text(p.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        except Exception:
            pass
    p.write_text(content, encoding="utf-8")


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
    leaf_md = read_leaf_md(target)
    return render_template(
        "folder.html",
        current_path=(target.relative_to(CONTENT_DIR)),
        subdirs=subdirs,
        images=images,
        index_md=index_md,
        leaf_md=leaf_md,
    )


@app.route("/folder/<path:subpath>/edit", methods=["GET", "POST"])
def edit_index(subpath: str):
    target = (CONTENT_DIR / subpath).resolve()
    if not is_within_content(target) or not target.exists() or not target.is_dir():
        abort(404)
    if request.method == "POST":
        raw = request.form.get("content", "")
        # rudimentary size check (uses MAX_CONTENT_LENGTH as guidance)
        if len(raw.encode("utf-8")) > app.config.get("MAX_CONTENT_LENGTH", 25 * 1024 * 1024):
            abort(400, description="Content too large")
        write_raw_index_md(target, raw)
        return redirect(url_for("view_folder", subpath=subpath))
    raw_md = read_raw_index_md(target)
    return render_template(
        "edit_index.html",
        current_path=(target.relative_to(CONTENT_DIR)),
        raw_md=raw_md,
    )


@app.route("/folder/<path:subpath>/edit-index", methods=["GET", "POST"])
def edit_leaf(subpath: str):
    target = (CONTENT_DIR / subpath).resolve()
    if not is_within_content(target) or not target.exists() or not target.is_dir():
        abort(404)
    if request.method == "POST":
        raw = request.form.get("content", "")
        if len(raw.encode("utf-8")) > app.config.get("MAX_CONTENT_LENGTH", 25 * 1024 * 1024):
            abort(400, description="Content too large")
        write_raw_leaf_md(target, raw)
        return redirect(url_for("view_folder", subpath=subpath))
    raw_md = read_raw_leaf_md(target)
    return render_template(
        "edit_leaf.html",
        current_path=(target.relative_to(CONTENT_DIR)),
        raw_md=raw_md,
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


def _run_hugo_build() -> tuple[bool, str]:
    """Attempt to build the Hugo site using Docker in multiple ways.
    Tries, in order:
      1) docker exec into running container `hugo_container`
      2) docker compose exec into service `hugo-server` (compose file at repo root)
      3) one-off docker run using `hugo_gallery` image with a bind mount
    Returns (ok, message_tail)."""
    repo = str(REPO_ROOT)
    example_dir = str(REPO_ROOT / "exampleSite")
    from shutil import which
    docker_bin = which("docker")
    cmds = []
    if docker_bin:
        # 1) exec into running container by name
        cmds.append(f"{docker_bin} exec -w /hugo-theme-gallery/exampleSite hugo_container hugo")
        # 2) compose exec (no TTY)
        cmds.append(f"{docker_bin} compose -f '{repo}/docker-compose-hugoflask.yml' exec -T hugo-server hugo")
        # 3) one-off run using the built image, bind-mount the repo
        cmds.append(f"{docker_bin} run --rm -v '{repo}':/hugo-theme-gallery -w /hugo-theme-gallery/exampleSite hugo_gallery hugo")
    last_err = None
    for c in cmds:
        try:
            proc = subprocess.run(["/bin/sh", "-lc", c], capture_output=True, text=True, timeout=300)
            ok = proc.returncode == 0
            combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            lines = [ln for ln in combined.splitlines() if ln.strip()]
            tail = "\n".join(lines[-12:]) if lines else ("OK" if ok else "Error")
            if len(tail) > 700:
                tail = tail[-700:]
            if ok:
                return True, tail
            else:
                last_err = tail
        except Exception as e:
            last_err = f"error: {e}"
    # If all docker-based attempts failed (or docker missing), try local hugo
    hugo_bin = which("hugo")
    if hugo_bin:
        try:
            proc = subprocess.run([hugo_bin], cwd=example_dir, capture_output=True, text=True, timeout=300)
            ok = proc.returncode == 0
            combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            lines = [ln for ln in combined.splitlines() if ln.strip()]
            tail = "\n".join(lines[-12:]) if lines else ("OK" if ok else "Error")
            return ok, (tail or ("OK" if ok else "Error"))
        except Exception as e:
            last_err = f"local hugo error: {e}"
    else:
        if not docker_bin:
            last_err = (last_err or "") + ("\n" if last_err else "") + "docker not found and no local 'hugo' binary available"

    return False, (last_err or "Unknown error")


@app.route("/deploy", methods=["POST"])
def deploy():
    # Return user to the current page with build status
    next_url = request.form.get("next") or request.referrer or url_for("index")
    ok, msg = _run_hugo_build()
    from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

    parsed = urlparse(next_url)
    q = dict(parse_qsl(parsed.query))
    q.update({"build": "ok" if ok else "err", "msg": msg})
    new_q = urlencode(q)
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_q, parsed.fragment))
    return redirect(new_url)


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
