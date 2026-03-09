"""
csv_to_json.py
--------------
translation-master.csv를 읽어서 언어별 JSON 파일로 자동 변환하는 스크립트.

사용법:
    python scripts/csv_to_json.py

CSV 형식:
    첫 번째 열: key (번역 키)
    두 번째 열~: 언어 코드 (ko, en, ja 등 헤더가 언어 코드가 됨)

예시:
    key,ko,en
    site.title,두근두근타운 데이터 허브,Heartopia Data Hub

결과:
    src/locales/ko.json
    src/locales/en.json
"""

import csv
import json
import os

# ── 경로 설정 ──────────────────────────────────────────────
# 스크립트 위치 기준으로 경로 자동 계산 (어디서 실행해도 동작)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

CSV_PATH = os.path.join(PROJECT_ROOT, "src", "locales", "translation-master.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "src", "locales")


def convert():
    """CSV를 읽어서 언어별 JSON 파일로 변환하는 메인 함수."""

    # CSV 파일 존재 여부 확인
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV 파일을 찾을 수 없어: {CSV_PATH}")
        return

    # CSV 읽기
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # 헤더에서 언어 목록 추출 (key 열 제외)
        fieldnames = reader.fieldnames
        if not fieldnames or "key" not in fieldnames:
            print("❌ CSV 첫 번째 열이 'key'여야 해.")
            return

        languages = [col for col in fieldnames if col != "key"]

        # 언어별로 빈 딕셔너리 초기화
        # 예: { "ko": {}, "en": {} }
        translations = {lang: {} for lang in languages}

        # 각 행을 읽어서 언어별 딕셔너리에 저장
        for row in reader:
            key = row["key"].strip()

            # 빈 줄이나 주석(#으로 시작) 건너뜀
            if not key or key.startswith("#"):
                continue

            for lang in languages:
                value = row.get(lang, "").strip()

                # 번역값이 비어있으면 경고 출력 (빈 문자열로 저장)
                if not value:
                    print(f"⚠️  번역 누락: [{lang}] {key}")

                # 점(.)으로 구분된 중첩 키 처리
                # 예: "nav.fish" → { "nav": { "fish": "어류 도감" } }
                set_nested(translations[lang], key, value)

    # 언어별 JSON 파일 저장
    for lang, data in translations.items():
        output_path = os.path.join(OUTPUT_DIR, f"{lang}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            # ensure_ascii=False: 한글 등 유니코드 문자 그대로 저장
            # indent=2: 읽기 좋게 들여쓰기
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ {lang}.json 생성 완료 → {output_path}")

    print(f"\n총 {len(languages)}개 언어 파일 생성 완료!")


def set_nested(dictionary, key, value):
    """
    점(.)으로 구분된 키를 중첩 딕셔너리로 변환.

    예:
        set_nested({}, "nav.fish", "어류 도감")
        → { "nav": { "fish": "어류 도감" } }
    """
    keys = key.split(".")
    current = dictionary

    # 마지막 키 직전까지 중첩 딕셔너리 생성
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    # 마지막 키에 값 저장
    current[keys[-1]] = value


if __name__ == "__main__":
    convert()
