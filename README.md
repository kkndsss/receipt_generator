# 🧾 SROIE Receipt Data Generator

본 도구는 OCR 학습을 위한 **SROIE 포맷(이미지, BBox 좌표, 핵심 엔티티)** 가상 영수증 데이터를 대량으로 생성하는 도구입니다. 실제 영수증의 '지저분한' 느낌과 다양한 레이아웃을 정교하게 재현하여 모델의 성능을 높이는 데 특화되어 있습니다.

---

## 🚀 주요 특징
- **10종 프리미엄 폰트**: 감열지 프린터, 도트 프린터 느낌의 전용 폰트가 내장되어 있습니다.
- **다채로운 레이아웃**: Classic, Modern, Dense 스타일 및 항목 무작위 셔플링을 지원합니다.
- **리얼리티 노이즈**: 배경 황변(Aging), 미세 회전, 모션 블러, Barrel 왜곡 등 실제 스캔본의 특징을 구현합니다.
- **SROIE 규격 준수**: 별도의 변환 없이 바로 학습에 사용할 수 있는 정답 포맷을 출력합니다.

---

## 🛠 옵션 가이드 (리얼리티 꿀팁)

초보자분들을 위해 각 슬라이더가 결과물에 어떤 영향을 주는지 상세히 설명합니다.

### 1. 기본 설정 (Basic)
- **Count**: 생성할 영수증의 총 개수입니다.
- **Font**: 특정 폰트를 지정하거나 `Random`으로 설정해 매 장마다 다른 폰트를 쓰게 할 수 있습니다.
- **Layout Style**: `Classic`(가운데 정렬), `Modern`(좌측 정렬), `Dense`(여백 최소화) 중 선택합니다.

### 2. 가공 설정 (Noise & Distortion)
| 옵션명 | 추천값 | 효과 설명 |
|:--- |:---:|:--- |
| **General Noise** | `0.3` | **이미지 전반의 지저분함.** 올릴수록 입자감이 심해지고 장당 밝기/대비 랜덤성이 커집니다. |
| **Line Jitter** | `0.5` | **인쇄 수평 불일치.** 실제 영수증의 '줄 비뚤어짐'을 재현합니다. |
| **BG Aging** | `0.7` | **종이 노후화.** 하얀 배경을 실제 감열지처럼 노랗고 낡은 느낌으로 바꿉니다. |
| **Barrel Distort** | `0.015` | **종이 굴곡.** 영수증이 말려 있거나 접힌 느낌을 주기 위해 이미지를 미세하게 볼록하게 만듭니다. |
| **Motion Blur** | `1~2` | **스캔 흔들림.** 카메라가 흔들렸을 때 발생하는 미세한 잔상을 만듭니다. |
| **JPEG Quality** | `80` | **화질 열화.** 값을 낮출수록(최소 30) 압축 노이즈가 심해져 실제 저화질 사진 느낌이 납니다. |

> [!TIP]
> **Auto-Randomize (✨)** 체크박스를 켜면, 슬라이더 설정값을 무시하고 매 장마다 해당 항목이 **완전 무작위**로 변합니다. 데이터의 다양성을 극대화할 때 유용합니다.

---

## 🎨 추천 조합 (Presets)

어떤 값을 줄지 고민된다면 다음 조합을 참고하세요!

#### 📸 "실제 폰카 촬영" 느낌 (High Realism)
- **Line Jitter**: 0.6 / **BG Aging**: 0.5 / **Barrel**: 0.020 / **JPEG**: 75
- *결과: 약간 휘어지고 색이 바랜 종이를 폰으로 찍은 듯한 느낌*

#### 📠 "오래된 팩스/스캔" 느낌 (Vintage Scan)
- **General Noise**: 0.6 / **Motion Blur**: 2 / **BG Aging**: 0.8 / **JPEG**: 60
- *결과: 입자감이 심하고 노랗게 뜬, 화질 나쁜 스캔본 느낌*

#### 📝 "깨끗한 렌더링" (Clean OCR)
- **모든 슬라이더**: 0 (단, Line Jitter는 0.1 정도 주는 것이 자연스러움)
- *결과: 텍스트가 명확하게 보이는 깔끔한 이미지*

---

## 📦 실행 방법

### 1. 실행 파일 (EXE) 사용
`dist/receipt_generator.exe` 파일을 실행하세요. Python 설치가 필요 없습니다!

### 2. 소스 코드에서 실행
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 앱 실행
python app.py
```

---

## 📄 출력 데이터 구조
지정한 폴더 내에 3개의 서브 폴더가 생성됩니다.
- `img/`: 영수증 이미지 (`.jpg`)
- `box/`: 8-point 좌표와 텍스트 (`.txt`). **구분선 기호는 제외**된 깔끔한 텍스트만 저장됩니다.
- `entities/`: `{company, date, address, total}` 정보가 담긴 JSON 파일.

---

## ⚖️ 폰트 및 라이선스
본 도구에 포함된 모든 폰트(VT323, IBM Plex Mono 등 10종)는 **SIL Open Font License** 또는 **Apache License 2.0** 하에 배포되는 오픈소스 폰트로, 상업적/연구용으로 자유롭게 사용 가능합니다.
| **VT323** | **[추천]** 전형적인 8비트/도트 매트릭스 프린터 스타일 | OFL |
| **IBM Plex Mono** | 가독성이 뛰어난 현대적 영수증 스타일 | OFL |
| **Space Mono** | 미래지향적/기계적인 느낌의 영수증 | OFL |
| **Nanum Gothic** | 깔끔한 나눔고딕 코딩용 가변폭 폰트 | OFL |
| **Anonymous Pro** | 좁은 간격의 기계식 폰트 | OFL |
| **Nova Mono** | 독특한 디자인의 기계적 폰트 | OFL |

## 디렉토리 구조

```
receipt_generator/
├── src/
│   ├── corpus.py      # 텍스트 코퍼스 (Faker + wordlist)
│   ├── layout.py      # Pillow 렌더러 (Line Jitter 포함)
│   ├── noise.py       # 노이즈 파이프라인
│   ├── exporter.py    # SROIE 포맷 저장
│   └── generator.py   # 메인 파이프라인
├── fonts/             # 폰트 (없으면 자동 다운로드)
├── app.py             # Tkinter UI
└── requirements.txt
```

## 출력 포맷

- `img/{id}.jpg` — 영수증 이미지
- `box/{id}.txt` — OCR bbox (8-point, SROIE 호환)
- `entities/{id}.txt` — JSON `{company, date, address, total}`

## 단일 실행파일로 빌드 (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "fonts;fonts" --name receipt_generator app.py
# 결과: dist/receipt_generator.exe
```
