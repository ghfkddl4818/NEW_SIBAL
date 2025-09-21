#!/usr/bin/env python3
"""Save Naver login session for Playwright tests."""

import asyncio
from pathlib import Path
from typing import Tuple

from playwright.async_api import async_playwright

CREDENTIAL_FILE = Path("계정.txt")
STORAGE_PATH = Path("playwright/storage_state.json")
STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_credentials(file_path: Path) -> Tuple[str, str]:
    raw = file_path.read_text(encoding="utf-8").strip().splitlines()
    if len(raw) < 2:
        raise ValueError("계정.txt needs at least two lines (id, password).")

    def clean(line: str) -> str:
        line = line.strip()
        for prefix in ("id=", "ID=", "user=", "username=", "pw=", "PW=", "password="):
            if line.lower().startswith(prefix.lower()):
                return line.split("=", 1)[1].strip()
        return line

    user = clean(raw[0])
    password = clean(raw[1])
    if not user or not password:
        raise ValueError("Empty id/password in 계정.txt")
    return user, password


async def main() -> None:
    user, password = load_credentials(CREDENTIAL_FILE)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://nid.naver.com/nidlogin.login", wait_until="networkidle")
        await page.fill("input#id", user)
        await page.fill("input#pw", password)
        await page.click("button.btn_login")
        await page.wait_for_load_state("networkidle")

        # Optional: redirect to shopping home to ensure session works
        await page.goto("https://shopping.naver.com/home", wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        await context.storage_state(path=STORAGE_PATH)
        await browser.close()
        print(f"Stored session to {STORAGE_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
