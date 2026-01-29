"""
Account monitoring service module for Telegram
"""

import asyncio
import logging
import time
import random
import json
from pathlib import Path
from typing import Optional
from io import BytesIO

from telethon import Button

logger = logging.getLogger("ig_monitor_bot")


class TelegramMonitorService:
    """Monitor service for Telegram"""

    def __init__(
        self,
        instagram_api,
        data_manager,
        screenshot_gen,
        telegram_client,
        config,
        bluetick_path: Path,
    ):
        self.instagram_api = instagram_api
        self.data_manager = data_manager
        self.screenshot_gen = screenshot_gen
        self.telegram_client = telegram_client
        self.config = config
        self.active_monitors = {}

        # Load verification badge
        self.verification_badge = None
        try:
            if bluetick_path.exists():
                with open(bluetick_path, "rb") as f:
                    self.verification_badge = f.read()
                logger.info("Verification badge loaded successfully")
            else:
                logger.warning(f"bluetick.png not found at {bluetick_path}")
        except Exception as e:
            logger.error(f"Error loading verification badge: {e}")

    # -----------------------------------------------------
    # Utility
    # -----------------------------------------------------

    def format_elapsed_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    # -----------------------------------------------------
    # Monitoring loop
    # -----------------------------------------------------

    async def monitor_account(self, username: str, chat_id: int):
        start_time = time.time()
        check_count = 0

        logger.info(f"[@{username}] 🚀 Started monitoring for chat {chat_id}")

        while self.data_manager.is_monitoring(username):
            check_count += 1
            check_interval = random.randint(
                self.config.min_check_interval,
                self.config.max_check_interval,
            )

            logger.info(f"[@{username}] 🔍 Check #{check_count} - Fetching profile...")

            try:
                status_code, data = await self.instagram_api.fetch_profile(username)
            except asyncio.TimeoutError:
                logger.error(f"[@{username}] ⏱️ Request timeout")
                logger.info(f"[@{username}] Retry after {check_interval}s")
                await asyncio.sleep(check_interval)
                continue
            except Exception as e:
                logger.error(
                    f"[@{username}] Fetch exception: {e}", exc_info=True
                )
                await asyncio.sleep(check_interval)
                continue

            # ✅ RECOVERY CHECK
            if (
                data
                and isinstance(data, dict)
                and data.get("data", {}).get("user")
            ):
                logger.info(f"[@{username}] 🎉 ACCOUNT RECOVERED")
                await self._handle_account_recovery(
                    username,
                    data,
                    chat_id,
                    start_time,
                )
                return

            logger.info(f"[@{username}] ⏰ Next check in {check_interval}s")
            await asyncio.sleep(check_interval)

        logger.info(f"[@{username}] ⏹️ Monitoring stopped")

    # -----------------------------------------------------
    # Recovery handler
    # -----------------------------------------------------

    async def _handle_account_recovery(
        self,
        username: str,
        data: dict,
        chat_id: int,
        start_time: float,
    ):
        user = data["data"]["user"]

        followers = user.get("edge_followed_by", {}).get("count", 0)
        following = user.get("edge_follow", {}).get("count", 0)
        posts = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
        profile_pic_url = (
            user.get("profile_pic_url_hd")
            or user.get("profile_pic_url")
        )
        full_name = user.get("full_name", "")
        bio = user.get("biography", "")
        is_verified = user.get("is_verified", False)

        elapsed_str = self.format_elapsed_time(time.time() - start_time)
        instagram_url = f"https://instagram.com/{username}"

        message_text = (
            f"✅ **Username unbanned!**\n\n"
            f"**@{username}** is now active again\n"
            f"👥 Followers: **{followers:,}**\n"
            f"⏱ Time elapsed: **{elapsed_str}**"
        )

        button = Button.url("View Profile", instagram_url)

        try:
            if self.config.generate_screenshots and profile_pic_url:
                await self._send_with_screenshot(
                    chat_id,
                    username,
                    profile_pic_url,
                    followers,
                    following,
                    posts,
                    full_name,
                    is_verified,
                    bio,
                    message_text,
                    button,
                )
            else:
                await self.telegram_client.send_message(
                    chat_id,
                    message_text,
                    buttons=[button],
                    parse_mode="md",
                )
        except Exception as e:
            logger.error(f"[@{username}] Notify error: {e}", exc_info=True)
            await self.telegram_client.send_message(
                chat_id,
                message_text,
                parse_mode="md",
            )

        self.data_manager.remove_account(username)
        self.active_monitors.pop(username, None)
        logger.info(f"[@{username}] Removed from monitoring list")

    # -----------------------------------------------------
    # Screenshot sender (IMAGE FIX)
    # -----------------------------------------------------

    async def _send_with_screenshot(
        self,
        chat_id: int,
        username: str,
        profile_pic_url: str,
        followers: int,
        following: int,
        posts: int,
        full_name: str,
        is_verified: bool,
        bio: str,
        message_text: str,
        button,
    ):
        try:
            image_data = await self.instagram_api.download_profile_picture(
                profile_pic_url
            )

            screenshot = await asyncio.to_thread(
                self.screenshot_gen.create_screenshot,
                username,
                image_data,
                followers,
                following,
                posts,
                full_name,
                bio,
                is_verified,
                self.verification_badge,
            )

            if not screenshot:
                raise ValueError("Screenshot generator returned empty result")

            # --------------------------------------------------
            # 🔥 HANDLE BOTH bytes AND BytesIO CORRECTLY
            # --------------------------------------------------
            if isinstance(screenshot, BytesIO):
                photo = screenshot
                photo.seek(0)
            elif isinstance(screenshot, (bytes, bytearray)):
                photo = BytesIO(screenshot)
            else:
                raise TypeError(f"Invalid screenshot type: {type(screenshot)}")

            # 🔥 CRITICAL: filename tells Telegram it's an IMAGE
            photo.name = f"{username}_profile.png"
            photo.seek(0)

            logger.info(
                f"[@{username}] Sending IMAGE ({photo.getbuffer().nbytes} bytes)"
            )

            await self.telegram_client.send_file(
                chat_id,
                file=photo,
                caption=message_text,
                buttons=[button],
                parse_mode="md",
                force_document=False,
            )

            logger.info(f"[@{username}] ✅ Screenshot sent as IMAGE")

        except Exception as e:
            logger.error(
                f"[@{username}] Screenshot send failed: {e}", exc_info=True
            )

            await self.telegram_client.send_message(
                chat_id,
                message_text,
                buttons=[button],
                parse_mode="md",
            )


    # -----------------------------------------------------
    # Task control
    # -----------------------------------------------------

    def start_monitoring(self, username: str, chat_id: int):
        task = asyncio.create_task(self.monitor_account(username, chat_id))
        self.active_monitors[username] = task
        logger.info(f"[@{username}] Monitor task created")
        return task

    def stop_monitoring(self, username: str):
        self.data_manager.remove_account(username)
        task = self.active_monitors.pop(username, None)
        if task:
            task.cancel()
            logger.info(f"[@{username}] Monitor task cancelled")

    def stop_all_monitoring(self):
        for username in list(self.active_monitors.keys()):
            self.stop_monitoring(username)
        self.data_manager.clear_all()
        logger.info("Stopped all monitoring tasks")

    def resume_all_monitoring(self):
        accounts = self.data_manager.get_all_accounts()
        for username, data in accounts.items():
            self.start_monitoring(username, data["chat_id"])
        if accounts:
            logger.info(f"Resumed monitoring for {len(accounts)} accounts")
