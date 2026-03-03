"""
noise.py — 영수증 이미지 노이즈·왜곡 후처리 파이프라인
렌더링된 깨끗한 이미지를 실제 스캔 영수증처럼 열화시킨다.
"""
import math
import random
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


# ──────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────
def _to_np(img: Image.Image) -> np.ndarray:
    return np.array(img, dtype=np.float32)


def _to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ──────────────────────────────────────────────
# 1. 배경 황변 (thermal paper aging)
# ──────────────────────────────────────────────
def apply_background_tint(img: Image.Image, strength: float = 0.5) -> Image.Image:
    """
    흰 배경을 크림/노란빛으로 변환.
    strength 0~1.
    """
    if strength <= 0:
        return img
    arr = _to_np(img)
    # 배경(밝은 픽셀)에만 황변 적용
    mask = arr.mean(axis=2) > 200   # shape (H, W)
    level = strength * 35  # 22 -> 35 로 상향
    arr[mask, 0] -= level * 0.1    # R 아주 약간 감소
    arr[mask, 1] -= level * 0.4    # G 약간 감소
    arr[mask, 2] -= level          # B 감소 (노랗게)
    return _to_pil(arr)


# ──────────────────────────────────────────────
# 2. 가우시안 노이즈
# ──────────────────────────────────────────────
def apply_gaussian_noise(img: Image.Image, sigma: float = 5.0) -> Image.Image:
    if sigma <= 0:
        return img
    arr = _to_np(img)
    noise = np.random.normal(0, sigma, arr.shape).astype(np.float32)
    return _to_pil(arr + noise)


# ──────────────────────────────────────────────
# 3. 미세 회전 + bbox 좌표 변환
# ──────────────────────────────────────────────
def _rotate_point(px, py, cx, cy, angle_rad):
    """점 (px,py)를 중심 (cx,cy) 기준으로 angle_rad 회전"""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    dx, dy = px - cx, py - cy
    nx = cx + dx * cos_a - dy * sin_a
    ny = cy + dx * sin_a + dy * cos_a
    return nx, ny


def apply_rotation(
    img: Image.Image,
    entries,           # List[BBoxEntry]
    angle_deg: float = 0.0,
) -> Tuple[Image.Image, list]:
    """
    이미지를 angle_deg 만큼 회전하고 bbox 좌표도 동기화.
    반환: (회전된 이미지, 업데이트된 entries)
    """
    if abs(angle_deg) < 0.01:
        return img, entries

    angle_rad = math.radians(angle_deg)
    w, h = img.size
    cx, cy = w / 2, h / 2

    rotated = img.rotate(-angle_deg, resample=Image.BICUBIC,
                         expand=True, fillcolor=(255, 255, 255))

    # expand=True 시 캔버스 크기 변하므로 offset 계산
    new_w, new_h = rotated.size
    ox = (new_w - w) / 2
    oy = (new_h - h) / 2

    from src.layout import BBoxEntry  # 순환 import 방지용 지연 import

    new_entries = []
    for e in entries:
        corners = [
            (e.x1, e.y1), (e.x2, e.y1),
            (e.x2, e.y2), (e.x1, e.y2),
        ]
        rotated_corners = [
            _rotate_point(px, py, cx, cy, angle_rad)
            for px, py in corners
        ]
        xs = [p[0] + ox for p in rotated_corners]
        ys = [p[1] + oy for p in rotated_corners]

        new_entries.append(BBoxEntry(
            x1=int(min(xs)), y1=int(min(ys)),
            x2=int(max(xs)), y2=int(max(ys)),
            text=e.text,
        ))

    return rotated, new_entries


# ──────────────────────────────────────────────
# 4. 원통형 왜곡 (barrel distortion)
# ──────────────────────────────────────────────
def apply_barrel_distortion(img: Image.Image, k: float = 0.015) -> Image.Image:
    """
    영수증이 약간 말려있는 느낌.
    k: 왜곡 계수 (0.01~0.03 권장)
    """
    if k <= 0:
        return img
    arr = np.array(img)
    h, w = arr.shape[:2]
    cx, cy = w / 2, h / 2

    # 역방향 매핑 (출력→입력)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    xn = (xs - cx) / cx
    yn = (ys - cy) / cy
    r2 = xn**2 + yn**2
    factor = 1 + k * r2
    xs_src = (xn * factor * cx + cx).astype(np.float32)
    ys_src = (yn * factor * cy + cy).astype(np.float32)

    # 범위 클리핑
    xs_src = np.clip(xs_src, 0, w - 1).astype(np.int32)
    ys_src = np.clip(ys_src, 0, h - 1).astype(np.int32)

    out = arr[ys_src, xs_src]
    return Image.fromarray(out)


# ──────────────────────────────────────────────
# 5. 밝기 / 대비 변동
# ──────────────────────────────────────────────
def apply_brightness_contrast(
    img: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.0,
) -> Image.Image:
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    return img


# ──────────────────────────────────────────────
# 6. 모션 블러 (스캔 흔들림)
# ──────────────────────────────────────────────
def apply_motion_blur(img: Image.Image, size: int = 2) -> Image.Image:
    if size <= 1:
        return img
    kernel = np.zeros((size, size))
    kernel[int((size - 1) / 2), :] = np.ones(size)
    kernel /= size
    from PIL import ImageFilter
    # PIL 에 직접 convolution 커널 전달
    kern_flat = kernel.flatten().tolist()
    img = img.filter(ImageFilter.Kernel(
        size=(size, size), kernel=kern_flat, scale=1, offset=0
    ))
    return img


# ──────────────────────────────────────────────
# 파이프라인 진입점
# ──────────────────────────────────────────────
def apply_pipeline(
    img: Image.Image,
    entries,
    opts: dict,
    rng: random.Random = None,
) -> Tuple[Image.Image, list]:
    """
    노이즈 파이프라인 전체 실행.

    opts 키:
        noise_strength  float 0~1   : 전체 강도 스케일 (UI 슬라이더)
        max_angle       float 0~5   : 최대 회전 각도 (도)
        jpeg_quality    int   60~100: JPEG 저장 품질 (exporter 에서 사용)
        bg_tint         bool        : 배경 황변 여부
        barrel          bool        : 원통형 왜곡 여부
        motion_blur     bool        : 모션 블러 여부
    """
    r = rng or random.Random()
    ns = opts.get("noise_strength", 0.5)

    # 1. 배경 황변
    bg_aging = opts.get("bg_aging", 0.0)
    if bg_aging > 0:
        # General Noise(ns)와 독립시키고 기본 강도 상향
        img = apply_background_tint(img, strength=bg_aging * r.uniform(0.8, 1.2))

    # 2. 가우시안 노이즈
    sigma = ns * r.uniform(0, 12)
    img = apply_gaussian_noise(img, sigma=sigma)

    # 3. 회전 (bbox 동기화)
    max_angle = opts.get("max_angle", 0.0)
    if max_angle > 0:
        angle = r.uniform(-max_angle, max_angle)
        img, entries = apply_rotation(img, entries, angle_deg=angle)

    # 4. 원통형 왜곡
    barrel_amt = opts.get("barrel_amt", 0.0)
    if barrel_amt > 0:
        # General Noise(ns)와 독립
        k = barrel_amt * r.uniform(0.8, 1.2)
        img = apply_barrel_distortion(img, k=k)

    # 5. 밝기/대비
    bright = r.uniform(1 - 0.15 * ns, 1 + 0.15 * ns)
    cont   = r.uniform(1 - 0.20 * ns, 1 + 0.20 * ns)
    img = apply_brightness_contrast(img, brightness=bright, contrast=cont)

    # 6. 모션 블러
    blur_size = opts.get("blur_size", 0)
    if blur_size > 0:
        # noise_strength가 낮으면 블러 확률적으로 적용하거나 약하게
        if ns > 0.2 or r.random() < 0.5:
            try:
                img = apply_motion_blur(img, size=int(blur_size))
            except Exception:
                pass

    return img, entries
