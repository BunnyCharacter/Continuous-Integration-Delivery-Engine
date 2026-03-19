import os
import requests
import time
import sys
import random
from datetime import datetime, timedelta, timezone

def get_now_wib():
    tz_wib = timezone(timedelta(hours=7))
    return datetime.now(tz_wib)

# ==========================================
# 🎯 MENGAMBIL PARAMETER DARI GITHUB ACTIONS
# ==========================================
RAW_ACTION = os.environ.get("ACTION_TYPE", "").strip().upper()

if "FOLLOW" in RAW_ACTION: ACTION_TYPE = "FOLLOW"
elif "STAR" in RAW_ACTION: ACTION_TYPE = "STARS"
elif "FORK" in RAW_ACTION: ACTION_TYPE = "FORKS"
elif "WATCH" in RAW_ACTION: ACTION_TYPE = "WATCH"
else: ACTION_TYPE = RAW_ACTION

if not ACTION_TYPE:
    print("❌ CRITICAL ERROR: Sinyal 'ACTION_TYPE' tidak ditemukan di file .yml!")
    sys.exit(1)

# ==========================================
# 🎯 MENYIAPKAN TARGET & KUOTA
# ==========================================
if ACTION_TYPE == "FOLLOW":
    RAW_TARGETS = os.environ.get("TARGET_USERS", "") or os.environ.get("TARGET_REPOS", "")
else:
    RAW_TARGETS = os.environ.get("TARGET_REPOS", "") or os.environ.get("TARGET_USERS", "")

TARGETS = [t.strip() for t in RAW_TARGETS.split(",") if t.strip()]

RAW_START = str(os.environ.get("INPUT_START", "1")).strip()
INPUT_QTY = int(os.environ.get("INPUT_QTY", 0))
INPUT_DUR = float(os.environ.get("INPUT_DUR", 0))

# ==========================================
# 🎨 FORMAT UI (MOBILE SAFE)
# ==========================================
L_TOP = "╔════════════════════════════════"
L_MID = "╠════════════════════════════════"
L_BOT = "╚════════════════════════════════"

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
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
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
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json", "X-GitHub-Api-Version": "2022-11-28"}
    try:
        if action_type == "STARS":
            res = requests.put(f"https://api.github.com/user/starred/{target}", headers=headers, timeout=10)
            return (res.status_code == 204), "STAR APPLIED" if res.status_code == 204 else f"FAILED ({res.status_code})"
        elif action_type == "FORKS":
            res = requests.post(f"https://api.github.com/repos/{target}/forks", headers=headers, timeout=10)
            return (res.status_code in [201, 202]), "FORKED" if res.status_code in [201, 202] else f"FAILED ({res.status_code})"
        elif action_type == "WATCH":
            res = requests.put(f"https://api.github.com/repos/{target}/subscription", headers=headers, json={"subscribed": True}, timeout=10)
            return (res.status_code == 200), "WATCH APPLIED" if res.status_code == 200 else f"FAILED ({res.status_code})"
        elif action_type == "FOLLOW":
            res = requests.put(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
            return (res.status_code == 204), "FOLLOW INJECTED" if res.status_code == 204 else f"FAILED ({res.status_code})"
    except: return False, "CONNECTION ERROR"
    return False, "UNKNOWN ERROR"

def main():
    tokens_raw = os.environ.get("WORKER_TOKENS", "")
    all_tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]
    
    if not all_tokens or not TARGETS:
        sys.exit(1)

    if "," in RAW_START:
        indices = [int(x.strip()) - 1 for x in RAW_START.split(",") if x.strip().isdigit()]
        tokens_to_use = [(i, all_tokens[i]) for i in indices if 0 <= i < len(all_tokens)]
    else:
        start_idx = max(0, int(RAW_START) - 1)
        tokens_to_use = [(start_idx + i, all_tokens[start_idx + i]) for i in range(INPUT_QTY) if 0 <= start_idx + i < len(all_tokens)]

    if not tokens_to_use:
        sys.exit(1)

    selected_target = TARGETS[0]
    base_delay = (INPUT_DUR * 3600) / max(1, len(tokens_to_use))
    
    idx_list = [str(idx + 1) for idx, _ in tokens_to_use]
    if len(idx_list) > 3 and idx_list == [str(i) for i in range(int(idx_list[0]), int(idx_list[-1])+1)]:
        worker_info = f"{len(tokens_to_use)} Nodes (#{idx_list[0]}-#{idx_list[-1]})"
    else:
        worker_info = f"{len(tokens_to_use)} Nodes ({','.join(idx_list)})"
    
    # 1. PESAN AWAL (INIT)
    pre_msg = (f"{L_TOP}\n"
               f"║ 🔴 <b>RESTRICTED CORP-SEC</b>\n"
               f"{L_MID}\n"
               f"║ ❖ <b>DIRECTIVE</b> : {ACTION_TYPE}_INJECT\n"
               f"║ ❖ <b>ASSET ID</b>  : <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
               f"║ ❖ <b>OPERATIVE</b> : {worker_info}\n"
               f"║ ❖ <b>THROTTLE</b>  : {INPUT_DUR} Hrs/Unit\n"
               f"{L_MID}\n"
               f"║ 🛡️ <i>Eng. by Abie Haryatmo</i>\n"
               f"║ 🤝 <b>XianBee Tech Store</b>\n"
               f"{L_MID}\n"
               f"║ <i>> Bypassing ICE...</i>\n"
               f"║ <code>ADMIN@CORP-SEC:~$ auth</code>\n"
               f"{L_BOT}")
    send_telegram_notification(pre_msg)

    success_count = 0
    
    for step_i, (real_idx, token) in enumerate(tokens_to_use):
        clean_token = token[4:] if token.startswith("ghp_") else token
        token_preview = f"{clean_token[:5]}...{clean_token[-4:]}"
        
        progress_pct = int((step_i / len(tokens_to_use)) * 100)
        bar = "▓" * (progress_pct // 10) + "░" * (10 - (progress_pct // 10))
        
        # 2. PESAN PROGRESS (LIVE)
        msg_live = (f"{L_TOP}\n"
                    f"║ 🟡 <b>OPERATION IN PROGRESS</b>\n"
                    f"{L_MID}\n"
                    f"║ ❖ <b>ASSET ID</b> : <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f"║ ❖ <b>UNIT</b>     : #{real_idx + 1} (<code>{token_preview}</code>)\n"
                    f"║ ❖ <b>QUEUE</b>    : SEQ {step_i}/{len(tokens_to_use)}\n"
                    f"║ ❖ <b>SYS LOAD</b> : <code>[{bar}] {progress_pct}%</code>\n"
                    f"{L_MID}\n"
                    f"║ 🛡️ <i>Eng. by Abie Haryatmo</i>\n"
                    f"║ 🤝 <b>XianBee Tech Store</b>\n"
                    f"{L_MID}\n"
                    f"║ <i>> Deploying payload...</i>\n"
                    f"║ <code>ADMIN@CORP-SEC:~$ monitor</code>\n"
                    f"{L_BOT}")
        
        sent_msgs = send_telegram_notification(msg_live)

        is_skipped = check_existing(token, selected_target, ACTION_TYPE)
        if is_skipped:
            res_msg = "ALREADY INJECTED"
            success_count += 1
            status_text = "🟡 <b>CACHE HIT (SKIPPED)</b>"
        else:
            success, info = perform_api_action(token, selected_target, ACTION_TYPE)
            if success: success_count += 1
            res_msg = info
            status_text = "🟢 <b>TRANSACTION LOGGED</b>" if success else "🔴 <b>TRANSACTION FAILED</b>"

        final_pct = int(((step_i + 1) / len(tokens_to_use)) * 100)
        final_bar = "▓" * (final_pct // 10) + "░" * (10 - (final_pct // 10))
        
        # 3. PESAN SELESAI 1 NODE
        msg_done = (f"{L_TOP}\n"
                    f"║ {status_text}\n"
                    f"{L_MID}\n"
                    f"║ ❖ <b>VALIDATION</b> : {res_msg}\n"
                    f"║ ❖ <b>ASSET ID</b>   : <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f"║ ❖ <b>UNIT</b>       : #{real_idx + 1} (<code>{token_preview}</code>)\n"
                    f"║ ❖ <b>SYS LOAD</b>   : <code>[{final_bar}] {final_pct}%</code>\n"
                    f"║ ❖ <b>TIMESTAMP</b>  : {get_now_wib().strftime('%H:%M:%S WIB')}\n"
                    f"{L_MID}\n"
                    f"║ 🛡️ <i>Eng. by Abie Haryatmo</i>\n"
                    f"║ 🤝 <b>XianBee Tech Store</b>\n"
                    f"{L_MID}\n"
                    f"║ <i>> Sync complete.</i>\n"
                    f"║ <code>ADMIN@CORP-SEC:~$ verify</code>\n"
                    f"{L_BOT}")
        
        edit_telegram_notification(sent_msgs, msg_done)

        if step_i < len(tokens_to_use) - 1:
            delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
            time.sleep(delay)

    # 4. PESAN REKAPITULASI AKHIR
    final_report = (f"{L_TOP}\n"
                    f"║ 🏁 <b>DAEMON TERMINATED</b>\n"
                    f"{L_MID}\n"
                    f"║ ❖ <b>JOB NAME</b>  : {ACTION_TYPE}_INJECT\n"
                    f"║ ❖ <b>ASSET ID</b>  : <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f"║ ❖ <b>EXIT CODE</b> : {success_count}/{len(tokens_to_use)} SUCCESS\n"
                    f"{L_MID}\n"
                    f"║ 🛡️ <i>Eng. by Abie Haryatmo</i>\n"
                    f"║ 🤝 <b>XianBee Tech Store</b>\n"
                    f"{L_MID}\n"
                    f"║ <i>> Shutting down uplink...</i>\n"
                    f"║ <code>ADMIN@CORP-SEC:~$ exit 0</code>\n"
                    f"{L_BOT}")
    send_telegram_notification(final_report)

if __name__ == "__main__":
    main()