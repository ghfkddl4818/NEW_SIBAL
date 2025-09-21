import pytesseract
from PIL import Image
import os
import json
from pathlib import Path

def process_images(input_dir: str, output_path: str, config, logger):
    pytesseract.pytesseract.tesseract_cmd = config.ocr.tesseract_cmd
    results = []
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    with open(output_path, 'w', encoding='utf-8') as f:
        for filename in image_files:
            try:
                image_path = os.path.join(input_dir, filename)
                text = pytesseract.image_to_string(
                    Image.open(image_path), 
                    lang=config.ocr.languages[0]+'+'+config.ocr.languages[1],
                    config=f'--psm {config.ocr.psm} --oem {config.ocr.oem}'
                )
                record = {"image_path": image_path, "text": text}
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                results.append(record)
                logger.info(f"Processed OCR for {filename}")
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
    return results
