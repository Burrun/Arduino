#!/usr/bin/env python3
"""
PGM 지문 이미지를 PNG로 변환하고 보기
사용법 : python3 view_fingerprint.py all
"""
import sys
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Pillow 라이브러리가 필요합니다:")
    print("pip install Pillow")
    sys.exit(1)


def pgm_to_png(pgm_path: str, output_path: str = None) -> str:
    """
    PGM 파일을 PNG로 변환
    
    Args:
        pgm_path: 입력 PGM 파일 경로
        output_path: 출력 PNG 파일 경로 (None이면 자동 생성)
    
    Returns:
        저장된 PNG 파일 경로
    """
    pgm_file = Path(pgm_path)
    
    if not pgm_file.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {pgm_path}")
    
    # 출력 경로 설정
    if output_path is None:
        output_path = pgm_file.with_suffix('.png')
    
    # PGM 이미지 열기
    try:
        img = Image.open(pgm_path)
        
        # PNG로 저장
        img.save(output_path)
        print(f"✅ 변환 완료: {output_path}")
        
        # 이미지 정보 출력
        print(f"   크기: {img.size[0]}x{img.size[1]}")
        print(f"   모드: {img.mode}")
        
        return str(output_path)
        
    except Exception as e:
        raise RuntimeError(f"이미지 변환 실패: {e}")


def convert_all_in_directory(directory: str = "data/fingerprints"):
    """
    디렉토리 내의 모든 PGM 파일을 PNG로 변환
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ 디렉토리가 없습니다: {directory}")
        return
    
    pgm_files = list(dir_path.glob("*.pgm"))
    
    if not pgm_files:
        print(f"❌ PGM 파일이 없습니다: {directory}")
        return
    
    print(f"\n📁 {len(pgm_files)}개의 PGM 파일 발견\n")
    
    for pgm_file in pgm_files:
        try:
            png_path = pgm_to_png(str(pgm_file))
        except Exception as e:
            print(f"❌ 변환 실패 {pgm_file.name}: {e}")


def show_latest_fingerprint(directory: str = "data/fingerprints"):
    """
    가장 최근의 지문 이미지를 PNG로 변환하고 경로 출력
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ 디렉토리가 없습니다: {directory}")
        return
    
    pgm_files = sorted(dir_path.glob("*.pgm"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not pgm_files:
        print(f"❌ PGM 파일이 없습니다: {directory}")
        return
    
    latest = pgm_files[0]
    print(f"\n📸 최신 지문 이미지: {latest.name}")
    
    try:
        png_path = pgm_to_png(str(latest))
        print(f"\n💡 이미지를 보려면:")
        print(f"   1. 파일 탐색기로 열기: {png_path}")
        print(f"   2. 라즈베리파이에서: feh {png_path}")
        print(f"   3. 원격에서 파일 다운로드 후 보기")
    except Exception as e:
        print(f"❌ 변환 실패: {e}")


def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python3 view_fingerprint.py <pgm파일>           # 특정 파일 변환")
        print("  python3 view_fingerprint.py all                 # 모든 PGM 파일 변환")
        print("  python3 view_fingerprint.py latest              # 최신 파일 변환")
        print("\n예제:")
        print("  python3 view_fingerprint.py data/fingerprints/fingerprint_20251114_225453.pgm")
        print("  python3 view_fingerprint.py all")
        print("  python3 view_fingerprint.py latest")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "all":
        convert_all_in_directory()
    elif command == "latest":
        show_latest_fingerprint()
    else:
        # 파일 경로로 간주
        try:
            png_path = pgm_to_png(command)
            print(f"\n💡 PNG 파일이 생성되었습니다: {png_path}")
        except Exception as e:
            print(f"❌ 오류: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()