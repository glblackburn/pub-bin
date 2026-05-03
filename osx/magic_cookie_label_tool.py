#!/usr/bin/env python3
"""Desktop labeler for magic-cookie vs not on sweeper PNGs (plan-016)."""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path
from typing import List, Literal, Optional, Tuple


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


_reexec_with_project_venv()

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
    return p.parse_args(argv)


State = Literal["unset", "present", "absent", "skip"]


def main(argv: List[str]) -> int:
    ns = parse_args(argv[1:])
    try:
        from PySide6.QtCore import Qt, QRect, QPoint, QSize, QTimer  # noqa: PLC0415
        from PySide6.QtGui import QPainter, QPen, QColor, QPixmap, QImage, QShortcut, QKeySequence  # noqa: PLC0415
        from PySide6.QtWidgets import (  # noqa: PLC0415
            QApplication,
            QHBoxLayout,
            QMainWindow,
            QMessageBox,
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

    store = LabelStore(labels_path)
    store.load()

    class ImageViewport(QWidget):
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

        def resizeEvent(self, e) -> None:  # noqa: N802
            super().resizeEvent(e)
            self.update()

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Magic cookie label tool (plan-016)")
            self._paths = paths
            self._index = 0
            self._store = store
            self._labels_path = labels_path
            self._state: State = "unset"
            self._viewport = ImageViewport()
            central = QWidget()
            lay = QVBoxLayout(central)
            lay.addWidget(self._viewport, stretch=1)
            btn_row = QHBoxLayout()
            for txt, slot in (
                ("Present (Y)", self._on_present),
                ("Absent (N)", self._on_absent),
                ("Skip (U)", self._on_skip),
                ("Clear box", self._on_clear_box),
                ("Save + next (Enter)", self._on_save_next),
                ("Prev", self._on_prev),
                ("Next", self._on_next),
            ):
                b = QPushButton(txt)
                b.clicked.connect(slot)
                btn_row.addWidget(b)
            lay.addLayout(btn_row)
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
                ("Backspace", self._on_clear_box),
                ("Left", self._on_prev),
                ("Right", self._on_next),
                ("Q", self.close),
            ):
                sc = QShortcut(QKeySequence(key), self)
                sc.activated.connect(slot)

        def _state_from_record(self, rec: Optional[LabelRecord]) -> State:
            if rec is None:
                return "unset"
            if rec.magic_cookie is True:
                return "present"
            if rec.magic_cookie is False:
                return "absent"
            return "skip"

        def _refresh_status(self) -> None:
            p = self._paths[self._index]
            n = len(self._paths)
            self.statusBar().showMessage(
                f"[{self._index + 1}/{n}] {p.name} | state={self._state} | labels={self._labels_path}"
            )

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

        def _on_prev(self) -> None:
            if self._index > 0:
                self._index -= 1
                self._load_frame()

        def _on_next(self) -> None:
            if self._index + 1 < len(self._paths):
                self._index += 1
                self._load_frame()

        def _on_save_next(self) -> None:
            if self._state == "unset":
                QMessageBox.information(self, "Choose label", "Press Y, N, or U before saving.")
                return
            path = self._paths[self._index]
            magic: Optional[bool]
            bbox: Optional[Tuple[int, int, int, int]]
            if self._state == "present":
                magic = True
                bbox = self._viewport.bbox_image_px()
                if bbox is None or bbox[2] < 1 or bbox[3] < 1:
                    QMessageBox.information(
                        self, "Bounding box required", "Drag a rectangle around the magic cookie before saving."
                    )
                    return
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
    raise SystemExit(main(sys.argv))
