"""
generator.py — 메인 파이프라인
corpus → layout → noise → export
"""
import random
import uuid
from typing import Callable, Optional

from src.corpus import generate_all
from src.exporter import save_receipt
from src.layout import ReceiptRenderer
from src.noise import apply_pipeline


def generate_batch(
    n: int,
    output_dir: str,
    opts: dict,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
):
    """
    영수증 n장 생성.

    Parameters
    ----------
    n           : 생성 수량
    output_dir  : 저장 폴더 (img/box/entities 하위 폴더 자동 생성)
    opts        : 옵션 dict (app.py에서 수집)
        font_name       str   : 렌더 폰트 이름
        body_size       int   : 본문 폰트 크기 (기본 12)
        n_items_min     int   : 최소 품목 수
        n_items_max     int   : 최대 품목 수
        noise_strength  float : 노이즈 강도 0~1
        max_angle       float : 최대 회전 각도
        jpeg_quality    int   : JPEG 품질 60~100
        bg_tint         bool  : 배경 황변
        barrel          bool  : 원통형 왜곡
        motion_blur     bool  : 모션 블러
        seed            int|None : 랜덤 시드 (None=랜덤)
    progress_cb : (current, total, receipt_id) → None

    Returns
    -------
    list[str] : 생성된 receipt_id 목록
    """
    seed = opts.get("seed", None)
    master_rng = random.Random(seed) if seed is not None else random.Random()

    # 기본 옵션들 추출
    font_fixed = opts.get("font_name", "Courier Prime")
    jitter_fixed = float(opts.get("line_jitter", 0.0))
    jpeg_fixed = int(opts.get("jpeg_quality", 85))
    blur_fixed = int(opts.get("blur_size", 0))
    bg_fixed   = float(opts.get("bg_aging", 0.3))
    barrel_fixed = float(opts.get("barrel_amt", 0.0))
    
    n_min = int(opts.get("n_items_min", 1))
    n_max = int(opts.get("n_items_max", 8))
    
    # 랜덤화 플래그
    r_font   = opts.get("rand_font", False)
    r_items  = opts.get("rand_items", False)
    r_noise  = opts.get("rand_noise", False)
    r_rot    = opts.get("rand_rot", False)
    r_jitter = opts.get("rand_jitter", False)
    r_bg     = opts.get("rand_bg", False)
    r_barrel = opts.get("rand_barrel", False)
    r_blur   = opts.get("rand_blur", False)
    r_jpeg   = opts.get("rand_jpeg", False)

    renderers = {}
    def get_renderer(f_name, j_max, rng):
        key = (f_name, j_max)
        if key not in renderers:
            renderers[key] = ReceiptRenderer(
                font_name=f_name, rng=rng, jitter_max_angle=j_max
            )
        return renderers[key]

    generated_ids = []

    for i in range(n):
        item_rng = random.Random(master_rng.randint(0, 2**31))
        
        # --- 파라미터 결정 ---
        cur_font = item_rng.choice(["Courier Prime", "Share Tech Mono", "Cutive Mono", "Special Elite", "OCR-B"]) if r_font else font_fixed
        cur_jitter = item_rng.uniform(0.0, 1.0) if r_jitter else jitter_fixed
        cur_n_items = item_rng.randint(1, 12) if r_items else item_rng.randint(n_min, n_max)
        cur_jpeg = item_rng.randint(65, 95) if r_jpeg else jpeg_fixed
        cur_blur = item_rng.randint(0, 4) if r_blur else blur_fixed
        
        cur_opts = opts.copy()
        cur_opts["blur_size"] = cur_blur
        if r_noise:
            cur_opts["noise_strength"] = item_rng.uniform(0.2, 0.8)
        if r_rot:
            cur_opts["max_angle"] = item_rng.uniform(1.0, 3.0)
        
        if r_bg:
            cur_opts["bg_aging"] = item_rng.uniform(0.1, 0.6)
        else:
            cur_opts["bg_aging"] = bg_fixed

        if r_barrel:
            cur_opts["barrel_amt"] = item_rng.uniform(0.005, 0.02)
        else:
            cur_opts["barrel_amt"] = barrel_fixed

        renderer = get_renderer(cur_font, cur_jitter, master_rng)
        corpus = generate_all(n_items=cur_n_items, seed=item_rng.randint(0, 2**31))

        img, entries = renderer.render(corpus)
        img, entries = apply_pipeline(img, entries, cur_opts, rng=random.Random(master_rng.randint(0, 2**31)))

        # --- 파일명 생성 ---
        prefix = opts.get("file_prefix", "aug")
        suffix = "".join([str(item_rng.randint(0, 9)) for _ in range(11)])
        receipt_id = f"{prefix}{suffix}"

        save_receipt(
            receipt_id=receipt_id, img=img, entries=entries, corpus=corpus,
            output_dir=output_dir, jpeg_quality=cur_jpeg
        )
        generated_ids.append(receipt_id)
        if progress_cb:
            progress_cb(i + 1, n, receipt_id)

    return generated_ids
