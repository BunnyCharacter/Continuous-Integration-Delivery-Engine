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

if os.name == 'nt':
    os.system('')

# ==========================================
# ⚙️ CONFIGURATION COMMAND CENTER
# ==========================================
TELEGRAM_BOT_TOKEN = "8275940423:AAEW8ZOn2ZoK64I2Bwcw9reJI7D0I1RmcrE"
ADMIN_ID = "6740043923"
USERS_FILE = "users.txt"
BROADCAST_CHATS = ["6740043923", "-1003626912079", "-1003798466502"]

# ==========================================
# ☁️ CLOUD TRIGGER CONFIGURATION (GITHUB ACTIONS)
# ==========================================
# Token PAT lu yang punya akses ke repo Actions (Wajib punya scope 'repo' atau 'workflow')
GITHUB_ADMIN_TOKEN = "ghp_TokenAdminLuDisini" 
# Nama Repo tempat file .yml lu disimpan (Pastikan Private!)
GITHUB_ACTION_REPO = "ithallodieh/XianBee-Cloud-Workers"

WORKFLOW_MAP = {
    "/stars": "auto_star.yml",
    "/forks": "auto_fork.yml",
    "/watch": "auto_watch.yml",
    "/follow": "auto_follow.yml"
}

# ==========================================
# 🧠 STATE MANAGEMENT & LOGGING
# ==========================================
PENDING_STATES = {}
ASCII_TIMER = None

C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_RESET = "\033[0m"

COLORS = [C_RED, C_YELLOW, C_GREEN, C_CYAN, C_BLUE, C_MAGENTA]

def log_terminal(message, level="INFO"):
    now = time.strftime("%H:%M:%S")
    prefix = f"{C_CYAN}[*]{C_RESET}" if level == "INFO" else f"{C_GREEN}[+]{C_RESET}" if level == "SUCCESS" else f"{C_RED}[-]{C_RESET}" if level == "ERROR" else f"{C_YELLOW}[~]{C_RESET}"
    text_color = C_CYAN if level == "INFO" else C_GREEN if level == "SUCCESS" else C_RED if level == "ERROR" else C_YELLOW

    term_cols, _ = shutil.get_terminal_size()
    box_width = 80 
    pad_left = max(0, (term_cols - box_width) // 2)
    indent = " " * pad_left

    lines = message.split('\n')
    print(f"{indent}{C_BLUE}[{now}]{C_RESET} {prefix} {text_color}{lines[0]}{C_RESET}")
    for line in lines[1:]:
        print(f"{indent}                  {text_color}{line}{C_RESET}")

def set_bot_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "help", "description": "Show command list"},
        {"command": "stars", "description": "Cloud: STARS on target"},
        {"command": "forks", "description": "Cloud: FORKS on target"},
        {"command": "watch", "description": "Cloud: WATCH on target"},
        {"command": "follow", "description": "Cloud: FOLLOW on target"},
        {"command": "allin", "description": "Cloud: ALL actions (Parallel)"},
        {"command": "clone", "description": "Stealth Clone repos (Local)"},
        {"command": "npm", "description": "Boost NPM package (Local)"},
        {"command": "scan", "description": "Get target intelligence"},
        {"command": "check", "description": "Check token health"},
        {"command": "ghost", "description": "Randomize GitHub profiles"},
        {"command": "unstar", "description": "Remove STARS from target"},
        {"command": "unwatch", "description": "Remove WATCH from target"},
        {"command": "unfollow", "description": "Unfollow target owner"},
        {"command": "cancel", "description": "Cancel a pending action"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=10)
    except: pass

def get_authorized_users():
    users = [ADMIN_ID]
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users.extend([line.strip() for line in f.readlines() if line.strip()])
    return list(set(users))

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        res = requests.post(url, json=payload, timeout=10).json()
        if res.get("ok"): return str(res.get("result", {}).get("message_id"))
    except: pass
    return None

def edit_message(chat_id, message_id, text):
    if not message_id: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def broadcast_message(text, exclude_id=None):
    sent_messages = {}
    for chat_id in BROADCAST_CHATS:
        if str(chat_id) == str(exclude_id): continue 
        msg_id = send_message(chat_id, text)
        if msg_id: sent_messages[chat_id] = msg_id
    return sent_messages

def edit_broadcast_message(sent_messages, text):
    for chat_id, msg_id in sent_messages.items():
        edit_message(chat_id, msg_id, text)

# ==========================================
# ☁️ CLOUD ACTIONS TRIGGER
# ==========================================
def trigger_github_workflow(workflow_file, target, quantity, duration, start_index):
    """Mengirim 4 Parameter Sinyal Webhook ke GitHub Actions"""
    url = f"https://api.github.com/repos/{GITHUB_ACTION_REPO}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_ADMIN_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main",
        "inputs": {
            "target": str(target),
            "quantity": str(quantity),
            "duration": str(duration),
            "start_index": str(start_index)
        }
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        if res.status_code == 204: return True, "✅ Cloud Action Dispatched Successfully"
        else: return False, f"❌ Failed to dispatch ({res.status_code}): {res.text}"
    except Exception as e:
        return False, f"❌ Error triggering cloud: {str(e)}"

# ==========================================
# 🔎 UTILITY FUNCTIONS
# ==========================================
def get_repo_info(repo):
    try:
        res = requests.get(f"https://api.github.com/repos/{repo}", timeout=10).json()
        if "message" in res and res["message"] == "Not Found": return None
        return {
            "stars": res.get("stargazers_count", 0),
            "forks": res.get("forks_count", 0),
            "watchers": res.get("subscribers_count", 0),
            "created": res.get("created_at", "Unknown")[:10],
            "size_kb": res.get("size", 0) 
        }
    except: return None

def get_user_repos(username):
    try:
        res = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100", timeout=10)
        if res.status_code == 200: return [repo['full_name'] for repo in res.json()]
    except: pass
    return []

def get_npm_latest_version(pkg_name):
    try:
        res = requests.get(f"https://registry.npmjs.org/{pkg_name}", timeout=10)
        if res.status_code == 200: return res.json().get("dist-tags", {}).get("latest")
    except: return None
    return None

def do_npm_boost(pkg_name, version, user_id, msg_id, bcast_msgs):
    download_url = f"https://registry.npmjs.org/{pkg_name}/-/{pkg_name}-{version}.tgz"
    success_count = 0
    session_target = random.randint(50, 100)
    for i in range(session_target):
        try:
            with requests.get(download_url, stream=True, timeout=5) as r:
                if r.status_code == 200: success_count += 1
        except: pass
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
        time.sleep(random.uniform(0.05, 0.2))
    return success_count

def print_main_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    term_cols, term_lines = shutil.get_terminal_size()
    print("\n" * max(1, (term_lines - 15) // 3))
    if pyfiglet:
        try:
            ascii_banner = pyfiglet.figlet_format("XIANBEE CLOUD", font="slant")
            for line in ascii_banner.split('\n'):
                if line.strip():
                    pad = max(0, (term_cols - len(line)) // 2)
                    print(" " * pad + f"{C_CYAN}{line}{C_RESET}")
        except: pass
    print("")
    subtitle = "🤖 CLOUD COMMAND CENTER IS ONLINE"
    sub_pad = max(0, (term_cols - len(subtitle)) // 2)
    print(" " * sub_pad + f"{C_MAGENTA}{subtitle}{C_RESET}\n")

def restore_terminal():
    global ASCII_TIMER
    print_main_banner()
    ASCII_TIMER = None

def display_ascii_art(text):
    global ASCII_TIMER
    if not pyfiglet: return False
    try:
        try: ascii_text = pyfiglet.figlet_format(text, font="graffiti")
        except: ascii_text = pyfiglet.figlet_format(text, font="standard")
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
        if ASCII_TIMER is not None: ASCII_TIMER.cancel()
        ASCII_TIMER = threading.Timer(60.0, restore_terminal)
        ASCII_TIMER.start()
        return True
    except Exception as e:
        log_terminal(f"Error displaying ASCII: {e}", "ERROR")
        return False

# ==========================================
# 👻 LOCAL ATTACK & UTILITY FUNCTIONS
# ==========================================
def do_ghost_mode(token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    companies = ["Freelance Developer", "Open Source", "Self-Employed", "Tech Startup", "Remote Worker"]
    locations = ["San Francisco, CA", "London, UK", "Berlin, Germany", "Tokyo, Japan", "Remote"]
    bios = ["Passionate developer.", "Building things.", "Open source contributor.", "Learning every day."]
    payload = {"company": random.choice(companies), "location": random.choice(locations), "bio": random.choice(bios)}
    try:
        res = requests.patch("https://api.github.com/user", headers=headers, json=payload, timeout=10)
        if res.status_code == 200: return f"┣ 👻 Disguise: SUCCESS\n┣ 🏢 {payload['company']}\n┣ 📍 {payload['location']}\n┗ 📝 {payload['bio']}"
        else: return f"┗ 🔴 Disguise: FAILED ({res.status_code})"
    except: return "┗ 🔴 Disguise: ERROR"

def do_action(token, repo, action_type):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    try: owner = repo.split('/')[0]
    except: owner = repo
    results = []

    # Hanya untuk UNSTAR, UNWATCH, UNFOLLOW (Reverse)
    if action_type == "/unstar":
        try:
            s_res = requests.delete(f"https://api.github.com/user/starred/{repo}", headers=headers, timeout=10)
            results.append("┣ ☆ Unstar : SUCCESS" if s_res.status_code == 204 else f"┣ 🔴 Unstar : FAILED ({s_res.status_code})")
        except: results.append("┣ 🔴 Unstar : ERROR")

    if action_type == "/unwatch":
        try:
            w_res = requests.delete(f"https://api.github.com/repos/{repo}/subscription", headers=headers, timeout=10)
            results.append("┣ 🙈 Unwatch: SUCCESS" if w_res.status_code == 204 else f"┣ 🔴 Unwatch: FAILED ({w_res.status_code})")
        except: results.append("┣ 🔴 Unwatch: ERROR")

    if action_type == "/unfollow":
        try:
            fl_res = requests.delete(f"https://api.github.com/user/following/{owner}", headers=headers, timeout=10)
            results.append("┣ 🚶 Unfollow: SUCCESS" if fl_res.status_code == 204 else f"┣ 🔴 Unfollow: FAILED ({fl_res.status_code})")
        except: results.append("┣ 🔴 Unfollow: ERROR")

    if results: results[-1] = "┗" + results[-1][1:]
    return "\n".join(results)

def run_local_revert_sequence(user_id, cmd_used, target_repo, tokens_to_use):
    """Executes UNSTAR/UNWATCH/UNFOLLOW Locally"""
    repo_url = f"https://github.com/{target_repo}"
    log_terminal(f"Initiating Local {cmd_used.upper()} sequence...", "INFO")
    msg_id = send_message(user_id, f"<blockquote>🚀 <b>REVERT COMMAND RECEIVED</b>\nMode: <b>{cmd_used.upper()}</b>\nTarget: <a href='{repo_url}'>{target_repo}</a>\nWorkers: <b>{len(tokens_to_use)} Nodes</b></blockquote>\n\n⏳ <i>Processing...</i>")
    
    for idx, token in enumerate(tokens_to_use):
        result = do_action(token, target_repo, cmd_used)
        clean_result = result.replace('┣', '').replace('┗', '')
        
        msg = (
            f"<blockquote>✦ <b>NODE #{idx+1} REPORT</b> ✦\n"
            f"❖ <b>Target:</b> <a href='{repo_url}'>{target_repo}</a>\n"
            f"❖ <b>Action:</b> {cmd_used.upper()}</blockquote>\n"
            f"<b>[ Status ]</b>\n<code>{result}</code>"
        )
        send_message(user_id, msg)
        if idx < len(tokens_to_use) - 1: time.sleep(5)
            
    final_alert = f"<blockquote>🎉 <b>REVERT ACCOMPLISHED!</b>\n{len(tokens_to_use)} workers successfully executed <b>{cmd_used.upper()}</b>.</blockquote>"
    send_message(user_id, final_alert)

def get_random_license(username, year):
    mit = f"""MIT License\n\nCopyright (c) {year} {username}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software..."""
    return mit, "MIT"

def do_stealth_clone(pat, target_repo, custom_repo_name=None, old_repo_name=None, status_cb=None):
    headers = {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github.v3+json"}
    if status_cb: status_cb("🔐 Validating Authentication Token...")
    user_res = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    if user_res.status_code != 200: return "❌ Failed to authenticate PAT."
    user_data = user_res.json()
    username, user_id, user_email = user_data.get("login"), user_data.get("id"), user_data.get("email")
    if not user_email: user_email = f"{user_id}+{username}@users.noreply.github.com"

    if status_cb: status_cb("📊 Analyzing repository size...")
    try:
        repo_info = requests.get(f"https://api.github.com/repos/{target_repo}", headers=headers, timeout=10).json()
        if (repo_info.get("size", 0) / 1024) > 500: return "❌ SKIPPED: Repo is too large (>500 MB)."
    except: pass

    repo_name = target_repo.split("/")[-1]
    if old_repo_name and custom_repo_name:
        repo_name = custom_repo_name
        requests.patch(f"https://api.github.com/repos/{username}/{old_repo_name}", headers=headers, json={"name": custom_repo_name}, timeout=10)
    elif old_repo_name and not custom_repo_name:
        repo_name = old_repo_name
    else:
        if custom_repo_name: repo_name = custom_repo_name
        requests.post("https://api.github.com/user/repos", headers=headers, json={"name": repo_name, "private": False}, timeout=10)

    work_dir = tempfile.mkdtemp()
    repo_dir = os.path.join(work_dir, repo_name)
    try:
        if status_cb: status_cb("⬇️ Downloading source code...")
        subprocess.run(["git", "clone", f"https://github.com/{target_repo}.git", repo_name], cwd=work_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        git_folder = os.path.join(repo_dir, ".git")
        if os.path.exists(git_folder):
            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWRITE); func(path)
            shutil.rmtree(git_folder, onerror=remove_readonly)
            
        github_wf = os.path.join(repo_dir, ".github", "workflows")
        if os.path.exists(github_wf): shutil.rmtree(github_wf, ignore_errors=True)

        original_target_name = target_repo.split("/")[-1]
        for filename in os.listdir(repo_dir):
            if filename.lower() == "readme.md":
                try:
                    with open(os.path.join(repo_dir, filename), "r", encoding="utf-8", errors="ignore") as f: content = f.read()
                    with open(os.path.join(repo_dir, filename), "w", encoding="utf-8", errors="ignore") as f: f.write(content.replace(original_target_name, repo_name))
                except: pass

        subprocess.run(["git", "init"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", username], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", user_email], cwd=repo_dir, check=True)
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial commit for project"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "remote", "add", "origin", f"https://{username}:{pat}@github.com/{username}/{repo_name}.git"], cwd=repo_dir, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=repo_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        requests.patch(f"https://api.github.com/repos/{username}/{repo_name}", headers=headers, json={"default_branch": "main"}, timeout=5)
        return "✅ SUCCESS [CLONED]"
    except Exception as e:
        return "❌ ERROR: Failed to clone."
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

# ==========================================
# 📡 TELEGRAM POLLING LISTENER
# ==========================================
def main():
    print_main_banner()
    log_terminal("Registering Bot Commands...", "PROCESS")
    set_bot_commands()

    last_update_id = 0
    valid_cloud_commands = ["/stars", "/forks", "/watch", "/follow", "/allin"]
    valid_local_revert = ["/unstar", "/unwatch", "/unfollow"]

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
                if user_id not in auth_users: continue

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
                        
                    action = state.get('action')

                    # ------------------------------------------
                    # ☁️ CLOUD ACTIONS INTERACTIVE FLOW (WIZARD MODE)
                    # ------------------------------------------
                    if action == 'wait_cloud_target':
                        target = text.strip()
                        if "github.com/" in target: target = target.split("github.com/")[-1]
                        target = target.split("?")[0].split("#")[0].strip("/")
                        if target.endswith(".git"): target = target[:-4]
                        
                        state['target'] = target
                        state['action'] = 'wait_cloud_qty'
                        send_message(user_id, f"🔢 <b>JUMLAH EKSEKUSI</b>\n\nBerapa banyak <b>{state['service'].upper()}</b> yang ingin ditembakkan ke <code>{target}</code>?\n<i>Contoh: 20</i>\n\n<i>Ketik /cancel untuk batal.</i>")
                        continue

                    elif action == 'wait_cloud_qty':
                        if not text.isdigit():
                            send_message(user_id, "❌ <b>Harus Angka!</b> Masukkan jumlah eksekusi (contoh: 20):")
                            continue
                        state['quantity'] = int(text)
                        state['action'] = 'wait_cloud_duration'
                        send_message(user_id, f"⏳ <b>DURASI PENGERJAAN</b>\n\nIngin diselesaikan dalam berapa <b>JAM</b>? (Makin lama makin aman).\n<i>Contoh: Ketik <b>1</b> untuk 1 jam, <b>5.5</b> untuk 5.5 jam.</i>")
                        continue

                    elif action == 'wait_cloud_duration':
                        try: duration = float(text.replace(',', '.'))
                        except:
                            send_message(user_id, "❌ <b>Harus Angka!</b> Masukkan durasi jam (contoh: 2.5):")
                            continue
                        if duration <= 0:
                            send_message(user_id, "❌ Durasi harus lebih dari 0.")
                            continue
                        state['duration'] = duration
                        state['action'] = 'wait_cloud_index'
                        send_message(user_id, f"🔑 <b>PILIH TOKEN DI SECRETS</b>\n\nMau mulai pakai token dari urutan ke berapa di Secrets GitHub lu?\n<i>Contoh: Ketik <b>1</b> untuk mulai dari token pertama.</i>")
                        continue

                    elif action == 'wait_cloud_index':
                        if not text.isdigit() or int(text) < 1:
                            send_message(user_id, "❌ <b>Harus Angka > 0!</b> Masukkan nomor urutan (contoh: 1):")
                            continue
                        start_index = int(text)
                        cmd_used = state['service']
                        target = state['target']
                        quantity = state['quantity']
                        duration = state['duration']
                        
                        del PENDING_STATES[user_id]
                        send_message(user_id, f"📡 <i>Transmitting <b>{cmd_used.upper()}</b> signal to GitHub Actions...</i>")
                        
                        if cmd_used == "/allin":
                            success_reports = []
                            for action_name, yml_name in WORKFLOW_MAP.items():
                                success, msg = trigger_github_workflow(yml_name, target, quantity, duration, start_index)
                                status_icon = "🟢" if success else "🔴"
                                success_reports.append(f"{status_icon} <b>{action_name[1:].upper()}</b>: {msg}")
                                time.sleep(1) 
                            final_report = "\n".join(success_reports)
                            result_msg = (
                                f"╔═════════════════════════╗\n"
                                f"   🚀 <b>PARALLEL CLOUD DEPLOYED</b>\n"
                                f"╚═════════════════════════╝\n\n"
                                f"🎯 <b>Target :</b> <a href='https://github.com/{target}'>{target}</a>\n"
                                f"📦 <b>Jumlah :</b> {quantity} Actions/Service\n"
                                f"⏳ <b>Durasi :</b> {duration} Jam\n"
                                f"🔑 <b>Token  :</b> Urutan #{start_index}\n\n"
                                f"<b>[ Dispatch Status ]</b>\n{final_report}\n\n"
                                f"<i>Mesin Cloud berjalan paralel di GitHub Actions!</i>"
                            )
                            send_message(user_id, result_msg)
                            broadcast_message(result_msg, exclude_id=user_id)
                        else:
                            yaml_file = WORKFLOW_MAP.get(cmd_used, "auto_star.yml")
                            success, msg = trigger_github_workflow(yaml_file, target, quantity, duration, start_index)
                            if success:
                                log_terminal(f"Cloud Deployment: {cmd_used} for {target}", "SUCCESS")
                                result_msg = (
                                    f"╔═════════════════════════╗\n"
                                    f"   🚀 <b>CLOUD DEPLOYED</b>\n"
                                    f"╚═════════════════════════╝\n\n"
                                    f"🛠️ <b>Action :</b> {cmd_used.upper()}\n"
                                    f"🎯 <b>Target :</b> <a href='https://github.com/{target}'>{target}</a>\n"
                                    f"📦 <b>Jumlah :</b> {quantity} Actions\n"
                                    f"⏳ <b>Durasi :</b> {duration} Jam\n"
                                    f"🔑 <b>Token  :</b> Mulai urutan #{start_index}\n\n"
                                    f"✅ Sinyal dieksekusi! GitHub Actions sedang memproses secara Stealth."
                                )
                                send_message(user_id, result_msg)
                                broadcast_message(result_msg, exclude_id=user_id)
                            else:
                                log_terminal(f"Cloud Deployment Failed: {msg}", "ERROR")
                                send_message(user_id, f"❌ <b>Cloud Dispatch Failed!</b>\nError: {msg}")
                        continue

                    # ------------------------------------------
                    # 🖥️ LOCAL ACTIONS (NPM, CLONE, SCAN, CHECK)
                    # ------------------------------------------
                    if action == 'wait_npm_package':
                        pkg_name = text.strip()
                        del PENDING_STATES[user_id]
                        send_message(user_id, f"🔍 <i>Checking registry for '{pkg_name}'...</i>")
                        version = get_npm_latest_version(pkg_name)
                        if not version:
                            send_message(user_id, f"❌ <b>FAILED!</b>\nPackage <code>{pkg_name}</code> not found.")
                            continue
                        init_msg = f"╔═════════════════════════╗\n   🚀 <b>NPM BOOST PIPELINE</b>\n╚═════════════════════════╝\n\n<i>Initializing download simulation for {pkg_name} v{version}...</i>"
                        msg_id = send_message(user_id, init_msg)
                        bcast_msgs = broadcast_message(init_msg, exclude_id=user_id)
                        success_hits = do_npm_boost(pkg_name, version, user_id, msg_id, bcast_msgs)
                        final_msg = f"╔═════════════════════════╗\n   ✅ <b>NPM BOOST COMPLETED</b>\n╚═════════════════════════╝\n\n❖ <b>Package:</b> <code>{pkg_name}</code>\n❖ <b>Version:</b> <code>v{version}</code>\n└ 🚀 <b>{success_hits} Downloads Simulated!</b>"
                        edit_message(user_id, msg_id, final_msg)
                        edit_broadcast_message(bcast_msgs, final_msg)
                        continue

                    elif action == 'wait_clone_mode':
                        state['clone_mode'] = text.strip()
                        if text.strip() == '1':
                            state['action'] = 'wait_clone_input'
                            send_message(user_id, f"👇 <b>MODE 1: STANDARD CLONE</b>\nFormat: <code>[PAT] [repo1] [repo2] ...</code>")
                        elif text.strip() == '2':
                            state['action'] = 'wait_clone_input'
                            send_message(user_id, f"👇 <b>MODE 2: CUSTOM NAME</b>\nFormat: <code>[PAT] [repo] [new_name] ...</code>")
                        elif text.strip() == '3':
                            state['action'] = 'wait_clone_pat_m3'
                            send_message(user_id, "✅ <b>Mode 3: Overwrite Old Repo</b>\n👇 Please send your <b>GitHub PAT</b>:")
                        continue

                    elif action == 'wait_clone_input':
                        mode = state.get('clone_mode', '1')
                        del PENDING_STATES[user_id]
                        words = [w.strip() for w in text.replace(',', ' ').replace('\n', ' ').split() if w.strip()]
                        pat_token, targets_raw = None, []
                        for w in words:
                            if w.startswith("ghp_") or w.startswith("github_pat_"):
                                if not pat_token: pat_token = w
                            else: targets_raw.append(w)

                        target_repos = []
                        if mode == '1':
                            target_repos = [(r.split("github.com/")[-1].replace(".git", "").strip("/"), None, None) for r in targets_raw]
                        elif mode == '2':
                            for i in range(0, len(targets_raw), 2):
                                r = targets_raw[i].split("github.com/")[-1].replace(".git", "").strip("/")
                                target_repos.append((r, None, targets_raw[i+1]))

                        for repo, old, cust in target_repos:
                            do_stealth_clone(pat_token, repo, cust, old)
                        send_message(user_id, "✅ <b>CLONE PIPELINE COMPLETED!</b>")
                        continue

                    # ------------------------------------------
                    # 🖥️ LOCAL REVERT WIZARD (/unstar, /unwatch)
                    # ------------------------------------------
                    elif action == 'wait_revert_args':
                        cmd = state.get('cmd_used')
                        text = f"{cmd} {text}"
                        del PENDING_STATES[user_id]
                        # Langsung lari ke logic di bawah karena PENDING_STATES di-delete
                        pass

                # ==========================
                # TRIGGER MENU & ROUTING
                # ==========================
                # 1. Menangkap Trigger Cloud Command
                cmd_used = None
                for cmd in valid_cloud_commands:
                    if text.startswith(cmd):
                        cmd_used = cmd
                        break
                if cmd_used:
                    parts = text.split()
                    if len(parts) > 1:
                        target = parts[1]
                        if "github.com/" in target: target = target.split("github.com/")[-1]
                        target = target.split("?")[0].split("#")[0].strip("/")
                        PENDING_STATES[user_id] = {'action': 'wait_cloud_qty', 'service': cmd_used, 'target': target}
                        send_message(user_id, f"🔢 <b>JUMLAH EKSEKUSI</b>\n\nBerapa banyak <b>{cmd_used.upper()}</b> yang ingin ditembakkan ke <code>{target}</code>?\n<i>Contoh: 20</i>\n\n<i>Ketik /cancel untuk batal.</i>")
                    else:
                        PENDING_STATES[user_id] = {'action': 'wait_cloud_target', 'service': cmd_used}
                        send_message(user_id, f"👇 <b>{cmd_used.upper()} CLOUD WIZARD INITIATED</b>\n\nMasukkan <b>Target Repositori / Username</b>:\n<i>Contoh: abieharyatmo/projek-keren</i>\n\n<i>Ketik /cancel untuk membatalkan.</i>")
                    continue

                # 2. Menangkap Trigger Local Revert Command
                cmd_used = None
                for cmd in valid_local_revert:
                    if text.startswith(cmd):
                        cmd_used = cmd
                        break
                if cmd_used:
                    parts = text.split()
                    if len(parts) == 1:
                        PENDING_STATES[user_id] = {'action': 'wait_revert_args', 'cmd_used': cmd_used}
                        send_message(user_id, f"👇 <b>{cmd_used.upper()} LOCAL COMMAND INITIATED</b>\n\nPlease send the Target and Tokens.\n<b>Format:</b> <code>[target] [tokens...]</code>\n\n<i>Type /cancel to abort.</i>")
                        continue
                    
                    target_input = parts[1].split("github.com/")[-1].strip("/")
                    tokens = [w.strip() for w in text.replace(',', ' ').replace('\n', ' ').split() if w.startswith("ghp_") or w.startswith("github_pat_")]
                    if tokens:
                        run_local_revert_sequence(user_id, cmd_used, target_input, tokens)
                    else:
                        send_message(user_id, "❌ <b>No valid tokens provided.</b>")
                    continue

                # 3. Utilities (NPM, Scan, Check, Clone)
                if text == "/start" or text == "/help":
                    help_msg = (
                        "<blockquote>🤖 <b>XIANBEE COMMAND CENTER</b></blockquote>\n\n"
                        "<b>🚀 DYNAMIC CLOUD ACTIONS (Aman & Background):</b>\n"
                        "👉 <code>/stars</code> <i>(Cloud: Stars Injection)</i>\n"
                        "👉 <code>/forks</code> <i>(Cloud: Forks Injection)</i>\n"
                        "👉 <code>/watch</code> <i>(Cloud: Watch Injection)</i>\n"
                        "👉 <code>/follow</code> <i>(Cloud: Follow Injection)</i>\n"
                        "👉 <code>/allin</code> <i>(Cloud: Parallel Combo)</i>\n\n"
                        "<b>🛠️ LOCAL UTILITIES:</b>\n"
                        "👉 <code>/scan [target]</code> <i>(Repo Intelligence)</i>\n"
                        "👉 <code>/check [tokens...]</code> <i>(Check token health)</i>\n"
                        "👉 <code>/clone</code> <i>(Stealth Clone Repos)</i>\n"
                        "👉 <code>/npm</code> <i>(Boost NPM Package)</i>\n"
                        "👉 <code>/ghost [tokens...]</code> <i>(Randomize profiles)</i>\n"
                        "👉 <code>/unstar [target] [tokens...]</code> <i>(Local Revert)</i>\n"
                    )
                    send_message(user_id, help_msg)
                    continue

                if text.strip() == "/npm":
                    PENDING_STATES[user_id] = {'action': 'wait_npm_package'}
                    send_message(user_id, "👇 <b>NPM BOOSTER INITIATED</b>\nEnter the NPM Package Name:")
                    continue

                if text.strip() == "/clone":
                    PENDING_STATES[user_id] = {'action': 'wait_clone_mode'}
                    menu_msg = "👇 <b>SELECT STEALTH CLONE MODE</b>\n<b>1.</b> Standard Clone\n<b>2.</b> Custom Name\n<b>3.</b> Overwrite Old Repo\n\n👉 <b>Reply with number 1, 2, or 3.</b>"
                    send_message(user_id, menu_msg)
                    continue

                if text.startswith("/check"):
                    tokens = [w.strip() for w in text.replace(',', ' ').split() if w.startswith("ghp_")]
                    if not tokens:
                        send_message(user_id, "❌ <b>No tokens provided!</b> Usage: <code>/check token1...</code>")
                        continue
                    init_msg = f"⏳ <b>SCANNING {len(tokens)} TOKENS...</b>"
                    msg_id = send_message(user_id, init_msg)
                    live, dead, live_list, dead_list = 0, 0, [], []
                    for i, t in enumerate(tokens):
                        try:
                            if requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {t}"}, timeout=5).status_code == 200:
                                live += 1; live_list.append(f"{t[:10]}...{t[-4:]}")
                            else:
                                dead += 1; dead_list.append(f"{t[:10]}...{t[-4:]}")
                        except: dead += 1; dead_list.append(f"{t[:10]}...{t[-4:]}")
                    report = f"<blockquote>🩺 <b>TOKEN HEALTH</b></blockquote>\n🟢 LIVE: {live}\n🔴 DEAD: {dead}"
                    edit_message(user_id, msg_id, report)
                    continue

                if text.startswith("/scan"):
                    targets = [w.strip() for w in text[5:].replace(',', ' ').split() if w.strip()]
                    if not targets:
                        PENDING_STATES[user_id] = {'action': 'wait_scan_target'}
                        send_message(user_id, "👇 <b>Please send Target Repositories to SCAN:</b>")
                        continue
                    for r in targets:
                        info = get_repo_info(r.split("github.com/")[-1].strip("/"))
                        if info: send_message(user_id, f"✅ <b>{r}</b>\nStars: {info['stars']} | Forks: {info['forks']} | Watch: {info['watchers']}")
                        else: send_message(user_id, f"❌ <b>{r}</b> Not Found")
                    continue

                if text.startswith("/ghost"):
                    tokens = [w.strip() for w in text.replace(',', ' ').split() if w.startswith("ghp_")]
                    for t in tokens:
                        res = do_ghost_mode(t)
                        send_message(user_id, f"👻 <b>GHOST REPORT</b>\n{res}")
                        time.sleep(2)
                    continue

            time.sleep(2)
        except KeyboardInterrupt:
            if ASCII_TIMER is not None: ASCII_TIMER.cancel()
            print(f"\n{C_RED}🛑 Bot stopped. Shutting down...{C_RESET}")
            break
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    main()
