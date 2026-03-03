"""
layout.py — Pillow 기반 영수증 렌더러
렌더링 시 각 텍스트 블록의 bbox 좌표를 함께 수집한다.
"""
import os
import sys
import random
import textwrap
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont


# ──────────────────────────────────────────────
# 리소스 경로 (PyInstaller 대응)
# ──────────────────────────────────────────────
def _resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


FONTS_DIR = _resource_path(os.path.join(os.path.pardir, "fonts"))

# 번들 폰트 파일명 목록 (fonts/ 폴더에 위치)
FONT_FILES = {
    "Courier Prime":   "CourierPrime-Regular.ttf",
    "Share Tech Mono": "ShareTechMono-Regular.ttf",
    "Cutive Mono":     "CutiveMono-Regular.ttf",
    "Special Elite":   "SpecialElite-Regular.ttf",
    "OCR-B":           "OCRB.ttf",
}


def get_font_path(font_name: str) -> Optional[str]:
    fname = FONT_FILES.get(font_name)
    if not fname:
        return None
    p = os.path.join(FONTS_DIR, fname)
    return p if os.path.exists(p) else None


def load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    p = get_font_path(font_name)
    if p:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    # fallback: PIL 기본 폰트
    return ImageFont.load_default()


# ──────────────────────────────────────────────
# 데이터 구조
# ──────────────────────────────────────────────
@dataclass
class BBoxEntry:
    """단일 텍스트 블록의 좌표 + 텍스트"""
    x1: int; y1: int
    x2: int; y2: int
    text: str


# ──────────────────────────────────────────────
# 렌더러
# ──────────────────────────────────────────────
class ReceiptRenderer:
    def __init__(
        self,
        font_name: str = "Courier Prime",
        body_size: int = 12,
        rng: Optional[random.Random] = None,
        jitter_max_angle: float = 0.0,
    ):
        self.font_name = font_name
        self.body_size = body_size
        self.rng = rng or random.Random()
        self.jitter_max_angle = jitter_max_angle

        # 본문 / 헤더 / 작은 글씨
        self.font_body  = load_font(font_name, body_size)
        self.font_title = load_font(font_name, body_size + 3)
        self.font_small = load_font(font_name, body_size - 1)

    # ── 내부 유틸 ──────────────────────────────
    def _text_wh(self, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
        """텍스트 너비/높이 계산"""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_text(
        self,
        draw: ImageDraw.Draw,
        entries: List[BBoxEntry],
        x: int, y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: Tuple = (0, 0, 0),
        align: str = "left",
        width: int = 0,
    ) -> int:
        """
        텍스트를 그리고 BBoxEntry 를 entries 에 추가.
        Returns: 다음 y 좌표
        """
        w, h = self._text_wh(text, font)
        if align == "center" and width:
            x_draw = x + (width - w) // 2
        elif align == "right" and width:
            x_draw = x + width - w
        else:
            x_draw = x

        draw.text((x_draw, y), text, font=font, fill=fill)

        # -- 지터(미세 기울기) 적용 --
        if self.jitter_max_angle > 0.01:
            jitter = self.rng.uniform(-self.jitter_max_angle, self.jitter_max_angle)
            # 텍스트만 회전시키기 위해 임시 RGBA 이미지 생성
            # 여백을 약간 줌 (회전 시 잘림 방지)
            pad = 4
            tw, th = w + pad * 2, h + pad * 2
            txt_img = Image.new("RGBA", (tw, th), (255, 255, 255, 0))
            txt_draw = ImageDraw.Draw(txt_img)
            txt_draw.text((pad, pad), text, font=font, fill=fill + (255,))

            # 회전
            rotated_txt = txt_img.rotate(jitter, resample=Image.BICUBIC, expand=True)
            rw, rh = rotated_txt.size

            # 메인 이미지에 투명도로 합성
            # 원본 위치에 덮어씌움 (배경이 흰색이므로 투명도 마스크 사용)
            paste_x = x_draw - (rw - tw) // 2 - pad
            paste_y = y - (rh - th) // 2 - pad

            # 원본 글씨 영역을 흰색으로 지우고 회전된 것으로 대체 (겹침 방지)
            draw.rectangle([x_draw, y, x_draw + w, y + h], fill=(255, 255, 255))
            draw._image.paste(rotated_txt, (paste_x, paste_y), rotated_txt)

            # bbox 업데이트 (단순화: 회전된 영역을 감싸는 직사각형)
            entries.append(BBoxEntry(
                x1=paste_x, y1=paste_y,
                x2=paste_x + rw, y2=paste_y + rh,
                text=text,
            ))
        else:
            draw.text((x_draw, y), text, font=font, fill=fill)
            entries.append(BBoxEntry(
                x1=x_draw, y1=y,
                x2=x_draw + w, y2=y + h,
                text=text,
            ))

        return y + h + 2   # 줄 간격 2px

    def _divider(
        self,
        draw: ImageDraw.Draw,
        entries: List[BBoxEntry],
        x: int, y: int,
        width: int,
        char: str = "-",
    ) -> int:
        n = max(1, width // max(1, self._text_wh(char, self.font_small)[0]))
        line = char * n
        return self._draw_text(draw, entries, x, y, line, self.font_small, width=width)

    # ── 섹션별 렌더러 ──────────────────────────
    def _render_header(self, draw, entries, corpus, x, y, w):
        # 회사명 (중앙, 굵게)
        y = self._draw_text(draw, entries, x, y, corpus["company"],
                            self.font_title, align="center", width=w)
        y += 2

        # 주소 (줄바꿈 포함)
        addr_lines = corpus["address"].split(", ")
        # 2~3줄로 합치기
        grouped = []
        buf = ""
        for part in addr_lines:
            if len(buf) + len(part) > 38:
                grouped.append(buf.rstrip(", "))
                buf = part + ", "
            else:
                buf += part + ", "
        if buf:
            grouped.append(buf.rstrip(", "))

        for line in grouped:
            y = self._draw_text(draw, entries, x, y, line,
                                self.font_small, align="center", width=w)
        y += 4
        return y

    def _render_doc_info(self, draw, entries, corpus, x, y, w):
        y = self._divider(draw, entries, x, y, w, "-")
        y = self._draw_text(draw, entries, x, y,
                            f"DOCUMENT NO : {corpus['doc_no']}",
                            self.font_small)

        # DATE 행: 라벨과 값을 같은 y에 배치
        date_y = y
        self._draw_text(draw, entries, x, date_y, "DATE:", self.font_small)
        y = self._draw_text(draw, entries, x + 60, date_y,
                            corpus["date_full"], self.font_small)

        # CASHIER 행: 라벨과 값을 같은 y에 배치
        cashier_y = y
        self._draw_text(draw, entries, x, cashier_y, "CASHIER:", self.font_small)
        y = self._draw_text(draw, entries, x + 70, cashier_y,
                            corpus["cashier"], self.font_small)

        y += 4
        y = self._divider(draw, entries, x, y, w, "-")
        y += 2
        # CASH BILL
        y = self._draw_text(draw, entries, x, y,
                            "CASH BILL", self.font_small, align="center", width=w)
        y += 6
        return y

    def _render_items_header(self, draw, entries, x, y, w):
        col_price  = x + int(w * 0.45)
        col_disc   = x + int(w * 0.63)
        col_amount = x + int(w * 0.80)

        # 첫 행: CODE/DESC  PRICE  DISC  AMOUNT
        header_y = y
        y = self._draw_text(draw, entries, x, header_y, "CODE/DESC", self.font_small)
        bh = self._text_wh("X", self.font_small)[1] + 2
        draw.text((col_price,  header_y), "PRICE",  font=self.font_small, fill=(0,0,0))
        draw.text((col_disc,   header_y), "DISC",   font=self.font_small, fill=(0,0,0))
        draw.text((col_amount, header_y), "AMOUNT", font=self.font_small, fill=(0,0,0))
        entries.append(BBoxEntry(col_price,  header_y, col_price  + self._text_wh("PRICE",  self.font_small)[0], header_y + bh, "PRICE"))
        entries.append(BBoxEntry(col_disc,   header_y, col_disc   + self._text_wh("DISC",   self.font_small)[0], header_y + bh, "DISC"))
        entries.append(BBoxEntry(col_amount, header_y, col_amount + self._text_wh("AMOUNT", self.font_small)[0], header_y + bh, "AMOUNT"))

        # 두 번째 행: QTY  RM  RM
        qty_y = y
        y = self._draw_text(draw, entries, x, qty_y, "QTY", self.font_small)
        draw.text((col_price,  qty_y), "RM", font=self.font_small, fill=(0,0,0))
        draw.text((col_amount, qty_y), "RM", font=self.font_small, fill=(0,0,0))
        entries.append(BBoxEntry(col_price,  qty_y, col_price  + self._text_wh("RM", self.font_small)[0], qty_y + bh, "RM"))
        entries.append(BBoxEntry(col_amount, qty_y, col_amount + self._text_wh("RM", self.font_small)[0], qty_y + bh, "RM"))
        y += 2
        return y

    def _render_items(self, draw, entries, corpus, x, y, w):
        col_price  = x + int(w * 0.45)
        col_disc   = x + int(w * 0.63)
        col_amount = x + int(w * 0.80)
        bh = self._text_wh("X", self.font_small)[1] + 2

        for item in corpus["items"]:
            # 바코드 (임의 13자리) + 품목명
            barcode = "".join([str(self.rng.randint(0, 9)) for _ in range(13)])
            y = self._draw_text(draw, entries, x, y, barcode,     self.font_small)
            y = self._draw_text(draw, entries, x, y, item["name"], self.font_small)

            # qty / price / disc / amount
            qty_txt  = f"{item['qty']} PC" if item["qty"] == 1 else f"{item['qty']} PCS"
            price_txt = f"{item['unit_price']:.2f}"
            disc_txt  = "0.00"
            amt_txt   = f"{item['amount']:.2f}"

            draw.text((x, y), qty_txt,   font=self.font_small, fill=(0,0,0))
            draw.text((col_price,  y), price_txt, font=self.font_small, fill=(0,0,0))
            draw.text((col_disc,   y), disc_txt,  font=self.font_small, fill=(0,0,0))
            draw.text((col_amount, y), amt_txt,   font=self.font_small, fill=(0,0,0))

            entries.append(BBoxEntry(x, y, x + self._text_wh(qty_txt, self.font_small)[0], y + bh, qty_txt))
            entries.append(BBoxEntry(col_price,  y, col_price  + self._text_wh(price_txt, self.font_small)[0], y + bh, price_txt))
            entries.append(BBoxEntry(col_disc,   y, col_disc   + self._text_wh(disc_txt,  self.font_small)[0], y + bh, disc_txt))
            entries.append(BBoxEntry(col_amount, y, col_amount + self._text_wh(amt_txt,   self.font_small)[0], y + bh, amt_txt))
            y += bh + 2

        return y

    def _render_totals(self, draw, entries, corpus, x, y, w):
        totals = corpus["totals"]
        col_label = x + int(w * 0.38)
        col_val   = x + int(w * 0.80)
        bh = self._text_wh("X", self.font_small)[1] + 2

        def _row(label, val_str):
            nonlocal y
            draw.text((col_label, y), label,   font=self.font_small, fill=(0,0,0))
            draw.text((col_val,   y), val_str,  font=self.font_small, fill=(0,0,0))
            entries.append(BBoxEntry(col_label, y, col_label + self._text_wh(label,   self.font_small)[0], y + bh, label))
            entries.append(BBoxEntry(col_val,   y, col_val   + self._text_wh(val_str, self.font_small)[0], y + bh, val_str))
            y += bh + 2

        _row("TOTAL:",                  f"{totals['subtotal']:.2f}")
        _row("ROUNDING ADJUSTMENT:",    f"{totals['rounding']:.2f}")
        _row("ROUNDED TOTAL (RM):",     f"{totals['rounded_total']:.2f}")
        y += 4
        _row("CASH",   f"{totals['cash']:.2f}")
        _row("CHANGE", f"{totals['change']:.2f}")
        return y

    def _render_footer(self, draw, entries, corpus, x, y, w):
        y += 12
        y = self._divider(draw, entries, x, y, w, "*")
        for line in corpus["footer"]:
            y = self._draw_text(draw, entries, x, y, line,
                                self.font_small, align="center", width=w)
        y = self._divider(draw, entries, x, y, w, "*")
        y += 6
        y = self._draw_text(draw, entries, x, y, "THANK YOU",
                            self.font_small, align="center", width=w)
        y = self._draw_text(draw, entries, x, y, "PLEASE COME AGAIN !",
                            self.font_small, align="center", width=w)
        return y

    # ── 공개 API ──────────────────────────────
    def render(self, corpus: dict) -> Tuple[Image.Image, List[BBoxEntry]]:
        """
        영수증 이미지 렌더링.
        Returns (PIL.Image, list[BBoxEntry])
        """
        width = self.rng.randint(440, 520)
        margin = 28

        # 1패스: 높이 계산을 위해 dummy Image 로 렌더
        height_estimate = 1200
        dummy = Image.new("RGB", (width, height_estimate), color=(255, 255, 255))
        dummy_draw = ImageDraw.Draw(dummy)
        dummy_entries: List[BBoxEntry] = []

        x = margin
        w = width - margin * 2
        y = margin

        y = self._render_header(dummy_draw, dummy_entries, corpus, x, y, w)
        y = self._render_doc_info(dummy_draw, dummy_entries, corpus, x, y, w)
        y = self._render_items_header(dummy_draw, dummy_entries, x, y, w)
        y = self._render_items(dummy_draw, dummy_entries, corpus, x, y, w)
        y = self._divider(dummy_draw, dummy_entries, x, y, w, "-")
        y = self._render_totals(dummy_draw, dummy_entries, corpus, x, y, w)
        y = self._render_footer(dummy_draw, dummy_entries, corpus, x, y, w)

        final_height = y + margin

        # 2패스: 실제 Image
        img = Image.new("RGB", (width, final_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        entries: List[BBoxEntry] = []

        x = margin
        y = margin
        y = self._render_header(draw, entries, corpus, x, y, w)
        y = self._render_doc_info(draw, entries, corpus, x, y, w)
        y = self._render_items_header(draw, entries, x, y, w)
        y = self._render_items(draw, entries, corpus, x, y, w)
        y = self._divider(draw, entries, x, y, w, "-")
        y = self._render_totals(draw, entries, corpus, x, y, w)
        y = self._render_footer(draw, entries, corpus, x, y, w)

        return img, entries
