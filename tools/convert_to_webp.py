"""
convert_to_webp.py
==================
heartopia 프로젝트의 이미지를 WebP 포맷으로 일괄 변환하는 스크립트.

[폴더 구조]
heartopia/
├── public/images/          ← 변환 대상 원본 이미지 (PNG, JPG 등)
│   ├── bird_img/
│   ├── crop_img/
│   ├── fish_img/
│   ├── food_img/
│   ├── insect_img/
│   └── main_img/
└── tools/
    └── convert_to_webp.py  ← 이 파일

[모드 — 변환과 삭제는 독립적으로 동작]

  ① 변환만  (기본)
      python tools/convert_to_webp.py
      → PNG/JPG → WebP 변환. 원본은 건드리지 않음.

  ② 삭제만  --delete-originals
      python tools/convert_to_webp.py --delete-originals
      → 변환 없이, 대응하는 .webp가 이미 있는 원본만 삭제.
      → 변환이 아직 안 된 파일은 절대 삭제하지 않음.

  ③ 변환 + 삭제  --convert-and-delete
      python tools/convert_to_webp.py --convert-and-delete
      → WebP로 변환한 뒤 원본도 삭제. 한 번에 처리.

[옵션]
    --quality             : WebP 변환 품질 (1~100, 기본값: 85)
    --force               : 이미 .webp가 있어도 덮어쓰기 (변환 모드에서만 유효)
    --dry-run             : 실제 변환/삭제 없이 대상 목록만 출력
    --delete-originals    : 삭제만 실행 (변환 없이)
    --convert-and-delete  : 변환 후 원본도 삭제

[예시]
    터미널에 입력
    python tools/convert_to_webp.py                             # 변환만
    python tools/convert_to_webp.py --quality 90               # 품질 90으로 변환
    python tools/convert_to_webp.py --force                    # 기존 webp 덮어쓰기
    python tools/convert_to_webp.py --dry-run                  # 변환 대상 미리 확인
    python tools/convert_to_webp.py --delete-originals         # 삭제만
    python tools/convert_to_webp.py --dry-run --delete-originals   # 삭제 대상 미리 확인
    python tools/convert_to_webp.py --convert-and-delete       # 변환 + 삭제 한 번에

[의존성]
    pip install Pillow
"""

import argparse
import sys
from pathlib import Path

# ── Pillow 설치 여부 확인 ────────────────────────────────────────
try:
    from PIL import Image
except ImportError:
    print("❌ Pillow가 설치되어 있지 않아.")
    print("   아래 명령어로 설치한 후 다시 실행해:")
    print("   pip install Pillow")
    sys.exit(1)


# ── 상수 ────────────────────────────────────────────────────────

# 이 스크립트 기준으로 images 폴더 경로 계산
# tools/convert_to_webp.py → ../public/images
SCRIPT_DIR  = Path(__file__).parent
IMAGES_DIR  = SCRIPT_DIR.parent / "public" / "images"

# 변환 대상 확장자 (소문자로 비교)
TARGET_EXTS = {".png", ".jpg", ".jpeg"}

# 기본 WebP 품질 (85: 용량 대비 화질 균형점)
DEFAULT_QUALITY = 85


# ── 변환 함수 ────────────────────────────────────────────────────

def convert_image(src: Path, quality: int, force: bool, dry_run: bool) -> str:
    """
    단일 이미지를 WebP로 변환.

    Args:
        src      : 원본 이미지 경로
        quality  : WebP 품질 (1~100)
        force    : True이면 기존 .webp 파일 덮어쓰기
        dry_run  : True이면 실제 변환 없이 로그만 출력

    Returns:
        결과 상태 문자열: 'converted' | 'skipped' | 'error'
    """
    dest = src.with_suffix(".webp")

    # 이미 변환된 파일이 있고 force 옵션 없으면 스킵
    if dest.exists() and not force:
        return "skipped"

    if dry_run:
        print(f"  [DRY-RUN] {src.relative_to(IMAGES_DIR.parent.parent)} → {dest.name}")
        return "converted"

    try:
        with Image.open(src) as img:
            # RGBA(투명도 포함) 이미지는 그대로 유지, RGB는 그대로 저장
            # PNG의 투명도(알파 채널)가 WebP에서도 보존됨
            img.save(dest, "WEBP", quality=quality, method=6)
            # method=6: 가장 느리지만 최고 압축률 (오프라인 변환이므로 속도 무관)
        return "converted"
    except Exception as e:
        print(f"  ❌ 변환 실패: {src.name} → {e}")
        return "error"


# ── 원본 삭제 함수 ───────────────────────────────────────────────

def delete_original(src: Path, dry_run: bool) -> bool:
    """
    같은 이름의 .webp 파일이 존재하는 경우 원본 파일 삭제.

    Args:
        src     : 삭제 대상 원본 파일 경로
        dry_run : True이면 실제 삭제 없이 로그만 출력

    Returns:
        삭제 성공 여부 (dry_run이면 항상 True)
    """
    dest = src.with_suffix(".webp")

    # 대응되는 .webp 파일이 없으면 삭제하지 않음 (안전 장치)
    if not dest.exists():
        print(f"  ⚠️  webp 없음, 삭제 스킵: {src.name}")
        return False

    if dry_run:
        print(f"  [DRY-RUN] 삭제 예정: {src.name}")
        return True

    try:
        src.unlink()  # 파일 삭제
        return True
    except Exception as e:
        print(f"  ❌ 삭제 실패: {src.name} → {e}")
        return False


# ── 메인 ────────────────────────────────────────────────────────

def main():
    # 인자 파서 설정
    parser = argparse.ArgumentParser(
        description="heartopia 이미지를 WebP로 일괄 변환"
    )
    parser.add_argument(
        "--quality", type=int, default=DEFAULT_QUALITY,
        help=f"WebP 변환 품질 (1~100, 기본값: {DEFAULT_QUALITY})"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="이미 .webp가 있어도 덮어쓰기 (변환 모드에서만 유효)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 변환/삭제 없이 대상 파일 목록만 출력"
    )
    parser.add_argument(
        "--delete-originals", action="store_true",
        help="변환 없이 삭제만 실행 (대응하는 .webp가 있는 원본만 삭제)"
    )
    parser.add_argument(
        "--convert-and-delete", action="store_true",
        help="WebP 변환 후 원본도 삭제 (한 번에 처리)"
    )
    args = parser.parse_args()

    # --delete-originals 와 --convert-and-delete 동시 사용 방지
    if args.delete_originals and args.convert_and_delete:
        print("❌ --delete-originals 와 --convert-and-delete 는 동시에 쓸 수 없어.")
        print("   삭제만         : --delete-originals")
        print("   변환 + 삭제   : --convert-and-delete")
        sys.exit(1)

    # 품질 범위 검증
    if not (1 <= args.quality <= 100):
        print("❌ --quality는 1~100 사이 값이어야 해.")
        sys.exit(1)

    # images 폴더 존재 여부 확인
    if not IMAGES_DIR.exists():
        print(f"❌ 이미지 폴더를 찾을 수 없어: {IMAGES_DIR}")
        print("   스크립트를 heartopia/tools/ 폴더 안에서 실행하고 있는지 확인해.")
        sys.exit(1)

    # 대상 파일 수집 (서브폴더 포함 재귀 탐색)
    targets = [
        f for f in IMAGES_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in TARGET_EXTS
    ]

    if not targets:
        print("처리할 이미지 파일이 없어.")
        sys.exit(0)

    # 실행 모드 결정
    # delete_only : 변환 없이 삭제만 (--delete-originals)
    # do_convert  : 변환 수행 여부
    # do_delete   : 삭제 수행 여부
    delete_only = args.delete_originals
    do_convert  = not delete_only                              # 삭제 전용이 아니면 변환
    do_delete   = args.delete_originals or args.convert_and_delete

    # 실행 정보 출력
    dry_label = "[DRY-RUN] " if args.dry_run else ""
    mode_str  = "삭제만" if delete_only else ("변환 + 삭제" if args.convert_and_delete else "변환만")
    print(f"{'='*52}")
    print(f"  {dry_label}실행 모드 : {mode_str}")
    print(f"  대상 폴더 : {IMAGES_DIR}")
    print(f"  파일 수   : {len(targets)}개")
    if do_convert:
        print(f"  변환 품질 : {args.quality}")
        print(f"  덮어쓰기  : {'ON' if args.force else 'OFF'}")
    print(f"{'='*52}")

    # 카운터
    count_converted = 0
    count_skipped   = 0
    count_error     = 0
    count_deleted   = 0

    current_folder  = None

    # ── 변환 단계 (--delete-originals 단독 시 완전히 스킵) ──────
    if do_convert:
        print(f"\n  {'[DRY-RUN] ' if args.dry_run else ''}🔄 WebP 변환 중...")

        for src in sorted(targets):
            folder = src.parent.name
            if folder != current_folder:
                print(f"\n📁 {folder}/")
                current_folder = folder

            result = convert_image(src, args.quality, args.force, args.dry_run)

            if result == "converted":
                count_converted += 1
                if not args.dry_run:
                    # 원본 → 변환 후 용량 비교 출력
                    dest      = src.with_suffix(".webp")
                    orig_kb   = src.stat().st_size / 1024
                    dest_kb   = dest.stat().st_size / 1024
                    saved_pct = (1 - dest_kb / orig_kb) * 100 if orig_kb > 0 else 0
                    print(f"  ✅ {src.name:50s} {orig_kb:6.1f}KB → {dest_kb:6.1f}KB  ({saved_pct:+.0f}%)")
            elif result == "skipped":
                count_skipped += 1
                print(f"  ⏭️  {src.name} (이미 변환됨, 스킵)")
            elif result == "error":
                count_error += 1

    # ── 삭제 단계 (--delete-originals 또는 --convert-and-delete) ─
    if do_delete:
        print(f"\n{'='*52}")
        print(f"  {'[DRY-RUN] ' if args.dry_run else ''}🗑️  원본 파일 삭제 중...")
        print(f"  (대응하는 .webp가 없는 파일은 삭제하지 않음)")
        print(f"{'='*52}")

        current_folder = None

        for src in sorted(targets):
            folder = src.parent.name
            if folder != current_folder:
                print(f"\n📁 {folder}/")
                current_folder = folder

            # .webp 존재 확인 후 삭제 (안전 장치)
            if delete_original(src, args.dry_run):
                count_deleted += 1

    # ── 최종 요약 ────────────────────────────────────────────────
    print(f"\n{'='*52}")
    print(f"  완료!")
    if do_convert:
        print(f"  변환  : {count_converted}개")
        print(f"  스킵  : {count_skipped}개")
        print(f"  오류  : {count_error}개")
    if do_delete:
        print(f"  삭제  : {count_deleted}개{'  (예정)' if args.dry_run else ''}")

    # 변환만 하고 삭제 안 했을 때 안내
    if do_convert and not do_delete and not args.dry_run and count_converted > 0:
        print(f"\n  💡 원본 파일은 삭제되지 않았어.")
        print(f"     HTML/JS 경로를 .webp로 교체 확인 후")
        print(f"     python tools/convert_to_webp.py --delete-originals")
    print(f"{'='*52}")


if __name__ == "__main__":
    main()
