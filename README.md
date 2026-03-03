# Receipt Data Generator

SROIE 포맷(img / box / entities) 영수증 합성 데이터 생성기.  
LayoutLM 훈련 데이터 증강 목적.

## 빠른 시작

```bash
pip install -r requirements.txt
python app.py
```

## 생성 옵션 가이드

| 옵션 | 설명 | 권장값 |
|---|---|---|
| **Output folder** | 생성된 이미지와 텍스트 파일이 저장될 경로. | - |
| **Count** | 생성할 영수증 총 개수 | - |
| **File Prefix** | 파일명의 시작 접두사. (기본값: 'aug') | aug |
| **Font** | 영수증에 사용할 폰트 (5종 및 랜덤) | Random |
| **Items (min/max)** | 각 영수증에 들어갈 품목 수의 범위. | 1 ~ 8 |
| **General Noise** | 가우시안 노이즈의 기본 강도 (0~1). | 0.4 |
| **Max rotation (°)** | 영수증 전체의 최대 기울기 각도. | 0.0 ~ 2.0 |
| **Line Jitter (°)** | **[핵심]** 각 줄별 개별 미세 회전 강도. 인쇄 불균형 재현. | 0.0 ~ 0.5 |
| **BG Aging strength** | 감열지가 오래되어 누렇게 변색된 효과의 강도. | 0.3 |
| **Barrel distort** | 영수증 종이가 둥글게 말려있는 듯한 왜곡 강도. | 0.0 |
| **Motion Blur amt** | 스캔 흔들림 효과의 밀림 정도 (0: 없음). | 0 |
| **JPEG quality** | JPEG 압축 손실 정도. 낮을수록 아티팩트가 심함. | 85 |
| **Auto-Randomize** | **[신규]** 체크한 항목(Font, Items, Noise, Rotation, Jitter, BG, Barrel, Blur, JPEG)을 매 장마다 자동 무작위화함. | - |
| **Fix seed** | 동일한 데이터를 재생성하기 위한 랜덤 시드 고정 | - |

## 🖋️ 폰트 및 라이선스 (Fonts & License)

본 프로젝트는 영수증 특유의 질감을 재현하기 위해 다음 10종의 오픈소스 폰트를 사용합니다. 모든 폰트는 **SIL Open Font License (OFL)** 또는 **Apache License 2.0** 하에 배포되므로, 상업적 이용 및 학습/연구 목적으로 자유롭게 사용할 수 있습니다.

| 폰트명 | 스타일 특징 | 라이선스 |
|---|---|---|
| **Courier Prime** | 클래식 도트 프린터 / 타자기 느낌 | OFL |
| **Share Tech Mono** | 세련된 현대식 감열 영수증 느낌 | OFL |
| **Cutive Mono** | 빈티지 타자기 스타일 | OFL |
| **Special Elite** | 거친 인쇄 질감이 살아있는 구형 영수증 | Apache 2.0 |
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
