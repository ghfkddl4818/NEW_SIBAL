#!/usr/bin/env python3
"""
누락된 이미지 자산 생성
네이버 쇼핑에서 캡처해야 할 이미지들의 플레이스홀더 생성
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

# 보조 스크립트가 루트 기준으로 자산을 생성하도록 설정
root_dir = Path(__file__).resolve().parents[1]
os.chdir(root_dir)

def create_placeholder_image(filename, text, width=200, height=40, bg_color='white', text_color='black'):
    """플레이스홀더 이미지 생성"""
    # 이미지 생성
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 기본 폰트 사용 (시스템에 따라 다름)
    try:
        font = ImageFont.load_default()
    except:
        font = None

    # 텍스트 위치 계산
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * 6  # 대략적인 추정
        text_height = 12

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # 텍스트 그리기
    draw.text((x, y), text, fill=text_color, font=font)

    # 테두리 추가
    draw.rectangle([0, 0, width-1, height-1], outline='gray', width=1)

    return img

def main():
    """누락된 이미지 자산들 생성"""
    assets_dir = "assets/img"

    # 디렉토리 존재 확인
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir, exist_ok=True)

    # 생성할 이미지들 정의
    missing_images = [
        {
            'filename': 'tab_shoppingmall.png',
            'text': '쇼핑몰',
            'width': 80,
            'height': 30,
            'bg_color': '#f0f0f0'
        },
        {
            'filename': 'sort_review_desc.png',
            'text': '리뷰많은순',
            'width': 100,
            'height': 25,
            'bg_color': '#ffffff'
        },
        {
            'filename': 'label_review.png',
            'text': '리뷰 303',
            'width': 80,
            'height': 20,
            'bg_color': '#ffffff'
        },
        {
            'filename': 'label_interest.png',
            'text': '관심고객 150',
            'width': 100,
            'height': 20,
            'bg_color': '#ffffff'
        }
    ]

    print("누락된 이미지 자산 생성 시작...")

    for img_config in missing_images:
        filepath = os.path.join(assets_dir, img_config['filename'])

        # 이미 존재하면 건너뛰기
        if os.path.exists(filepath):
            print(f"이미 존재함: {img_config['filename']}")
            continue

        # 플레이스홀더 이미지 생성
        img = create_placeholder_image(
            img_config['filename'],
            img_config['text'],
            img_config['width'],
            img_config['height'],
            img_config['bg_color']
        )

        # 저장
        img.save(filepath)
        print(f"생성 완료: {img_config['filename']} ({img_config['width']}x{img_config['height']})")

    print("모든 플레이스홀더 이미지 생성 완료!")
    print("주의: 실제 환경에서는 네이버 쇼핑에서 직접 캡처한 이미지로 교체해야 합니다.")

if __name__ == "__main__":
    main()
