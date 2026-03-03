"""
app.py — Tkinter 기반 영수증 생성기 UI
PyInstaller --onefile --windowed 빌드 대응
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# PyInstaller 리소스 경로
def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# ──────────────────────────────────────────────
# 폰트 자동 다운로드
# ──────────────────────────────────────────────
FONT_URLS = {
    "CourierPrime-Regular.ttf":   "https://github.com/quoteunquoteapps/CourierPrime/raw/master/fonts/ttf/CourierPrime-Regular.ttf",
    "ShareTechMono-Regular.ttf":  "https://github.com/google/fonts/raw/main/ofl/sharetechmono/ShareTechMono-Regular.ttf",
    "CutiveMono-Regular.ttf":     "https://github.com/google/fonts/raw/main/ofl/cutivemono/CutiveMono-Regular.ttf",
    "SpecialElite-Regular.ttf":   "https://github.com/google/fonts/raw/main/apache/specialelite/SpecialElite-Regular.ttf",
    "OCRB.ttf":                   "https://github.com/twardoch/ur-ocrb-font/raw/master/fonts/OCRB.ttf",
}


def ensure_fonts(log_cb=None):
    fonts_dir = resource_path("fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    missing = [f for f in FONT_URLS if not os.path.exists(os.path.join(fonts_dir, f))]
    if not missing:
        return
    try:
        import requests
    except ImportError:
        if log_cb:
            log_cb("[WARN] requests 없음 — 폰트 자동 다운로드 불가. 기본 폰트 사용.")
        return

    for fname in missing:
        url = FONT_URLS[fname]
        dest = os.path.join(fonts_dir, fname)
        if log_cb:
            log_cb(f"[폰트 다운로드] {fname} ...")
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
            if log_cb:
                log_cb(f"  ✓ {fname}")
        except Exception as e:
            if log_cb:
                log_cb(f"  ✗ {fname}: {e}")


# ──────────────────────────────────────────────
# 메인 앱
# ──────────────────────────────────────────────
class ReceiptGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Receipt Data Generator — SROIE Format")
        self.resizable(False, False)
        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI 구성 ───────────────────────────────
    def _build_ui(self):
        PAD = dict(padx=8, pady=4)

        # ── 상단 제목
        title_frame = tk.Frame(self, bg="#2C3E50")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(
            title_frame,
            text="📄  Receipt Data Generator",
            font=("Segoe UI", 16, "bold"),
            bg="#2C3E50", fg="white",
            pady=10, padx=14,
        ).pack(anchor="w")

        # ── 왼쪽 옵션 패널
        left = tk.LabelFrame(self, text="Generation Options", font=("Segoe UI", 10, "bold"),
                             padx=10, pady=8)
        left.grid(row=1, column=0, sticky="nw", padx=12, pady=8)

        # 출력 경로
        tk.Label(left, text="Output folder:", anchor="w").grid(row=0, column=0, sticky="w", **PAD)
        self.var_output = tk.StringVar(value=os.path.join(os.getcwd(), "output"))
        tk.Entry(left, textvariable=self.var_output, width=32).grid(row=0, column=1, **PAD)
        tk.Button(left, text="Browse…", command=self._browse_output).grid(row=0, column=2, **PAD)

        # 생성 개수
        tk.Label(left, text="Count:", anchor="w").grid(row=1, column=0, sticky="w", **PAD)
        self.var_count = tk.IntVar(value=100)
        tk.Spinbox(left, from_=1, to=9999, textvariable=self.var_count, width=8).grid(
            row=1, column=1, sticky="w", **PAD)

        # 파일명 프리픽스
        tk.Label(left, text="File Prefix:", anchor="w").grid(row=1, column=2, sticky="w", **PAD)
        self.var_prefix = tk.StringVar(value="aug")
        tk.Entry(left, textvariable=self.var_prefix, width=8).grid(row=1, column=2, sticky="e", **PAD)

        # 폰트
        tk.Label(left, text="Font:", anchor="w").grid(row=2, column=0, sticky="w", **PAD)
        self.var_font = tk.StringVar(value="Random")
        font_choices = ["Random", "Courier Prime", "Share Tech Mono",
                        "Cutive Mono", "Special Elite", "OCR-B"]
        ttk.Combobox(left, textvariable=self.var_font, values=font_choices,
                     state="readonly", width=22).grid(row=2, column=1, sticky="w", **PAD)

        # 품목 수 범위
        tk.Label(left, text="Items (min/max):", anchor="w").grid(row=3, column=0, sticky="w", **PAD)
        item_frame = tk.Frame(left)
        item_frame.grid(row=3, column=1, sticky="w", **PAD)
        self.var_items_min = tk.IntVar(value=1)
        self.var_items_max = tk.IntVar(value=8)
        tk.Spinbox(item_frame, from_=1, to=20, textvariable=self.var_items_min, width=5).pack(side="left")
        tk.Label(item_frame, text=" ~ ").pack(side="left")
        tk.Spinbox(item_frame, from_=1, to=20, textvariable=self.var_items_max, width=5).pack(side="left")

        # 구분선
        ttk.Separator(left, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=6)

        # 노이즈 강도 (가우시안 노이즈 기본 스케일)
        self._make_scale(left, row=5, label="General Noise:",
                         varname="var_noise", from_=0.0, to=1.0, resolution=0.05,
                         default=0.4)
        # 최대 회전 각도
        self._make_scale(left, row=6, label="Max rotation (°):",
                         varname="var_angle", from_=0.0, to=5.0, resolution=0.5,
                         default=0.0)
        # 줄별 지터 (미세 기울기)
        self._make_scale(left, row=7, label="Line Jitter (°):",
                         varname="var_line_jitter", from_=0.0, to=2.0, resolution=0.1,
                         default=0.0)
        
        # 배경 황변 (Thermal Aging)
        self._make_scale(left, row=8, label="BG Aging strength:",
                         varname="var_bg_aging", from_=0.0, to=1.0, resolution=0.1,
                         default=0.3)
        
        # 원통형 왜곡 (Barrel)
        self._make_scale(left, row=9, label="Barrel distort:",
                         varname="var_barrel_amt", from_=0.0, to=0.05, resolution=0.005,
                         default=0.0)

        # 모션 블러 (Blur)
        self._make_scale(left, row=10, label="Motion Blur amt:",
                         varname="var_blur_size", from_=0, to=5, resolution=1,
                         default=0, as_int=True)

        # JPEG 품질
        self._make_scale(left, row=11, label="JPEG quality:",
                         varname="var_jpeg", from_=60, to=100, resolution=5,
                         default=85, as_int=True)

        # 구분선
        ttk.Separator(left, orient="horizontal").grid(
            row=12, column=0, columnspan=3, sticky="ew", pady=8)

        # 랜덤 모드 (세분화)
        rand_frame = tk.LabelFrame(left, text="✨ Auto-Randomize (Override sliders)", fg="#E67E22")
        rand_frame.grid(row=13, column=0, columnspan=3, sticky="ew", **PAD)
        
        self.var_rand_font   = tk.BooleanVar(value=False)
        self.var_rand_items  = tk.BooleanVar(value=False)
        self.var_rand_noise  = tk.BooleanVar(value=False)
        self.var_rand_rot    = tk.BooleanVar(value=False)
        self.var_rand_jitter = tk.BooleanVar(value=False)
        self.var_rand_bg     = tk.BooleanVar(value=False)
        self.var_rand_barrel = tk.BooleanVar(value=False)
        self.var_rand_blur   = tk.BooleanVar(value=False)
        self.var_rand_jpeg   = tk.BooleanVar(value=False)

        # 3줄로 배치 (3개씩)
        tk.Checkbutton(rand_frame, text="Font", variable=self.var_rand_font).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(rand_frame, text="Items", variable=self.var_rand_items).grid(row=0, column=1, sticky="w")
        tk.Checkbutton(rand_frame, text="Noise", variable=self.var_rand_noise).grid(row=0, column=2, sticky="w")
        
        tk.Checkbutton(rand_frame, text="Rotation", variable=self.var_rand_rot).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(rand_frame, text="Jitter", variable=self.var_rand_jitter).grid(row=1, column=1, sticky="w")
        tk.Checkbutton(rand_frame, text="BG-Tint", variable=self.var_rand_bg).grid(row=1, column=2, sticky="w")
        
        tk.Checkbutton(rand_frame, text="Barrel", variable=self.var_rand_barrel).grid(row=2, column=0, sticky="w")
        tk.Checkbutton(rand_frame, text="Blur", variable=self.var_rand_blur).grid(row=2, column=1, sticky="w")
        tk.Checkbutton(rand_frame, text="JPEG", variable=self.var_rand_jpeg).grid(row=2, column=2, sticky="w")

        # 구분선
        ttk.Separator(left, orient="horizontal").grid(
            row=15, column=0, columnspan=3, sticky="ew", pady=6)

        # 랜덤 시드
        seed_frame = tk.Frame(left)
        seed_frame.grid(row=16, column=0, columnspan=3, sticky="w", **PAD)
        self.var_use_seed = tk.BooleanVar(value=False)
        tk.Checkbutton(seed_frame, text="Fix seed:", variable=self.var_use_seed).pack(side="left")
        self.var_seed = tk.IntVar(value=42)
        tk.Spinbox(seed_frame, from_=0, to=99999999, textvariable=self.var_seed, width=10).pack(side="left")

        # ── 오른쪽 로그 패널
        right = tk.LabelFrame(self, text="Log", font=("Segoe UI", 10, "bold"),
                              padx=10, pady=8)
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=8)

        self.log_box = scrolledtext.ScrolledText(
            right, width=42, height=22, state="disabled",
            font=("Consolas", 9), bg="#1E1E1E", fg="#D4D4D4",
        )
        self.log_box.pack(fill="both", expand=True)

        # ── 하단 진행바 + 버튼
        bottom = tk.Frame(self)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))

        self.progress = ttk.Progressbar(bottom, orient="horizontal",
                                        mode="determinate", length=420)
        self.progress.pack(side="left", padx=(0, 10))

        self.lbl_progress = tk.Label(bottom, text="Ready", fg="#555", font=("Segoe UI", 9))
        self.lbl_progress.pack(side="left")

        self.btn_generate = tk.Button(
            bottom, text="▶  Generate", font=("Segoe UI", 11, "bold"),
            bg="#27AE60", fg="white", activebackground="#1E8449",
            relief="flat", padx=16, pady=6,
            command=self._on_generate,
        )
        self.btn_generate.pack(side="right")

    def _make_scale(self, parent, row, label, varname, from_, to, resolution,
                    default, as_int=False):
        PAD = dict(padx=8, pady=2)
        tk.Label(parent, text=label, anchor="w").grid(row=row, column=0, sticky="w", **PAD)
        var = tk.DoubleVar(value=default) if not as_int else tk.IntVar(value=int(default))
        setattr(self, varname, var)
        scale = tk.Scale(parent, variable=var, from_=from_, to=to,
                         resolution=resolution, orient="horizontal",
                         length=180, sliderlength=16)
        scale.grid(row=row, column=1, sticky="w", **PAD)
        val_lbl = tk.Label(parent, textvariable=var, width=5, anchor="w")
        val_lbl.grid(row=row, column=2, sticky="w")

    def _browse_output(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.var_output.set(d)

    # ── 로그 ─────────────────────────────────
    def _log(self, msg: str):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _do)

    # ── 생성 실행 ─────────────────────────────
    def _collect_opts(self) -> dict:
        font_sel = self.var_font.get()
        import random as _rnd
        if font_sel == "Random":
            font_name = _rnd.choice([
                "Courier Prime", "Share Tech Mono",
                "Cutive Mono", "Special Elite", "OCR-B",
            ])
        else:
            font_name = font_sel

        return {
            "font_name":     font_name,
            "body_size":     12,
            "n_items_min":   self.var_items_min.get(),
            "n_items_max":   self.var_items_max.get(),
            "line_jitter":   self.var_line_jitter.get(),
            "noise_strength":self.var_noise.get(),
            "max_angle":     self.var_angle.get(),
            "jpeg_quality":  int(self.var_jpeg.get()),
            "bg_aging":      self.var_bg_aging.get(),
            "barrel_amt":    self.var_barrel_amt.get(),
            "blur_size":     int(self.var_blur_size.get()),
            "rand_font":     self.var_rand_font.get(),
            "rand_items":    self.var_rand_items.get(),
            "rand_noise":    self.var_rand_noise.get(),
            "rand_rot":      self.var_rand_rot.get(),
            "rand_jitter":   self.var_rand_jitter.get(),
            "rand_bg":       self.var_rand_bg.get(),
            "rand_barrel":   self.var_rand_barrel.get(),
            "rand_blur":     self.var_rand_blur.get(),
            "rand_jpeg":     self.var_rand_jpeg.get(),
            "file_prefix":   self.var_prefix.get().strip() or "aug",
            "seed":          self.var_seed.get() if self.var_use_seed.get() else None,
        }

    def _on_generate(self):
        n = self.var_count.get()
        output_dir = self.var_output.get().strip()
        if not output_dir:
            messagebox.showerror("Error", "Output folder is required.")
            return
        if n < 1:
            messagebox.showerror("Error", "Count must be ≥ 1.")
            return

        opts = self._collect_opts()
        self.btn_generate.config(state="disabled", text="Generating…")
        self.progress["value"] = 0
        self.progress["maximum"] = n
        self._log(f"\n{'='*40}")
        self._log(f"Starting generation: {n} receipts → {output_dir}")
        self._log(f"Font: {opts['font_name']}  |  Noise: {opts['noise_strength']:.2f}  "
                  f"|  Angle: ±{opts['max_angle']}°  |  JPEG: {opts['jpeg_quality']}")
        self._log(f"{'='*40}")

        def _run():
            # 폰트 다운로드 (없으면)
            ensure_fonts(log_cb=self._log)

            def _prog(cur, total, rid):
                def _update():
                    self.progress["value"] = cur
                    self.lbl_progress.config(text=f"{cur}/{total}  ({rid})")
                    if cur % max(1, total // 20) == 0 or cur == total:
                        self._log(f"  [{cur:>4}/{total}] {rid}")
                self.after(0, _update)

            try:
                from src.generator import generate_batch
                ids = generate_batch(n, output_dir, opts, progress_cb=_prog)
                def _done():
                    self._log(f"\n✓ Done! {len(ids)} receipts saved to:")
                    self._log(f"  {output_dir}")
                    self.lbl_progress.config(text=f"Done — {len(ids)} receipts")
                    self.btn_generate.config(state="normal", text="▶  Generate")
                    messagebox.showinfo("Complete",
                                        f"{len(ids)} receipts generated!\n\n{output_dir}")
                self.after(0, _done)
            except Exception as ex:
                import traceback
                tb = traceback.format_exc()
                def _err():
                    self._log(f"\n[ERROR] {ex}\n{tb}")
                    self.btn_generate.config(state="normal", text="▶  Generate")
                    messagebox.showerror("Error", str(ex))
                self.after(0, _err)

        threading.Thread(target=_run, daemon=True).start()


# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = ReceiptGeneratorApp()
    app.mainloop()
