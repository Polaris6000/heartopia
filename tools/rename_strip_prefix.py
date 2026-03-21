"""
rename_strip_prefix.py
──────────────────────
파일명 앞의 공통 접두사를 제거하는 리네임 유틸리티

사용법 (프로젝트 루트에서 실행):
    # 미리보기 (실제 변경 없음)
    python tools/rename_strip_prefix.py public/images/insect_img spr_ui_item_normal_p_insect_

    # 실제 적용
    python tools/rename_strip_prefix.py public/images/insect_img spr_ui_item_normal_p_insect_ --apply

    # 여러 폴더 한 번에
    python tools/rename_strip_prefix.py public/images/insect_img public/images/bird_img public/images/fish_img spr_ui_item_normal_p_ --apply

    # 확장자 필터
    python tools/rename_strip_prefix.py public/images/insect_img spr_ui_item_normal_p_insect_ --ext .webp .png --apply

    # 하위 폴더까지 재귀 탐색
    python tools/rename_strip_prefix.py public/images spr_ui_item_normal_p_ --recursive --apply

참고: 폴더 경로는 항상 프로젝트 루트 기준으로 해석됩니다.
"""

import argparse
from pathlib import Path


def collect_targets(folders: list[Path], prefix: str, extensions: list[str] | None, recursive: bool) -> list[tuple[Path, Path]]:
    """이름 변경 대상 (원본 경로, 변경 후 경로) 목록 반환"""
    targets: list[tuple[Path, Path]] = []

    for folder in folders:
        if not folder.is_dir():
            print(f"  [경고] 폴더 없음: {folder}")
            continue

        pattern = "**/*" if recursive else "*"
        for src in sorted(folder.glob(pattern)):
            if not src.is_file():
                continue
            if extensions and src.suffix.lower() not in extensions:
                continue
            if not src.name.startswith(prefix):
                continue

            new_name = src.name[len(prefix):]
            dst = src.with_name(new_name)
            targets.append((src, dst))

    return targets


def rename_files(targets: list[tuple[Path, Path]], apply: bool) -> None:
    if not targets:
        print("변경 대상 파일이 없습니다.")
        return

    max_len = max(len(str(src)) for src, _ in targets)
    conflicts: list[tuple[Path, Path]] = []

    print(f"\n{'파일명 변경 미리보기' if not apply else '파일명 변경 적용'} ({len(targets)}개)\n")
    print(f"  {'원본':<{max_len}}  →  변경 후")
    print("  " + "─" * (max_len + 30))

    for src, dst in targets:
        print(f"  {str(src):<{max_len}}  →  {dst.name}")
        if dst.exists():
            conflicts.append((src, dst))

    if conflicts:
        print(f"\n  [충돌] 이미 존재하는 파일명 {len(conflicts)}개 — 건너뜁니다:")
        for src, dst in conflicts:
            print(f"    {dst}")

    if not apply:
        print("\n  ※ 위는 미리보기입니다. 실제 적용하려면 --apply 옵션을 추가하세요.")
        return

    # 실제 리네임
    ok, skipped = 0, 0
    for src, dst in targets:
        if dst.exists():
            skipped += 1
            continue
        src.rename(dst)
        ok += 1

    print(f"\n완료: {ok}개 변경, {skipped}개 건너뜀")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="파일명 앞의 접두사를 제거합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("folders", nargs="+", type=Path, help="대상 폴더 경로 (여러 개 지정 가능)")
    parser.add_argument("prefix", help="제거할 접두사 문자열")
    parser.add_argument("--apply", action="store_true", help="실제로 파일명을 변경합니다 (없으면 미리보기만)")
    parser.add_argument("--ext", nargs="+", metavar="EXT", help="처리할 확장자 필터 (예: .webp .png)")
    parser.add_argument("--recursive", action="store_true", help="하위 폴더까지 재귀 탐색")

    args = parser.parse_args()

    # 스크립트 위치(tools/)의 상위 = 프로젝트 루트
    # 상대 경로로 받은 폴더를 프로젝트 루트 기준으로 해석 (절대 경로면 그대로 사용)
    project_root = Path(__file__).resolve().parent.parent
    args.folders = [
        (project_root / f).resolve() if not f.is_absolute() else f.resolve()
        for f in args.folders
    ]

    extensions = [e if e.startswith(".") else f".{e}" for e in args.ext] if args.ext else None

    print(f"접두사  : '{args.prefix}'")
    print(f"대상 폴더: {', '.join(str(f) for f in args.folders)}")
    if extensions:
        print(f"확장자  : {', '.join(extensions)}")
    if args.recursive:
        print("탐색 방식: 재귀 (하위 폴더 포함)")

    targets = collect_targets(args.folders, args.prefix, extensions, args.recursive)
    rename_files(targets, apply=args.apply)


if __name__ == "__main__":
    main()