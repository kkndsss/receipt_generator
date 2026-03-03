"""
corpus.py — 영수증 텍스트 코퍼스 생성 (Faker + 커스텀 wordlist)
말레이시아식 영어 영수증 패턴을 재현한다.
"""
import random
from faker import Faker

fake = Faker("en_US")

# ──────────────────────────────────────────────
# 법인 접미사 (말레이시아식)
# ──────────────────────────────────────────────
COMPANY_SUFFIXES = [
    "SDN BHD", "SDN. BHD.", "BHD", "CO. LTD", "(M) SDN BHD",
    "ENTERPRISE", "TRADING", "& CO", "GROUP SDN BHD",
    "INDUSTRIES SDN BHD", "HOLDINGS BHD",
]

COMPANY_TYPES = [
    "BOOK STORE", "MART", "SUPERSTORE", "MINIMARKET", "PHARMACY",
    "ELECTRONICS", "HARDWARE", "FASHION", "FOOD & BEVERAGE",
    "CONVENIENCE STORE", "STATIONERY", "SUPPLIES",
]

FIRST_NAMES = [
    "TAN", "WONG", "LIM", "CHAI", "ONG", "LEE", "CHEAH", "KOH",
    "GOH", "YEOH", "AHMAD", "HASSAN", "ISMAIL", "RAZAK", "RASHID",
    "KUMAR", "RAJAN", "KRISHNAN", "MUTHU", "GANESH",
]

TAMAN_NAMES = [
    "TAMAN DAYA", "TAMAN MAJU", "TAMAN BAHAGIA", "TAMAN INDAH",
    "TAMAN SRI MUDA", "TAMAN PELANGI", "TAMAN SETIA", "TAMAN JAYA",
    "TAMAN MEGAH", "TAMAN PUTRA", "TAMAN DAMAI",
]

STATES = [
    ("JOHOR BAHRU", "JOHOR", "80000"),
    ("KUALA LUMPUR", "WILAYAH PERSEKUTUAN", "50000"),
    ("PETALING JAYA", "SELANGOR", "46000"),
    ("KUCHING", "SARAWAK", "93000"),
    ("KOTA KINABALU", "SABAH", "88000"),
    ("IPOH", "PERAK", "30000"),
    ("ALOR SETAR", "KEDAH", "05000"),
    ("SEREMBAN", "NEGERI SEMBILAN", "70000"),
    ("MELAKA", "MELAKA", "75000"),
    ("SHAH ALAM", "SELANGOR", "40000"),
]

ROAD_PREFIXES = ["JALAN", "LORONG", "PERSIARAN", "LEBUH"]
ROAD_NAMES = [
    "SAGU", "MAJU", "BAHAGIA", "SEJAHTERA", "INDAH",
    "BESAR", "UTAMA", "BUNGA", "DAMAI", "SETIA",
]

# ──────────────────────────────────────────────
# 품목 wordlist
# ──────────────────────────────────────────────
ITEMS = [
    # 식음료
    ("COCA COLA 1.5L", (3.50, 4.50)),
    ("PEPSI 1.5L", (3.50, 4.50)),
    ("100 PLUS 1.5L", (3.80, 4.80)),
    ("MILO 3IN1 BOX 30S", (14.00, 18.00)),
    ("NESTUM ORIGINAL 500G", (9.00, 12.00)),
    ("MAGGI MEE GORENG 5S", (4.50, 6.00)),
    ("DUTCH LADY MILK 1L", (6.00, 8.00)),
    ("TESCO MINERAL WATER 1.5L", (1.20, 2.00)),
    ("F&N ORANGE 1.5L", (3.80, 5.00)),
    ("MUNCHYS LEXUS 165G", (5.00, 7.00)),
    ("GARDENIA WHITE BREAD", (3.00, 4.50)),
    ("ANCHOR CHEDDAR SLICES", (12.00, 16.00)),
    ("HEINZ KETCHUP 300ML", (6.00, 9.00)),
    # 문구/소모품
    ("A4 PAPER 80GSM 500S", (15.00, 22.00)),
    ("KF MODELLING CLAY KIDDY", (7.00, 12.00)),
    ("STABILO HIGHLIGHTER SET", (8.00, 14.00)),
    ("PILOT G2 PEN 0.7 BLK", (3.50, 5.00)),
    ("SCOTCH TAPE 24MM 30M", (2.50, 4.00)),
    ("STAPLER NO.10 MINI", (5.00, 9.00)),
    # 생활용품
    ("DETTOL HANDWASH 250ML", (8.00, 12.00)),
    ("SHOKUBUTSU BODY FOAM 750ML", (14.00, 19.00)),
    ("SOFTLAN FABRIC CONDITIONER", (11.00, 16.00)),
    ("DYNAMO DETERGENT 1.6KG", (18.00, 25.00)),
    ("FAIRY DISHWASH 500ML", (9.00, 13.00)),
    ("MAXWELL 100W BULB", (5.00, 9.00)),
    ("AA BATTERY 4PCS", (6.00, 10.00)),
    # 전자/기타
    ("USB CABLE TYPE-C 1M", (12.00, 20.00)),
    ("HDMI CABLE 1.5M", (15.00, 25.00)),
    ("EXTENSION CORD 3M", (18.00, 28.00)),
]

CASHIER_NAMES = [
    "MANIS", "RINA", "SITI", "AMINAH", "FARAH",
    "KUMAR", "RAJAN", "HASSAN", "HAFIZ", "AZMAN",
    "JENNY", "WENDY", "LIN", "MAY", "NANCY",
]

FOOTER_LINES = [
    ["GOODS SOLD ARE NOT RETURNABLE OR", "EXCHANGEABLE"],
    ["NO REFUND AFTER PAYMENT", "PLEASE CHECK YOUR ITEMS"],
    ["THANK YOU FOR YOUR PURCHASE", "HAVE A NICE DAY!"],
    ["ALL PRICES INCLUDE GST WHERE APPLICABLE"],
    ["KEEP THIS RECEIPT FOR WARRANTY CLAIM"],
    ["RECEIPT REQUIRED FOR EXCHANGE WITHIN 7 DAYS"],
]


def _rnd_price(lo, hi):
    """0.50 단위 가격 생성"""
    p = random.uniform(lo, hi)
    return round(round(p * 2) / 2, 2)


def generate_company():
    """회사명 생성"""
    style = random.randint(0, 2)
    if style == 0:
        name = random.choice(FIRST_NAMES)
        suffix = random.choice(COMPANY_SUFFIXES)
        return f"{name} {suffix}"
    elif style == 1:
        t = random.choice(TAMAN_NAMES).split()[1]
        ctype = random.choice(COMPANY_TYPES)
        suffix = random.choice(COMPANY_SUFFIXES)
        return f"{t} {ctype} {suffix}"
    else:
        word = fake.last_name().upper()
        suffix = random.choice(COMPANY_SUFFIXES)
        return f"{word} {suffix}"


def generate_address():
    """말레이시아식 주소 생성"""
    state_info = random.choice(STATES)
    city, state, base_postcode = state_info

    taman = random.choice(TAMAN_NAMES)
    road_prefix = random.choice(ROAD_PREFIXES)
    road_name = random.choice(ROAD_NAMES)
    road_num = random.randint(1, 20)

    # 건물 번호 (간혹 복수)
    if random.random() < 0.4:
        no = f"NO.{random.randint(1,99)}"
    else:
        a = random.randint(1, 50)
        b, c = a + random.randint(2, 4), a + random.randint(5, 8)
        no = f"NO.{a},{b} & {c}"

    # 우편번호 변동
    postcode = str(int(base_postcode) + random.randint(0, 999)).zfill(5)

    return f"{no}, {road_prefix} {road_name} {road_num}, {taman}, {postcode} {city}, {state}."


def generate_date(rng=None):
    """날짜+시간 생성 (SROIE 포맷)"""
    r = rng or random
    from datetime import datetime, timedelta
    base = datetime(2016, 1, 1)
    delta = timedelta(days=r.randint(0, 365 * 5), hours=r.randint(7, 21),
                      minutes=r.randint(0, 59), seconds=r.randint(0, 59))
    dt = base + delta
    hour = dt.hour
    ampm = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return dt.strftime(f"%d/%m/%Y {hour12}:%M:%S {ampm}")


def generate_items(n_items=None, rng=None):
    """
    품목 리스트 생성
    Returns list of dicts: {name, qty, unit_price, amount}
    """
    r = rng or random
    if n_items is None:
        n_items = r.randint(1, 8)

    pool = r.sample(ITEMS, min(n_items, len(ITEMS)))
    result = []
    for name, price_range in pool:
        qty = r.randint(1, 3)
        unit_price = _rnd_price(*price_range)
        amount = round(unit_price * qty, 2)
        result.append({
            "name": name,
            "qty": qty,
            "unit_price": unit_price,
            "amount": amount,
        })
    return result


def generate_totals(items):
    """
    합계 계산
    Returns dict: {subtotal, rounding, rounded_total, cash, change}
    """
    subtotal = round(sum(i["amount"] for i in items), 2)
    # ROUNDING ADJUSTMENT: 가장 가까운 0.05 단위
    rounded = round(round(subtotal / 0.05) * 0.05, 2)
    rounding = round(rounded - subtotal, 2)

    # CASH: rounded_total 이상의 깔끔한 금액
    cash_options = [0.5, 1, 2, 5, 10, 20, 50, 100]
    cash = next((rounded + c for c in cash_options if rounded + c >= rounded), rounded)
    for c in cash_options:
        if c >= rounded:
            cash = round(c, 2)
            break
    else:
        cash = rounded

    change = round(cash - rounded, 2)
    return {
        "subtotal": subtotal,
        "rounding": rounding,
        "rounded_total": rounded,
        "cash": cash,
        "change": change,
    }


def generate_doc_no(rng=None):
    r = rng or random
    prefix = "".join(r.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    num = r.randint(10000000, 99999999)
    return f"{prefix}{num}"


def generate_cashier():
    return random.choice(CASHIER_NAMES)


def generate_footer():
    return random.choice(FOOTER_LINES)


def generate_all(n_items=None, seed=None):
    """
    영수증 전체 코퍼스 생성
    Returns dict with all fields
    """
    rng = random.Random(seed) if seed is not None else random
    company = generate_company()
    address = generate_address()
    date_str = generate_date(rng)
    items = generate_items(n_items, rng)
    totals = generate_totals(items)
    return {
        "company": company,
        "address": address,
        "date": date_str,             # DD/MM/YYYY H:MM:SS AM (entities/렌더링 공용)
        "doc_no": generate_doc_no(rng),
        "cashier": generate_cashier(),
        "items": items,
        "totals": totals,
        "total": f"{totals['rounded_total']:.2f}",  # entities용
        "footer": generate_footer(),
    }
