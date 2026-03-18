import os #WRKFLW
import requests
import time
import sys
import random
from datetime import datetime, timedelta, timezone

def get_now_wib():
    tz_wib = timezone(timedelta(hours=7))
    return datetime.now(tz_wib)

# ==========================================
# 🎯 UNIVERSAL DYNAMIC CONFIGURATION
# ==========================================
# ACTION_TYPE bisa diisi: STARS, FORKS, WATCH, FOLLOW
ACTION_TYPE = os.environ.get("ACTION_TYPE", "STARS").strip().upper()

if ACTION_TYPE == "FOLLOW":
    RAW_TARGETS = os.environ.get("TARGET_USERS", "")
    TARGET_LABEL = "Target User"
else:
    RAW_TARGETS = os.environ.get("TARGET_REPOS", "")
    TARGET_LABEL = "Target Repo"

TARGETS = [t.strip() for t in RAW_TARGETS.split(",") if t.strip()]

INPUT_QTY = int(os.environ.get("INPUT_QTY", 0))
INPUT_DUR = float(os.environ.get("INPUT_DUR", 0))
INPUT_START = int(os.environ.get("INPUT_START", 1))

QUOTES = [
    '"Talk is cheap. Show me the code." – Linus Torvalds',
    '"Simplicity is the soul of efficiency." – Austin Freeman',
    '"Make it work, make it right, make it fast." – Kent Beck',
    '"Automate the boring stuff, master the complex." – Abie Haryatmo',
    '"Clean code always looks like it was written by someone who cares." – Robert C. Martin'
]

def send_telegram_notification(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_ids_raw: return {}
    chat_ids = [chat_id.strip() for chat_id in chat_ids_raw.split(",") if chat_id.strip()]
    sent_messages = {}
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try:
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                sent_messages[chat_id] = res.json()['result']['message_id']
        except: pass
    return sent_messages

def edit_telegram_notification(sent_messages, new_message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token or not sent_messages: return
    for chat_id, msg_id in sent_messages.items():
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": msg_id, "text": new_message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try: requests.post(url, json=payload, timeout=15)
        except: pass

def check_existing(token, target, action_type):
    """Mengecek apakah token ini sudah pernah melakukan aksi ke target sebelumnya"""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json", "X-GitHub-Api-Version": "2022-11-28"}
    try:
        if action_type == "STARS":
            return requests.get(f"https://api.github.com/user/starred/{target}", headers=headers, timeout=10).status_code == 204
        elif action_type == "WATCH":
            res = requests.get(f"https://api.github.com/repos/{target}/subscription", headers=headers, timeout=10)
            return res.status_code == 200 and res.json().get("subscribed") == True
        elif action_type == "FOLLOW":
            return requests.get(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10).status_code == 204
        elif action_type == "FORKS":
            user_res = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            if user_res.status_code == 200:
                username = user_res.json().get("login")
                repo_name = target.split("/")[-1] 
                check_res = requests.get(f"https://api.github.com/repos/{username}/{repo_name}", headers=headers, timeout=10)
                return check_res.status_code == 200 and check_res.json().get("fork") == True
    except: pass
    return False

def perform_api_action(token, target, action_type):
    """Mengeksekusi API GitHub sesuai dengan Action Type yang diminta"""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json", "X-GitHub-Api-Version": "2022-11-28"}
    try:
        if action_type == "STARS":
            res = requests.put(f"https://api.github.com/user/starred/{target}", headers=headers, timeout=10)
            if res.status_code == 204: return True, "⭐ <b>STAR STATUS ACTIVE</b>"
            return False, f"❌ <b>STAR FAILED</b> ({res.status_code})"
            
        elif action_type == "FORKS":
            res = requests.post(f"https://api.github.com/repos/{target}/forks", headers=headers, timeout=10)
            if res.status_code in [201, 202]: return True, "📦 <b>REPOSITORY FORKED</b>"
            return False, f"❌ <b>FORK FAILED</b> ({res.status_code})"
            
        elif action_type == "WATCH":
            res = requests.put(f"https://api.github.com/repos/{target}/subscription", headers=headers, json={"subscribed": True}, timeout=10)
            if res.status_code == 200: return True, "👁️ <b>WATCH STATUS ACTIVE</b>"
            return False, f"❌ <b>WATCH FAILED</b> ({res.status_code})"
            
        elif action_type == "FOLLOW":
            res = requests.put(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
            if res.status_code == 204: return True, "🫂 <b>FOLLOW STATUS ACTIVE</b>"
            return False, f"❌ <b>FOLLOW FAILED</b> ({res.status_code})"
    except:
        return False, f"❌ <b>{action_type} ERROR</b>"

def do_action(token, target, token_idx, sent_msgs, current_step, total_steps):
    target_url = f"https://github.com/{target}"
    token_preview = f"{token[:8]}...{token[-4:]}"
    
    def update_loading(action_text):
        progress_pct = int((current_step / total_steps) * 100)
        bar_len = 10
        filled = int(progress_pct / 10)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        msg = (f"╔════════════════════╗\n"
               f"   ⏳ <b>LIVE EXECUTION</b>\n"
               f"╚════════════════════╝\n\n"
               f"🔄 <i>{action_text}</i>\n"
               f"══════════════════════\n"
               f"🎯 <b>{TARGET_LABEL} :</b> <a href='{target_url}'>{target}</a>\n"
               f"🤖 <b>Node   :</b> #{token_idx + 1} ({token_preview})\n"
               f"📊 <b>Proses :</b> <code>[{bar}] {progress_pct}%</code>\n"
               f"🔢 <b>Status :</b> {current_step} dari {total_steps} Selesai\n\n"
               f"🛡️ <i>Engineered by Abie Haryatmo</i>\n"
               f"🤝 <b>Powered by XianBeeStore</b>")
        edit_telegram_notification(sent_msgs, msg)

    results = []
    
    update_loading("Checking worker status...")
    if check_existing(token, target, ACTION_TYPE):
        results.append(f"⚠️ <b>TASK SKIPPED</b> (Already {ACTION_TYPE.lower()}ed)")
        return True, "\n".join(results)
        
    update_loading(f"Deploying {ACTION_TYPE} protocol...")
    time.sleep(random.randint(5, 10)) 
    
    is_success, msg = perform_api_action(token, target, ACTION_TYPE)
    results.append(msg)
        
    return False, "\n".join(results)

def main():
    time.sleep(random.randint(1, 5))
    tokens_raw = os.environ.get("WORKER_TOKENS", "")
    tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]
    
    if not tokens or not TARGETS:
        print("❌ ERROR: Worker credentials or Target missing!")
        sys.exit(1)

    is_manual_trigger = INPUT_QTY > 0

    # =========================================================
    # 🧠 EKSEKUSI MODE MANUAL (TELEGRAM TRIGGER)
    # =========================================================
    if is_manual_trigger:
        start_idx = INPUT_START - 1 
        end_idx = start_idx + INPUT_QTY
        tokens_to_use = tokens[start_idx:end_idx]
        total_qty = len(tokens_to_use)
        
        if not tokens_to_use:
            send_telegram_notification(f"❌ <b>EXECUTION ABORTED</b>\nToken habis atau urutan #{INPUT_START} tidak tersedia.")
            sys.exit(1)

        base_delay = (INPUT_DUR * 3600) / max(1, total_qty)
        selected_target = TARGETS[0]
        target_url = f"https://github.com/{selected_target}"

        pre_msg = (f"╔════════════════════╗\n"
                   f" ⚙️ <b>CLOUD WORKER AWAKE</b>\n"
                   f"╚════════════════════╝\n\n"
                   f"<i>Mode: DYNAMIC {ACTION_TYPE} INJECTION</i>\n"
                   f"🎯 <b>{TARGET_LABEL}:</b> <a href='{target_url}'>{selected_target}</a>\n"
                   f"🤖 <b>Tokens:</b> Urutan #{INPUT_START} s/d #{start_idx + total_qty}\n"
                   f"⏳ <b>Pacing:</b> {INPUT_DUR} Jam (~{int(base_delay)} dtk/node)\n\n"
                   f"🛡️ <i>Engineered by Abie Haryatmo</i>")
        send_telegram_notification(pre_msg)

        success_count = 0
        for i, token in enumerate(tokens_to_use):
            token_idx = start_idx + i
            token_preview = f"{token[:8]}...{token[-4:]}"
            time_str = get_now_wib().strftime('%d/%m/%Y %H:%M:%S WIB')
            selected_quote = random.choice(QUOTES)
            
            progress_pct = int(((i) / total_qty) * 100)
            bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))
            
            init_msg = (f"╔════════════════════╗\n"
                        f" ⏳ <b>PREPARING WORKER...</b>\n"
                        f"╚════════════════════╝\n\n"
                        f"<i>Establishing secure connection to GitHub API...</i>\n"
                        f"══════════════════════\n"
                        f"🎯 <b>{TARGET_LABEL} :</b> <a href='{target_url}'>{selected_target}</a>\n"
                        f"🤖 <b>Node   :</b> #{token_idx + 1} ({token_preview})\n"
                        f"📊 <b>Proses :</b> <code>[{bar}] {progress_pct}%</code>\n"
                        f"🔢 <b>Status :</b> {i} dari {total_qty} Selesai\n\n"
                        f"🛡️ <i>Engineered by Abie Haryatmo</i>")
            sent_msgs = send_telegram_notification(init_msg)

            is_skipped, result = do_action(token, selected_target, token_idx, sent_msgs, i+1, total_qty)
            
            if "ACTIVE" in result or "FORKED" in result or "SKIPPED" in result: success_count += 1
            
            final_pct = int(((i + 1) / total_qty) * 100)
            final_bar = "█" * int(final_pct / 10) + "░" * (10 - int(final_pct / 10))

            final_msg = (
                f"╔════════════════════╗\n"
                f" 🚀 <b>DEPLOYMENT SUCCESS</b>\n"
                f"╚════════════════════╝\n\n"
                f"{result}\n"
                f"══════════════════════\n"
                f"🎯 <b>{TARGET_LABEL} :</b> <a href='{target_url}'>{selected_target}</a>\n"
                f"🤖 <b>Node   :</b> #{token_idx + 1} ({token_preview})\n"
                f"📊 <b>Proses :</b> <code>[{final_bar}] {final_pct}%</code>\n"
                f"⏱️ <b>Waktu  :</b> {time_str}\n\n"
                f"#CloudAutomation\n"
                f"<i>{selected_quote}</i>"
            )
            if sent_msgs: edit_telegram_notification(sent_msgs, final_msg)
            
            if i < total_qty - 1:
                actual_delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
                time.sleep(actual_delay)

        final_msg = (f"╔════════════════════╗\n"
                     f" ✅ <b>MISSION ACCOMPLISHED</b>\n"
                     f"╚════════════════════╝\n\n"
                     f"<b>Action:</b> {ACTION_TYPE} INJECTION\n"
                     f"<b>Target:</b> <a href='{target_url}'>{selected_target}</a>\n"
                     f"<b>Success:</b> {success_count}/{total_qty} Nodes\n\n"
                     f"🛡️ <i>Engineered by Abie Haryatmo</i>")
        send_telegram_notification(final_msg)
        sys.exit(0)

    # =========================================================
    # 🧠 LOGIKA DYNAMIC DAYS BERDASARKAN JUMLAH TUGAS (CRON MODE)
    # =========================================================
    all_tasks = []
    for t_idx in range(len(tokens)):
        for r_idx in range(len(TARGETS)):
            all_tasks.append((t_idx, r_idx))

    total_tasks = len(all_tasks)
    target_days = 4 + (total_tasks // 100) if total_tasks >= 100 else 5
        
    total_runs_target = target_days * 24
    run_number = int(os.environ.get("GITHUB_RUN_NUMBER", 1))
    current_run_in_cycle = ((run_number - 1) % total_runs_target) + 1
    
    task_start = int((current_run_in_cycle - 1) * total_tasks / total_runs_target)
    task_end = int(current_run_in_cycle * total_tasks / total_runs_target)
    tasks_to_process = task_end - task_start

    if tasks_to_process == 0: sys.exit(0)

    for i in range(task_start, task_end):
        token_idx, target_idx = all_tasks[i]
        selected_token = tokens[token_idx]
        selected_target = TARGETS[target_idx]
        target_url = f"https://github.com/{selected_target}"
        time_str = get_now_wib().strftime('%d/%m/%Y %H:%M:%S WIB')
        token_preview = selected_token[-6:]
        selected_quote = QUOTES[i % len(QUOTES)]
        
        current_step = (i - task_start) + 1
        
        progress_pct = int(((current_step - 1) / tasks_to_process) * 100)
        bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))
        
        init_msg = (f"╔════════════════════╗\n"
                    f" ⏳ <b>PREPARING WORKER...</b>\n"
                    f"╚════════════════════╝\n\n"
                    f"<i>Establishing secure connection to GitHub API...</i>\n"
                    f"══════════════════════\n"
                    f"🎯 <b>{TARGET_LABEL} :</b> <a href='{target_url}'>{selected_target}</a>\n"
                    f"🤖 <b>Node   :</b> #{token_idx + 1} ({token_preview})\n"
                    f"📊 <b>Proses :</b> <code>[{bar}] {progress_pct}%</code>\n"
                    f"🔢 <b>Status :</b> {current_step - 1} dari {tasks_to_process} Selesai\n\n"
                    f"🛡️ <i>Engineered by Abie Haryatmo</i>")
        sent_msgs = send_telegram_notification(init_msg)
        
        is_skipped, result = do_action(selected_token, selected_target, token_idx, sent_msgs, current_step, tasks_to_process)
        
        final_pct = int((current_step / tasks_to_process) * 100)
        final_bar = "█" * int(final_pct / 10) + "░" * (10 - int(final_pct / 10))
        
        final_msg = (
            f"╔════════════════════╗\n"
            f" 🚀 <b>DEPLOYMENT SUCCESS</b>\n"
            f"╚════════════════════╝\n\n"
            f"{result}\n"
            f"══════════════════════\n"
            f"🎯 <b>{TARGET_LABEL} :</b> <a href='{target_url}'>{selected_target}</a>\n"
            f"🤖 <b>Node   :</b> #{token_idx + 1} ({token_preview})\n"
            f"📊 <b>Proses :</b> <code>[{final_bar}] {final_pct}%</code>\n"
            f"⏱️ <b>Waktu  :</b> {time_str}\n\n"
            f"#DevOpsMode #CloudAutomation\n"
            f"<i>{selected_quote}</i>"
        )
        if sent_msgs: edit_telegram_notification(sent_msgs, final_msg)
        
        if i < task_end - 1:
            if is_skipped: time.sleep(2) 
            else: time.sleep(random.randint(20, 40))

if __name__ == "__main__":
    main()
