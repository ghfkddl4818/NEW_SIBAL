#!/usr/bin/env python3
"""
이미지 자산 검증 스크립트
"""
import os
from pathlib import Path

# 루트 기준에서 자산 확인
root_dir = Path(__file__).resolve().parents[1]
os.chdir(root_dir)

def main():
    # 이미지 파일들 검증
    image_files = {
        'detail_button': 'assets/img/detail_button.png',
        'fireshot_save': 'assets/img/fireshot_save.png',
        'analysis_start': 'assets/img/analysis_start.png',
        'excel_download': 'assets/img/excel_download.png',
        'review_button': 'assets/img/review_button.png',
        'review_context': 'assets/img/review_context.png',
        'popup_context': 'assets/img/popup_context.png',
        'result_context': 'assets/img/result_context.png',
        'crawling_tool': 'assets/img/crawling_tool.png',
        'tab_shoppingmall': 'assets/img/tab_shoppingmall.png',
        'sort_review_desc': 'assets/img/sort_review_desc.png',
        'label_review': 'assets/img/label_review.png',
        'label_interest': 'assets/img/label_interest.png'
    }

    print('이미지 자산 검증 결과:')
    missing = []
    total_size = 0

    for key, path in image_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size
            print(f'OK {key}: {path} ({size} bytes)')
        else:
            print(f'NG {key}: {path} - 파일 없음')
            missing.append(key)

    print(f'\n총 {len(image_files)}개 파일 중:')
    print(f'- 존재: {len(image_files) - len(missing)}개')
    print(f'- 누락: {len(missing)}개')
    print(f'- 총 크기: {total_size:,} bytes')

    if missing:
        print(f'누락된 파일들: {missing}')
        return False
    else:
        print('모든 이미지 자산이 준비되었습니다!')
        return True

if __name__ == "__main__":
    success = main()
    print(f"검증 결과: {'성공' if success else '실패'}")
