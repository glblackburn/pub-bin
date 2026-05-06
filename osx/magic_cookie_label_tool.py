#!/usr/bin/env python3
"""Desktop labeler for magic-cookie vs not on sweeper PNGs (plan-016)."""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path
from typing import List, Literal, Optional, Sequence, Tuple


def _reexec_with_project_venv() -> None:
    if os.environ.get("OSX_VENV_REEXEC") == "1":
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, ".venv", "bin", "python3")
    if not os.path.exists(venv_python):
        return
    if os.path.realpath(sys.prefix) == os.path.realpath(os.path.join(script_dir, ".venv")):
        return
    env = dict(os.environ)
    env["OSX_VENV_REEXEC"] = "1"
    os.execve(venv_python, [venv_python, os.path.abspath(__file__), *sys.argv[1:]], env)


_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from magic_cookie_labels import (  # noqa: E402
    TOOL_VERSION,
    LabelRecord,
    LabelStore,
    display_rect_to_image_bbox,
    image_bbox_to_display_rect,
    sha256_file,
    utc_now_iso,
)


def _repo_root() -> Path:
    # ``_script_dir`` is ``<repo>/osx``; repo root is one level up.
    return Path(_script_dir).resolve().parent


def default_image_dir() -> Path:
    """Resolved repo path ``docs/osx/screenshots/golden-sweeper-captures`` (sweeper PNG corpus)."""
    return (_repo_root() / "docs" / "osx" / "screenshots" / "golden-sweeper-captures").resolve()


def default_labels_path() -> Path:
    """Default JSONL next to the sweeper corpus (same directory as ``default_image_dir()``)."""
    return (default_image_dir() / "magic-cookie-labels.jsonl").resolve()


def gather_png_paths(image_dir: Path) -> List[Path]:
    out: List[Path] = []
    for p in sorted(image_dir.glob("*.png")):
        if "-annotated" in p.name or "-v2-annotated" in p.name:
            continue
        out.append(p)
    return out


def png_path_matches_search_query(path: Path, query: str) -> bool:
    """True if ``query`` matches this corpus path: resolved file equality, else basename substring (case-insensitive)."""
    q = (query or "").strip()
    if not q:
        return False
    try:
        cand = Path(q).expanduser()
        if cand.is_file() and path.resolve() == cand.resolve():
            return True
    except (OSError, ValueError):
        pass
    return q.lower() in path.name.lower()


def png_indices_matching_query(paths: Sequence[Path], query: str) -> List[int]:
    """Indices into ``paths`` (sorted order) where ``png_path_matches_search_query`` is true."""
    return [i for i, p in enumerate(paths) if png_path_matches_search_query(p, query)]


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Label magic cookie present/absent on PNG captures (plan-016).")
    p.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help=f"Directory of PNGs (default: {default_image_dir()})",
    )
    p.add_argument(
        "--labels",
        type=Path,
        default=None,
        help=f"JSONL output path (default: {default_labels_path()})",
    )
    p.add_argument(
        "--jump-query",
        default="",
        metavar="SUBSTRING",
        help="On startup, open the first PNG whose basename contains SUBSTRING (case-insensitive), "
        "or whose path equals a resolved file path. Warns to stderr if no match.",
    )
    return p.parse_args(argv)


State = Literal["unset", "present", "absent", "skip"]


def main(argv: List[str]) -> int:
    ns = parse_args(argv[1:])
    try:
        from PySide6.QtCore import Qt, QRect, QPoint, QSize, QTimer, Signal  # noqa: PLC0415
        from PySide6.QtGui import QPainter, QPen, QColor, QPixmap, QImage, QShortcut, QKeySequence  # noqa: PLC0415
        from PySide6.QtWidgets import (  # noqa: PLC0415
            QApplication,
            QDialog,
            QDialogButtonBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPlainTextEdit,
            QPushButton,
            QStatusBar,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:  # pragma: no cover - GUI optional in CI
        raise SystemExit(
            "Error: PySide6 is required for the label tool.\n"
            "Install: python3 -m pip install -r osx/requirements.txt\n"
            "Or: make -C osx setup"
        ) from exc

    image_dir = (ns.image_dir or default_image_dir()).expanduser().resolve()
    if not image_dir.is_dir():
        raise SystemExit(f"Error: image directory not found: {image_dir}")
    labels_path = (ns.labels or default_labels_path()).expanduser().resolve()

    paths = gather_png_paths(image_dir)
    if not paths:
        raise SystemExit(f"Error: no PNG files in {image_dir}")

    initial_index = 0
    bootstrap_find: Optional[Tuple[str, List[int]]] = None
    jump_q = (ns.jump_query or "").strip()
    if jump_q:
        bhits = png_indices_matching_query(paths, jump_q)
        if bhits:
            initial_index = bhits[0]
            bootstrap_find = (jump_q, bhits)
        else:
            print(
                f"Warning: --jump-query {jump_q!r} matched no PNG under {image_dir}; starting at first frame.",
                file=sys.stderr,
            )

    store = LabelStore(labels_path)
    store.load()

    HELP_TEXT = """\
Magic cookie label tool — quick reference
========================================

Purpose
-------
You walk PNG captures (default: golden sweeper raw frames, sorted by filename).
For each image you choose Present, Absent, or Skip, optionally draw a box, then
save. Rows are appended to a JSONL file (see status bar for path).

Present (Y)
-----------
A magic (golden-type) cookie is visible. Drag a rectangle around it in the
image. Enter / Save + next requires a box. Drawing a box also switches to
Present.

Absent (N)
----------
No magic cookie in this frame. Any box is cleared. No bounding box is stored.

Skip (U) — unsure / defer
-------------------------
You looked at the frame but will not commit to present vs absent (unclear
image, wrong capture, occlusion, wrong game state, etc.). On save, the JSONL
stores magic_cookie as null with no bbox — the frame is still “reviewed” so
pipelines can ignore it or treat it separately from true/false training labels.

Clear box (Backspace)
---------------------
Removes only the yellow rectangle. It does not change Present / Absent / Skip.

Save + next (Enter)
-------------------
Writes the current image’s label into the JSONL (the whole file is rewritten),
then moves to the next PNG.

Save & quit (Ctrl+Shift+W)
--------------------------
Saves the current image if it is labeled, then closes. If nothing is selected
for this image, asks whether to quit anyway — images you already saved with
Save + next are already on disk.

Prev / Next (Left / Right)
--------------------------
Browse without writing the current image to disk.

Prev unlabeled / Next unlabeled (Alt+Left / Alt+Right)
------------------------------------------------------
Jump to another image that has **no row yet** in the JSONL for this labels file
(same idea as “unset” on load: never saved). The unlabeled scan wraps around the list.
If every image already has a saved row, a message says so. If only the
current image lacks a row, “next” / “prev” report that you are already on the
only one.

Find image (Ctrl+F, F3, or button)
----------------------------------
Jump to a PNG by **basename substring** (case-insensitive), e.g. a sweeper stem
fragment, or paste a **full file path** if it resolves to the same file as one
of the corpus entries. **OK** / **Enter** selects the **first** match in sorted
filename order. **F3** moves to the **next** match for the last successful
query (wraps). If there is no prior query, **F3** opens the find dialog.

Command line: **--jump-query SUBSTRING** opens the tool already positioned on
the first matching frame (same rules as the dialog).

Quit (Q or close window)
-------------------------
If Present, Absent, or Skip is selected for the current image, you are asked to
save that decision or discard edits for this image only.

Restarts
--------
The JSONL is reloaded when you start the tool; saved rows show again when you
open each image. The list always starts at the first PNG in sorted order; use Next unlabeled
(Alt+Right) or Prev unlabeled (Alt+Left) to jump among images that still have
no JSONL row.

Shortcuts
---------
Y Present · N Absent · U Skip · Enter save+next · Ctrl+Shift+W save&quit ·
Backspace clear box · Left/Right prev/next image · Alt+Left/Alt+Right prev/next
unlabeled (no JSONL row) · Ctrl+F find image · F3 find next match · Q quit ·
F1 or Help = this window
"""

    class ImageViewport(QWidget):
        box_completed = Signal()

        def __init__(self) -> None:
            super().__init__()
            self._pixmap = QPixmap()
            self._img_w = 0
            self._img_h = 0
            self._drag_start: Optional[QPoint] = None
            self._rubber = QRect()
            self.setMinimumSize(480, 360)
            self.setMouseTracking(True)

        def set_image(self, path: Path) -> bool:
            img = QImage(str(path))
            if img.isNull():
                self._pixmap = QPixmap()
                self._img_w = self._img_h = 0
                return False
            self._img_w = img.width()
            self._img_h = img.height()
            self._pixmap = QPixmap.fromImage(img)
            self._drag_start = None
            self._rubber = QRect()
            self.update()
            return True

        def clear_box(self) -> None:
            self._drag_start = None
            self._rubber = QRect()
            self.update()

        def apply_record(self, rec: Optional[LabelRecord]) -> None:
            self._drag_start = None
            self._rubber = QRect()
            if rec is None or rec.magic_cookie is not True or rec.bbox_px is None:
                self.update()
                return
            x, y, w, h = rec.bbox_px
            ww, hh = self.width(), self.height()
            if ww < 2 or hh < 2 or self._img_w < 1:
                self.update()
                return
            x1, y1, x2, y2 = image_bbox_to_display_rect(ww, hh, self._img_w, self._img_h, x, y, w, h)
            left = min(x1, x2)
            top = min(y1, y2)
            rw = max(1, int(math.ceil(max(x1, x2) - left)))
            rh = max(1, int(math.ceil(max(y1, y2) - top)))
            self._rubber = QRect(int(math.floor(left)), int(math.floor(top)), rw, rh)
            self.update()

        def bbox_image_px(self) -> Optional[Tuple[int, int, int, int]]:
            if self._pixmap.isNull() or self._rubber.isNull():
                return None
            return display_rect_to_image_bbox(
                self.width(),
                self.height(),
                self._img_w,
                self._img_h,
                float(self._rubber.left()),
                float(self._rubber.top()),
                float(self._rubber.right()),
                float(self._rubber.bottom()),
            )

        def paintEvent(self, _ev) -> None:  # noqa: N802
            p = QPainter(self)
            p.fillRect(self.rect(), QColor(32, 32, 32))
            if self._pixmap.isNull():
                return
            w, h = self.width(), self.height()
            iw, ih = self._img_w, self._img_h
            sc = min(w / float(iw), h / float(ih))
            dw = int(iw * sc)
            dh = int(ih * sc)
            ox = int((w - dw) * 0.5)
            oy = int((h - dh) * 0.5)
            tgt = QRect(ox, oy, dw, dh)
            p.drawPixmap(tgt, self._pixmap, self._pixmap.rect())
            if not self._rubber.isNull():
                pen = QPen(QColor(255, 220, 0))
                pen.setWidth(2)
                p.setPen(pen)
                p.drawRect(self._rubber)

        def mousePressEvent(self, e) -> None:  # noqa: N802
            if e.button() == Qt.LeftButton:
                self._drag_start = e.position().toPoint()
                self._rubber = QRect(self._drag_start, QSize(0, 0))
                self.update()

        def mouseMoveEvent(self, e) -> None:  # noqa: N802
            if self._drag_start is None:
                return
            self._rubber = QRect(self._drag_start, e.position().toPoint()).normalized()
            self.update()

        def mouseReleaseEvent(self, e) -> None:  # noqa: N802
            if e.button() == Qt.LeftButton and self._drag_start is not None:
                self._rubber = QRect(self._drag_start, e.position().toPoint()).normalized()
                self._drag_start = None
                self.update()
                if not self._rubber.isNull():
                    self.box_completed.emit()

        def resizeEvent(self, e) -> None:  # noqa: N802
            super().resizeEvent(e)
            self.update()

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Magic cookie label tool (plan-016)")
            self._paths = paths
            self._index = initial_index
            self._store = store
            self._labels_path = labels_path
            self._state: State = "unset"
            self._find_query = ""
            self._find_match_indices: List[int] = []
            self._find_match_cursor = 0
            if bootstrap_find is not None:
                self._find_query = bootstrap_find[0]
                self._find_match_indices = list(bootstrap_find[1])
                self._find_match_cursor = 0
            self._viewport = ImageViewport()
            self._viewport.box_completed.connect(self._on_box_drawn)
            central = QWidget()
            lay = QVBoxLayout(central)
            lay.addWidget(self._viewport, stretch=1)
            btn_row = QHBoxLayout()
            _btn_tips = {
                "Skip (U)": (
                    "Unsure / defer: saves magic_cookie=null (no box). Use when you cannot "
                    "say present vs absent but want this frame marked as reviewed."
                ),
                "Prev unlabeled": "Go to the previous PNG that has no saved row in this JSONL (Alt+Left). Wraps.",
                "Next unlabeled": "Go to the next PNG that has no saved row in this JSONL (Alt+Right). Wraps.",
                "Find image…": "Jump by basename substring or full path (Ctrl+F). F3 = next match for last query.",
            }
            for txt, slot in (
                ("Present (Y)", self._on_present),
                ("Absent (N)", self._on_absent),
                ("Skip (U)", self._on_skip),
                ("Clear box", self._on_clear_box),
                ("Save + next (Enter)", self._on_save_next),
                ("Save & quit", self._on_save_and_quit),
                ("Prev", self._on_prev),
                ("Next", self._on_next),
                ("Help", self._on_help),
            ):
                b = QPushButton(txt)
                b.clicked.connect(slot)
                tip = _btn_tips.get(txt)
                if tip:
                    b.setToolTip(tip)
                btn_row.addWidget(b)
            lay.addLayout(btn_row)
            jump_row = QHBoxLayout()
            for txt, slot in (
                ("Prev unlabeled", self._on_prev_unlabeled),
                ("Next unlabeled", self._on_next_unlabeled),
            ):
                b = QPushButton(txt)
                b.clicked.connect(slot)
                tip = _btn_tips.get(txt)
                if tip:
                    b.setToolTip(tip)
                jump_row.addWidget(b)
            find_btn = QPushButton("Find image…")
            find_btn.clicked.connect(self._on_find_image)
            tip = _btn_tips.get("Find image…")
            if tip:
                find_btn.setToolTip(tip)
            jump_row.addWidget(find_btn)
            lay.addLayout(jump_row)
            self.setCentralWidget(central)
            sb = QStatusBar()
            self.setStatusBar(sb)
            self._refresh_status()
            self._load_frame()
            for key, slot in (
                ("Y", self._on_present),
                ("N", self._on_absent),
                ("U", self._on_skip),
                ("Return", self._on_save_next),
                ("Ctrl+Shift+W", self._on_save_and_quit),
                ("Backspace", self._on_clear_box),
                ("Left", self._on_prev),
                ("Right", self._on_next),
                ("Alt+Left", self._on_prev_unlabeled),
                ("Alt+Right", self._on_next_unlabeled),
                ("Ctrl+F", self._on_find_image),
                ("F3", self._on_find_next),
                ("Q", self.close),
                ("F1", self._on_help),
            ):
                sc = QShortcut(QKeySequence(key), self)
                sc.activated.connect(slot)

        def _on_help(self) -> None:
            dlg = QDialog(self)
            dlg.setWindowTitle("Magic cookie labeler — help")
            v = QVBoxLayout(dlg)
            body = QPlainTextEdit(HELP_TEXT)
            body.setReadOnly(True)
            body.setMinimumSize(520, 400)
            v.addWidget(body)
            box = QDialogButtonBox(QDialogButtonBox.Ok)
            box.accepted.connect(dlg.accept)
            v.addWidget(box)
            dlg.exec()

        def _state_from_record(self, rec: Optional[LabelRecord]) -> State:
            if rec is None:
                return "unset"
            if rec.magic_cookie is True:
                return "present"
            if rec.magic_cookie is False:
                return "absent"
            return "skip"

        def _find_status_suffix(self) -> str:
            if not self._find_match_indices:
                return ""
            k = self._find_match_cursor + 1
            n = len(self._find_match_indices)
            return f" | Find «{self._find_query}»: {k}/{n}"

        def _refresh_status(self) -> None:
            p = self._paths[self._index]
            n = len(self._paths)
            tail = (
                " — Save+next writes JSONL; Alt+Left/Right = unlabeled · Ctrl+F find · F3 next match"
            )
            self.statusBar().showMessage(
                f"[{self._index + 1}/{n}] {p.name} | state={self._state} | labels={self._labels_path}"
                f"{self._find_status_suffix()}{tail}"
            )

        def _apply_find_query(self, raw: str) -> bool:
            q = raw.strip()
            if not q:
                return False
            indices = png_indices_matching_query(self._paths, q)
            if not indices:
                return False
            self._find_query = q
            self._find_match_indices = indices
            self._find_match_cursor = 0
            self._index = indices[0]
            self._load_frame()
            return True

        def _on_find_image(self) -> None:
            dlg = QDialog(self)
            dlg.setWindowTitle("Find image")
            v = QVBoxLayout(dlg)
            v.addWidget(QLabel("PNG basename substring or full path to a corpus file:"))
            edit = QLineEdit()
            edit.setPlaceholderText("e.g. golden-sweeper-20260504-223259-223436-f00001")
            if self._find_query:
                edit.setText(self._find_query)
            v.addWidget(edit)
            box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            v.addWidget(box)
            box.accepted.connect(dlg.accept)
            box.rejected.connect(dlg.reject)
            edit.returnPressed.connect(dlg.accept)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            text = edit.text()
            if not self._apply_find_query(text):
                QMessageBox.information(
                    self,
                    "Find",
                    f"No PNG matches «{text.strip()}» in this folder.",
                )

        def _on_find_next(self) -> None:
            if not self._find_match_indices:
                self._on_find_image()
                return
            self._find_match_cursor = (self._find_match_cursor + 1) % len(self._find_match_indices)
            self._index = self._find_match_indices[self._find_match_cursor]
            self._load_frame()

        def _load_frame(self) -> None:
            path = self._paths[self._index]
            if not self._viewport.set_image(path):
                QMessageBox.warning(self, "Load error", f"Could not load image:\n{path}")
                return
            rec = self._store.get(path)
            self._state = self._state_from_record(rec)

            def apply() -> None:
                self._viewport.apply_record(rec)

            QTimer.singleShot(0, apply)
            self._refresh_status()

        def _on_box_drawn(self) -> None:
            self._state = "present"
            self._refresh_status()

        def _on_present(self) -> None:
            self._state = "present"
            self._refresh_status()

        def _on_absent(self) -> None:
            self._state = "absent"
            self._viewport.clear_box()
            self._refresh_status()

        def _on_skip(self) -> None:
            self._state = "skip"
            self._viewport.clear_box()
            self._refresh_status()

        def _on_clear_box(self) -> None:
            self._viewport.clear_box()
            self.update()

        def _record_for_current(self) -> Tuple[Optional[LabelRecord], Optional[str]]:
            """Build ``LabelRecord`` for the current image, or ``(None, err)`` if present without a valid box."""
            if self._state == "unset":
                return None, None
            path = self._paths[self._index]
            magic: Optional[bool]
            bbox: Optional[Tuple[int, int, int, int]]
            if self._state == "present":
                magic = True
                bbox = self._viewport.bbox_image_px()
                if bbox is None or bbox[2] < 1 or bbox[3] < 1:
                    return None, "Drag a rectangle around the magic cookie before saving."
            elif self._state == "absent":
                magic = False
                bbox = None
            else:
                magic = None
                bbox = None
            rec = LabelRecord(
                image_path=str(path.resolve()),
                image_sha256=sha256_file(path),
                image_wh=(self._viewport._img_w, self._viewport._img_h),
                magic_cookie=magic,
                bbox_px=bbox,
                labeled_at=utc_now_iso(),
                tool_version=TOOL_VERSION,
            )
            return rec, None

        def _on_save_and_quit(self) -> None:
            if self._state == "unset":
                r = QMessageBox.question(
                    self,
                    "Quit?",
                    "No label is selected for this image (nothing will be written for it).\n\n"
                    "Images you already saved with Save + next are already in the JSONL file.\nQuit anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if r != QMessageBox.Yes:
                    return
            else:
                rec, err = self._record_for_current()
                if err:
                    QMessageBox.information(self, "Cannot save", err)
                    return
                assert rec is not None
                self._store.upsert(rec)
                self._store.save()
            self.close()

        def closeEvent(self, event) -> None:  # noqa: N802
            if self._state == "unset":
                event.accept()
                return
            dlg = QMessageBox(self)
            dlg.setIcon(QMessageBox.Question)
            dlg.setWindowTitle("Quit labeling?")
            dlg.setText(
                "Save the current image to the JSONL before quitting?\n\n"
                "Images you already saved with Save + next are on disk."
            )
            save_btn = dlg.addButton("Save current", QMessageBox.AcceptRole)
            discard_btn = dlg.addButton("Discard edits for current", QMessageBox.DestructiveRole)
            cancel_btn = dlg.addButton("Cancel", QMessageBox.RejectRole)
            dlg.exec()
            clicked = dlg.clickedButton()
            if clicked == cancel_btn:
                event.ignore()
                return
            if clicked == save_btn:
                rec, err = self._record_for_current()
                if err:
                    QMessageBox.information(self, "Cannot save", err)
                    event.ignore()
                    return
                assert rec is not None
                self._store.upsert(rec)
                self._store.save()
                event.accept()
                return
            event.accept()

        def _on_prev(self) -> None:
            if self._index > 0:
                self._index -= 1
                self._load_frame()

        def _on_next(self) -> None:
            if self._index + 1 < len(self._paths):
                self._index += 1
                self._load_frame()

        def _any_unlabeled_on_disk(self) -> bool:
            return any(self._store.get(p) is None for p in self._paths)

        def _next_unlabeled_index(self) -> Optional[int]:
            """Index after ``self._index`` (wrapping) whose path has no JSONL row, or ``None``."""
            n = len(self._paths)
            for step in range(1, n):
                i = (self._index + step) % n
                if self._store.get(self._paths[i]) is None:
                    return i
            return None

        def _prev_unlabeled_index(self) -> Optional[int]:
            """Index before ``self._index`` (wrapping) whose path has no JSONL row, or ``None``."""
            n = len(self._paths)
            for step in range(1, n):
                i = (self._index - step) % n
                if self._store.get(self._paths[i]) is None:
                    return i
            return None

        def _on_next_unlabeled(self) -> None:
            if not self._any_unlabeled_on_disk():
                QMessageBox.information(
                    self,
                    "No unlabeled images",
                    "Every PNG in this folder already has a saved row in the JSONL.",
                )
                return
            j = self._next_unlabeled_index()
            if j is None:
                QMessageBox.information(
                    self,
                    "No other unlabeled image",
                    "Only this image lacks a saved row in the JSONL; there is no other frame to jump to.",
                )
                return
            self._index = j
            self._load_frame()

        def _on_prev_unlabeled(self) -> None:
            if not self._any_unlabeled_on_disk():
                QMessageBox.information(
                    self,
                    "No unlabeled images",
                    "Every PNG in this folder already has a saved row in the JSONL.",
                )
                return
            j = self._prev_unlabeled_index()
            if j is None:
                QMessageBox.information(
                    self,
                    "No other unlabeled image",
                    "Only this image lacks a saved row in the JSONL; there is no other frame to jump to.",
                )
                return
            self._index = j
            self._load_frame()

        def _on_save_next(self) -> None:
            if self._state == "unset":
                QMessageBox.information(self, "Choose label", "Press Y, N, or U before saving.")
                return
            rec, err = self._record_for_current()
            if err:
                QMessageBox.information(self, "Bounding box required", err)
                return
            assert rec is not None
            self._store.upsert(rec)
            self._store.save()
            if self._index + 1 < len(self._paths):
                self._index += 1
                self._state = "unset"
                self._load_frame()
            else:
                QMessageBox.information(self, "Done", "Last image saved. Closing.")
                self.close()

    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(960, 720)
    win.show()
    return int(app.exec())


if __name__ == "__main__":
    _reexec_with_project_venv()
    raise SystemExit(main(sys.argv))
