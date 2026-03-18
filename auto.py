import os #WRKFLW
import sys
import requests
import time
import threading
import shutil

try:
    import pyfiglet
except ImportError:
    pyfiglet = None

if os.name == 'nt':
    os.system('')

# ==========================================
# ⚙️ CONFIGURATION COMMAND CENTER
# ==========================================
TELEGRAM_BOT_TOKEN = "8275940423:AAEW8ZOn2ZoK64I2Bwcw9reJI7D0I1RmcrE" # Ganti kalau tokennya beda
ADMIN_ID = "6740043923"
USERS_FILE = "users.txt"
BROADCAST_CHATS = ["6740043923", "-1003626912079", "-1003798466502"]

# ==========================================
# ☁️ MULTI-CLOUD ENGINES CONFIGURATION
# ==========================================
CLOUD_ENGINES = {
    "1": {"name": "Engine 1 (Main)", "token": "ghp_TokenAdminUtamaLuDisini", "repo": "ithallodieh/XianBee-Cloud-Workers"},
    "2": {"name": "Engine 2", "token": "ghp_TokenAdminMesinDuaDisini", "repo": "username2/Repo-Mesin-2"},
    "3": {"name": "Engine 3", "token": "ghp_TokenAdminMesinTigaDisini", "repo": "username3/Repo-Mesin-3"},
    "4": {"name": "Engine 4", "token": "ghp_TokenAdminMesinEmpatDisini", "repo": "username4/Repo-Mesin-4"},
    "5": {"name": "Engine 5", "token": "ghp_TokenAdminMesinLimaDisini", "repo": "username5/Repo-Mesin-5"},
    "6": {"name": "Engine 6", "token": "ghp_TokenAdminMesinEnamDisini", "repo": "username6/Repo-Mesin-6"},
    "7": {"name": "Engine 7", "token": "ghp_TokenAdminMesinTujuhDisini", "repo": "username7/Repo-Mesin-7"},
    "8": {"name": "Engine 8", "token": "ghp_TokenAdminMesinDelapanDisini", "repo": "username8/Repo-Mesin-8"},
    "9": {"name": "Engine 9", "token": "ghp_TokenAdminMesinSembilanDisini", "repo": "username9/Repo-Mesin-9"},
    "10": {"name": "Engine 10", "token": "ghp_TokenAdminMesinSepuluhDisini", "repo": "username10/Repo-Mesin-10"}
}

WORKFLOW_MAP = {
    "/stars": "auto_star.yml",
    "/forks": "auto_fork.yml",
    "/watch": "auto_watch.yml",
    "/follow": "auto_follow.yml"
}

# ==========================================
# 🌍 BILINGUAL DICTIONARY (MULTI-LANGUAGE)
# ==========================================
USER_LANG = {} # Menyimpan preferensi bahasa per user_id

LANG_DICT = {
    "id": {
        "help": "<blockquote>🤖 <b>XIANBEE COMMAND CENTER</b></blockquote>\n\n<b>🚀 DYNAMIC CLOUD ACTIONS:</b>\n👉 <code>/stars</code> <i>(Cloud: Stars Injection)</i>\n👉 <code>/forks</code> <i>(Cloud: Forks Injection)</i>\n👉 <code>/watch</code> <i>(Cloud: Watch Injection)</i>\n👉 <code>/follow</code> <i>(Cloud: Follow Injection)</i>\n👉 <code>/allin</code> <i>(Cloud: Parallel Combo)</i>\n\n👉 <code>/cancel</code> <i>(Batalkan perintah saat ini)</i>\n",
        "err_invalid_engine": "❌ <b>Pilihan tidak valid!</b> Masukkan nomor mesin yang ada di daftar:",
        "prompt_engine": "👇 <b>{cmd} CLOUD WIZARD INITIATED</b>\n\nPilih <b>Mesin Cloud</b> yang mau dipakai untuk eksekusi ini:\n\n{engine_list}\n\n<i>Balas dengan angka. Ketik /cancel untuk membatalkan.</i>",
        "prompt_target": "✅ Mesin <b>{engine}</b> dipilih.\n\n👇 Masukkan <b>Target Repositori / Username</b>:\n<i>Contoh: abieharyatmo/projek-keren</i>\n\n<i>Ketik /cancel untuk membatalkan.</i>",
        "prompt_qty": "🔢 <b>JUMLAH EKSEKUSI</b>\n\nBerapa banyak <b>{service}</b> yang ingin ditembakkan ke <code>{target}</code>?\n<i>Contoh: 20</i>\n\n<i>Ketik /cancel untuk batal.</i>",
        "err_number": "❌ <b>Harus Angka!</b> Masukkan angka yang valid:",
        "prompt_duration": "⏳ <b>DURASI PENGERJAAN</b>\n\nIngin diselesaikan dalam berapa <b>JAM</b>? (Makin lama makin aman).\n<i>Contoh: Ketik <b>1</b> untuk 1 jam, <b>5.5</b> untuk 5.5 jam.</i>",
        "err_duration": "❌ Durasi harus lebih dari 0.",
        "prompt_index": "🔑 <b>PILIH TOKEN DI SECRETS</b>\n\nMau mulai pakai token dari urutan ke berapa di Secrets GitHub lu?\n<i>Contoh: Ketik <b>1</b> untuk mulai dari token pertama.</i>",
        "transmitting": "📡 <i>Transmitting <b>{cmd}</b> signal to <b>{engine}</b>...</i>",
        "parallel_deployed": "╔═════════════════════════╗\n   🚀 <b>PARALLEL CLOUD DEPLOYED</b>\n╚═════════════════════════╝\n\n🖥️ <b>Engine :</b> {engine}\n🎯 <b>Target :</b> <a href='https://github.com/{target}'>{target}</a>\n📦 <b>Jumlah :</b> {qty} Actions/Service\n⏳ <b>Durasi :</b> {dur} Jam\n🔑 <b>Token  :</b> Urutan #{index}\n\n<b>[ Dispatch Status ]</b>\n{status}\n\n<i>Mesin Cloud berjalan paralel di GitHub Actions!</i>",
        "cloud_deployed": "╔═════════════════════════╗\n   🚀 <b>CLOUD DEPLOYED</b>\n╚═════════════════════════╝\n\n🖥️ <b>Engine :</b> {engine}\n🛠️ <b>Action :</b> {cmd}\n🎯 <b>Target :</b> <a href='https://github.com/{target}'>{target}</a>\n📦 <b>Jumlah :</b> {qty} Actions\n⏳ <b>Durasi :</b> {dur} Jam\n🔑 <b>Token  :</b> Mulai urutan #{index}\n\n✅ Sinyal dieksekusi! GitHub Actions sedang memproses secara Stealth.",
        "cloud_failed": "❌ <b>Cloud Dispatch Failed!</b>\nError: {msg}",
        "cancelled": "🚫 <b>Aksi Dibatalkan.</b>"
    },
    "en": {
        "help": "<blockquote>🤖 <b>XIANBEE COMMAND CENTER</b></blockquote>\n\n<b>🚀 DYNAMIC CLOUD ACTIONS:</b>\n👉 <code>/stars</code> <i>(Cloud: Stars Injection)</i>\n👉 <code>/forks</code> <i>(Cloud: Forks Injection)</i>\n👉 <code>/watch</code> <i>(Cloud: Watch Injection)</i>\n👉 <code>/follow</code> <i>(Cloud: Follow Injection)</i>\n👉 <code>/allin</code> <i>(Cloud: Parallel Combo)</i>\n\n👉 <code>/cancel</code> <i>(Cancel current command)</i>\n",
        "err_invalid_engine": "❌ <b>Invalid choice!</b> Enter a number from the list:",
        "prompt_engine": "👇 <b>{cmd} CLOUD WIZARD INITIATED</b>\n\nSelect the <b>Cloud Engine</b> to use for this execution:\n\n{engine_list}\n\n<i>Reply with a number. Type /cancel to abort.</i>",
        "prompt_target": "✅ Engine <b>{engine}</b> selected.\n\n👇 Enter <b>Target Repository / Username</b>:\n<i>Example: abieharyatmo/awesome-project</i>\n\n<i>Type /cancel to abort.</i>",
        "prompt_qty": "🔢 <b>EXECUTION QUANTITY</b>\n\nHow many <b>{service}</b> injections for <code>{target}</code>?\n<i>Example: 20</i>\n\n<i>Type /cancel to abort.</i>",
        "err_number": "❌ <b>Must be a Number!</b> Enter a valid number:",
        "prompt_duration": "⏳ <b>EXECUTION DURATION</b>\n\nHow many <b>HOURS</b> should this take? (Longer = Safer).\n<i>Example: Type <b>1</b> for 1 hr, <b>5.5</b> for 5.5 hrs.</i>",
        "err_duration": "❌ Duration must be greater than 0.",
        "prompt_index": "🔑 <b>SELECT TOKEN INDEX</b>\n\nWhich token index in GitHub Secrets should we start from?\n<i>Example: Type <b>1</b> for the first token.</i>",
        "transmitting": "📡 <i>Transmitting <b>{cmd}</b> signal to <b>{engine}</b>...</i>",
        "parallel_deployed": "╔═════════════════════════╗\n   🚀 <b>PARALLEL CLOUD DEPLOYED</b>\n╚═════════════════════════╝\n\n🖥️ <b>Engine :</b> {engine}\n🎯 <b>Target :</b> <a href='https://github.com/{target}'>{target}</a>\n📦 <b>Quantity :</b> {qty} Actions/Service\n⏳ <b>Duration :</b> {dur} Hours\n🔑 <b>Token  :</b> Index #{index}\n\n<b>[ Dispatch Status ]</b>\n{status}\n\n<i>Cloud engines are now running in parallel on GitHub Actions!</i>",
        "cloud_deployed": "╔═════════════════════════╗\n   🚀 <b>CLOUD DEPLOYED</b>\n╚═════════════════════════╝\n\n🖥️ <b>Engine :</b> {engine}\n🛠️ <b>Action :</b> {cmd}\n🎯 <b>Target :</b> <a href='https://github.com/{target}'>{target}</a>\n📦 <b>Quantity :</b> {qty} Actions\n⏳ <b>Duration :</b> {dur} Hours\n🔑 <b>Token  :</b> Starting index #{index}\n\n✅ Signal Dispatched! GitHub Actions is processing stealthily.",
        "cloud_failed": "❌ <b>Cloud Dispatch Failed!</b>\nError: {msg}",
        "cancelled": "🚫 <b>Action Cancelled.</b>"
    }
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
    """Mengatur menu garis miring (/) di Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "Start / Change Language"},
        {"command": "stars", "description": "Cloud: STARS on target"},
        {"command": "forks", "description": "Cloud: FORKS on target"},
        {"command": "watch", "description": "Cloud: WATCH on target"},
        {"command": "follow", "description": "Cloud: FOLLOW on target"},
        {"command": "allin", "description": "Cloud: ALL actions (Parallel)"},
        {"command": "cancel", "description": "Cancel current action"},
        {"command": "help", "description": "Show guide menu"}
    ]
    try: requests.post(url, json={"commands": commands}, timeout=10)
    except: pass

def get_authorized_users():
    users = [ADMIN_ID]
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users.extend([line.strip() for line in f.readlines() if line.strip()])
    return list(set(users))

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup: payload["reply_markup"] = reply_markup
    try:
        res = requests.post(url, json=payload, timeout=10).json()
        if res.get("ok"): return str(res.get("result", {}).get("message_id"))
    except: pass
    return None

def edit_message(chat_id, message_id, text, reply_markup=None):
    if not message_id: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup: payload["reply_markup"] = reply_markup
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def broadcast_message(text, exclude_id=None):
    sent_messages = {}
    for chat_id in BROADCAST_CHATS:
        if str(chat_id) == str(exclude_id): continue 
        msg_id = send_message(chat_id, text)
        if msg_id: sent_messages[chat_id] = msg_id
    return sent_messages

# ==========================================
# ☁️ CLOUD ACTIONS TRIGGER
# ==========================================
def trigger_github_workflow(engine_id, workflow_file, target, quantity, duration, start_index):
    engine = CLOUD_ENGINES.get(engine_id)
    if not engine:
        return False, "❌ Error: Mesin Cloud tidak ditemukan di konfigurasi."

    url = f"https://api.github.com/repos/{engine['repo']}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {engine['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main", # Ganti "master" jika repo lu pakai branch master
        "inputs": {
            "target": str(target),
            "quantity": str(quantity),
            "duration": str(duration),
            "start_index": str(start_index)
        }
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        if res.status_code == 204: return True, f"✅ Signal success ({engine['name']})"
        else: return False, f"❌ Failed dispatch ({res.status_code}): {res.text}"
    except Exception as e:
        return False, f"❌ Error triggering {engine['name']}: {str(e)}"

# ==========================================
# 🖥️ TERMINAL DISPLAY
# ==========================================
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

# ==========================================
# 📡 TELEGRAM POLLING LISTENER
# ==========================================
def main():
    print_main_banner()
    log_terminal("Registering Bot Commands...", "PROCESS")
    set_bot_commands() 

    last_update_id = 0
    valid_cloud_commands = ["/stars", "/forks", "/watch", "/follow", "/allin"]

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            response = requests.get(url, timeout=35).json()
            
            for update in response.get("result", []):
                last_update_id = update["update_id"]
                
                # Handling Callback (Inline Keyboard) dan Teks Biasa
                is_callback = False
                text = ""
                user_id = ""
                username = "Unknown"
                chat_id = ""
                message_id = None
                callback_data = ""

                if "message" in update:
                    message = update["message"]
                    text = message.get("text", "")
                    user_id = str(message.get("from", {}).get("id", ""))
                    username = message.get("from", {}).get("username", "Unknown")
                    chat_id = str(message.get("chat", {}).get("id", ""))
                elif "callback_query" in update:
                    callback = update["callback_query"]
                    is_callback = True
                    callback_data = callback.get("data", "")
                    user_id = str(callback.get("from", {}).get("id", ""))
                    username = callback.get("from", {}).get("username", "Unknown")
                    msg_obj = callback.get("message", {})
                    chat_id = str(msg_obj.get("chat", {}).get("id", ""))
                    message_id = msg_obj.get("message_id")
                    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback["id"]}, timeout=5)
                    except: pass
                
                auth_users = get_authorized_users()
                if user_id not in auth_users: continue

                # Ambil preferensi bahasa, default Indonesia
                lang = USER_LANG.get(user_id, "id")
                lang_data = LANG_DICT[lang]

                # ==========================
                # CALLBACK HANDLER (PILIH BAHASA)
                # ==========================
                if is_callback:
                    if callback_data in ["lang_id", "lang_en"]:
                        lang = "id" if callback_data == "lang_id" else "en"
                        USER_LANG[user_id] = lang
                        log_terminal(f"User @{username} switched language to {lang.upper()}", "INFO")
                        edit_message(chat_id, message_id, LANG_DICT[lang]["help"])
                    continue

                if not text: continue

                if ASCII_TIMER is None:
                    cmd_name = text.split()[0] if text.startswith("/") else "Interactive Reply"
                    log_terminal(f"Received input from @{username} ({lang.upper()}): {cmd_name}", "INFO")

                # ==========================
                # MENU UTAMA & PILIH BAHASA
                # ==========================
                if text == "/start" or text == "/help":
                    markup = {
                        "inline_keyboard": [
                            [
                                {"text": "🇮🇩 Indonesia", "callback_data": "lang_id"},
                                {"text": "🇬🇧 English", "callback_data": "lang_en"}
                            ]
                        ]
                    }
                    send_message(chat_id, "🌐 <b>Select Language / Pilih Bahasa:</b>", reply_markup=markup)
                    continue

                # ==========================
                # INTERACTIVE STATE HANDLER
                # ==========================
                if user_id in PENDING_STATES:
                    state = PENDING_STATES[user_id]
                    
                    if text == "/cancel":
                        del PENDING_STATES[user_id]
                        log_terminal("Action Cancelled by user.", "INFO")
                        send_message(user_id, lang_data["cancelled"])
                        continue
                        
                    action = state.get('action')

                    if action == 'wait_cloud_engine':
                        engine_key = text.strip()
                        if engine_key not in CLOUD_ENGINES:
                            send_message(user_id, lang_data["err_invalid_engine"])
                            continue
                        
                        state['engine'] = engine_key
                        state['action'] = 'wait_cloud_target'
                        engine_name = CLOUD_ENGINES[engine_key]['name']
                        send_message(user_id, lang_data["prompt_target"].format(engine=engine_name))
                        continue

                    elif action == 'wait_cloud_target':
                        target = text.strip()
                        if "github.com/" in target: target = target.split("github.com/")[-1]
                        target = target.split("?")[0].split("#")[0].strip("/")
                        if target.endswith(".git"): target = target[:-4]
                        
                        state['target'] = target
                        state['action'] = 'wait_cloud_qty'
                        send_message(user_id, lang_data["prompt_qty"].format(service=state['service'].upper(), target=target))
                        continue

                    elif action == 'wait_cloud_qty':
                        if not text.isdigit():
                            send_message(user_id, lang_data["err_number"])
                            continue
                        state['quantity'] = int(text)
                        state['action'] = 'wait_cloud_duration'
                        send_message(user_id, lang_data["prompt_duration"])
                        continue

                    elif action == 'wait_cloud_duration':
                        try: duration = float(text.replace(',', '.'))
                        except:
                            send_message(user_id, lang_data["err_number"])
                            continue
                        if duration <= 0:
                            send_message(user_id, lang_data["err_duration"])
                            continue
                        state['duration'] = duration
                        state['action'] = 'wait_cloud_index'
                        send_message(user_id, lang_data["prompt_index"])
                        continue

                    elif action == 'wait_cloud_index':
                        if not text.isdigit() or int(text) < 1:
                            send_message(user_id, lang_data["err_number"])
                            continue
                        
                        start_index = int(text)
                        cmd_used = state['service']
                        target = state['target']
                        quantity = state['quantity']
                        duration = state['duration']
                        engine_id = state['engine']
                        engine_name = CLOUD_ENGINES[engine_id]['name']
                        
                        del PENDING_STATES[user_id]
                        send_message(user_id, lang_data["transmitting"].format(cmd=cmd_used.upper(), engine=engine_name))
                        
                        if cmd_used == "/allin":
                            success_reports = []
                            for action_name, yml_name in WORKFLOW_MAP.items():
                                success, msg = trigger_github_workflow(engine_id, yml_name, target, quantity, duration, start_index)
                                status_icon = "🟢" if success else "🔴"
                                success_reports.append(f"{status_icon} <b>{action_name[1:].upper()}</b>: {msg}")
                                time.sleep(1) 
                            
                            final_report = "\n".join(success_reports)
                            result_msg = lang_data["parallel_deployed"].format(
                                engine=engine_name, target=target, qty=quantity, dur=duration, index=start_index, status=final_report
                            )
                            send_message(user_id, result_msg)
                            broadcast_message(result_msg, exclude_id=user_id)
                        else:
                            yaml_file = WORKFLOW_MAP.get(cmd_used, "auto_star.yml")
                            success, msg = trigger_github_workflow(engine_id, yaml_file, target, quantity, duration, start_index)
                            if success:
                                log_terminal(f"Cloud Deployment: {cmd_used} for {target} on {engine_name}", "SUCCESS")
                                result_msg = lang_data["cloud_deployed"].format(
                                    engine=engine_name, cmd=cmd_used.upper(), target=target, qty=quantity, dur=duration, index=start_index
                                )
                                send_message(user_id, result_msg)
                                broadcast_message(result_msg, exclude_id=user_id)
                            else:
                                log_terminal(f"Cloud Deployment Failed: {msg}", "ERROR")
                                send_message(user_id, lang_data["cloud_failed"].format(msg=msg))
                        continue

                # ==========================
                # TRIGGER MENU & ROUTING
                # ==========================
                cmd_used = None
                for cmd in valid_cloud_commands:
                    if text.startswith(cmd):
                        cmd_used = cmd
                        break
                        
                if cmd_used:
                    PENDING_STATES[user_id] = {'action': 'wait_cloud_engine', 'service': cmd_used}
                    engine_list = "\n".join([f"<b>{k}.</b> {v['name']}" for k, v in CLOUD_ENGINES.items()])
                    
                    msg_engine = lang_data["prompt_engine"].format(cmd=cmd_used.upper(), engine_list=engine_list)
                    send_message(user_id, msg_engine)
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
