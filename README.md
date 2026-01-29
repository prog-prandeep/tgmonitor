# 📁 Complete File Structure & Setup Guide

## Directory Structure

```
TelegramIGMonitor/
│
├── modules/                              # Shared modules (reusable)
│   ├── __init__.py                       # Empty
│   ├── config_manager.py                 # ✅ Created
│   ├── data_manager.py                   # ✅ Created
│   ├── session_manager.py                # ✅ Created
│   ├── instagram_api.py                  # ✅ Created (with detailed logs)
│   ├── screenshot_gen.py                 # ✅ Use from your Discord bot
│   └── monitor_service.py                # ✅ Created
│
├── client1/                              # Client 1 directory
│   ├── main.py                           # ✅ Created - RUN THIS
│   ├── config.json                       # You create (template below)
│   ├── session.json                      # You create (template below)
│   ├── monitored.json                    # Auto-generated
│   ├── client1.session                   # Auto-generated
│   └── client1.log                       # Auto-generated logs
│
├── bluetick.png                          # Instagram verification badge
├── requirements.txt                      # ✅ Created
└── generate_session.py                   # ✅ Created

```

---

## 🚀 Step-by-Step Setup

### **Step 1: Create Directory Structure**

```bash
mkdir -p TelegramIGMonitor/modules
mkdir -p TelegramIGMonitor/client1
cd TelegramIGMonitor
```

### **Step 2: Copy Files**

1. **Copy from artifacts:**
   - `requirements.txt`
   - `generate_session.py`
   - `modules/__init__.py`
   - `modules/config_manager.py`
   - `modules/data_manager.py`
   - `modules/session_manager.py`
   - `modules/instagram_api.py`
   - `modules/monitor_service.py`
   - `client1/main.py`

2. **Copy from your Discord bot:**
   - `modules/screenshot_gen.py` (use the one from artifact "modules/screenshot_gen.py")

3. **Add verification badge:**
   - Place `bluetick.png` in root directory

---

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

---

### **Step 4: Generate Telegram Session**

```bash
python generate_session.py
```

Follow the prompts:
1. Enter API_ID
2. Enter API_HASH
3. Enter phone number
4. Enter code from Telegram
5. Copy the STRING SESSION output

---

### **Step 5: Create client1/config.json**

```json
{
  "api_id": "12345678",
  "api_hash": "your_api_hash_here",
  "string_session": "YOUR_LONG_STRING_SESSION_HERE",
  "proxy_url": "http://username:password@proxy.com:8080",
  "min_check_interval": 300,
  "max_check_interval": 600,
  "generate_screenshots": true
}
```

**Get API credentials:**
1. Go to https://my.telegram.org
2. Login → API Development Tools
3. Create app → Get `api_id` and `api_hash`

---

### **Step 6: Create client1/session.json**

```json
{
  "sessions": [
    "YOUR_INSTAGRAM_SESSION_ID_1",
    "YOUR_INSTAGRAM_SESSION_ID_2",
    "YOUR_INSTAGRAM_SESSION_ID_3"
  ]
}
```

**Get Instagram session IDs:**
1. Login to Instagram on browser
2. Open DevTools (F12) → Application → Cookies
3. Copy the `sessionid` cookie value
4. Repeat for multiple accounts (recommended 3+)

---

### **Step 7: Run the Bot!**

```bash
cd client1
python main.py
```

---

## 📝 Usage Commands

Type these commands in **any** Telegram chat:

```
.add @nasa @spacex           # Start monitoring
.add                         # Reply to message to extract usernames
.list                        # Show monitored accounts
.remove @nasa                # Stop monitoring specific account
.removeall                   # Stop all monitoring
.help                        # Show help
```

---

## 🔍 What Was Fixed

### ✅ **Better Logging from Instagram API:**
```
[@username] Instagram API Response: HTTP 200
[@username] ✅ Account is ACTIVE (profile fetched successfully)
[@username] 🎉 ACCOUNT RECOVERED! Sending notification...
```

### ✅ **Proper Directory Structure:**
- All reusable code in `modules/`
- Each client has its own directory with config/session/logs
- Easy to add `client2`, `client3`, etc.

### ✅ **Account Recovery Detection:**
The bot now properly detects when accounts are unbanned:
```python
if data and data.get("data", {}).get("user"):
    # Check username match
    if response_username == requested_username:
        logger.info(f"[@{username}] ✅ Account is ACTIVE")
        # Send notification!
```

---

## 📊 Log Output Examples

### Starting the bot:
```
==================================================
Initializing Instagram Monitor Bot - Client 1
==================================================
✅ Configuration loaded
✅ Using string session
Loaded 3 Instagram session(s)
✅ All modules initialized
✅ Command handlers registered
==================================================
Starting Telegram Client...
==================================================
✅ Logged in as: John (@john_doe)
📊 Currently monitoring: 2 account(s)
🔄 Resuming monitoring for existing accounts...
[@nasa] Resuming monitoring...
[@spacex] Resuming monitoring...
==================================================
✅ BOT IS READY!
==================================================
```

### During monitoring:
```
[@nasa] 🔍 Check #1 - Fetching profile...
[@nasa] Instagram API Response: HTTP 404
[@nasa] ⏳ Account not found/suspended (404)
[@nasa] ⏰ Next check in 345s

[@nasa] 🔍 Check #2 - Fetching profile...
[@nasa] Instagram API Response: HTTP 200
[@nasa] ✅ Account is ACTIVE (profile fetched successfully)
[@nasa] 🎉 ACCOUNT RECOVERED! Sending notification...
[@nasa] Generating screenshot...
[@nasa] ✅ Screenshot sent successfully
[@nasa] Removed from monitoring list
```

---

## 🎯 Key Features

✅ **Detailed logging** - See exactly what's happening with Instagram API  
✅ **Clean separation** - Modules vs Client configs  
✅ **Multiple clients support** - Easy to add client2, client3...  
✅ **Auto-resume** - Continues monitoring after restart  
✅ **Username extraction** - Supports @username and instagram.com/username  
✅ **Screenshot generation** - Beautiful Instagram-style notifications  
✅ **Rate limiting** - Automatic session rotation on errors  

---

## 🐛 Troubleshooting

### Bot doesn't detect recovery:
- Check `client1.log` for detailed API responses
- Ensure Instagram session IDs are valid
- Verify proxy is working

### "Invalid Telegram session":
```bash
python generate_session.py
```
Copy new string session to `config.json`

### Screenshots not working:
- Ensure `bluetick.png` exists in root directory
- Check if PIL/Pillow is installed
- Set `"generate_screenshots": false` in config to disable

---

## 📦 All Required Files Checklist

- [ ] `modules/__init__.py`
- [ ] `modules/config_manager.py`
- [ ] `modules/data_manager.py`
- [ ] `modules/session_manager.py`
- [ ] `modules/instagram_api.py`
- [ ] `modules/screenshot_gen.py`
- [ ] `modules/monitor_service.py`
- [ ] `client1/main.py`
- [ ] `client1/config.json` (you create)
- [ ] `client1/session.json` (you create)
- [ ] `bluetick.png`
- [ ] `requirements.txt`
- [ ] `generate_session.py`

---

## 🎉 You're All Set!

The bot is now properly structured with detailed logging. You'll see exactly when accounts get unbanned with full Instagram API response details in the logs!
