import asyncio, json
from core.config import load_config
from llm.gemini_client import GeminiClient

async def main():
    cfg = load_config("config/config.yaml")
    client = GeminiClient(cfg)
    user_payload = "제품명: 콜드브루 커피. 원재료: 원두, 정제수. 특징: 무설탕, 산미 낮음."
    with open(f"{cfg.paths.prompts_dir}/product_structuring.json", "r", encoding="utf-8") as f:
        prompt = json.load(f)
    obj = await client.generate(prompt, user_payload)
    with open("outputs/smoke_struct.log", "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())