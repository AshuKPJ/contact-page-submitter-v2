# app/workers/automation/captcha_handler.py
from typing import Optional
from playwright.async_api import Page
from app.workers.utils.logger import WorkerLogger
from app.services.captcha_service import CaptchaService


class CaptchaResult:
    def __init__(self, solved: bool, captcha_type: Optional[str] = None):
        self.solved = solved
        self.captcha_type = captcha_type


class CaptchaHandler:
    def __init__(self, user_id=None, campaign_id=None):
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)
        self.captcha_service = None
        self.has_credentials = False

        if user_id:
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                self.captcha_service = CaptchaService(
                    db=db, user_id=user_id, campaign_id=campaign_id
                )
                self.has_credentials = self.captcha_service.dbc.enabled
            finally:
                db.close()

    async def handle_captcha_if_present(self, page: Page) -> CaptchaResult:
        """Handle CAPTCHA if present on page."""
        if not self.captcha_service:
            return CaptchaResult(False)

        try:
            solved = await self.captcha_service.solve_if_present(page)
            return CaptchaResult(solved, "image_captcha" if solved else None)
        except Exception as e:
            self.logger.error(f"CAPTCHA handling error: {e}")
            return CaptchaResult(False)
