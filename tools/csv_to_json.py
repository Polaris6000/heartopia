"""
csv_to_json.py
==============
heartopia 프로젝트의 CSV 데이터를 JSON 포맷으로 변환하는 범용 스크립트.

[폴더 구조]
heartopia/
├── src/data/                       ← 변환된 JSON 파일이 저장됨 (자동 덮어쓰기)
│   ├── insect_data.json
│   ├── bird_data.json
│   └── season_ice/
│       ├── season_ice_insect.json
│       └── season_ice_bird.json
└── tools/
    ├── csv/                        ← 원본 CSV 파일을 여기에 넣으면 됨
    │   ├── 곤충.csv
    │   └── 새.csv
    └── csv_to_json.py              ← 이 파일

[사용법]
  # 모든 타입 일괄 변환
  python tools/csv_to_json.py

  # 특정 타입만 변환
  python tools/csv_to_json.py insect
  python tools/csv_to_json.py bird
  python tools/csv_to_json.py insect bird

[새 타입 추가 방법]
  1. convert_*_row() 함수 작성
  2. CONVERTERS 딕셔너리에 항목 추가
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
    },
    "bird": {
        "label":          "새",
        "csv_file":       "새.csv",
        "main_output":    DATA_DIR / "bird_data.json",
        "season_output":  DATA_DIR / "season_ice" / "season_ice_bird.json",
        "converter":      convert_bird_row,
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
      python tools/csv_to_json.py            # 전체 변환
      python tools/csv_to_json.py insect     # 곤충만 변환
      python tools/csv_to_json.py bird       # 새만 변환
      python tools/csv_to_json.py insect bird # 곤충 + 새 변환
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

        label = CONVERTERS[data_type]["label"]
        print(f"\n  [{label}] 변환 중...")
        convert(data_type)

    print(f"\n{'─' * 45}\n  완료!\n{'─' * 45}\n")


if __name__ == "__main__":
    main()
