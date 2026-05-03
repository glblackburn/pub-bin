# Plan 016 — Magic cookie screenshot labeler (PySide)

**Status:** **Shipped (v1)** — [`osx/magic_cookie_label_tool.py`](../../../osx/magic_cookie_label_tool.py) (PySide6 UI), [`osx/magic_cookie_labels.py`](../../../osx/magic_cookie_labels.py) (JSONL schema + coordinate math + store). **Normative** for label file format and tool behavior.

**Related:** [plan-015 — golden / magic cookie sweeper](plan-015-cookie-clicker-golden-cookie-sweeper.md) (detector consumes same **image pixel** space as stored `bbox_px`), [`osx/cookie_clicker_golden_sweeper.py`](../../../osx/cookie_clicker_golden_sweeper.py), [`docs/osx/golden-sweeper-corpus-INDEX.md`](../golden-sweeper-corpus-INDEX.md).

---

## 1. Terminology

| Term | Meaning |
|------|---------|
| **Magic cookie** | Operator-visible golden / “special” pickup in Cookie Clicker (same informal sense as plan-015). |
| **Label** | One saved decision for one image file: present / absent / skip, optional **bounding box** in **image pixels**. |
| **Image pixel space** | Coordinates relative to the PNG bitmap origin (top-left), before any Quartz global mapping — matches [`detect_magic_cookie_hits`](../../../osx/cookie_clicker_golden_sweeper.py) input. |

---

## 2. Goals

1. Walk a directory of **PNG** captures in a stable sorted order (default: golden sweeper raw frames; skip `*-annotated*` / `*-v2-annotated*` name patterns).
2. Let the operator set **magic_cookie** = yes / no / skip (unsure) per frame using keyboard and/or buttons.
3. When **yes**, require a **single** axis-aligned **drag rectangle** on the image; store **`[x, y, w, h]`** integers (top-left, width, height) in image pixels.
4. Append or upsert records in **JSONL** (one JSON object per line) for downstream tuning and evaluation scripts.
5. **Resume:** reloading the JSONL rebuilds state so revisiting a file updates the same logical record (keyed by **resolved absolute path**).

---

## 3. Non-goals (v1)

- No cloud sync, multi-user DB, or web UI.
- No in-tool training or threshold auto-tuning (separate follow-on scripts).
- No multi-box or polygon labels (plan **v2**).

---

## 4. Data model (normative JSONL)

Each line is one JSON object:

| Key | Type | Required | Meaning |
|-----|------|----------|---------|
| `schema_version` | int | yes | **`1`** |
| `image_path` | string | yes | **Absolute** path at save time (stable for local resume). |
| `image_sha256` | string | yes | SHA-256 of file bytes at label time. |
| `image_wh` | [int, int] | yes | `[width, height]` in pixels. |
| `magic_cookie` | bool \| null | yes | `true` = present, `false` = absent, `null` = skip / unsure. |
| `bbox_px` | [int,int,int,int] \| null | yes | `null` when `magic_cookie` is not `true`; else **`[x, y, w, h]`** image pixels. |
| `labeled_at` | string | yes | ISO8601 timestamp (UTC recommended). |
| `tool_version` | string | yes | Static tool id string for provenance. |

**Rule:** If `magic_cookie` is **`true`**, `bbox_px` must be a non-degenerate rectangle (`w >= 1`, `h >= 1`).

---

## 5. CLI

```text
osx/magic_cookie_label_tool.py [--image-dir DIR] [--labels FILE.jsonl]
```

- **`--image-dir`:** default `docs/osx/screenshots/golden-sweeper-captures` relative to repo root (resolved from cwd or `PUB_BIN` / script parent heuristic documented in `--help`).
- **`--labels`:** default **`docs/osx/screenshots/golden-sweeper-captures/magic-cookie-labels.jsonl`** under the repo root (same folder as the default image corpus; typically gitignored with that directory). Independent of a custom **`--image-dir`** unless **`--labels`** is overridden.

---

## 6. UI and shortcuts (v1)

- **Stack:** PySide6 — main window, custom paint widget for scaled image + rubber-band rect, status bar (path, index `i/n`, current classification).
- **Shortcuts:** `Y` present, `N` absent, `U` skip/unsure, `Enter` save and next, `Backspace` clear box, `Left` / `Right` prev / next, `P` previous without save (optional), `Q` quit.
- **Present flow:** press `Y` (or button) → drag box → `Enter` saves; validation errors shown in status bar if box missing.

---

## 7. Coordinate mapping

The image is **letterboxed** inside the widget preserving aspect ratio. Pointer events map through inverse transform (widget → image pixels) with clamping; see [`display_rect_to_image_bbox`](../../../osx/magic_cookie_labels.py) in tests.

---

## 8. Implementation files

| Path | Role |
|------|------|
| [`osx/magic_cookie_labels.py`](../../../osx/magic_cookie_labels.py) | Schema constants, `LabelRecord`, `LabelStore`, `sha256_file`, `display_rect_to_image_bbox`. |
| [`osx/magic_cookie_label_tool.py`](../../../osx/magic_cookie_label_tool.py) | `main()`, Qt app, window, `ImageViewport` widget. |
| [`osx/requirements.txt`](../../../osx/requirements.txt) | Add **`PySide6`**. |
| [`osx/tests/test_magic_cookie_labels.py`](../../../osx/tests/test_magic_cookie_labels.py) | Store round-trip + bbox mapping math. |

---

## 9. Testing

- **Automated:** `LabelStore` load/save/upsert; `display_rect_to_image_bbox` with known geometry (no Qt head).
- **Manual (v1):** launch tool on 3–5 fixtures; verify save line appears in JSONL and reopening shows prior classification.

---

## 10. Follow-on (not v1)

- `tools/eval_magic_cookie_labels.py` — compare `bbox_px` to `detect_magic_cookie_hits` (IoU / centroid).
- Export fixed-size **crops** for template or ML pipelines (plan-015 §5).

---

## 11. Open questions (deferred)

1. **PySide6 vs PyQt6** — v1 uses **PySide6** (LGPL-friendly).
2. Optional **distractor box** on absent frames — not in v1.
3. Whether to commit a redacted **labels.jsonl** — default keeps it beside gitignored captures; operators may copy elsewhere for CI.
