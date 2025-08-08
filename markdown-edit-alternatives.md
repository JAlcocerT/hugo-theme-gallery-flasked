# Markdown Editing Alternatives (for Flask _index.md live edit)

This doc compares lightweight ways to edit Markdown in the Flask app and outlines minimal integration steps.

## Options Overview

- **Editor.md (pandao/editor.md)**
  - Pros: Feature-rich, built-in preview.
  - Cons: jQuery dependency; relatively heavy and older stack.
  - Weight: Medium–heavy.
  - Link: https://github.com/pandao/editor.md

- **TUI Editor (nhn/tui.editor)**
  - Pros: Polished UI, Markdown + WYSIWYG modes, active project.
  - Cons: Heavier bundle, more dependencies; likely overkill for simple edits.
  - Weight: Heavy.
  - Links: https://github.com/nhn/tui.editor • https://ui.toast.com/tui-editor

- **EasyMDE (recommended lightweight)**
  - Pros: Single JS+CSS via CDN, no framework required, nice UX, live preview, simple to wire up.
  - Cons: Fewer plugins than TUI; client-side preview only (usually fine).
  - Weight: Light.
  - Link: https://github.com/Ionaru/easy-markdown-editor

- **Textarea + marked.js (ultra-light DIY)**
  - Pros: Minimal deps; a `<textarea>` + `marked` (CDN) for live preview.
  - Cons: No toolbar/shortcuts by default; custom UX if needed.
  - Weight: Ultra-light.
  - Link (marked): https://github.com/markedjs/marked

## Recommendation

- For the simplest, light, and maintainable solution: **EasyMDE**.
- For absolute minimal footprint and full control: **Textarea + marked.js**.

## Minimal Integration (EasyMDE)

- Routes in `flask_app/app.py`:
  - `GET /folder/<subpath>/edit` → read raw `_index.md` (create if missing) and render editor.
  - `POST /folder/<subpath>/edit` → write changes back to `_index.md`. Optionally make a backup `_index.md.bak`.
- Template `templates/edit_index.html`:
  - Include EasyMDE via CDN:
    ```html
    <link rel="stylesheet" href="https://unpkg.com/easymde/dist/easymde.min.css">
    <script src="https://unpkg.com/easymde/dist/easymde.min.js"></script>
    ```
  - `<textarea id="md">{{ raw_md }}</textarea>` then `new EasyMDE({ element: document.getElementById('md') })`.
  - Buttons: Save (POST), Cancel (back to folder).
- Security & Safety:
  - Use existing `is_within_content()` to constrain path.
  - Backup before write; validate size (reuse `MAX_CONTENT_LENGTH`).

## Minimal Integration (Textarea + marked.js)

- Same GET/POST routes as above.
- Template adds a split view:
  - Left: `<textarea>` (bound to form POST).
  - Right: `<div id="preview"></div>` updated via `marked(textarea.value)` on `input`.
  - Include `marked` via CDN:
    ```html
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    ```
- Pros: No toolbar; smallest JS.

## Advanced (Optional Later)

- Parse YAML front matter to edit `title`, `description` separately from body.
- Add drag-and-drop uploads, image paste handling.
- Sanitize rendered HTML (e.g., `bleach`) if rendering server-side.
- Auth or basic protection for write endpoints.

## Summary

- Pick **EasyMDE** for a quick, polished editor with minimal setup.
- Pick **Textarea + marked.js** for the lightest possible dependency footprint.
- TUI/Editor.md are powerful but heavier than needed for simple `_index.md` edits.
