# app/workers/automation/popup_handler.py
"""Intelligent handler for popups, cookie banners, and overlays with comprehensive detection."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from playwright.async_api import Page, ElementHandle

from app.workers.utils.logger import WorkerLogger

logger = logging.getLogger(__name__)


class PopupHandler:
    """Handles various types of popups, modals, and overlays that block content."""

    def __init__(
        self, user_id: Optional[str] = None, campaign_id: Optional[str] = None
    ):
        self.logger = WorkerLogger(user_id=user_id, campaign_id=campaign_id)

        # Cookie consent patterns (prioritized for acceptance)
        self.cookie_accept_patterns = [
            # High confidence button text patterns
            'button:has-text("Accept All")',
            'button:has-text("Accept all cookies")',
            'button:has-text("Accept Cookies")',
            'button:has-text("Accept")',
            'button:has-text("Allow All")',
            'button:has-text("Allow Cookies")',
            'button:has-text("I Agree")',
            'button:has-text("I Accept")',
            'button:has-text("Agree")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            'button:has-text("Understood")',
            'button:has-text("Continue")',
            # Link patterns
            'a:has-text("Accept All")',
            'a:has-text("Accept Cookies")',
            'a:has-text("Accept")',
            'a:has-text("I Agree")',
            # ID/Class based selectors (high confidence)
            "#accept-cookies",
            "#acceptCookies",
            "#cookie-accept",
            ".accept-cookies",
            ".cookie-accept",
            ".accept-button",
            # Data attribute selectors
            '[data-action="accept"]',
            "[data-cookie-accept]",
            "[data-accept-cookies]",
            "[data-cc-accept]",
            # Popular framework patterns
            ".cc-btn.cc-dismiss",  # Cookie Consent plugin
            ".cc-allow",  # Cookie Consent
            "#onetrust-accept-btn-handler",  # OneTrust
            ".optanon-allow-all",  # OneTrust alternative
            ".cky-btn-accept",  # CookieYes
            ".cookie-consent-accept",  # Generic
            ".gdpr-accept",  # GDPR compliance
            ".eu-cookie-accept",  # EU Cookie Law
            # Aria label based (accessibility)
            'button[aria-label*="Accept" i]',
            'button[aria-label*="Allow" i]',
            'button[title*="Accept" i]',
            'button[title*="Allow" i]',
            # Pattern matching for contains
            '[class*="accept"][class*="cookie" i]',
            '[id*="accept"][id*="cookie" i]',
            '[class*="cookie"][class*="accept" i]',
            '[id*="cookie"][id*="accept" i]',
        ]

        # Popup close patterns (for dismissing non-essential popups)
        self.popup_close_patterns = [
            # Close button patterns with high confidence
            'button[aria-label*="Close" i]',
            'button[title*="Close" i]',
            'button:has-text("×")',
            'button:has-text("✕")',
            'button:has-text("X")',
            'button:has-text("Close")',
            # Dismissal text patterns
            'button:has-text("No thanks")',
            'button:has-text("No, thanks")',
            'button:has-text("Maybe later")',
            'button:has-text("Not now")',
            'button:has-text("Skip")',
            'button:has-text("Dismiss")',
            'button:has-text("Not interested")',
            'button:has-text("Continue without")',
            # Link patterns for dismissal
            'a:has-text("Close")',
            'a:has-text("No thanks")',
            'a:has-text("Skip")',
            'a:has-text("×")',
            # Class/ID patterns for close buttons
            ".close",
            ".close-button",
            ".modal-close",
            ".popup-close",
            ".dialog-close",
            ".overlay-close",
            ".dismiss",
            "#close",
            "#closeModal",
            "#closePopup",
            # Icon-based close buttons
            ".fa-times",
            ".fa-close",
            ".icon-close",
            ".icon-x",
            'svg[class*="close"]',
            'i[class*="close"]',
            # Data attribute patterns
            '[data-dismiss="modal"]',
            '[data-action="close"]',
            "[data-close]",
            "[data-popup-close]",
            # Generic patterns with lower confidence
            '[class*="close"]',
            '[id*="close"]',
        ]

        # Modal/overlay container patterns for identification
        self.modal_patterns = [
            # Generic modal selectors
            ".modal",
            ".popup",
            ".overlay",
            ".dialog",
            ".lightbox",
            ".modal-backdrop",
            ".modal-overlay",
            ".popup-overlay",
            # Role-based selectors (accessibility)
            '[role="dialog"]',
            '[role="alertdialog"]',
            '[aria-modal="true"]',
            # Cookie-specific containers
            ".cookie-banner",
            ".cookie-notice",
            ".cookie-consent",
            ".cookie-bar",
            ".cookie-popup",
            "#cookie-banner",
            "#cookie-notice",
            "#cookie-consent",
            '[class*="cookie-banner"]',
            '[class*="cookie-notice"]',
            '[class*="cookie-consent"]',
            '[id*="cookie-banner"]',
            '[id*="cookie-notice"]',
            # GDPR specific
            ".gdpr-banner",
            ".gdpr-notice",
            ".gdpr-consent",
            '[class*="gdpr"]',
            '[id*="gdpr"]',
            # Newsletter/subscription popups
            ".newsletter-popup",
            ".subscribe-popup",
            ".email-popup",
            ".signup-popup",
            '[class*="newsletter-popup"]',
            '[class*="subscribe-popup"]',
            '[class*="email-popup"]',
            # Age verification
            ".age-gate",
            ".age-verification",
            '[class*="age-gate"]',
            '[class*="age-verification"]',
            # Chat widgets
            ".chat-widget",
            ".chat-popup",
            "#chat-widget",
            '[class*="chat-widget"]',
            # Exit intent and promotion popups
            ".exit-popup",
            ".exit-intent",
            ".promo-popup",
            '[class*="exit-popup"]',
            '[class*="exit-intent"]',
            '[class*="promo"]',
        ]

        # Track handled elements to avoid duplicates
        self.handled_elements: Set[str] = set()

    async def handle_all_popups(
        self, page: Page, max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Main method to handle all types of popups and overlays.

        Returns:
            Dictionary with results of popup handling
        """
        results = {
            "cookies_handled": False,
            "popups_closed": 0,
            "overlays_removed": 0,
            "chat_hidden": False,
            "special_popups": 0,
            "total_handled": 0,
            "errors": [],
            "details": [],
        }

        try:
            for attempt in range(max_attempts):
                self.logger.info(f"Popup handling attempt {attempt + 1}/{max_attempts}")
                attempt_handled = 0

                # 1. Handle cookie consent first (highest priority)
                cookie_result = await self._handle_cookie_consent(page)
                if cookie_result:
                    results["cookies_handled"] = True
                    attempt_handled += 1
                    results["details"].append("Cookie consent handled")

                # 2. Close newsletter/promotional popups
                popups_closed = await self._close_promotional_popups(page)
                if popups_closed > 0:
                    results["popups_closed"] += popups_closed
                    attempt_handled += popups_closed
                    results["details"].append(
                        f"Closed {popups_closed} promotional popups"
                    )

                # 3. Remove blocking overlay elements
                overlays_removed = await self._remove_blocking_overlays(page)
                if overlays_removed > 0:
                    results["overlays_removed"] += overlays_removed
                    attempt_handled += overlays_removed
                    results["details"].append(
                        f"Removed {overlays_removed} blocking overlays"
                    )

                # 4. Hide chat widgets that might interfere
                chat_hidden = await self._hide_chat_widgets(page)
                if chat_hidden:
                    results["chat_hidden"] = True
                    attempt_handled += 1
                    results["details"].append("Chat widgets hidden")

                # 5. Handle special popups (age gates, location, etc.)
                special_handled = await self._handle_special_popups(page)
                if special_handled > 0:
                    results["special_popups"] += special_handled
                    attempt_handled += special_handled
                    results["details"].append(
                        f"Handled {special_handled} special popups"
                    )

                # 6. Remove high z-index blocking elements
                blocking_removed = await self._remove_high_zindex_blockers(page)
                if blocking_removed > 0:
                    attempt_handled += blocking_removed
                    results["details"].append(
                        f"Removed {blocking_removed} z-index blockers"
                    )

                results["total_handled"] += attempt_handled

                # Wait for animations and DOM updates
                await asyncio.sleep(1)

                # Check if page is now interactable
                if await self._is_page_interactable(page):
                    self.logger.info(
                        f"Page is interactable after {attempt + 1} attempts"
                    )
                    break

                # If nothing was handled this attempt, no point continuing
                if attempt_handled == 0:
                    self.logger.info("No more popups detected")
                    break

            # Final interactability check
            results["page_interactable"] = await self._is_page_interactable(page)

            self.logger.info(
                f"Popup handling complete: {results['total_handled']} elements handled"
            )

        except Exception as e:
            self.logger.error(f"Error in popup handling: {e}")
            results["errors"].append(str(e))

        return results

    async def _handle_cookie_consent(self, page: Page) -> bool:
        """Handle cookie consent banners with prioritized acceptance."""
        try:
            # Try each accept pattern in order of confidence
            for selector in self.cookie_accept_patterns:
                try:
                    elements = await page.query_selector_all(selector)

                    for element in elements:
                        if not await element.is_visible():
                            continue

                        # Check if not already handled
                        element_id = await self._get_element_id(element)
                        if element_id in self.handled_elements:
                            continue

                        # Verify it's actually a cookie-related button
                        if await self._is_cookie_related(element):
                            self.logger.info(f"Accepting cookie consent: {selector}")

                            try:
                                await element.click(timeout=3000)
                                self.handled_elements.add(element_id)

                                # Wait for banner to disappear
                                await asyncio.sleep(1)

                                self.logger.info("Cookie consent accepted successfully")
                                return True

                            except Exception as click_error:
                                self.logger.debug(
                                    f"Click failed for {selector}: {click_error}"
                                )
                                continue

                except Exception as e:
                    self.logger.debug(f"Error with cookie selector {selector}: {e}")
                    continue

            # Alternative: Try to hide cookie banners directly
            return await self._hide_cookie_banner_directly(page)

        except Exception as e:
            self.logger.warning(f"Cookie consent handling error: {e}")
            return False

    async def _is_cookie_related(self, element: ElementHandle) -> bool:
        """Check if element is actually cookie-related."""
        try:
            # Check element text content
            text = await element.inner_text()
            text_lower = text.lower() if text else ""

            # Check nearby text for cookie context
            context = await element.evaluate(
                """
                (el) => {
                    const parent = el.closest('.cookie-banner, .cookie-notice, .cookie-consent, [class*="cookie"], [id*="cookie"]');
                    if (parent) {
                        return parent.textContent || '';
                    }
                    
                    // Check siblings for cookie context
                    const container = el.parentElement;
                    if (container) {
                        return container.textContent || '';
                    }
                    
                    return '';
                }
            """
            )

            context_lower = context.lower() if context else ""

            # Look for cookie-related keywords
            cookie_keywords = [
                "cookie",
                "cookies",
                "gdpr",
                "privacy",
                "consent",
                "data protection",
                "tracking",
                "analytics",
            ]

            combined_text = f"{text_lower} {context_lower}"
            return any(keyword in combined_text for keyword in cookie_keywords)

        except:
            return True  # Default to true if we can't check

    async def _hide_cookie_banner_directly(self, page: Page) -> bool:
        """Hide cookie banner using JavaScript if accept button not found."""
        try:
            cookie_hidden = await page.evaluate(
                """
                () => {
                    const selectors = [
                        '.cookie-banner', '.cookie-notice', '.cookie-consent',
                        '.cookie-bar', '.gdpr-banner', '.gdpr-notice',
                        '[class*="cookie-banner"]', '[class*="cookie-notice"]',
                        '[id*="cookie-banner"]', '[id*="cookie-notice"]',
                        '[class*="gdpr"]', '[id*="gdpr"]'
                    ];
                    
                    let hidden = false;
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            if (el && el.offsetParent !== null) {
                                el.style.display = 'none';
                                el.style.visibility = 'hidden';
                                el.remove();
                                hidden = true;
                            }
                        });
                    }
                    return hidden;
                }
            """
            )

            if cookie_hidden:
                self.logger.info("Cookie banner hidden via JavaScript")

            return cookie_hidden

        except Exception as e:
            self.logger.warning(f"Error hiding cookie banner: {e}")
            return False

    async def _close_promotional_popups(self, page: Page) -> int:
        """Close newsletter and promotional popups."""
        closed_count = 0

        try:
            # Try each close pattern
            for selector in self.popup_close_patterns:
                try:
                    elements = await page.query_selector_all(selector)

                    for element in elements:
                        if not await element.is_visible():
                            continue

                        element_id = await self._get_element_id(element)
                        if element_id in self.handled_elements:
                            continue

                        # Check if it's part of a promotional popup/modal
                        is_promotional_close = await self._is_promotional_close_button(
                            element
                        )

                        if is_promotional_close:
                            try:
                                await element.click(timeout=3000)
                                self.handled_elements.add(element_id)
                                closed_count += 1
                                self.logger.info(
                                    f"Closed promotional popup: {selector}"
                                )
                                await asyncio.sleep(0.5)

                            except Exception as click_error:
                                self.logger.debug(
                                    f"Click failed for {selector}: {click_error}"
                                )
                                continue

                except Exception as e:
                    self.logger.debug(f"Error with close selector {selector}: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Error closing promotional popups: {e}")

        return closed_count

    async def _is_promotional_close_button(self, element: ElementHandle) -> bool:
        """Check if element is a close button for promotional content."""
        try:
            # Check if it's part of a modal/popup container
            is_popup_close = await element.evaluate(
                """
                (el) => {
                    let parent = el;
                    for (let i = 0; i < 10; i++) {
                        parent = parent.parentElement;
                        if (!parent) break;
                        
                        const classes = parent.className || '';
                        const id = parent.id || '';
                        const text = parent.textContent || '';
                        
                        // Check for modal/popup indicators
                        if (classes.includes('modal') || classes.includes('popup') ||
                            classes.includes('overlay') || classes.includes('dialog') ||
                            classes.includes('newsletter') || classes.includes('subscribe') ||
                            id.includes('modal') || id.includes('popup') ||
                            id.includes('newsletter') || id.includes('subscribe')) {
                            
                            // Additional check for promotional content
                            const lowerText = text.toLowerCase();
                            if (lowerText.includes('newsletter') || lowerText.includes('subscribe') ||
                                lowerText.includes('email') || lowerText.includes('discount') ||
                                lowerText.includes('offer') || lowerText.includes('signup')) {
                                return true;
                            }
                            
                            // Generic modal/popup
                            return true;
                        }
                    }
                    return false;
                }
            """
            )

            return is_popup_close

        except Exception as e:
            self.logger.debug(f"Error checking promotional close button: {e}")
            return False

    async def _remove_blocking_overlays(self, page: Page) -> int:
        """Remove overlay elements that might be blocking interaction."""
        removed_count = 0

        try:
            removed_count = await page.evaluate(
                """
                () => {
                    let count = 0;
                    
                    // Find elements with high z-index that might be overlays
                    const allElements = document.querySelectorAll('*');
                    const overlays = [];
                    
                    allElements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const zIndex = parseInt(style.zIndex);
                        const position = style.position;
                        
                        // Check for high z-index overlays
                        if (zIndex > 9990 && (position === 'fixed' || position === 'absolute')) {
                            const rect = el.getBoundingClientRect();
                            const isLarge = rect.width >= window.innerWidth * 0.3 && 
                                          rect.height >= window.innerHeight * 0.3;
                            
                            if (isLarge || el.className.includes('overlay') || 
                                el.className.includes('modal') || el.className.includes('popup') ||
                                el.className.includes('backdrop')) {
                                overlays.push(el);
                            }
                        }
                    });
                    
                    // Remove overlays
                    overlays.forEach(el => {
                        // Don't remove if it contains important content
                        const text = el.textContent || '';
                        if (text.length > 500) return; // Probably has real content
                        
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.remove();
                        count++;
                    });
                    
                    // Also remove common overlay classes
                    const overlaySelectors = [
                        '.modal-backdrop', '.modal-overlay', '.popup-overlay',
                        '.overlay:not(button):not(a)', '[class*="overlay"]:not(button):not(a)',
                        '.backdrop', '.screen-overlay'
                    ];
                    
                    overlaySelectors.forEach(selector => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                const style = window.getComputedStyle(el);
                                if (style.position === 'fixed' || style.position === 'absolute') {
                                    el.style.display = 'none';
                                    el.remove();
                                    count++;
                                }
                            });
                        } catch (e) {
                            // Selector might be invalid, skip
                        }
                    });
                    
                    return count;
                }
            """
            )

            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} blocking overlay elements")

        except Exception as e:
            self.logger.warning(f"Error removing blocking overlays: {e}")

        return removed_count

    async def _hide_chat_widgets(self, page: Page) -> bool:
        """Hide chat widgets that might interfere with form interaction."""
        try:
            chat_hidden = await page.evaluate(
                """
                () => {
                    const chatSelectors = [
                        // Intercom
                        '#intercom-container', '.intercom-launcher', '.intercom-messenger',
                        // Drift  
                        '#drift-widget', '.drift-widget-container', '#drift-widget-container',
                        // Crisp
                        '.crisp-client', '#crisp-chatbox', '.crisp-1472p7s',
                        // LiveChat
                        '#livechat-compact-container', '#chat-widget', '.livechat-widget',
                        // Zendesk
                        '.zEWidget-launcher', '#launcher', '.u-IsVisible.zEWidget-launcher',
                        // Facebook Messenger
                        '.fb_dialog', '.fb-customerchat', '#fb-root',
                        // Tawk.to
                        '#tawkchat-container', '.tawk-container', '#tawkChatFrame',
                        // Freshchat
                        '#fc_widget', '.freshchat-widget',
                        // HubSpot
                        '#hubspot-conversations-widget', '.hs-chatflows-widget',
                        // Generic chat widgets
                        '.chat-widget', '.chat-launcher', '.chat-bubble', '.chat-button',
                        '[class*="chat-widget"]', '[id*="chat-widget"]', '[class*="chat-launcher"]',
                        // Support widgets
                        '.support-widget', '.help-widget', '[class*="support-widget"]'
                    ];
                    
                    let hidden = false;
                    chatSelectors.forEach(selector => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                if (el && el.offsetParent !== null) {
                                    el.style.display = 'none';
                                    el.style.visibility = 'hidden';
                                    el.style.opacity = '0';
                                    el.style.pointerEvents = 'none';
                                    hidden = true;
                                }
                            });
                        } catch (e) {
                            // Invalid selector, skip
                        }
                    });
                    
                    return hidden;
                }
            """
            )

            if chat_hidden:
                self.logger.info("Chat widget(s) hidden")

            return chat_hidden

        except Exception as e:
            self.logger.warning(f"Error hiding chat widgets: {e}")
            return False

    async def _handle_special_popups(self, page: Page) -> int:
        """Handle special popups like age gates, location confirmations, etc."""
        handled = 0

        try:
            # Age verification popups
            age_selectors = [
                'button:has-text("I am 18")',
                'button:has-text("I am 21")',
                'button:has-text("Yes, I am")',
                'button:has-text("Yes")',
                'button:has-text("Enter")',
                'button:has-text("Confirm")',
                'button:has-text("Continue")',
                'button[class*="age-confirm"]',
                'button[class*="age-verify"]',
                "button[data-age-confirm]",
            ]

            for selector in age_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            element_id = await self._get_element_id(element)
                            if element_id not in self.handled_elements:
                                await element.click(timeout=3000)
                                self.handled_elements.add(element_id)
                                handled += 1
                                self.logger.info("Handled age verification popup")
                                await asyncio.sleep(1)
                                break
                except Exception as e:
                    self.logger.debug(f"Error with age selector {selector}: {e}")
                    continue

            # Location/country selection popups
            location_selectors = [
                'button:has-text("Continue to site")',
                'button:has-text("Stay on")',
                'button:has-text("Confirm location")',
                'button:has-text("United States")',
                'button:has-text("US")',
                'a:has-text("Continue")',
                'a:has-text("Stay")',
                '[data-country="US"]',
                "[data-location-confirm]",
            ]

            for selector in location_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            element_id = await self._get_element_id(element)
                            if element_id not in self.handled_elements:
                                await element.click(timeout=3000)
                                self.handled_elements.add(element_id)
                                handled += 1
                                self.logger.info("Handled location confirmation popup")
                                await asyncio.sleep(1)
                                break
                except Exception as e:
                    self.logger.debug(f"Error with location selector {selector}: {e}")
                    continue

            # Notification permission popups
            notification_selectors = [
                'button:has-text("Block")',
                'button:has-text("Not now")',
                'button:has-text("Maybe later")',
                'button:has-text("No thanks")',
                '[data-notification="deny"]',
                '[data-permission="deny"]',
            ]

            for selector in notification_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            # Check if it's in a notification context
                            context = await element.evaluate(
                                """
                                (el) => {
                                    const container = el.closest('[class*="notification"], [class*="permission"], [id*="notification"]');
                                    return container ? container.textContent : '';
                                }
                            """
                            )

                            if context and (
                                "notification" in context.lower()
                                or "permission" in context.lower()
                            ):
                                element_id = await self._get_element_id(element)
                                if element_id not in self.handled_elements:
                                    await element.click(timeout=3000)
                                    self.handled_elements.add(element_id)
                                    handled += 1
                                    self.logger.info(
                                        "Handled notification permission popup"
                                    )
                                    await asyncio.sleep(1)
                                    break
                except Exception as e:
                    self.logger.debug(
                        f"Error with notification selector {selector}: {e}"
                    )
                    continue

        except Exception as e:
            self.logger.warning(f"Error handling special popups: {e}")

        return handled

    async def _remove_high_zindex_blockers(self, page: Page) -> int:
        """Remove elements with extremely high z-index that block interaction."""
        try:
            removed_count = await page.evaluate(
                """
                () => {
                    let count = 0;
                    const elements = document.querySelectorAll('*');
                    
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const zIndex = parseInt(style.zIndex);
                        
                        // Elements with suspiciously high z-index
                        if (zIndex > 99999) {
                            const rect = el.getBoundingClientRect();
                            
                            // If it's covering significant area but has little content
                            if (rect.width > 100 && rect.height > 100) {
                                const text = el.textContent || '';
                                const hasMinimalContent = text.trim().length < 50;
                                
                                if (hasMinimalContent) {
                                    el.style.display = 'none';
                                    el.remove();
                                    count++;
                                }
                            }
                        }
                    });
                    
                    return count;
                }
            """
            )

            if removed_count > 0:
                self.logger.info(
                    f"Removed {removed_count} high z-index blocking elements"
                )

            return removed_count

        except Exception as e:
            self.logger.warning(f"Error removing high z-index blockers: {e}")
            return 0

    async def _is_page_interactable(self, page: Page) -> bool:
        """Check if the page is now interactable."""
        try:
            # Comprehensive interactability check
            is_interactable = await page.evaluate(
                """
                () => {
                    // Check if body has overflow hidden (might indicate modal)
                    const bodyStyle = window.getComputedStyle(document.body);
                    if (bodyStyle.overflow === 'hidden') {
                        // Check if there's still a visible modal blocking interaction
                        const visibleModals = document.querySelectorAll(
                            '.modal:not([style*="display: none"]), ' +
                            '[role="dialog"]:not([style*="display: none"]), ' +
                            '.popup:not([style*="display: none"])'
                        );
                        
                        for (const modal of visibleModals) {
                            const style = window.getComputedStyle(modal);
                            if (style.display !== 'none' && style.visibility !== 'hidden') {
                                const rect = modal.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    return false; // Still has blocking modal
                                }
                            }
                        }
                    }
                    
                    // Check if we can interact with key elements
                    const interactiveElements = document.querySelectorAll(
                        'input, textarea, button, a, select'
                    );
                    
                    let interactableCount = 0;
                    for (const el of interactiveElements) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            // Check if element is clickable at its center
                            const centerX = rect.x + rect.width / 2;
                            const centerY = rect.y + rect.height / 2;
                            const elementAtPoint = document.elementFromPoint(centerX, centerY);
                            
                            if (elementAtPoint === el || el.contains(elementAtPoint)) {
                                interactableCount++;
                                if (interactableCount >= 3) {
                                    return true; // Found enough interactable elements
                                }
                            }
                        }
                    }
                    
                    // If we have any form elements that are accessible, consider it interactable
                    const forms = document.querySelectorAll('form');
                    if (forms.length > 0) {
                        for (const form of forms) {
                            const formStyle = window.getComputedStyle(form);
                            if (formStyle.display !== 'none' && formStyle.visibility !== 'hidden') {
                                return true;
                            }
                        }
                    }
                    
                    // Default to true if we can't determine otherwise
                    return interactableCount > 0;
                }
            """
            )

            return is_interactable

        except Exception as e:
            self.logger.warning(f"Error checking page interactability: {e}")
            return True  # Assume it's interactable if check fails

    async def _get_element_id(self, element: ElementHandle) -> str:
        """Get a unique identifier for an element to track handled elements."""
        try:
            element_id = await element.evaluate(
                """
                (el) => {
                    // Create a unique identifier based on element properties
                    const tag = el.tagName;
                    const id = el.id || '';
                    const className = el.className || '';
                    const text = (el.textContent || '').substring(0, 50);
                    const parent = el.parentElement ? el.parentElement.tagName : '';
                    
                    return `${tag}-${id}-${className}-${text}-${parent}`.replace(/\\s+/g, '-');
                }
            """
            )
            return element_id
        except Exception as e:
            # Fallback to element hash if evaluation fails
            return str(hash(str(element)))

    async def wait_for_popups_and_handle(
        self, page: Page, wait_time: int = 3
    ) -> Dict[str, Any]:
        """
        Wait for popups to appear and then handle them.
        Useful for popups that appear after page load with delay.
        """
        self.logger.info(f"Waiting {wait_time} seconds for delayed popups...")
        await asyncio.sleep(wait_time)

        return await self.handle_all_popups(page)

    async def handle_specific_popup_type(
        self, page: Page, popup_type: str
    ) -> Dict[str, Any]:
        """
        Handle specific type of popup.

        Args:
            page: Playwright page object
            popup_type: Type of popup ('cookie', 'newsletter', 'chat', 'age', 'location')
        """
        result = {"success": False, "handled": 0, "error": None}

        try:
            if popup_type == "cookie":
                success = await self._handle_cookie_consent(page)
                result["success"] = success
                result["handled"] = 1 if success else 0

            elif popup_type == "newsletter":
                handled = await self._close_promotional_popups(page)
                result["success"] = handled > 0
                result["handled"] = handled

            elif popup_type == "chat":
                success = await self._hide_chat_widgets(page)
                result["success"] = success
                result["handled"] = 1 if success else 0

            elif popup_type == "age":
                handled = await self._handle_special_popups(page)
                result["success"] = handled > 0
                result["handled"] = handled

            elif popup_type == "overlay":
                handled = await self._remove_blocking_overlays(page)
                result["success"] = handled > 0
                result["handled"] = handled

            else:
                result["error"] = f"Unknown popup type: {popup_type}"

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Error handling {popup_type} popup: {e}")

        return result
