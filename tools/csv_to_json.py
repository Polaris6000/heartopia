"""
csv_to_json.py
==============
heartopia 프로젝트의 CSV 데이터를 JSON 포맷으로 변환하는 범용 스크립트.

[폴더 구조]
heartopia/
├── src/data/                       ← 변환된 JSON 파일이 저장됨 (자동 덮어쓰기)
│   ├── insect_data.json
│   ├── bird_data.json
│   ├── recipes.json
│   └── season_ice/
│       ├── season_ice_insect.json
│       ├── season_ice_bird.json
│       └── season_ice_recipes.json
└── tools/
    ├── csv/                        ← 원본 CSV 파일을 여기에 넣으면 됨
    │   ├── 곤충.csv
    │   ├── 새.csv
    │   └── 레시피.csv
    └── csv_to_json.py              ← 이 파일

[사용법]
  # 모든 타입 일괄 변환
  python tools/csv_to_json.py

  # 특정 타입만 변환
  python tools/csv_to_json.py insect
  python tools/csv_to_json.py bird
  python tools/csv_to_json.py recipe
  python tools/csv_to_json.py insect bird recipe

[새 타입 추가 방법]
  1. convert_*_row() 함수 작성
  2. CONVERTERS 딕셔너리에 항목 추가
     - 일반 배열 출력: 기본 convert() 사용
     - 래퍼 객체 출력: custom_fn 키에 전용 변환 함수 지정
  3. tools/csv/ 폴더에 CSV 파일 배치
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────

# 이 스크립트 위치 기준으로 프로젝트 루트를 계산
TOOLS_DIR = Path(__file__).parent          # tools/
PROJECT_ROOT = TOOLS_DIR.parent            # heartopia/
CSV_DIR = TOOLS_DIR / "csv"               # tools/csv/
DATA_DIR = PROJECT_ROOT / "src" / "data"  # src/data/


# ─────────────────────────────────────────
# 공통 파싱 유틸리티
# ─────────────────────────────────────────

def parse_list_field(value: str) -> list[str]:
    """
    쉼표로 구분된 문자열을 리스트로 변환.
    예: "아침, 낮, 저녁" → ["아침", "낮", "저녁"]
    """
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_special(value: str) -> bool | str:
    """
    시즌 컬럼 값을 JSON의 special 필드로 변환.
    - "일반" → False
    - 그 외("희귀", "유인기", "특수", "빙설 시즌", "보너스 스테이지" 등) → 문자열 그대로
    """
    stripped = value.strip()
    if stripped == "일반":
        return False
    return stripped


def parse_int(value: str) -> int | None:
    """
    문자열을 정수로 변환. 비어 있거나 변환 불가 시 None 반환.
    """
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def parse_number(value: str) -> int | float | None:
    """
    문자열을 숫자로 변환.
    - 소수점 없는 정수형이면 int 반환 (예: "2" → 2)
    - 소수점 있는 실수형이면 float 반환 (예: "1.5" → 1.5)
    - 비어 있거나 변환 불가 시 None 반환
    레시피 등급 배수처럼 int/float이 혼재하는 경우에 사용.
    """
    v = value.strip() if value else ""
    if not v:
        return None
    try:
        f = float(v)
        # 소수점 이하가 없으면 int로 반환해 JSON에서 "1.0" 대신 "1"로 표기
        return int(f) if f == int(f) else f
    except ValueError:
        return None


def parse_motion(value: str) -> dict[str, list[str]] | None:
    """
    모션 조건 문자열을 딕셔너리로 변환.

    입력 예: "아침: 맑음 / 낮: 맑음, 비 / 새벽: 맑음"
    출력 예: {"아침": ["맑음"], "낮": ["맑음", "비"], "새벽": ["맑음"]}

    비어 있으면 None 반환 (JSON에서 키 자체를 생략하기 위함).
    """
    if not value or not value.strip():
        return None

    result: dict[str, list[str]] = {}

    # " / " 기준으로 시간대별 조건을 분리
    parts = value.split(" / ")
    for part in parts:
        part = part.strip()
        if ": " not in part:
            continue
        time_key, conditions_str = part.split(": ", 1)
        # 쉼표로 구분된 날씨 조건을 리스트로 변환
        conditions = [c.strip() for c in conditions_str.split(",") if c.strip()]
        if conditions:
            result[time_key.strip()] = conditions

    return result if result else None


# ─────────────────────────────────────────
# 곤충(Insect) 변환 로직
# ─────────────────────────────────────────

def convert_insect_row(row: dict[str, str]) -> dict[str, Any] | None:
    """
    CSV 한 행을 곤충 JSON 객체로 변환.

    CSV 컬럼: 이름, 레벨, 서식지, 시간대, 날씨, 판매가, 시즌, 이미지ID
    JSON 필드: name, level, habitat, time, weather, price, special, image
    """
    name = row["이름"].strip()
    if not name:
        return None  # 빈 행 무시

    obj: dict[str, Any] = {
        "name":    name,
        "level":   parse_int(row["레벨"]),
        "habitat": row["서식지"].strip(),
        "time":    parse_list_field(row["시간대"]),
        "weather": parse_list_field(row["날씨"]),
        "price":   parse_int(row["판매가"]),
        "special": parse_special(row["시즌"]),
    }

    # image가 없는 항목(일부 빙설 시즌 곤충)은 키를 포함하지 않음
    image = parse_int(row.get("이미지ID", ""))
    if image is not None:
        obj["image"] = image

    return obj


# ─────────────────────────────────────────
# 새(Bird) 변환 로직
# ─────────────────────────────────────────

def convert_bird_row(row: dict[str, str]) -> dict[str, Any] | None:
    """
    CSV 한 행을 새 JSON 객체로 변환.

    CSV 컬럼: 이름, 레벨, 서식지, 카테고리, 시간대, 날씨, 판매가, 시즌, 이미지ID,
              깃털 다듬기 조건, 날개 펴기 조건
    JSON 필드: name, level, habitat, time, weather, price, special, category,
               motion_preening(선택), motion_wingspread(선택), image
    """
    name = row["이름"].strip()
    if not name:
        return None  # 빈 행 무시

    obj: dict[str, Any] = {
        "name":     name,
        "level":    parse_int(row["레벨"]),
        "habitat":  row["서식지"].strip(),
        "time":     parse_list_field(row["시간대"]),
        "weather":  parse_list_field(row["날씨"]),
        "price":    parse_int(row["판매가"]),
        "special":  parse_special(row["시즌"]),
        "category": row["카테고리"].strip(),
    }

    # 모션 조건은 값이 있을 때만 키를 추가
    preening = parse_motion(row.get("깃털 다듬기 조건", ""))
    if preening is not None:
        obj["motion_preening"] = preening

    wingspread = parse_motion(row.get("날개 펴기 조건", ""))
    if wingspread is not None:
        obj["motion_wingspread"] = wingspread

    # image는 값이 있을 때만 추가
    image = parse_int(row.get("이미지ID", ""))
    if image is not None:
        obj["image"] = image

    return obj


# ─────────────────────────────────────────
# 레시피(Recipe) 변환 로직
# ─────────────────────────────────────────

# 레시피 변환 중 CSV에서 추출한 등급 배수를 임시 저장하는 모듈 수준 변수.
# convert_recipe() 호출 시 초기화된 뒤 convert_recipe_row()에서 값이 채워진다.
_recipe_grade_mult: dict[str, int | float] = {}
_recipe_stamina_mult: dict[str, int | float] = {}


def convert_recipe_row(row: dict[str, str]) -> dict[str, Any] | None:
    """
    CSV 한 행을 레시피 JSON 객체로 변환.

    CSV 컬럼 (recipes_관리.xlsx → CSV 내보내기 기준):
      이름, 판매가(1등급), 스태미나(1등급),
      재료1, 재료2, 재료3, 재료4,   ← 각 재료를 개별 컬럼으로 관리
      이미지, 시즌, 버프,            ← 버프 컬럼 추가
      (빈 열), 등급, 판매 배수, 스태미나 배수

    JSON 필드: name, price, stamina, ingredients, image(선택), buff(선택)

    부수 효과:
      '등급' 컬럼에 값이 있는 행은 _recipe_grade_mult / _recipe_stamina_mult에
      등급 배수를 저장한다 (아이템 데이터와 동일 행에 공존 가능).
    """
    global _recipe_grade_mult, _recipe_stamina_mult

    # ── 등급 배수 정보 추출 (해당 열이 채워진 행에서만 실행) ──────────────
    grade_str = row.get("등급", "").strip()
    if grade_str:
        # "1등급" → "1", "2등급" → "2", ...
        grade_num    = grade_str.replace("등급", "").strip()
        price_mult   = parse_number(row.get("판매 배수", ""))
        stamina_mult = parse_number(row.get("스태미나 배수", ""))
        if price_mult is not None:
            _recipe_grade_mult[grade_num] = price_mult
        if stamina_mult is not None:
            _recipe_stamina_mult[grade_num] = stamina_mult

    # ── 아이템 데이터 변환 ────────────────────────────────────────────────
    name = row["이름"].strip()
    if not name:
        return None  # 이름 없는 행 무시

    # 판매가가 비어 있는 행은 데이터 행이 아님 (범례, 메모 등) → 건너뜀
    if not row.get("판매가(1등급)", "").strip():
        return None

    # 재료1~4 컬럼을 읽어 비어 있지 않은 값만 리스트로 결합
    # (엑셀에서 재료를 개별 컬럼으로 관리하므로 빈 셀은 건너뜀)
    ingredients = [
        v for key in ("재료1", "재료2", "재료3", "재료4")
        if (v := row.get(key, "").strip())
    ]

    obj: dict[str, Any] = {
        "name":        name,
        "price":       parse_int(row["판매가(1등급)"]),
        "stamina":     parse_int(row["스태미나(1등급)"]),
        "ingredients": ingredients,
    }

    # 이미지: 빈 값(일부 빙설 시즌 레시피)은 키 자체를 포함하지 않음
    image = row.get("이미지", "").strip()
    if image:
        obj["image"] = image

    # 버프: 값이 있을 때만 키 추가
    buff = row.get("버프", "").strip()
    if buff:
        obj["buff"] = buff

    return obj


def convert_recipe(data_type: str) -> None:
    """
    레시피 CSV를 읽어 recipes.json / season_ice_recipes.json으로 변환.

    일반 convert()와 달리 출력 형식이 단순 배열이 아닌 래퍼 객체:
      {
        "gradeMultipliers":  { "1": 1, "2": 1.5, ... },
        "staminaMultipliers": { "1": 1.0, "2": 1.2, ... },
        "items": [ { ... }, ... ]
      }

    빙설 시즌 레시피("시즌" 컬럼이 SEASON_ICE_VALUES에 해당)는
    season_ice_recipes.json에 동일 래퍼 구조로 분리 저장.
    """
    global _recipe_grade_mult, _recipe_stamina_mult

    # 등급 배수 저장소 초기화 (이전 호출 결과가 남지 않도록)
    _recipe_grade_mult   = {}
    _recipe_stamina_mult = {}

    config   = CONVERTERS[data_type]
    csv_path = CSV_DIR / config["csv_file"]

    # CSV 파일 존재 여부 확인
    if not csv_path.exists():
        print(f"  ❌ CSV 파일을 찾을 수 없음: {csv_path}")
        print(f"     → tools/csv/ 폴더에 '{config['csv_file']}' 파일을 넣어주세요.")
        return

    main_items:   list[dict] = []  # 일반 시즌 레시피
    season_items: list[dict] = []  # 빙설 시즌 레시피

    # CSV 읽기 (BOM 포함 UTF-8 대응)
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obj = convert_recipe_row(row)  # 등급 배수도 이 안에서 추출됨
            if obj is None:
                continue

            # 시즌 분류: 빙설 시즌이면 special 필드 추가 후 분리
            season_val = parse_special(row.get("시즌", "일반"))
            if season_val in SEASON_ICE_VALUES:
                obj["special"] = season_val  # 빙설 시즌 아이템에만 special 부여
                season_items.append(obj)
            else:
                main_items.append(obj)

    # ── 메인 데이터 저장 (래퍼 구조) ────────────────────────────────────
    main_output: dict[str, Any] = {
        "gradeMultipliers":   _recipe_grade_mult,
        "staminaMultipliers": _recipe_stamina_mult,
        "items":              main_items,
    }
    main_path = config["main_output"]
    main_path.parent.mkdir(parents=True, exist_ok=True)
    with open(main_path, "w", encoding="utf-8") as f:
        json.dump(main_output, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {main_path.relative_to(PROJECT_ROOT)}  ({len(main_items)}개)")

    # ── 빙설 시즌 데이터 저장 (래퍼 구조, 데이터가 있을 때만) ────────────
    if season_items:
        season_output: dict[str, Any] = {
            "gradeMultipliers":   _recipe_grade_mult,
            "staminaMultipliers": _recipe_stamina_mult,
            "items":              season_items,
        }
        season_path = config["season_output"]
        season_path.parent.mkdir(parents=True, exist_ok=True)
        with open(season_path, "w", encoding="utf-8") as f:
            json.dump(season_output, f, ensure_ascii=False, indent=2)
        print(f"  ✅ {season_path.relative_to(PROJECT_ROOT)}  ({len(season_items)}개)")
    else:
        print(f"  ℹ️  빙설 시즌 데이터 없음 → season 파일 미생성")


# ─────────────────────────────────────────
# 변환기 설정 테이블
# ─────────────────────────────────────────
# 새 데이터 타입을 추가할 때 여기에만 항목을 넣으면 됨.

CONVERTERS: dict[str, dict[str, Any]] = {
    "insect": {
        "label":          "곤충",
        "csv_file":       "곤충.csv",
        "main_output":    DATA_DIR / "insect_data.json",
        "season_output":  DATA_DIR / "season_ice" / "season_ice_insect.json",
        "converter":      convert_insect_row,
        # custom_fn 없음 → 기본 convert() 사용 (단순 배열 출력)
    },
    "bird": {
        "label":          "새",
        "csv_file":       "새.csv",
        "main_output":    DATA_DIR / "bird_data.json",
        "season_output":  DATA_DIR / "season_ice" / "season_ice_bird.json",
        "converter":      convert_bird_row,
        # custom_fn 없음 → 기본 convert() 사용 (단순 배열 출력)
    },
    "recipe": {
        "label":          "레시피",
        "csv_file":       "레시피.csv",
        "main_output":    DATA_DIR / "recipes.json",
        "season_output":  DATA_DIR / "season_ice" / "season_ice_recipes.json",
        "converter":      convert_recipe_row,
        # 출력이 단순 배열이 아닌 래퍼 객체({ gradeMultipliers, staminaMultipliers, items })
        # 이므로 전용 변환 함수를 지정한다.
        "custom_fn":      convert_recipe,
    },
    # ── 추가 예시 ──────────────────────────────────────────────────────
    # "fish": {
    #     "label":         "물고기",
    #     "csv_file":      "물고기.csv",
    #     "main_output":   DATA_DIR / "fish_data.json",
    #     "season_output": DATA_DIR / "season_ice" / "season_ice_fish.json",
    #     "converter":     convert_fish_row,   # 위에 함수 정의 필요
    # },
    # ───────────────────────────────────────────────────────────────────
}

# 빙설 시즌으로 분류될 special 값 목록
SEASON_ICE_VALUES = {"빙설 시즌"}


# ─────────────────────────────────────────
# 변환 실행 함수
# ─────────────────────────────────────────

def save_json(path: Path, data: list[dict]) -> None:
    """JSON 파일로 저장. 부모 디렉토리가 없으면 자동 생성."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def convert(data_type: str) -> None:
    """
    지정된 타입의 CSV를 읽어 메인 JSON과 빙설 시즌 JSON으로 분리 저장.

    Args:
        data_type: CONVERTERS 딕셔너리의 키 (예: "insect", "bird")
    """
    config = CONVERTERS[data_type]
    csv_path = CSV_DIR / config["csv_file"]

    # CSV 파일 존재 여부 확인
    if not csv_path.exists():
        print(f"  ❌ CSV 파일을 찾을 수 없음: {csv_path}")
        print(f"     → tools/csv/ 폴더에 '{config['csv_file']}' 파일을 넣어주세요.")
        return

    main_data: list[dict]   = []  # 일반 시즌 데이터
    season_data: list[dict] = []  # 빙설 시즌 데이터

    # CSV 읽기 (BOM 포함 UTF-8 대응)
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obj = config["converter"](row)
            if obj is None:
                continue  # 빈 행 건너뜀

            # special 값에 따라 메인 / 빙설 시즌으로 분류
            if obj.get("special") in SEASON_ICE_VALUES:
                season_data.append(obj)
            else:
                main_data.append(obj)

    # 메인 데이터 저장
    save_json(config["main_output"], main_data)
    print(f"  ✅ {config['main_output'].relative_to(PROJECT_ROOT)}  ({len(main_data)}개)")

    # 빙설 시즌 데이터 저장 (데이터가 있을 때만)
    if season_data:
        save_json(config["season_output"], season_data)
        print(f"  ✅ {config['season_output'].relative_to(PROJECT_ROOT)}  ({len(season_data)}개)")
    else:
        print(f"  ℹ️  빙설 시즌 데이터 없음 → season 파일 미생성")


# ─────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────

def main() -> None:
    """
    CLI 인자에 따라 단일 또는 전체 타입을 변환.

    사용법:
      python tools/csv_to_json.py               # 전체 변환
      python tools/csv_to_json.py insect        # 곤충만 변환
      python tools/csv_to_json.py bird          # 새만 변환
      python tools/csv_to_json.py recipe        # 레시피만 변환
      python tools/csv_to_json.py insect bird   # 곤충 + 새 변환
    """
    # 변환할 타입 목록 결정
    if len(sys.argv) > 1:
        requested = sys.argv[1:]
    else:
        requested = list(CONVERTERS.keys())

    print(f"\n{'─' * 45}")
    print(f"  heartopia CSV → JSON 변환기")
    print(f"  CSV 소스: {CSV_DIR.relative_to(PROJECT_ROOT)}/")
    print(f"{'─' * 45}")

    for data_type in requested:
        if data_type not in CONVERTERS:
            available = ", ".join(CONVERTERS.keys())
            print(f"\n  ❌ 알 수 없는 타입: '{data_type}'")
            print(f"     사용 가능: {available}")
            continue

        label    = CONVERTERS[data_type]["label"]
        print(f"\n  [{label}] 변환 중...")

        # custom_fn이 지정된 타입은 해당 함수로 처리 (래퍼 구조 등 특수 출력)
        # 지정되지 않은 타입은 기본 convert() 함수로 처리 (단순 배열 출력)
        custom_fn = CONVERTERS[data_type].get("custom_fn")
        if custom_fn is not None:
            custom_fn(data_type)
        else:
            convert(data_type)

    print(f"\n{'─' * 45}\n  완료!\n{'─' * 45}\n")


if __name__ == "__main__":
    main()
