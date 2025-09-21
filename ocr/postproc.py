import re
import json

def clean_ocr_output(input_path: str, output_path: str, logger):
    cleaned_records = []
    with open(input_path, 'r', encoding='utf-8') as f_in, open(output_path, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            record = json.loads(line)
            text = record.get('text', '')
            
            # Remove control characters
            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
            # Replace multiple spaces/newlines with a single one
            text = re.sub(r'\s{2,}', ' ', text).strip()
            
            lines = text.split('\n')
            # Filter out very short lines
            cleaned_lines = [l.strip() for l in lines if len(l.strip()) > 2]
            cleaned_text = '\n'.join(cleaned_lines)

            cleaned_record = {"image_path": record["image_path"], "cleaned_text": cleaned_text}
            f_out.write(json.dumps(cleaned_record, ensure_ascii=False) + '\n')
            cleaned_records.append(cleaned_record)
    logger.info(f"Cleaned OCR output written to {output_path}")
    return cleaned_records
