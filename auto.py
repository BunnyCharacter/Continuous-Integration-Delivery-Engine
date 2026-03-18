import os
import sys
import requests
import time
import random
import threading
import shutil
import subprocess
import tempfile
import stat

try:
    import pyfiglet
except ImportError:
    pyfiglet = None

# Trigger to activate ANSI colors in Windows CMD/Git Bash
if os.name == 'nt':
    os.system('')

# ==========================================
# ⚙️ CONFIGURATION COMMAND CENTER
# ==========================================
TELEGRAM_BOT_TOKEN = "8275940423:AAEW8ZOn2ZoK64I2Bwcw9reJI7D0I1RmcrE"

# 👑 ADMIN ID (Only Admin can add/remove other users)
ADMIN_ID = "6740043923"
USERS_FILE = "users.txt"

# 📢 BROADCAST CHANNELS (Where success/failure logs are sent)
# Fill with your Group/Channel IDs, e.g.: ["6740043923", "-1003626912079"]
BROADCAST_CHATS = ["6740043923", "-1003626912079", "-1003798466502"]

# ==========================================
# 🧠 STATE MANAGEMENT & LOGGING
# ==========================================
PENDING_STATES = {}
ASCII_TIMER = None

# ANSI Colors for Terminal
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_RESET = "\033[0m"

# Rainbow Gradient
COLORS = [C_RED, C_YELLOW, C_GREEN, C_CYAN, C_BLUE, C_MAGENTA]

def log_terminal(message, level="INFO"):
    """Function to print logs to terminal in hacker console style (CENTERED)"""
    now = time.strftime("%H:%M:%S")
    if level == "INFO":
        prefix = f"{C_CYAN}[*]{C_RESET}"
        text_color = C_CYAN
    elif level == "SUCCESS":
        prefix = f"{C_GREEN}[+]{C_RESET}"
        text_color = C_GREEN
    elif level == "ERROR":
        prefix = f"{C_RED}[-]{C_RESET}"
        text_color = C_RED
    elif level == "PROCESS":
        prefix = f"{C_YELLOW}[~]{C_RESET}"
        text_color = C_YELLOW
    else:
        prefix = f"{C_BLUE}[>]{C_RESET}"
        text_color = C_RESET

    # Calculate screen width for center alignment
    term_cols, _ = shutil.get_terminal_size()
    box_width = 80 # Assume average log length is 80 characters
    pad_left = max(0, (term_cols - box_width) // 2)
    indent = " " * pad_left

    lines = message.split('\n')
    # Print first line with timestamp
    print(f"{indent}{C_BLUE}[{now}]{C_RESET} {prefix} {text_color}{lines[0]}{C_RESET}")
    # Print remaining lines with indentation
    for line in lines[1:]:
        print(f"{indent}                  {text_color}{line}{C_RESET}")

# ==========================================
# 🚀 CORE FUNCTIONS
# ==========================================
def set_bot_commands():
    """Set the Telegram bot menu commands so they autocomplete when typing /"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "help", "description": "Show command list & usage examples"},
        {"command": "check", "description": "Check token health (Live/Dead)"},
        {"command": "scan", "description": "Get target repository intelligence"},
        {"command": "clone", "description": "Stealth Clone repos (Interactive Wizard)"},
        {"command": "npm", "description": "Boost NPM package downloads"},
        {"command": "stars", "description": "Execute STARS on target"},
        {"command": "forks", "description": "Execute FORKS on target"},
        {"command": "watch", "description": "Execute WATCH on target"},
        {"command": "follow", "description": "Execute FOLLOW on target owner"},
        {"command": "allin", "description": "Execute ALL actions (Combo)"},
        {"command": "ghost", "description": "Randomize GitHub profiles to avoid bans"},
        {"command": "ascii", "description": "Display colorful ASCII text on server terminal"},
        {"command": "unstar", "description": "Remove STARS from target"},
        {"command": "unwatch", "description": "Remove WATCH from target"},
        {"command": "unfollow", "description": "Unfollow target owner"},
        {"command": "adduser", "description": "[Admin] Authorize a new user ID"},
        {"command": "users", "description": "List all authorized users"},
        {"command": "cancel", "description": "Cancel a pending interactive action"}
    ]
    try:
        res = requests.post(url, json={"commands": commands}, timeout=10)
        if res.status_code == 200:
            log_terminal("Bot commands menu registered successfully.", "SUCCESS")
    except Exception as e:
        log_terminal(f"Failed to set bot commands: {e}", "ERROR")

def get_authorized_users():
    """Load authorized users from users.txt"""
    users = [ADMIN_ID]
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users.extend([line.strip() for line in f.readlines() if line.strip()])
    return list(set(users))

def send_message(chat_id, text):
    """Send a direct message and return the message ID for editing"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        res = requests.post(url, json=payload, timeout=10).json()
        if res.get("ok"):
            return str(res.get("result", {}).get("message_id"))
    except Exception:
        pass
    return None

def edit_message(chat_id, message_id, text):
    """Edit an existing message to create a live loading effect"""
    if not message_id: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def broadcast_message(text, exclude_id=None):
    """Broadcast to all channels, excluding a specific ID to prevent duplicate messages"""
    sent_messages = {}
    for chat_id in BROADCAST_CHATS:
        if str(chat_id) == str(exclude_id):
            continue 
        msg_id = send_message(chat_id, text)
        if msg_id:
            sent_messages[chat_id] = msg_id
    return sent_messages

def edit_broadcast_message(sent_messages, text):
    """Edit existing broadcasted messages to simulate live loading"""
    for chat_id, msg_id in sent_messages.items():
        edit_message(chat_id, msg_id, text)

def get_repo_info(repo):
    """Fetch live repository intelligence from GitHub"""
    try:
        res = requests.get(f"https://api.github.com/repos/{repo}", timeout=10).json()
        if "message" in res and res["message"] == "Not Found":
            return None
        return {
            "stars": res.get("stargazers_count", 0),
            "forks": res.get("forks_count", 0),
            "watchers": res.get("subscribers_count", 0),
            "created": res.get("created_at", "Unknown")[:10],
            "size_kb": res.get("size", 0) 
        }
    except Exception:
        return None

def get_user_repos(username):
    """Fetch recent public repositories for a specific user (up to 100)"""
    try:
        res = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100", timeout=10)
        if res.status_code == 200:
            return [repo['full_name'] for repo in res.json()]
    except Exception:
        pass
    return []

# ==========================================
# 📦 NPM BOOSTER FUNCTIONS
# ==========================================
def get_npm_latest_version(pkg_name):
    """Fetch the latest version of an NPM package from the public registry"""
    try:
        res = requests.get(f"https://registry.npmjs.org/{pkg_name}", timeout=10)
        if res.status_code == 200:
            return res.json().get("dist-tags", {}).get("latest")
    except:
        return None
    return None

def do_npm_boost(pkg_name, version, user_id, msg_id, bcast_msgs):
    """Simulate package downloads to boost stats"""
    download_url = f"https://registry.npmjs.org/{pkg_name}/-/{pkg_name}-{version}.tgz"
    success_count = 0
    session_target = random.randint(50, 100) # Random burst count
    
    for i in range(session_target):
        try:
            with requests.get(download_url, stream=True, timeout=5) as r:
                if r.status_code == 200:
                    success_count += 1
        except:
            pass
        
        # Update UI every 15 hits to avoid Telegram rate limits
        if (i + 1) % 15 == 0 or (i + 1) == session_target:
            bar_length = 10
            filled = int((i + 1) / session_target * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            percent = int((i + 1) / session_target * 100)
            
            step_msg = (
                f"╔═════════════════════════╗\n"
                f"   🚀 <b>NPM BOOST PIPELINE</b>\n"
                f"╚═════════════════════════╝\n\n"
                f"<b>[Target]</b> : <code>{pkg_name}</code>\n"
                f"<b>[Version]</b>: <code>v{version}</code>\n\n"
                f"📊 <b>Progress:</b> <code>[{bar}] {percent}%</code>\n"
                f"🎯 <b>Hits:</b> <code>{success_count}/{session_target}</code>\n\n"
                f"🛡️ <i>Engineered by Abie Haryatmo</i>"
            )
            edit_message(user_id, msg_id, step_msg)
            edit_broadcast_message(bcast_msgs, step_msg)
            
        time.sleep(random.uniform(0.05, 0.2)) # Slight delay to mimic normal traffic
            
    return success_count

# ==========================================
# 🖥️ TERMINAL DISPLAY FUNCTIONS
# ==========================================
def print_main_banner():
    """Prints the default standby banner on the terminal (GIANT & CENTERED)"""
    os.system('cls' if os.name == 'nt' else 'clear')
    term_cols, term_lines = shutil.get_terminal_size()
    
    print("\n" * max(1, (term_lines - 15) // 3))
    
    if pyfiglet:
        try:
            ascii_banner = pyfiglet.figlet_format("XIANBEE", font="slant")
            for line in ascii_banner.split('\n'):
                if line.strip():
                    pad = max(0, (term_cols - len(line)) // 2)
                    print(" " * pad + f"{C_CYAN}{line}{C_RESET}")
        except:
            pass
            
    print("")
    
    subtitle = "🤖 COMMAND CENTER IS ONLINE"
    sub_pad = max(0, (term_cols - len(subtitle)) // 2)
    print(" " * sub_pad + f"{C_MAGENTA}{subtitle}{C_RESET}\n")
    
    wait_msg = "Waiting for incoming commands from Telegram..."
    wait_pad = max(0, (term_cols - len(wait_msg)) // 2)
    print(" " * wait_pad + f"{C_YELLOW}{wait_msg}{C_RESET}")
    
    stop_msg = "Press Ctrl+C to stop the bot."
    stop_pad = max(0, (term_cols - len(stop_msg)) // 2)
    print(" " * stop_pad + f"{C_RED}{stop_msg}{C_RESET}\n")
    
    line_sep = "=" * 60
    sep_pad = max(0, (term_cols - len(line_sep)) // 2)
    print(" " * sep_pad + f"{C_MAGENTA}{line_sep}{C_RESET}\n")

def restore_terminal():
    """Restores the terminal back to normal after showing ASCII"""
    global ASCII_TIMER
    print_main_banner()
    ASCII_TIMER = None

def display_ascii_art(text):
    """Displays colorful ASCII art on the terminal for 60 seconds"""
    global ASCII_TIMER
    if not pyfiglet:
        return False
        
    try:
        try:
            ascii_text = pyfiglet.figlet_format(text, font="graffiti")
        except:
            try:
                ascii_text = pyfiglet.figlet_format(text, font="3-d")
            except:
                ascii_text = pyfiglet.figlet_format(text, font="standard")
            
        ascii_lines = ascii_text.split('\n')
        term_cols, term_lines = shutil.get_terminal_size()
        
        max_line_len = max(len(line) for line in ascii_lines) if ascii_lines else 0
        pad_left = max(0, (term_cols - max_line_len) // 2)
        pad_top = max(0, (term_lines - len(ascii_lines) - 2) // 2)
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print('\n' * pad_top, end='')
        
        for i, line in enumerate(ascii_lines):
            c = COLORS[i % len(COLORS)]
            print(" " * pad_left + f"{c}{line}{C_RESET}")
            
        bottom_text = "⏳ Displaying for 60 seconds. Do not close terminal..."
        pad_bottom_text = max(0, (term_cols - len(bottom_text)) // 2)
        print("\n" + " " * pad_bottom_text + bottom_text)
        
        if ASCII_TIMER is not None:
            ASCII_TIMER.cancel()
            
        ASCII_TIMER = threading.Timer(60.0, restore_terminal)
        ASCII_TIMER.start()
        return True
    except Exception as e:
        log_terminal(f"Error displaying ASCII: {e}", "ERROR")
        return False

# ==========================================
# 👻 ATTACK & UTILITY FUNCTIONS
# ==========================================
def do_ghost_mode(token):
    """Randomize GitHub profile to avoid spam detection"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    companies = ["Freelance Developer", "Open Source", "Self-Employed", "Tech Startup", "Remote Worker", "Indie Hacker", "Cyber Security Dept"]
    locations = ["San Francisco, CA", "London, UK", "Berlin, Germany", "Tokyo, Japan", "New York", "Remote", "Singapore", "Toronto, Canada"]
    bios = ["Passionate developer.", "Building things.", "Open source contributor.", "Coffee to code converter.", "Tech enthusiast.", "Learning every day.", "DevOps & Cloud Explorer."]
    
    payload = {
        "company": random.choice(companies),
        "location": random.choice(locations),
        "bio": random.choice(bios)
    }
    
    try:
        res = requests.patch("https://api.github.com/user", headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            return f"┣ 👻 Disguise: SUCCESS\n┣ 🏢 {payload['company']}\n┣ 📍 {payload['location']}\n┗ 📝 {payload['bio']}"
        else:
            return f"┗ 🔴 Disguise: FAILED ({res.status_code})"
    except Exception:
        return "┗ 🔴 Disguise: ERROR"

def do_action(token, repo, action_type):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        owner = repo.split('/')[0]
    except Exception:
        owner = repo

    results = []

    if action_type in ["/stars", "/allin"]:
        star_url = f"https://api.github.com/user/starred/{repo}"
        try:
            s_res = requests.put(star_url, headers=headers, timeout=10)
            results.append("┣ ★ Star   : GRANTED" if s_res.status_code == 204 else f"┣ 🔴 Star   : FAILED ({s_res.status_code})")
        except Exception:
            results.append("┣ 🔴 Star   : ERROR")
        if action_type == "/allin": time.sleep(10)

    if action_type in ["/forks", "/allin"]:
        fork_url = f"https://api.github.com/repos/{repo}/forks"
        try:
            f_res = requests.post(fork_url, headers=headers, timeout=10)
            results.append("┣ ⎇ Fork   : DEPLOYED" if f_res.status_code == 202 else f"┣ 🔴 Fork   : FAILED ({f_res.status_code})")
        except Exception:
            results.append("┣ 🔴 Fork   : ERROR")
        if action_type == "/allin": time.sleep(10)

    if action_type in ["/watch", "/allin"]:
        watch_url = f"https://api.github.com/repos/{repo}/subscription"
        try:
            w_res = requests.put(watch_url, headers=headers, json={"subscribed": True}, timeout=10)
            results.append("┣ 👁 Watch  : ACTIVE" if w_res.status_code == 200 else f"┣ 🔴 Watch  : FAILED ({w_res.status_code})")
        except Exception:
            results.append("┣ 🔴 Watch  : ERROR")
        if action_type == "/allin": time.sleep(10)

    if action_type in ["/follow", "/allin"]:
        follow_url = f"https://api.github.com/user/following/{owner}"
        try:
            fl_res = requests.put(follow_url, headers=headers, timeout=10)
            results.append("┣ 👤 Follow : SUCCESS" if fl_res.status_code == 204 else f"┣ 🔴 Follow : FAILED ({fl_res.status_code})")
        except Exception:
            results.append("┣ 🔴 Follow : ERROR")

    if action_type == "/unstar":
        star_url = f"https://api.github.com/user/starred/{repo}"
        try:
            s_res = requests.delete(star_url, headers=headers, timeout=10)
            results.append("┣ ☆ Unstar : SUCCESS" if s_res.status_code == 204 else f"┣ 🔴 Unstar : FAILED ({s_res.status_code})")
        except Exception:
            results.append("┣ 🔴 Unstar : ERROR")

    if action_type == "/unwatch":
        watch_url = f"https://api.github.com/repos/{repo}/subscription"
        try:
            w_res = requests.delete(watch_url, headers=headers, timeout=10)
            results.append("┣ 🙈 Unwatch: SUCCESS" if w_res.status_code == 204 else f"┣ 🔴 Unwatch: FAILED ({w_res.status_code})")
        except Exception:
            results.append("┣ 🔴 Unwatch: ERROR")

    if action_type == "/unfollow":
        follow_url = f"https://api.github.com/user/following/{owner}"
        try:
            fl_res = requests.delete(follow_url, headers=headers, timeout=10)
            results.append("┣ 🚶 Unfollow: SUCCESS" if fl_res.status_code == 204 else f"┣ 🔴 Unfollow: FAILED ({fl_res.status_code})")
        except Exception:
            results.append("┣ 🔴 Unfollow: ERROR")

    if results:
        results[-1] = "┗" + results[-1][1:]
        
    return "\n".join(results)

def get_random_license(username, year):
    """Returns random license text and its name (5 Complete Options)"""
    mit = f"""MIT License

Copyright (c) {year} {username}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

    isc = f"""ISC License

Copyright (c) {year}, {username}

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

    bsd2 = f"""BSD 2-Clause License

Copyright (c) {year}, {username}
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

    bsd3 = f"""BSD 3-Clause License

Copyright (c) {year}, {username}
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

    unlicense = f"""This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>"""

    licenses = [
        (mit, "MIT"),
        (isc, "ISC"),
        (bsd2, "BSD-2-Clause"),
        (bsd3, "BSD-3-Clause"),
        (unlicense, "The Unlicense")
    ]
    
    return random.choice(licenses)

def do_stealth_clone(pat, target_repo, custom_repo_name=None, old_repo_name=None, status_cb=None):
    """Perform a stealth clone with Auto Size Guard, README Sync, and full branch wipe"""
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github.v3+json"
    }

    if status_cb: status_cb("🔐 Validating Authentication Token...")
    user_res = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    if user_res.status_code != 200:
        return "❌ Failed to authenticate PAT."
        
    user_data = user_res.json()
    username = user_data.get("login")
    user_id = user_data.get("id")
    user_email = user_data.get("email")
    
    # GitHub Contribution Graph STRICT REQUIREMENT:
    # Commit email must exactly match the account's verified email or strict ID-based noreply
    if not user_email:
        user_email = f"{user_id}+{username}@users.noreply.github.com"

    # ====================================================
    # 🛡️ AUTO SIZE GUARD (Max 500 MB)
    # ====================================================
    if status_cb: status_cb("📊 Analyzing repository size...")
    try:
        repo_info_res = requests.get(f"https://api.github.com/repos/{target_repo}", headers=headers, timeout=10)
        if repo_info_res.status_code == 200:
            repo_size_kb = repo_info_res.json().get("size", 0)
            repo_size_mb = repo_size_kb / 1024
            if repo_size_mb > 500: 
                return f"❌ SKIPPED: Repo is too large ({repo_size_mb:.1f} MB). Max limit is 500 MB."
            if status_cb: status_cb(f"✅ Size verified ({repo_size_mb:.1f} MB). Safe to clone.")
    except Exception as e:
        log_terminal(f"Size check failed: {e}", "WARNING")

    repo_name = target_repo.split("/")[-1]

    # Mode Handling
    if old_repo_name and custom_repo_name:
        # Mode Rename & Overwrite (Internal API fallback)
        if status_cb: status_cb(f"♻️ Renaming old repository '{old_repo_name}' to '{custom_repo_name}'...")
        repo_name = custom_repo_name
        rename_url = f"https://api.github.com/repos/{username}/{old_repo_name}"
        rename_res = requests.patch(rename_url, headers=headers, json={"name": custom_repo_name}, timeout=10)
        if rename_res.status_code not in [200, 201]:
            repo_name = old_repo_name
    elif old_repo_name and not custom_repo_name:
        # Mode 3: JUST OVERWRITE (Keep old name!)
        repo_name = old_repo_name
        if status_cb: status_cb(f"♻️ Target is existing repository '{repo_name}'. Preparing to overwrite...")
    else:
        # Mode 1 & 2: Create New
        if custom_repo_name:
            repo_name = custom_repo_name
        if status_cb: status_cb(f"🆕 Creating repository '{repo_name}'...")
        create_res = requests.post("https://api.github.com/user/repos", headers=headers, json={"name": repo_name, "private": False}, timeout=10)

    work_dir = tempfile.mkdtemp()
    repo_dir = os.path.join(work_dir, repo_name)
    try:
        if status_cb: status_cb(f"⬇️ Downloading source code from '{target_repo}'...")
        clone_url = f"https://github.com/{target_repo}.git"
        subprocess.run(["git", "clone", clone_url, repo_name], cwd=work_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        if status_cb: status_cb("🧹 Sanitizing repository (Removing old workflows & Git history)...")
        # 1. Wipe Git History
        git_folder = os.path.join(repo_dir, ".git")
        if os.path.exists(git_folder):
            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(git_folder, onerror=remove_readonly)
            
        # 2. Wipe Workflows to prevent GitHub push errors
        github_workflows_folder = os.path.join(repo_dir, ".github", "workflows")
        if os.path.exists(github_workflows_folder):
            shutil.rmtree(github_workflows_folder, ignore_errors=True)

        # ====================================================
        # 🔄 FITUR BARU: AUTO-SYNC README TITLE & CONTENT
        # ====================================================
        if status_cb: status_cb("🔄 Syncing repository name inside README.md...")
        original_target_name = target_repo.split("/")[-1]
        for filename in os.listdir(repo_dir):
            if filename.lower() == "readme.md":
                readme_path = os.path.join(repo_dir, filename)
                try:
                    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    # Mengganti semua string nama repo lama dengan nama repo lu
                    content = content.replace(original_target_name, repo_name)
                    
                    with open(readme_path, "w", encoding="utf-8", errors="ignore") as f:
                        f.write(content)
                except:
                    pass

        # 3. Inject Open Source License
        if status_cb: status_cb("📝 Injecting Open Source License...")
        license_path = os.path.join(repo_dir, "LICENSE")
        current_year = time.strftime("%Y")
        license_content, license_name = get_random_license(username, current_year)
        with open(license_path, "w", encoding="utf-8") as f:
            f.write(license_content)

        if status_cb: status_cb("🏗️ Rebuilding repository structure...")
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", username], cwd=repo_dir, check=True)
        # Email update so the green dot registers in contribution calendar
        subprocess.run(["git", "config", "user.email", user_email], cwd=repo_dir, check=True)
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial commit for DevOps/AIML project"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)

        if status_cb: status_cb("🚀 Force pushing deployment to origin (main)...")
        remote_url = f"https://{username}:{pat}@github.com/{username}/{repo_name}.git"
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=repo_dir, check=True)
        
        # PUSH HANYA KE MAIN
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        # UBAH DEFAULT BRANCH KE MAIN VIA API
        if status_cb: status_cb("⚙️ Setting 'main' as default branch...")
        requests.patch(f"https://api.github.com/repos/{username}/{repo_name}", headers=headers, json={"default_branch": "main"}, timeout=5)

        # HAPUS MASTER JIKA ADA (Biar nggak belang & lisensi kebaca)
        try:
            subprocess.run(["git", "push", "origin", "--delete", "master"], cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

        return f"✅ SUCCESS [{license_name}]"
        
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        log_terminal(f"Git Execution Failed:\n{err_msg}", "ERROR")
        short_err = err_msg.split('\n')[0][:60]
        return f"❌ GIT ERROR: {short_err}..."
    except Exception as e:
        log_terminal(f"System Error: {e}", "ERROR")
        return f"❌ SYS ERROR: Failed to process."
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

def run_attack_sequence(user_id, cmd_used, target_repo, tokens_to_use):
    """Executes the attack logic and broadcasts the results"""
    repo_url = f"https://github.com/{target_repo}"
    
    log_terminal(f"Initiating {cmd_used.upper()} sequence...", "INFO")
    log_terminal(f"Target: {target_repo} | Workers: {len(tokens_to_use)} Nodes", "INFO")
    
    msg_id = send_message(user_id, f"<blockquote>🚀 <b>COMMAND RECEIVED</b>\nMode: <b>{cmd_used.upper()}</b>\nTarget: <a href='{repo_url}'>{target_repo}</a>\nWorkers: <b>{len(tokens_to_use)} Nodes</b></blockquote>\n\n⏳ <i>Processing... (Execution reports will be broadcasted)</i>")
    bcast_msgs = broadcast_message(f"<blockquote>🚀 <b>COMMAND RECEIVED</b>\nMode: <b>{cmd_used.upper()}</b>\nTarget: <a href='{repo_url}'>{target_repo}</a>\nWorkers: <b>{len(tokens_to_use)} Nodes</b></blockquote>\n\n⏳ <i>Processing...</i>", exclude_id=user_id)

    for idx, token in enumerate(tokens_to_use):
        log_terminal(f"Deploying Node #{idx+1} for {cmd_used.upper()}...", "PROCESS")
        
        result = do_action(token, target_repo, cmd_used)
        
        clean_result = result.replace('┣', '').replace('┗', '').replace('🔴', '[FAIL]').replace('★', '[OK]').replace('⎇', '[OK]').replace('👁', '[OK]').replace('👤', '[OK]').replace('☆', '[OK]').replace('🙈', '[OK]').replace('🚶', '[OK]')
        log_terminal(f"Node #{idx+1} Execution Status:\n{clean_result}", "SUCCESS")
        
        msg = (
            f"<blockquote>✦ <b>NODE #{idx+1} REPORT</b> ✦\n"
            f"❖ <b>Target:</b> <a href='{repo_url}'>{target_repo}</a>\n"
            f"❖ <b>Action:</b> {cmd_used.upper()}</blockquote>\n"
            f"<b>[ Execution Status ]</b>\n<code>{result}</code>"
        )
        
        send_message(user_id, msg)
        broadcast_message(msg, exclude_id=user_id)
        
        if idx < len(tokens_to_use) - 1:
            log_terminal("Cooldown 20 seconds to avoid spam detection...", "PROCESS")
            time.sleep(20)
            
    log_terminal(f"MISSION ACCOMPLISHED: {cmd_used.upper()} completed on {target_repo}.", "SUCCESS")
    final_alert = f"<blockquote>🎉 <b>MISSION ACCOMPLISHED!</b>\n{len(tokens_to_use)} workers successfully executed <b>{cmd_used.upper()}</b> on <a href='{repo_url}'>{target_repo}</a>.</blockquote>"
    send_message(user_id, final_alert)
    broadcast_message(final_alert, exclude_id=user_id)

# ==========================================
# 📡 TELEGRAM POLLING LISTENER
# ==========================================
def main():
    print_main_banner()

    log_terminal("Registering Bot Commands...", "PROCESS")
    set_bot_commands()

    last_update_id = 0
    valid_commands = ["/stars", "/forks", "/watch", "/follow", "/allin", "/unstar", "/unwatch", "/unfollow", "/clone", "/npm"]

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            response = requests.get(url, timeout=35).json()
            
            for update in response.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "")
                user_id = str(message.get("from", {}).get("id", ""))
                username = message.get("from", {}).get("username", "Unknown")
                
                auth_users = get_authorized_users()
                if user_id not in auth_users:
                    if text:
                        log_terminal(f"Blocked unauthorized access attempt from ID: {user_id}", "ERROR")
                    continue

                if text:
                    if ASCII_TIMER is None:
                        cmd_name = text.split()[0] if text.startswith("/") else "Interactive Reply"
                        log_terminal(f"Received input from @{username} (ID: {user_id}): {cmd_name}", "INFO")

                # ==========================
                # INTERACTIVE STATE HANDLER
                # ==========================
                if user_id in PENDING_STATES:
                    state = PENDING_STATES[user_id]
                    
                    if text == "/cancel":
                        del PENDING_STATES[user_id]
                        log_terminal("Action Cancelled by user.", "INFO")
                        send_message(user_id, "🚫 <b>Action Cancelled.</b>")
                        continue
                        
                    action = state.get('action', 'wait_repo_choice')
                    
                    # ------------------------------------------
                    # NPM BOOSTER INTERACTIVE FLOW
                    # ------------------------------------------
                    if action == 'wait_npm_package':
                        pkg_name = text.strip()
                        del PENDING_STATES[user_id]
                        
                        send_message(user_id, f"🔍 <i>Checking registry for '{pkg_name}'...</i>")
                        version = get_npm_latest_version(pkg_name)
                        
                        if not version:
                            send_message(user_id, f"❌ <b>FAILED!</b>\nPackage <code>{pkg_name}</code> not found on NPM Registry.")
                            continue
                            
                        init_msg = (
                            f"╔═════════════════════════╗\n"
                            f"   🚀 <b>NPM BOOST PIPELINE</b>\n"
                            f"╚═════════════════════════╝\n\n"
                            f"<i>Initializing download simulation for {pkg_name} v{version}...</i>\n\n"
                            f"🛡️ <i>Engineered by Abie Haryatmo</i>"
                        )
                        msg_id = send_message(user_id, init_msg)
                        bcast_msgs = broadcast_message(init_msg, exclude_id=user_id)
                        
                        log_terminal(f"Boosting NPM package {pkg_name} (v{version})...", "PROCESS")
                        
                        success_hits = do_npm_boost(pkg_name, version, user_id, msg_id, bcast_msgs)
                        
                        final_msg = (
                            f"╔═════════════════════════╗\n"
                            f"   ✅ <b>NPM BOOST COMPLETED</b>\n"
                            f"╚═════════════════════════╝\n\n"
                            f"❖ <b>Package:</b> <code>{pkg_name}</code>\n"
                            f"❖ <b>Version:</b> <code>v{version}</code>\n"
                            f"└ 🚀 <b>{success_hits} Downloads Simulated!</b>\n\n"
                            f"Deploy, Scale, Automate. The future is now.\n"
                            f"🛡️ <i>Engineered by Abie Haryatmo</i>"
                        )
                        edit_message(user_id, msg_id, final_msg)
                        edit_broadcast_message(bcast_msgs, final_msg)
                        log_terminal(f"NPM Boost completed for {pkg_name}. Hits: {success_hits}", "SUCCESS")
                        continue

                    # ------------------------------------------
                    # CLONE INTERACTIVE FLOW (WIZARD MODE)
                    # ------------------------------------------
                    elif action == 'wait_clone_mode':
                        if text.strip() not in ['1', '2', '3']:
                            send_message(user_id, "❌ <b>Invalid Choice!</b>\nPlease reply with number <b>1, 2, or 3</b>.\n<i>Type /cancel to abort.</i>")
                            continue
                            
                        state['clone_mode'] = text.strip()
                        
                        if text.strip() == '1':
                            state['action'] = 'wait_clone_input'
                            instruction = "👇 <b>MODE 1: STANDARD CLONE</b>\n\nEnter your <b>PAT</b> and the <b>Target Repos</b>.\nSeparate them using spaces, commas, or new lines.\n\n<b>Format:</b>\n<code>[PAT] [repo1] [repo2] ...</code>\n\n<b>Example:</b>\n<code>ghp_xxx ownerA/repoA ownerB/repoB</code>"
                            send_message(user_id, f"✅ Mode {text.strip()} Selected!\n\n{instruction}\n\n<i>*Type /cancel to abort.</i>")
                        
                        elif text.strip() == '2':
                            state['action'] = 'wait_clone_input'
                            instruction = "👇 <b>MODE 2: CUSTOM NAME CLONE</b>\n\nEnter your <b>PAT</b> and pairs of <b>[Target Repo] [New Name]</b>.\nSeparate them using spaces, commas, or new lines.\n\n<b>Format:</b>\n<code>[PAT] [repo1] [new_name1] [repo2] [new_name2] ...</code>\n\n<b>Example:</b>\n<code>ghp_xxx owner/repo my-new-project</code>"
                            send_message(user_id, f"✅ Mode {text.strip()} Selected!\n\n{instruction}\n\n<i>*Type /cancel to abort.</i>")
                        
                        elif text.strip() == '3':
                            state['action'] = 'wait_clone_pat_m3'
                            send_message(user_id, "✅ <b>Mode 3 Selected! (Overwrite Old Repo)</b>\n\n👇 First, please send your <b>GitHub PAT</b> (Personal Access Token):\n\n<i>Type /cancel to abort.</i>")
                        continue

                    # --- MODE 1 & 2 INPUT HANDLER ---
                    elif action == 'wait_clone_input':
                        mode = state.get('clone_mode', '1')
                        del PENDING_STATES[user_id]

                        raw_text = text.replace(',', ' ').replace('\n', ' ')
                        words = [w.strip() for w in raw_text.split() if w.strip()]
                        
                        pat_token = None
                        targets_raw = []

                        for w in words:
                            if w.startswith("ghp_") or w.startswith("github_pat_"):
                                if not pat_token:
                                    pat_token = w
                            else:
                                targets_raw.append(w)

                        if not pat_token:
                            send_message(user_id, "❌ <b>PAT Not Found!</b>\nToken must start with 'ghp_' or 'github_pat_'.")
                            continue

                        if not targets_raw:
                            send_message(user_id, "❌ <b>No targets found!</b>\nPlease provide at least 1 target repository.")
                            continue

                        target_repos = []
                        if mode == '1':
                            for repo in targets_raw:
                                if "github.com/" in repo:
                                    repo = repo.split("github.com/")[-1]
                                repo_clean = repo.split("?")[0].split("#")[0].replace(".git", "").strip("/")
                                target_repos.append((repo_clean, None, None))
                                
                        elif mode == '2':
                            if len(targets_raw) % 2 != 0:
                                send_message(user_id, "❌ <b>Invalid Format!</b>\nThis mode requires pairs (Even number of items). Ensure each target repo has a matching custom name.")
                                continue
                                
                            for i in range(0, len(targets_raw), 2):
                                repo = targets_raw[i]
                                paired_name = targets_raw[i+1]
                                if "github.com/" in repo:
                                    repo = repo.split("github.com/")[-1]
                                repo_clean = repo.split("?")[0].split("#")[0].replace(".git", "").strip("/")
                                target_repos.append((repo_clean, None, paired_name))

                        execute_pipeline = True

                    # --- MODE 3 SPECIFIC WIZARD FLOW (STRICT 1-BY-1 INPUT) ---
                    elif action == 'wait_clone_pat_m3':
                        pat = text.strip()
                        if not pat.startswith("ghp_") and not pat.startswith("github_pat_"):
                            send_message(user_id, "❌ <b>Invalid PAT!</b>\nToken must start with 'ghp_' or 'github_pat_'.\nPlease try again or type /cancel.")
                            continue
                        
                        send_message(user_id, "⏳ <i>Verifying PAT and fetching your repositories...</i>")
                        
                        headers = {
                            "Authorization": f"Bearer {pat}", 
                            "Accept": "application/vnd.github.v3+json"
                        }
                        
                        try:
                            user_res = requests.get("https://api.github.com/user", headers=headers, timeout=10)
                            if user_res.status_code != 200:
                                send_message(user_id, "❌ <b>PAT Authentication Failed!</b>\nPlease check your token and try again, or type /cancel.")
                                continue
                            username_target = user_res.json().get("login")
                        except Exception as e:
                            log_terminal(f"API Error: {e}", "ERROR")
                            send_message(user_id, "❌ <b>Connection Error!</b>\nFailed to reach GitHub API. Try again or type /cancel.")
                            continue

                        try:
                            repo_res = requests.get("https://api.github.com/user/repos?sort=updated&per_page=100&affiliation=owner", headers=headers, timeout=15)
                            if repo_res.status_code == 200:
                                repos = [r['full_name'] for r in repo_res.json()]
                            else:
                                repos = []
                        except:
                            repos = []

                        if not repos:
                            send_message(user_id, f"❌ <b>No repositories found in your account ({username_target}).</b>\nPlease ensure you have repositories or type /cancel.")
                            continue

                        state['pat'] = pat
                        state['old_repos_list'] = repos
                        state['action'] = 'wait_clone_select_m3'

                        repo_list_msg = f"<blockquote>📁 <b>YOUR REPOSITORIES ({username_target})</b></blockquote>\n"
                        for i, r in enumerate(repos):
                            repo_list_msg += f"<b>{i+1}.</b> <code>{r}</code>\n"

                        repo_list_msg += f"\n👉 <b>Reply with the numbers of the repos you want to OVERWRITE.</b>\n<i>(Separate with spaces or commas, e.g., 1, 3, 5)</i>\n\n⚠️ <b>WARNING:</b> The selected repos will be completely overwritten!"
                        send_message(user_id, repo_list_msg)
                        continue

                    elif action == 'wait_clone_select_m3':
                        raw_numbers = text.replace(',', ' ').split()
                        repos = state['old_repos_list']
                        selected_old = []
                        
                        try:
                            for num_str in raw_numbers:
                                num = int(num_str)
                                if 1 <= num <= len(repos):
                                    full_name = repos[num-1]
                                    repo_name_only = full_name.split('/')[-1] 
                                    if repo_name_only not in selected_old:
                                        selected_old.append(repo_name_only)
                        except ValueError:
                            pass 

                        if not selected_old:
                            send_message(user_id, "❌ <b>No valid numbers selected.</b>\nPlease try again using numbers from the list (e.g., 1, 3, 5).")
                            continue

                        state['selected_old'] = selected_old
                        state['current_m3_index'] = 0
                        state['collected_targets'] = [] # Menyimpan target yang dikumpulkan
                        state['action'] = 'wait_clone_target_1by1'

                        first_old = selected_old[0]
                        msg = (f"✅ <b>You selected {len(selected_old)} repos to OVERWRITE.</b>\n"
                               f"<i>To prevent mix-ups, we will process them ONE BY ONE.</i>\n\n"
                               f"👇 <b>STEP 1/{len(selected_old)}:</b>\n"
                               f"Please send the <b>Target Repo</b> to clone into <code>{first_old}</code>\n"
                               f"<i>(Example: owner/repo)</i>\n\n"
                               f"<i>Type /cancel to abort.</i>")
                        send_message(user_id, msg)
                        continue

                    elif action == 'wait_clone_target_1by1':
                        raw_text = text.replace('\n', ' ').strip()
                        if not raw_text:
                            send_message(user_id, "❌ <b>Input is empty!</b>\nPlease provide a target repo.")
                            continue
                            
                        target_raw = raw_text.split()[0]
                        if "github.com/" in target_raw:
                            target_raw = target_raw.split("github.com/")[-1]
                        target_clean = target_raw.split("?")[0].split("#")[0].replace(".git", "").strip("/")
                        
                        if "/" not in target_clean:
                            send_message(user_id, "❌ <b>Invalid Format!</b>\nPlease use owner/repo format.")
                            continue
                            
                        idx = state['current_m3_index']
                        old_name = state['selected_old'][idx]
                        
                        # Simpan ke daftar koleksi alih-alih eksekusi langsung
                        state['collected_targets'].append((target_clean, old_name, None))
                        
                        state['current_m3_index'] += 1
                        if state['current_m3_index'] < len(state['selected_old']):
                            next_old = state['selected_old'][state['current_m3_index']]
                            next_msg = (
                                f"👇 <b>STEP {state['current_m3_index']+1}/{len(state['selected_old'])}:</b>\n"
                                f"Great! Now send the <b>Target Repo</b> to clone into <code>{next_old}</code>\n"
                                f"<i>(Type /cancel to abort the rest)</i>"
                            )
                            send_message(user_id, next_msg)
                            execute_pipeline = False
                        else:
                            # Kalau semua input sudah kekumpul, siapkan eksekusi di UNIFIED DASHBOARD
                            target_repos = state['collected_targets']
                            pat_token = state['pat']
                            del PENDING_STATES[user_id]
                            execute_pipeline = True
                    else:
                        execute_pipeline = False

                    # --- DEVOPS UNIFIED EXECUTION PIPELINE DASHBOARD (ALL MODES) ---
                    if execute_pipeline:
                        log_terminal(f"Initiating Stealth Clone for {len(target_repos)} repos...", "PROCESS")
                        
                        # Siapkan list status buat semua repo
                        repo_statuses = []
                        for repo, old_name, custom_name in target_repos:
                            if old_name and custom_name:
                                display_name = f"{old_name} ➔ {custom_name}"
                            elif old_name and not custom_name:
                                display_name = f"{old_name} (Overwritten)"
                            elif custom_name:
                                display_name = custom_name
                            else:
                                display_name = repo.split('/')[-1]
                                
                            repo_statuses.append({
                                "target": repo,
                                "deploy": display_name,
                                "state": "⏳ Pending...",
                                "result": ""
                            })

                        def build_dashboard_msg(live_log="", is_finished=False):
                            header = "✅ <b>PIPELINE COMPLETED</b>" if is_finished else "🚀 <b>STEALTH CLONE PIPELINE</b>"
                            msg = f"╔═════════════════════════╗\n   {header}\n╚═════════════════════════╝\n\n"
                            
                            for r in repo_statuses:
                                msg += f"❖ <b>{r['target']}</b> ➡️ {r['deploy']}\n"
                                if r['result']:
                                    msg += f"  └ {r['result']}\n\n"
                                else:
                                    msg += f"  └ Status: <i>{r['state']}</i>\n\n"
                                    
                            if live_log and not is_finished:
                                msg += f"══════════════════════\n<b>[Live Logs]</b>\n{live_log}\n\n"
                                
                            if is_finished:
                                msg += "Deploy, Scale, Automate. The future is now.\n"
                                
                            msg += "🛡️ <i>Engineered by Abie Haryatmo</i>"
                            return msg

                        # Kirim dashboard awal ke user dan broadcast
                        msg_id = send_message(user_id, build_dashboard_msg("Initializing deployment pipeline..."))
                        bcast_msgs = broadcast_message(build_dashboard_msg("Initializing deployment pipeline..."), exclude_id=user_id)

                        # Mulai eksekusi per repo
                        for i, (repo, old_name, custom_name) in enumerate(target_repos):
                            repo_statuses[i]['state'] = "🔄 Processing..."
                            
                            def clone_status_updater(step_msg):
                                repo_statuses[i]['state'] = step_msg
                                live_msg = build_dashboard_msg(step_msg)
                                edit_message(user_id, msg_id, live_msg)
                                edit_broadcast_message(bcast_msgs, live_msg)

                            log_terminal(f"Cloning {repo} as {repo_statuses[i]['deploy']}...", "PROCESS")
                            res = do_stealth_clone(pat_token, repo, custom_name, old_name, status_cb=clone_status_updater)
                            
                            repo_statuses[i]['result'] = res
                            repo_statuses[i]['state'] = "✅ Done"
                            log_terminal(f"Clone result for {repo}: {res}", "INFO")

                            # Update dashboard setelah 1 repo selesai, siap pindah ke repo berikutnya
                            transition_msg = build_dashboard_msg("Moving to next repository...")
                            edit_message(user_id, msg_id, transition_msg)
                            edit_broadcast_message(bcast_msgs, transition_msg)

                        # Pipeline benar-benar selesai
                        final_msg = build_dashboard_msg(is_finished=True)
                        edit_message(user_id, msg_id, final_msg)
                        edit_broadcast_message(bcast_msgs, final_msg)
                        continue

                    # ------------------------------------------
                    # INTERACTIVE SCAN BULK & BROADCAST 
                    # ------------------------------------------
                    elif action == 'wait_scan_target':
                        del PENDING_STATES[user_id]
                        
                        raw_text = text.replace(',', ' ').replace('\n', ' ')
                        targets_raw = [w.strip() for w in raw_text.split() if w.strip()]
                        
                        target_repos = []
                        for w in targets_raw:
                            repo = w
                            if "github.com/" in repo:
                                repo = repo.split("github.com/")[-1]
                            repo = repo.split("?")[0].split("#")[0].strip("/")
                            if repo.endswith(".git"):
                                repo = repo[:-4]
                            
                            if "/" in repo:
                                target_repos.append(repo)
                            else:
                                # Auto expand username
                                user_repos = get_user_repos(repo)
                                if user_repos:
                                    target_repos.extend(user_repos[:15]) # Limit top 15
                                    
                        # Remove duplicates while preserving order
                        target_repos = list(dict.fromkeys(target_repos))
                        
                        if not target_repos:
                            send_message(user_id, "❌ <b>No valid repositories found!</b>\nPlease provide valid GitHub links or owner/repo format.")
                            continue
                            
                        log_terminal(f"Initiating bulk scan for {len(target_repos)} repos...", "PROCESS")
                        
                        init_msg = f"⏳ <b>SCANNING {len(target_repos)} REPOSITORIES...</b>\n📊 <b>Progress:</b> <code>[░░░░░░░░░░] 0%</code>"
                        msg_id = send_message(user_id, init_msg)
                        bcast_msgs = broadcast_message(init_msg, exclude_id=user_id)
                        
                        report = (f"╔═════════════════════════╗\n"
                                  f"   📊 <b>TARGET INTELLIGENCE</b>\n"
                                  f"╚═════════════════════════╝\n\n")
                        
                        for i, repo in enumerate(target_repos):
                            info = get_repo_info(repo)
                            
                            if info:
                                size_mb = info.get('size_kb', 0) / 1024
                                report += (
                                    f"❖ <b><a href='https://github.com/{repo}'>{repo}</a></b>\n"
                                    f"   ├ ★ Stars : {info['stars']} | ⎇ Forks : {info['forks']}\n"
                                    f"   └ 👁 Watch : {info['watchers']} | 📦 Size : {size_mb:.2f} MB\n\n"
                                )
                            else:
                                report += f"❖ <b><a href='https://github.com/{repo}'>{repo}</a></b>\n   └ ❌ Not Found / Private\n\n"
                                
                            bar_length = 10
                            filled = int((i + 1) / len(target_repos) * bar_length)
                            bar = "█" * filled + "░" * (bar_length - filled)
                            percent = int((i + 1) / len(target_repos) * 100)
                            anim = ["⏳", "⌛"][i % 2]
                            
                            loading_text = f"{anim} <b>SCANNING {len(target_repos)} REPOSITORIES...</b>\n\n📊 <b>Progress:</b> <code>[{bar}] {percent}%</code>\n🔍 <b>Scanning:</b> <code>{repo}...</code>"
                            
                            if msg_id: edit_message(user_id, msg_id, loading_text)
                            if bcast_msgs: edit_broadcast_message(bcast_msgs, loading_text)
                            
                            time.sleep(1) # Prevent API limits
                            
                        report += f"💯 <i>Scan completed for {len(target_repos)} repositories.</i>"
                        
                        if msg_id: edit_message(user_id, msg_id, report)
                        else: send_message(user_id, report)
                        
                        if bcast_msgs: edit_broadcast_message(bcast_msgs, report)
                        else: broadcast_message(report, exclude_id=user_id)
                        
                        continue

                    # ------------------------------------------
                    # OTHER INTERACTIVE FLOWS
                    # ------------------------------------------
                    elif action == 'wait_repo_choice':
                        if text.isdigit():
                            choice = int(text)
                            repos = state['repos']
                            
                            if 1 <= choice <= len(repos):
                                selected_repo = repos[choice - 1]
                                cmd_used = state['cmd_used']
                                tokens_to_use = state.get('tokens', [])
                                
                                del PENDING_STATES[user_id]
                                
                                # Process Attack
                                run_attack_sequence(user_id, cmd_used, selected_repo, tokens_to_use)
                                continue
                            else:
                                send_message(user_id, f"❌ <b>Invalid Number!</b>\nPlease choose a number between 1 and {len(repos)}, or type /cancel.")
                                continue
                        else:
                            send_message(user_id, "⚠️ <b>Pending Action Detected!</b>\nPlease reply with the repository number, or type /cancel to abort.")
                            continue

                    elif action == 'wait_adduser_id':
                        text = f"/adduser {text}"
                        del PENDING_STATES[user_id]
                    elif action == 'wait_check_tokens':
                        text = f"/check {text}"
                        del PENDING_STATES[user_id]
                    elif action == 'wait_ghost_tokens':
                        text = f"/ghost {text}"
                        del PENDING_STATES[user_id]
                    elif action == 'wait_ascii_text':
                        text = f"/ascii {text}"
                        del PENDING_STATES[user_id]
                    elif action == 'wait_attack_args':
                        cmd = state.get('cmd_used')
                        text = f"{cmd} {text}"
                        del PENDING_STATES[user_id]

                # ==========================
                # NORMAL COMMAND PROCESSING
                # ==========================
                if text == "/start" or text == "/help":
                    help_msg = (
                        "<blockquote>🤖 <b>XIANBEESTORE COMMAND CENTER</b></blockquote>\n\n"
                        "<b>Intelligence & Utilities:</b>\n"
                        "👉 <code>/scan</code> <i>(Bulk Target Intelligence)</i>\n"
                        "👉 <code>/check [tokens...]</code> <i>(Check token health)</i>\n"
                        "👉 <code>/clone</code> <i>(Stealth Clone Repos - Interactive)</i>\n"
                        "👉 <code>/npm</code> <i>(Boost NPM Package Downloads)</i>\n"
                        "👉 <code>/ghost [tokens...]</code> <i>(Randomize profiles to avoid bans)</i>\n"
                        "👉 <code>/ascii [text]</code> <i>(Display ASCII art on terminal)</i>\n\n"
                        "<b>Attack Commands (Auto Counts Tokens):</b>\n"
                        "👉 <code>/stars [target] [tokens...]</code>\n"
                        "👉 <code>/forks [target] [tokens...]</code>\n"
                        "👉 <code>/watch [target] [tokens...]</code>\n"
                        "👉 <code>/follow [target] [tokens...]</code>\n"
                        "👉 <code>/allin [target] [tokens...]</code>\n\n"
                        "<b>Undo / Revert Commands:</b>\n"
                        "👉 <code>/unstar [target] [tokens...]</code>\n"
                        "👉 <code>/unwatch [target] [tokens...]</code>\n"
                        "👉 <code>/unfollow [target] [tokens...]</code>\n\n"
                        "<b>User Management:</b>\n"
                        "👉 <code>/adduser [ID]</code> <i>(Admin only)</i>\n"
                        "👉 <code>/users</code> <i>(List authorized users)</i>\n\n"
                        "<i>*Note: The bot will automatically use ALL provided tokens. To limit nodes, add a number before target (e.g., /allin 5 delmore77/repo)</i>"
                    )
                    send_message(user_id, help_msg)
                    continue

                if text.strip() == "/npm":
                    PENDING_STATES[user_id] = {'action': 'wait_npm_package'}
                    send_message(user_id, "👇 <b>NPM BOOSTER INITIATED</b>\n\nPlease enter the <b>NPM Package Name</b> you want to boost:\n<i>Example: my-awesome-package</i>\n\n<i>Type /cancel to abort.</i>")
                    continue

                if text.strip() == "/clone":
                    PENDING_STATES[user_id] = {'action': 'wait_clone_mode'}
                    menu_msg = (
                        "👇 <b>SELECT STEALTH CLONE MODE</b>\n\n"
                        "<b>1.</b> 🆕 Standard Clone <i>(Create new with original name)</i>\n"
                        "<b>2.</b> ✏️ Custom Name Clone <i>(Create new with custom name)</i>\n"
                        "<b>3.</b> ♻️ Overwrite Old Repo <i>(Replace your old repo contents)</i>\n\n"
                        "👉 <b>Reply with number 1, 2, or 3.</b>\n"
                        "<i>Type /cancel to abort.</i>"
                    )
                    send_message(user_id, menu_msg)
                    continue
                elif text.startswith("/clone "):
                    send_message(user_id, "ℹ️ <b>Clone Feature Updated!</b>\nPlease just type <code>/clone</code> to enter the interactive menu.")
                    continue

                if text.startswith("/ascii"):
                    parts = text.split(" ", 1)
                    if len(parts) == 1:
                        PENDING_STATES[user_id] = {'action': 'wait_ascii_text'}
                        send_message(user_id, "👇 <b>Please enter the text you want to display on terminal:</b>\n<i>Example: I LOVE YOU</i>\n\n<i>Type /cancel to abort.</i>")
                        continue
                    
                    ascii_text = parts[1]
                    
                    if not pyfiglet:
                        log_terminal("User tried to run /ascii but pyfiglet is missing.", "ERROR")
                        send_message(user_id, "❌ <b>Library Missing!</b>\nPlease run <code>pip install pyfiglet</code> on your server terminal first.")
                        continue
                        
                    log_terminal(f"Activating ASCII Display for text: {ascii_text}", "PROCESS")
                    if display_ascii_art(ascii_text):
                        send_message(user_id, f"✅ <b>SUCCESS!</b>\nText <b>{ascii_text}</b> is now flashing on your server terminal for 60 seconds. 😎")
                    else:
                        send_message(user_id, "❌ <b>FAILED!</b> Error displaying ASCII on terminal.")
                    continue

                if text.startswith("/adduser"):
                    if user_id != ADMIN_ID:
                        log_terminal(f"Non-admin ID {user_id} tried to use /adduser", "ERROR")
                        send_message(user_id, "❌ <b>Access Denied!</b> Only Admin can add new users.")
                        continue
                    parts = text.split()
                    if len(parts) == 1:
                        PENDING_STATES[user_id] = {'action': 'wait_adduser_id'}
                        send_message(user_id, "👇 <b>Please enter the Telegram ID to authorize:</b>\n\n<i>Type /cancel to abort.</i>")
                        continue
                    if len(parts) != 2:
                        send_message(user_id, "❌ <b>Invalid Format!</b>\nUsage: <code>/adduser [Telegram_ID]</code>")
                        continue
                    
                    new_id = parts[1]
                    if new_id in auth_users:
                        send_message(user_id, f"⚠️ User <b>{new_id}</b> is already authorized.")
                        continue
                        
                    with open(USERS_FILE, "a") as f:
                        f.write(new_id + "\n")
                    log_terminal(f"New user authorized: {new_id}", "SUCCESS")
                    send_message(user_id, f"✅ <b>SUCCESS!</b>\nUser <b>{new_id}</b> has been added to the whitelist.")
                    send_message(new_id, "🎉 <b>WELCOME!</b>\nYou have been authorized to use XianBeeStore Command Center. Type /help to see available commands.")
                    continue

                if text == "/users":
                    if user_id != ADMIN_ID:
                        send_message(user_id, "❌ <b>Access Denied!</b> Only Admin can view user list.")
                        continue
                    
                    log_terminal("Admin requested user list.", "INFO")
                    users_list = "\n".join([f"👤 <code>{uid}</code>" + (" (Admin)" if uid == ADMIN_ID else "") for uid in auth_users])
                    send_message(user_id, f"<blockquote>👥 <b>AUTHORIZED USERS</b></blockquote>\n{users_list}")
                    continue

                if text.startswith("/scan"):
                    parts = text.split()
                    if len(parts) == 1:
                        PENDING_STATES[user_id] = {'action': 'wait_scan_target'}
                        # Teks diperbarui agar lebih jelas dan informatif
                        send_message(user_id, "👇 <b>Please send the Target Repositories to SCAN:</b>\n<i>You can paste full GitHub links or owner/repo format.</i>\n<i>Separate using spaces, commas, or new lines.</i>\n\n<i>Type /cancel to abort.</i>")
                        continue

                    # Direct bulk scan mode (skip interactive prompt if provided in one line)
                    raw_text = text[5:].replace(',', ' ').replace('\n', ' ')
                    targets_raw = [w.strip() for w in raw_text.split() if w.strip()]
                    
                    target_repos = []
                    for w in targets_raw:
                        repo = w
                        if "github.com/" in repo:
                            repo = repo.split("github.com/")[-1]
                        repo = repo.split("?")[0].split("#")[0].strip("/")
                        if repo.endswith(".git"):
                            repo = repo[:-4]
                        
                        if "/" in repo:
                            target_repos.append(repo)
                        else:
                            # Auto expand username
                            user_repos = get_user_repos(repo)
                            if user_repos:
                                target_repos.extend(user_repos[:15]) # Limit to 15 to avoid spam
                                
                    target_repos = list(dict.fromkeys(target_repos)) # Remove duplicates
                    
                    if not target_repos:
                        send_message(user_id, "❌ <b>No valid repositories found!</b>\nPlease provide valid GitHub links or owner/repo format.")
                        continue
                        
                    log_terminal(f"Initiating bulk scan for {len(target_repos)} repos...", "PROCESS")
                    
                    init_msg = f"⏳ <b>SCANNING {len(target_repos)} REPOSITORIES...</b>\n<pre>Progress: [░░░░░░░░░░] 0%</pre>"
                    msg_id = send_message(user_id, init_msg)
                    bcast_msgs = broadcast_message(init_msg, exclude_id=user_id)
                    
                    report = (f"╔═════════════════════════╗\n"
                              f"   📊 <b>TARGET INTELLIGENCE</b>\n"
                              f"╚═════════════════════════╝\n\n")
                    
                    for i, repo in enumerate(target_repos):
                        info = get_repo_info(repo)
                        
                        if info:
                            size_mb = info.get('size_kb', 0) / 1024
                            report += (
                                f"❖ <b><a href='https://github.com/{repo}'>{repo}</a></b>\n"
                                f"   ├ ★ Stars : {info['stars']} | ⎇ Forks : {info['forks']}\n"
                                f"   └ 👁 Watch : {info['watchers']} | 📦 Size : {size_mb:.2f} MB\n\n"
                            )
                        else:
                            report += f"❖ <b><a href='https://github.com/{repo}'>{repo}</a></b>\n   └ ❌ Not Found / Private\n\n"
                            
                        bar_length = 10
                        filled = int((i + 1) / len(target_repos) * bar_length)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        percent = int((i + 1) / len(target_repos) * 100)
                        anim = ["⏳", "⌛"][i % 2]
                        
                        loading_text = f"{anim} <b>SCANNING {len(target_repos)} REPOSITORIES...</b>\n\n<pre>Progress: [{bar}] {percent}%\nScanning: {repo}...</pre>"
                        
                        if msg_id: edit_message(user_id, msg_id, loading_text)
                        if bcast_msgs: edit_broadcast_message(bcast_msgs, loading_text)
                        
                        time.sleep(1) # Prevent API limits
                        
                    report += f"💯 <i>Scan completed for {len(target_repos)} repositories.</i>"
                    
                    if msg_id: edit_message(user_id, msg_id, report)
                    else: send_message(user_id, report)
                    
                    if bcast_msgs: edit_broadcast_message(bcast_msgs, report)
                    else: broadcast_message(report, exclude_id=user_id)
                    
                    continue

                if text.startswith("/check"):
                    parts = text.split()
                    if len(parts) == 1:
                        PENDING_STATES[user_id] = {'action': 'wait_check_tokens'}
                        send_message(user_id, "👇 <b>Please send the tokens you want to check:</b>\n<i>Paste multiple tokens separated by spaces, commas, or new lines.</i>\n\n<i>Type /cancel to abort.</i>")
                        continue

                    raw_text = text.replace(',', ' ').replace('\n', ' ')
                    tokens = [w.strip() for w in raw_text.split() if w.startswith("ghp_") or w.startswith("github_pat_")]
                    
                    if not tokens:
                        send_message(user_id, "❌ <b>No valid tokens provided!</b>\nUsage: <code>/check token1, token2...</code>")
                        continue
                    
                    log_terminal(f"Initiating health check for {len(tokens)} tokens...", "PROCESS")
                    
                    init_msg = f"⏳ <b>SCANNING {len(tokens)} TOKENS...</b>\n📊 <b>Progress:</b> <code>[░░░░░░░░░░] 0%</code>"
                    msg_id = send_message(user_id, init_msg)
                    bcast_msgs = broadcast_message(init_msg, exclude_id=user_id)
                    
                    live = 0
                    dead = 0
                    live_list = []
                    dead_list = []
                    
                    for i, token in enumerate(tokens):
                        log_terminal(f"Pinging Node #{i+1}...", "PROCESS")
                        headers = {"Authorization": f"Bearer {token}"}
                        try:
                            res = requests.get("https://api.github.com/user", headers=headers, timeout=5)
                            if res.status_code == 200:
                                live += 1
                                masked_token = f"{token[:10]}...{token[-4:]}" if len(token) > 15 else token
                                live_list.append(f"Node #{i+1}: {masked_token}")
                                log_terminal(f"Node #{i+1}: ALIVE 🟢", "SUCCESS")
                            else:
                                dead += 1
                                masked_token = f"{token[:10]}...{token[-4:]}" if len(token) > 15 else token
                                dead_list.append(f"Node #{i+1}: {masked_token}")
                                log_terminal(f"Node #{i+1}: DEAD 🔴", "ERROR")
                        except Exception:
                            dead += 1
                            masked_token = f"{token[:10]}...{token[-4:]}" if len(token) > 15 else token
                            dead_list.append(f"Node #{i+1}: {masked_token}")
                            log_terminal(f"Node #{i+1}: ERROR 🔴", "ERROR")
                            
                            bar_length = 10
                            filled = int((i + 1) / len(tokens) * bar_length)
                            bar = "█" * filled + "░" * (bar_length - filled)
                            percent = int((i + 1) / len(tokens) * 100)
                            anim = ["⏳", "⌛"][i % 2]
                            
                            loading_text = f"{anim} <b>SCANNING {len(tokens)} TOKENS...</b>\n\n📊 <b>Progress:</b> <code>[{bar}] {percent}%</code>\n📡 <b>Checking Node #{i+1}...</b>"
                            
                            if msg_id: edit_message(user_id, msg_id, loading_text)
                            if bcast_msgs: edit_broadcast_message(bcast_msgs, loading_text)
                            
                        if i < len(tokens) - 1:
                            time.sleep(2)
                    
                    live_details = ""
                    if live_list:
                        live_details = "\n\n<b>🟢 ACTIVE / LIVE TOKENS:</b>\n" + "\n".join([f"<code>{t}</code>" for t in live_list])

                    dead_details = ""
                    if dead_list:
                        dead_details = "\n\n<b>💀 SUSPENDED / DEAD TOKENS:</b>\n" + "\n".join([f"<code>{t}</code>" for t in dead_list])

                    log_terminal(f"Check Complete | LIVE: {live} | DEAD: {dead}", "INFO")
                    report_msg = (
                        "<blockquote>🩺 <b>TOKEN HEALTH REPORT</b></blockquote>\n"
                        f"<b>Total Nodes :</b> <code>{len(tokens)}</code>\n"
                        f"🟢 <b>LIVE     :</b> <code>{live}</code>\n"
                        f"🔴 <b>DEAD     :</b> <code>{dead}</code>\n{live_details}{dead_details}\n"
                        "\n<i>*Dead tokens might be suspended or rate-limited.</i>"
                    )
                    
                    if msg_id: edit_message(user_id, msg_id, report_msg)
                    else: send_message(user_id, report_msg)
                    
                    if bcast_msgs: edit_broadcast_message(bcast_msgs, report_msg)
                    else: broadcast_message(report_msg, exclude_id=user_id)
                        
                    continue

                if text.startswith("/ghost"):
                    parts = text.split()
                    if len(parts) == 1:
                        PENDING_STATES[user_id] = {'action': 'wait_ghost_tokens'}
                        send_message(user_id, "👇 <b>Please send the tokens for GHOST MODE:</b>\n<i>Paste multiple tokens separated by spaces, commas, or new lines.</i>\n\n<i>Type /cancel to abort.</i>")
                        continue

                    raw_text = text.replace(',', ' ').replace('\n', ' ')
                    tokens = [w.strip() for w in raw_text.split() if w.startswith("ghp_") or w.startswith("github_pat_")]
                    
                    if not tokens:
                        send_message(user_id, "❌ <b>No valid tokens provided!</b>\nUsage: <code>/ghost token1, token2...</code>")
                        continue
                    
                    log_terminal(f"Activating GHOST MODE for {len(tokens)} workers...", "PROCESS")
                    
                    init_msg = f"⏳ <b>ACTIVATING GHOST MODE ON {len(tokens)} NODES...</b>\nPlease wait, randomizing profiles..."
                    send_message(user_id, init_msg)
                    broadcast_message(init_msg, exclude_id=user_id)
                    
                    for idx, token in enumerate(tokens):
                        log_terminal(f"Disguising Node #{idx+1}...", "PROCESS")
                        result = do_ghost_mode(token)
                        
                        clean_res = result.replace('┣', '').replace('┗', '')
                        log_terminal(f"Node #{idx+1} Disguised:\n{clean_res}", "SUCCESS")
                        
                        msg = (
                            f"<blockquote>✦ <b>NODE #{idx+1} GHOST REPORT</b> ✦\n"
                            f"❖ <b>Action:</b> GHOST PROFILE UPDATE</blockquote>\n"
                            f"<b>[ Profile Status ]</b>\n<code>{result}</code>"
                        )
                        send_message(user_id, msg)
                        broadcast_message(msg, exclude_id=user_id)
                        
                        if idx < len(tokens) - 1:
                            time.sleep(5)
                            
                    log_terminal("Ghost Mode sequence completed.", "INFO")
                    final_ghost = f"<blockquote>🎉 <b>GHOST MODE COMPLETE!</b>\n{len(tokens)} workers successfully disguised.</blockquote>"
                    send_message(user_id, final_ghost)
                    broadcast_message(final_ghost, exclude_id=user_id)
                    continue

                cmd_used = None
                for cmd in valid_commands:
                    if text.startswith(cmd):
                        cmd_used = cmd
                        break

                if cmd_used:
                    parts = text.split()
                    
                    if len(parts) == 1:
                        PENDING_STATES[user_id] = {'action': 'wait_attack_args', 'cmd_used': cmd_used}
                        send_message(user_id, f"👇 <b>{cmd_used.upper()} COMMAND INITIATED</b>\n\nPlease send the Target and Tokens.\n<b>Format:</b> <code>[target] [tokens...]</code>\n<i>Example: delmore77/repo ghp_xxx, ghp_yyy</i>\n\n<i>Type /cancel to abort.</i>")
                        continue

                    if len(parts) < 2:
                        error_msg = (
                            f"❌ <b>INCOMPLETE COMMAND!</b>\n"
                            f"Please provide the target repo and the tokens.\n\n"
                            f"<b>📖 Format:</b>\n"
                            f"<code>{cmd_used} [target_repo] [tokens...]</code> <i>(Auto uses all tokens)</i>\n"
                            f"<code>{cmd_used} [count] [target_repo] [tokens...]</code>\n\n"
                            f"<b>💡 Examples:</b>\n"
                            f"<code>{cmd_used} delmore77/repo ghp_xxx, ghp_yyy</code>\n"
                            f"<code>{cmd_used} 2 delmore77 ghp_xxx, ghp_yyy, ghp_zzz</code>"
                        )
                        send_message(user_id, error_msg)
                        continue
                        
                    count_str = "all"
                    if parts[1].isdigit() or parts[1].lower() == "all":
                        count_str = parts[1]
                        if len(parts) > 2:
                            target_input = parts[2]
                        else:
                            send_message(user_id, "❌ <b>Invalid Format!</b> Missing target repository/username.")
                            continue
                    elif len(parts) > 2 and (parts[2].isdigit() or parts[2].lower() == "all"):
                        target_input = parts[1]
                        count_str = parts[2]
                    else:
                        target_input = parts[1]

                    if "github.com/" in target_input:
                        target_input = target_input.split("github.com/")[-1]
                    target_input = target_input.split("?")[0].split("#")[0].strip("/")
                    if target_input.endswith(".git"):
                        target_input = target_input[:-4]

                    raw_text = text.replace(',', ' ').replace('\n', ' ')
                    tokens = [w.strip() for w in raw_text.split() if w.startswith("ghp_") or w.startswith("github_pat_")]
                        
                    if not tokens:
                        send_message(user_id, "❌ <b>No valid tokens found in your message!</b>\nPlease provide tokens starting with 'ghp_' or 'github_pat_'.")
                        continue

                    if count_str.lower() == "all":
                        count = len(tokens)
                    else:
                        count = int(count_str)

                    tokens_to_use = tokens[:count]
                    if len(tokens_to_use) < count:
                        log_terminal(f"User requested {count} workers, but only {len(tokens)} valid tokens provided.", "ERROR")
                        send_message(user_id, f"⚠️ <b>Warning:</b> You requested {count} workers, but only provided {len(tokens)} valid tokens. Proceeding with available tokens.")
                        
                    if "/" not in target_input:
                        log_terminal(f"Searching repos for user: {target_input}...", "PROCESS")
                        send_message(user_id, f"🔍 <b>SEARCHING REPOSITORIES FOR:</b> <code>{target_input}</code>...")
                        repos = get_user_repos(target_input)
                        
                        if not repos:
                            log_terminal(f"No repos found for {target_input}", "ERROR")
                            send_message(user_id, f"❌ <b>No public repositories found</b> for user <code>{target_input}</code>.")
                            continue
                            
                        log_terminal(f"Found {len(repos)} repos. Waiting for user choice to execute {cmd_used.upper()}.", "SUCCESS")
                        repo_list_msg = f"<blockquote>📁 <b>REPOSITORIES FOR {target_input}</b></blockquote>\n"
                        for i, r in enumerate(repos):
                            repo_list_msg += f"<b>{i+1}.</b> <code>{r}</code>\n"
                        
                        repo_list_msg += f"\n👉 <b>Reply with a number (1-{len(repos)})</b> to execute {cmd_used.upper()}.\n<i>Type /cancel to abort.</i>"
                        
                        PENDING_STATES[user_id] = {
                            'action': 'wait_repo_choice',
                            'cmd_used': cmd_used,
                            'count': count,
                            'tokens': tokens_to_use,
                            'repos': repos
                        }
                        
                        send_message(user_id, repo_list_msg)
                        continue

                    run_attack_sequence(user_id, cmd_used, target_input, tokens_to_use)

            time.sleep(2)
            
        except KeyboardInterrupt:
            if ASCII_TIMER is not None:
                ASCII_TIMER.cancel()
            print(f"\n{C_RED}🛑 Bot stopped by user (Ctrl+C). Shutting down...{C_RESET}")
            break
        except Exception as e:
            log_terminal(f"Polling Error: {e}", "ERROR")
            time.sleep(5)

if __name__ == "__main__":
    main()
