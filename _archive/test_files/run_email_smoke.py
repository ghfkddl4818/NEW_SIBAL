import asyncio, json
from core.config import load_config
from llm.gemini_client import GeminiClient
from compose.composer import compose_final_email

async def main():
    cfg = load_config("config/config.yaml")
    client = GeminiClient(cfg)
    with open(f"{cfg.paths.prompts_dir}/cold_email.json", "r", encoding="utf-8") as f:
        prompt = json.load(f)
    draft = await client.generate(prompt, "리뷰 적음 / OCR 텍스트 없음 / 테스트 케이스")
    final = compose_final_email(draft, cfg.policy)
    with open("outputs/smoke_email.log", "w", encoding="utf-8") as f:
        f.write(json.dumps(final, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())