# -*- coding: utf-8 -*-
"""
Playwright-based automation engine for contact-page submissions.

Public API:
- start()
- stop()
- process(url: str, user_data: dict) -> dict

Returns a dict like:
{
  "success": bool,
  "method": "form" | "email" | "none",
  "error": Optional[str],
  "details": {
     "primary_email": Optional[str],
     "emails_found": List[str],
     "submitted_via": Optional[str],   # selector/button text
     "success_hint": Optional[str],    # text that indicated success
  }
}
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.form_service import FormService
from app.services.captcha_service import CaptchaService

# Playwright
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeout,
)

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,63}", re.I)

SUCCESS_HINTS = [
    "thank you",
    "success",
    "we'll be in touch",
    "we will be in touch",
    "message sent",
    "submission received",
    "your message has been sent",
    "we have received your",
    "thanks for contacting",
]


@dataclass
class EngineConfig:
    headless: bool = True
    slow_mo: int = 0
    form_timeout_ms: int = 30000
    email_extract_timeout_ms: int = 10000
    navigate_timeout_ms: int = 20000
    min_wait_after_submit_ms: int = 1500


class BrowserAutomation:
    def __init__(self, *, headless: bool = True, slow_mo: int = 0) -> None:
        self.cfg = EngineConfig(
            headless=headless,
            slow_mo=slow_mo,
            form_timeout_ms=int(getattr(settings, "FORM_TIMEOUT_SECONDS", 30)) * 1000,
            email_extract_timeout_ms=int(
                getattr(settings, "EMAIL_EXTRACTION_TIMEOUT", 10)
            )
            * 1000,
            navigate_timeout_ms=20000,
            min_wait_after_submit_ms=1500,
        )
        self._pw = None
        self._browser: Optional[Browser] = None
        self._ctx: Optional[BrowserContext] = None
        self._form_service = FormService()
        self._captcha_service = CaptchaService()

    # ---------- lifecycle

    async def start(self) -> None:
        if self._browser:
            return
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.cfg.headless, slow_mo=self.cfg.slow_mo or 0
        )
        self._ctx = await self._browser.new_context(ignore_https_errors=True)
        logger.info(
            "[ENGINE] Browser started (headless=%s, slow_mo=%sms)",
            self.cfg.headless,
            self.cfg.slow_mo,
        )

    async def stop(self) -> None:
        try:
            if self._ctx:
                await self._ctx.close()
        finally:
            self._ctx = None
            try:
                if self._browser:
                    await self._browser.close()
            finally:
                self._browser = None
                if self._pw:
                    await self._pw.stop()
                self._pw = None
        logger.info("[ENGINE] Browser stopped")

    # ---------- public

    async def process(self, url: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entrypoint: navigate → find form → fill → submit → detect success.
        Fallback: scrape emails if no form found.
        """
        page = await self._new_page()
        try:
            nav_ok, final_url, nav_err = await self._safe_goto(page, url)
            if not nav_ok:
                return self._result(False, "none", f"Navigation failed: {nav_err}")

            # 1) Try to find & fill a form
            form_found, form_info = await self._find_form(page)
            if form_found:
                logger.info("[ENGINE] Form detected on %s", final_url)
                solved = await self._maybe_solve_captcha(page)
                if not solved:
                    logger.debug("[ENGINE] No captcha / not required")

                filled = await self._fill_form(page, form_info, user_data)
                if not filled:
                    logger.warning(
                        "[ENGINE] Could not fill form reliably, falling back to email scan"
                    )
                else:
                    submitted, via_selector, submit_err = await self._submit_form(
                        page, form_info
                    )
                    if submitted:
                        success, hint = await self._wait_for_success(page)
                        if success:
                            return self._result(
                                True,
                                "form",
                                None,
                                details={
                                    "submitted_via": via_selector,
                                    "success_hint": hint,
                                },
                            )
                        # If HTTP accepted but no hint, still consider success if page changed/url changed substantially
                        logger.warning(
                            "[ENGINE] Submitted but no clear success hint detected"
                        )
                    else:
                        logger.warning("[ENGINE] Submit click failed: %s", submit_err)

            # 2) Fallback to email extraction
            emails = await self._extract_emails(page)
            primary = emails[0] if emails else None
            if primary:
                logger.info("[ENGINE] Fallback email extracted: %s", primary)
                return self._result(
                    True,
                    "email",
                    None,
                    details={"primary_email": primary, "emails_found": emails},
                )

            return self._result(False, "none", "No form found and no emails detected")
        except Exception as e:  # noqa: BLE001
            logger.exception("[ENGINE] process() error: %s", e)
            return self._result(False, "none", str(e))
        finally:
            await self._close_page(page)

    # ---------- internals

    async def _new_page(self) -> Page:
        if not self._ctx:
            raise RuntimeError("Engine not started. Call start() first.")
        p = await self._ctx.new_page()
        # lower default timeouts; we manage our own where needed
        p.set_default_timeout(self.cfg.form_timeout_ms)
        return p

    async def _close_page(self, page: Optional[Page]) -> None:
        try:
            if page:
                await page.close()
        except Exception:
            pass

    async def _safe_goto(self, page: Page, url: str) -> Tuple[bool, str, Optional[str]]:
        candidates = self._url_variants(url)
        last_err = None
        for cand in candidates:
            try:
                logger.info("[ENGINE] Navigating: %s", cand)
                resp = await page.goto(
                    cand,
                    wait_until="domcontentloaded",
                    timeout=self.cfg.navigate_timeout_ms,
                )
                # Some sites block — still proceed if DOM loaded
                if resp and resp.status >= 400:
                    last_err = f"HTTP {resp.status}"
                else:
                    return True, page.url, None
            except PWTimeout as te:
                last_err = f"timeout: {te}"
            except Exception as e:
                last_err = str(e)
        return False, url, last_err

    def _url_variants(self, url: str) -> List[str]:
        u = url.strip()
        if u.startswith("http://") or u.startswith("https://"):
            return [u]
        return [f"https://{u}", f"http://{u}"]

    async def _find_form(self, page: Page) -> Tuple[bool, Dict[str, Any]]:
        """
        Use FormService to locate a suitable form. As a backup, try heuristics here too.
        """
        try:
            info = await self._form_service.detect_form(page)
            if info and info.get("inputs"):
                return True, info
        except Exception:
            logger.debug("[ENGINE] FormService.detect_form failed; trying heuristics")

        # Heuristic fallback
        form = await page.query_selector("form")
        if not form:
            return False, {}

        inputs = await page.query_selector_all(
            "input, textarea, select, [contenteditable='true']"
        )
        if not inputs:
            return False, {}

        return True, {"form": form, "inputs": inputs}

    async def _maybe_solve_captcha(self, page: Page) -> bool:
        try:
            return await self._captcha_service.solve_if_present(
                page, timeout_ms=self.cfg.form_timeout_ms
            )
        except Exception:
            return False

    async def _fill_form(
        self, page: Page, form_info: Dict[str, Any], user_data: Dict[str, Any]
    ) -> bool:
        """
        Try both FormService fill and our own mapping fallback.
        """
        try:
            ok = await self._form_service.fill_form(page, form_info, user_data)
            if ok:
                return True
        except Exception:
            logger.debug(
                "[ENGINE] FormService.fill_form failed; using fallback mapping"
            )

        # fallback mapping by labels/placeholders/name attributes
        mapping = self._field_mapping(user_data)
        filled_any = False
        for selector, value in mapping:
            try:
                el = await self._find_field(page, selector)
                if not el:
                    continue
                tag = (await el.evaluate("e=>e.tagName")).lower()
                if tag in ("input", "textarea"):
                    await el.fill(value or "")
                    filled_any = True
                elif tag == "select":
                    try:
                        await el.select_option(value)
                        filled_any = True
                    except Exception:
                        pass
            except Exception:
                continue

        return filled_any

    def _field_mapping(self, user: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        Pairs of (selector heuristic, value)
        """
        name_full = f"{(user.get('first_name') or '').strip()} {(user.get('last_name') or '').strip()}".strip()
        mapping: List[Tuple[str, str]] = [
            # name
            (
                "input[name*=name i], input[id*=name i], input[placeholder*=name i]",
                name_full or user.get("first_name") or "",
            ),
            # first
            (
                "input[name*=first i], input[id*=first i], input[placeholder*=first i]",
                user.get("first_name") or "",
            ),
            # last
            (
                "input[name*=last i], input[id*=last i], input[placeholder*=last i]",
                user.get("last_name") or "",
            ),
            # email
            (
                "input[type=email], input[name*=mail i], input[id*=mail i], input[placeholder*=mail i]",
                user.get("email") or "",
            ),
            # phone
            (
                "input[type=tel], input[name*=phone i], input[id*=phone i], input[placeholder*=phone i]",
                user.get("phone_number") or "",
            ),
            # company
            (
                "input[name*=company i], input[id*=company i], input[placeholder*=company i]",
                user.get("company_name") or "",
            ),
            # subject
            (
                "input[name*=subject i], input[id*=subject i], input[placeholder*=subject i]",
                user.get("subject") or "",
            ),
            # message
            (
                "textarea[name*=message i], textarea[id*=message i], textarea[placeholder*=message i], textarea",
                user.get("message") or "",
            ),
            # website
            (
                "input[name*=website i], input[id*=website i], input[placeholder*=website i], input[type=url]",
                user.get("website_url") or "",
            ),
        ]
        return mapping

    async def _find_field(self, page: Page, selector: str):
        try:
            return await page.query_selector(selector)
        except Exception:
            return None

    async def _submit_form(
        self, page: Page, form_info: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        # Try a proper submit button first
        buttons = await page.query_selector_all(
            "button[type=submit], input[type=submit], button:has-text('Send'), button:has-text('Submit'), button:has-text('Contact'), button:has-text('Send Message')"
        )
        # If the form element is there, prefer clicking inside it
        submit_selector_used: Optional[str] = None
        for b in buttons:
            try:
                submit_selector_used = await b.evaluate("e => e.outerHTML.slice(0, 80)")
                await b.click()
                await page.wait_for_load_state(
                    "networkidle", timeout=self.cfg.form_timeout_ms
                )
                await asyncio.sleep(self.cfg.min_wait_after_submit_ms / 1000.0)
                return True, submit_selector_used, None
            except Exception as e:
                last_err = str(e)

        # Fallback: try to submit via Enter on last text field
        try:
            text_inputs = await page.query_selector_all("input[type=text], textarea")
            if text_inputs:
                await text_inputs[-1].press("Enter")
                await page.wait_for_load_state(
                    "networkidle", timeout=self.cfg.form_timeout_ms
                )
                await asyncio.sleep(self.cfg.min_wait_after_submit_ms / 1000.0)
                return True, "fallback:Enter", None
        except Exception as e:
            last_err = str(e)

        return False, submit_selector_used, locals().get("last_err")

    async def _wait_for_success(self, page: Page) -> Tuple[bool, Optional[str]]:
        """
        Look for friendly success hints after submission.
        """
        try:
            # Try text hints
            content = (await page.content()).lower()
            for hint in SUCCESS_HINTS:
                if hint in content:
                    return True, hint

            # Try toast/alert-ish roles
            # (don't fail if not present; just return False)
            return False, None
        except Exception:
            return False, None

    async def _extract_emails(self, page: Page) -> List[str]:
        """
        Very simple page scan + mailto: href harvest.
        """
        emails: List[str] = []

        # 1) mailto: links
        try:
            links = await page.query_selector_all("a[href^='mailto:']")
            for a in links:
                href = await a.get_attribute("href")
                if href:
                    m = EMAIL_RE.search(href)
                    if m:
                        emails.append(m.group(0))
        except Exception:
            pass

        # 2) scan visible text
        try:
            text = await page.text_content("body")
            if text:
                emails.extend(EMAIL_RE.findall(text))
        except Exception:
            pass

        # normalize
        norm = sorted({e.strip().strip(".;,") for e in emails if e})
        return norm

    # end class
