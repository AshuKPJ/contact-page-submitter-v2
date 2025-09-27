# app/core/browser.py
from __future__ import annotations

import os
import asyncio
from typing import (
    Optional,
    Dict,
    Any,
    List,
    Literal,
    Union,
    Callable,
    Awaitable,
    Any,
)

# ---- Env flags --------------------------------------------------------------
ENABLE_BROWSER = os.getenv("FEATURE_USE_BROWSER", "true").lower() != "false"
HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() != "false"
SLOW_MO_MS = int(os.getenv("BROWSER_SLOW_MO_MS", "0") or "0")
# ---------------------------------------------------------------------------

_browser = None  # type: ignore
_playwright = None  # type: ignore
_lock = asyncio.Lock()


async def get_browser():
    """Lazily start Playwright + Chromium when first needed."""
    if not ENABLE_BROWSER:
        raise RuntimeError("Browser disabled by FEATURE_USE_BROWSER=false")

    global _browser, _playwright
    if _browser:
        return _browser

    async with _lock:
        if _browser:
            return _browser
        try:
            from playwright.async_api import async_playwright  # type: ignore

            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                headless=HEADLESS,
                slow_mo=SLOW_MO_MS if SLOW_MO_MS > 0 else 0,
            )
            return _browser
        except Exception as e:
            raise RuntimeError(f"Failed to start browser: {e}") from e


async def new_page(**kwargs):
    browser = await get_browser()
    context = await browser.new_context()
    page = await context.new_page()
    if "user_agent" in kwargs:
        await context.set_extra_http_headers({"User-Agent": kwargs["user_agent"]})
    return page


async def with_page(fn: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
    browser = await get_browser()
    context = await browser.new_context()
    page = await context.new_page()
    try:
        return await fn(page, *args, **kwargs)
    finally:
        try:
            await context.close()
        except Exception:
            pass


async def close_browser():
    global _browser, _playwright
    try:
        if _browser:
            await _browser.close()
            _browser = None
        if _playwright:
            await _playwright.stop()
            _playwright = None
    except Exception:
        pass
