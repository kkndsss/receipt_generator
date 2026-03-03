"""
exporter.py — SROIE 포맷으로 img/box/entities 파일 저장
"""
import io
import json
import os
from typing import List

from PIL import Image

from src.layout import BBoxEntry


def _ensure_dirs(output_dir: str):
    for sub in ("img", "box", "entities"):
        os.makedirs(os.path.join(output_dir, sub), exist_ok=True)


def _entries_to_8point(e: BBoxEntry) -> str:
    """
    직사각형 bbox → 8-point polygon (TL,TR,BR,BL)
    포맷: x1,y1,x2,y2,x3,y3,x4,y4,text
    """
    x1, y1, x2, y2 = e.x1, e.y1, e.x2, e.y2
    return f"{x1},{y1},{x2},{y1},{x2},{y2},{x1},{y2},{e.text}"


def save_receipt(
    receipt_id: str,
    img: Image.Image,
    entries: List[BBoxEntry],
    corpus: dict,
    output_dir: str,
    jpeg_quality: int = 85,
):
    """
    영수증 데이터 3종 저장.
    - img/{receipt_id}.jpg
    - box/{receipt_id}.txt
    - entities/{receipt_id}.txt
    """
    _ensure_dirs(output_dir)

    # ── img ──────────────────────────────────
    img_path = os.path.join(output_dir, "img", f"{receipt_id}.jpg")
    img.convert("RGB").save(img_path, "JPEG", quality=jpeg_quality)

    # ── box ──────────────────────────────────
    box_path = os.path.join(output_dir, "box", f"{receipt_id}.txt")
    with open(box_path, "w", encoding="utf-8") as f:
        for e in entries:
            if e.text.strip():
                f.write(_entries_to_8point(e) + "\n")

    # ── entities ─────────────────────────────
    entities = {
        "company": corpus["company"],
        "date":    corpus["date"],
        "address": corpus["address"].rstrip("."),
        "total":   corpus["total"],
    }
    ent_path = os.path.join(output_dir, "entities", f"{receipt_id}.txt")
    with open(ent_path, "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=4, ensure_ascii=False)
