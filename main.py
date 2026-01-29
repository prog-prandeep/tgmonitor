"""
Telegram Instagram Monitor - Client 1
Main entry point for the userbot
"""

import asyncio
import logging
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List

from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config_manager import Config
from modules.data_manager import DataManager
from modules.session_manager import SessionManager
from modules.instagram_api import InstagramAPI
from modules.screenshot_gen import ScreenshotGenerator
from modules.monitor_service import TelegramMonitorService

# Setup logging
CLIENT_DIR = Path(__file__).parent
LOG_FILE = CLIENT_DIR / "client1.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ig_monitor_bot")

# File paths
CONFIG_FILE = CLIENT_DIR / "config.json"
MONITORED_FILE = CLIENT_DIR / "monitored.json"
SESSION_FILE = CLIENT_DIR / "session.json"
BLUETICK_PATH = CLIENT_DIR.parent / "bluetick.png"


class InstagramMonitorBot:
    """Main Telegram userbot"""
    def __init__(self):
        logger.info("="*50)
        logger.info("Initializing Instagram Monitor Bot - Client 1")
        logger.info("="*50)
        
        # Load config
        self.config = Config(CONFIG_FILE)
        logger.info("✅ Configuration loaded")
        
        # Initialize Telegram client
        self.client = TelegramClient(
            str(CLIENT_DIR / "client1"),  # Session file name
            self.config.api_id,
            self.config.api_hash
        )
        
        # If string session provided, use it
        if self.config.string_session and self.config.string_session != "YOUR_STRING_SESSION":
            self.client = TelegramClient(
                StringSession(self.config.string_session),
                self.config.api_id,
                self.config.api_hash
            )
            logger.info("✅ Using string session")
        else:
            logger.info("✅ Using session file (client1.session)")
        
        # Initialize managers
        self.session_manager = SessionManager(SESSION_FILE)
        self.data_manager = DataManager(MONITORED_FILE)
        self.screenshot_gen = ScreenshotGenerator()
        self.instagram_api = InstagramAPI(self.session_manager, self.config.proxy_url)
        self.monitor_service = TelegramMonitorService(
            self.instagram_api,
            self.data_manager,
            self.screenshot_gen,
            self.client,
            self.config,
            BLUETICK_PATH
        )
        
        logger.info("✅ All modules initialized")
        
        self._setup_handlers()
        logger.info("✅ Command handlers registered")
    
    def _setup_handlers(self):
        """Setup command handlers"""
        
        @self.client.on(events.NewMessage(pattern=r'^\.add(?:\s+(.+))?$', outgoing=True))
        async def add_handler(event):
            await self._handle_add(event)
        
        @self.client.on(events.NewMessage(pattern=r'^\.list$', outgoing=True))
        async def list_handler(event):
            await self._handle_list(event)
        
        @self.client.on(events.NewMessage(pattern=r'^\.remove\s+(.+)$', outgoing=True))
        async def remove_handler(event):
            await self._handle_remove(event)
        
        @self.client.on(events.NewMessage(pattern=r'^\.removeall$', outgoing=True))
        async def removeall_handler(event):
            await self._handle_removeall(event)
        
        @self.client.on(events.NewMessage(pattern=r'^\.help$', outgoing=True))
        async def help_handler(event):
            await self._handle_help(event)
    
    def _extract_usernames(self, text: str) -> List[str]:
        """Extract Instagram usernames from text"""
        if not text:
            return []
        
        usernames = []
        
        # Pattern 1: @username
        usernames.extend(re.findall(r'@([a-zA-Z0-9._]+)', text))
        
        # Pattern 2: instagram.com/username or ig.com/username
        usernames.extend(re.findall(r'(?:instagram|ig)\.com/([a-zA-Z0-9._]+)', text, re.IGNORECASE))
        
        # Remove duplicates and clean
        return list(set([u.strip() for u in usernames if u.strip()]))
    
    async def _handle_add(self, event):
        """Handle .add command"""
        try:
            usernames = []
            
            # Check if replying to a message
            if event.reply_to_msg_id:
                reply_msg = await event.get_reply_message()
                if reply_msg and reply_msg.text:
                    usernames = self._extract_usernames(reply_msg.text)
                    logger.info(f"Extracted {len(usernames)} username(s) from replied message")
            
            # Check command arguments
            match = re.match(r'^\.add\s+(.+)$', event.text)
            if match:
                cmd_usernames = self._extract_usernames(match.group(1))
                usernames.extend(cmd_usernames)
                logger.info(f"Extracted {len(cmd_usernames)} username(s) from command")
            
            if not usernames:
                await event.edit("❌ No usernames found. Use: `.add @username` or reply to a message")
                await asyncio.sleep(3)
                await event.delete()
                return
            
            chat_id = event.chat_id
            added = []
            already_monitoring = []
            
            for username in usernames:
                if self.data_manager.is_monitoring(username):
                    already_monitoring.append(username)
                    logger.info(f"[@{username}] Already being monitored")
                else:
                    self.data_manager.add_account(username, chat_id)
                    self.monitor_service.start_monitoring(username, chat_id)
                    added.append(username)
            
            # Build response
            response = ""
            if added:
                response += f"✅ **Monitoring started:**\n"
                for u in added:
                    response += f"└ @{u}\n"
            
            if already_monitoring:
                if response:
                    response += "\n"
                response += f"⚠️ **Already monitoring:**\n"
                for u in already_monitoring:
                    response += f"└ @{u}\n"
            
            await event.edit(response, parse_mode='md')
            await asyncio.sleep(5)
            await event.delete()
            
        except Exception as e:
            logger.error(f"Error in add handler: {e}", exc_info=True)
            try:
                await event.edit("❌ Failed to add accounts")
                await asyncio.sleep(3)
                await event.delete()
            except:
                pass
    
    async def _handle_list(self, event):
        """Handle .list command"""
        try:
            accounts = self.data_manager.get_all_accounts()
            
            if not accounts:
                await event.edit("📋 No accounts being monitored")
                await asyncio.sleep(3)
                await event.delete()
                return
            
            response = f"📋 **Monitoring {len(accounts)} account(s):**\n\n"
            for username, data in accounts.items():
                added_at = datetime.fromisoformat(data['added_at']).strftime('%Y-%m-%d %H:%M')
                response += f"└ @{username} (since {added_at})\n"
            
            await event.edit(response, parse_mode='md')
            await asyncio.sleep(8)
            await event.delete()
            
        except Exception as e:
            logger.error(f"Error in list handler: {e}", exc_info=True)
            try:
                await event.edit("❌ Failed to list accounts")
                await asyncio.sleep(3)
                await event.delete()
            except:
                pass
    
    async def _handle_remove(self, event):
        """Handle .remove command"""
        try:
            match = re.match(r'^\.remove\s+(.+)$', event.text)
            if not match:
                await event.edit("❌ Usage: `.remove @username`")
                await asyncio.sleep(3)
                await event.delete()
                return
            
            username = match.group(1).strip().lstrip('@')
            
            if self.data_manager.is_monitoring(username):
                self.monitor_service.stop_monitoring(username)
                await event.edit(f"✅ Stopped monitoring **@{username}**", parse_mode='md')
            else:
                await event.edit(f"❌ Not monitoring **@{username}**", parse_mode='md')
            
            await asyncio.sleep(3)
            await event.delete()
            
        except Exception as e:
            logger.error(f"Error in remove handler: {e}", exc_info=True)
            try:
                await event.edit("❌ Failed to remove account")
                await asyncio.sleep(3)
                await event.delete()
            except:
                pass
    
    async def _handle_removeall(self, event):
        """Handle .removeall command"""
        try:
            accounts = self.data_manager.get_all_accounts()
            count = len(accounts)
            
            if count == 0:
                await event.edit("📋 No accounts to remove")
                await asyncio.sleep(3)
                await event.delete()
                return
            
            self.monitor_service.stop_all_monitoring()
            await event.edit(f"✅ Stopped monitoring all **{count}** account(s)", parse_mode='md')
            
            await asyncio.sleep(3)
            await event.delete()
            
        except Exception as e:
            logger.error(f"Error in removeall handler: {e}", exc_info=True)
            try:
                await event.edit("❌ Failed to stop monitoring")
                await asyncio.sleep(3)
                await event.delete()
            except:
                pass
    
    async def _handle_help(self, event):
        """Handle .help command"""
        try:
            help_text = (
                "**Instagram Monitor Commands**\n\n"
                "`.add @user1 @user2` - Start monitoring\n"
                "`.add` (reply to msg) - Extract & monitor\n"
                "`.list` - Show monitored accounts\n"
                "`.remove @username` - Stop monitoring\n"
                "`.removeall` - Stop all monitoring\n"
                "`.help` - This message\n\n"
                "**Track banned accounts. Get instant alerts.**"
            )
            
            await event.edit(help_text, parse_mode='md')
            await asyncio.sleep(10)
            await event.delete()
            
        except Exception as e:
            logger.error(f"Error in help handler: {e}", exc_info=True)
            try:
                await event.delete()
            except:
                pass
    
    async def start(self):
        """Start the bot"""
        logger.info("="*50)
        logger.info("Starting Telegram Client...")
        logger.info("="*50)
        
        await self.client.connect()
        
        # Check if authorized
        if not await self.client.is_user_authorized():
            logger.error("❌ Telegram session is invalid or expired!")
            logger.error("Please run generate_session.py or login manually")
            raise SystemExit("Invalid Telegram session")
        
        me = await self.client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        
        monitored = len(self.data_manager.get_all_accounts())
        logger.info(f"📊 Currently monitoring: {monitored} account(s)")
        
        # Resume monitoring for existing accounts
        if monitored > 0:
            logger.info("🔄 Resuming monitoring for existing accounts...")
            self.monitor_service.resume_all_monitoring()
        
        logger.info("="*50)
        logger.info("✅ BOT IS READY!")
        logger.info("="*50)
        
        await self.client.run_until_disconnected()
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping bot...")
        self.monitor_service.stop_all_monitoring()
        await self.instagram_api.close()
        await self.client.disconnect()
        logger.info("✅ Bot stopped gracefully")


async def main():
    """Main entry point"""
    bot = InstagramMonitorBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Received interrupt signal (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        await bot.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")