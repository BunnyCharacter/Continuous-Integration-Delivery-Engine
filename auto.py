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

# Normalisasi ACTION_TYPE agar tahan banting dari typo
if "FOLLOW" in RAW_ACTION:
    ACTION_TYPE = "FOLLOW"
elif "STAR" in RAW_ACTION:
    ACTION_TYPE = "STARS"
elif "FORK" in RAW_ACTION:
    ACTION_TYPE = "FORKS"
elif "WATCH" in RAW_ACTION:
    ACTION_TYPE = "WATCH"
else:
    ACTION_TYPE = RAW_ACTION

if not ACTION_TYPE:
    print("❌ CRITICAL ERROR: Sinyal 'ACTION_TYPE' tidak ditemukan di file .yml!")
    sys.exit(1)

print("="*50)
print("🚀 XIANBEE CORP-SEC ENGINE STARTING")
print("="*50)
print(f"🎯 DIRECTIVE : {ACTION_TYPE}")
print("="*50)

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
# 🎨 TEMA UI CORP-SEC (HAZARD TAPE)
# ==========================================
B = "◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤"

# Footer konstan untuk disisipkan di semua notifikasi
FOOTER = (f"{B}\n"
          f"🛡️ <i>Engineered by Abie Haryatmo</i>\n"
          f"🤝 <b>Powered by XianBee Tech Store</b>\n"
          f"{B}")

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
            return (res.status_code == 204), "[ 200 OK ] STAR APPLIED" if res.status_code == 204 else f"[ {res.status_code} ] FAILED"
        elif action_type == "FORKS":
            res = requests.post(f"https://api.github.com/repos/{target}/forks", headers=headers, timeout=10)
            return (res.status_code in [201, 202]), "[ 201 CREATED ] FORKED" if res.status_code in [201, 202] else f"[ {res.status_code} ] FAILED"
        elif action_type == "WATCH":
            res = requests.put(f"https://api.github.com/repos/{target}/subscription", headers=headers, json={"subscribed": True}, timeout=10)
            return (res.status_code == 200), "[ 200 OK ] WATCH APPLIED" if res.status_code == 200 else f"[ {res.status_code} ] FAILED"
        elif action_type == "FOLLOW":
            res = requests.put(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
            return (res.status_code == 204), "[ 200 OK ] FOLLOW INJECTED" if res.status_code == 204 else f"[ {res.status_code} ] FAILED"
    except: return False, "[ 500 ] CONNECTION ERROR"
    return False, "[ 500 ] UNKNOWN ERROR"

def main():
    tokens_raw = os.environ.get("WORKER_TOKENS", "")
    all_tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]
    
    if not all_tokens or not TARGETS:
        print("❌ ERROR: Tokens atau Target kosong. Exiting...")
        sys.exit(1)

    if "," in RAW_START:
        indices = [int(x.strip()) - 1 for x in RAW_START.split(",") if x.strip().isdigit()]
        tokens_to_use = [(i, all_tokens[i]) for i in indices if 0 <= i < len(all_tokens)]
    else:
        start_idx = max(0, int(RAW_START) - 1)
        tokens_to_use = [(start_idx + i, all_tokens[start_idx + i]) for i in range(INPUT_QTY) if 0 <= start_idx + i < len(all_tokens)]

    if not tokens_to_use:
        print("❌ ERROR: Tidak ada token yang valid untuk format urutan tersebut. Exiting...")
        sys.exit(1)

    selected_target = TARGETS[0]
    base_delay = (INPUT_DUR * 3600) / max(1, len(tokens_to_use))
    
    idx_list = [str(idx + 1) for idx, _ in tokens_to_use]
    if len(idx_list) > 3 and idx_list == [str(i) for i in range(int(idx_list[0]), int(idx_list[-1])+1)]:
        worker_info = f"{len(tokens_to_use)} Units (Idx: #{idx_list[0]} - #{idx_list[-1]})"
    else:
        worker_info = f"{len(tokens_to_use)} Units (Idx: {', '.join(idx_list)})"
    
    # 1. NOTIFIKASI AWAL (INIT)
    pre_msg = (f"{B}\n"
               f"🔴 <b>[ RESTRICTED ] CORP-SEC TERMINAL</b>\n"
               f"{B}\n"
               f"🛡️ <b>DIRECTIVE :</b> <code>[ {ACTION_TYPE}_INJECTION ]</code>\n"
               f"🎯 <b>ASSET ID  :</b> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
               f"🖥️ <b>OPERATIVE :</b> <code>{worker_info}</code>\n"
               f"⏱️ <b>THROTTLE  :</b> <code>{INPUT_DUR} Hrs / Unit</code>\n"
               f"{FOOTER}\n"
               f"<i>Authorization granted. Bypassing ICE...</i>\n"
               f"<code>ADMIN@CORP-SEC:~$ authorize_strike</code>\n"
               f"{B}")
    send_telegram_notification(pre_msg)

    success_count = 0
    
    for step_i, (real_idx, token) in enumerate(tokens_to_use):
        clean_token = token[4:] if token.startswith("ghp_") else token
        token_preview = f"{clean_token[:5]}...{clean_token[-4:]}"
        print(f"[{step_i+1}/{len(tokens_to_use)}] Processing Node #{real_idx + 1}: {token_preview}")
        
        progress_pct = int((step_i / len(tokens_to_use)) * 100)
        bar = "▓" * (progress_pct // 10) + "░" * (10 - (progress_pct // 10))
        
        # 2. NOTIFIKASI PROGRESS (LIVE)
        msg_live = (f"{B}\n"
                    f"🟡 <b>[ OVERRIDE ] BYPASSING FIREWALL...</b>\n"
                    f"{B}\n"
                    f"🎯 <b>ASSET ID  :</b> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f"🤖 <b>UNIT      :</b> <code>Operative-#{real_idx + 1}</code>\n"
                    f"🔑 <b>KEYCARD   :</b> <code>{token_preview}</code>\n"
                    f"📈 <b>QUEUE     :</b> <code>SEQ {step_i}/{len(tokens_to_use)}</code>\n"
                    f"🔋 <b>SYS LOAD  :</b> <code>[{bar}] {progress_pct}%</code>\n"
                    f"{FOOTER}\n"
                    f"<i>Injecting payload to target asset...</i>\n"
                    f"<code>ADMIN@CORP-SEC:~$ monitor_traffic</code>\n"
                    f"{B}")
        
        sent_msgs = send_telegram_notification(msg_live)

        is_skipped = check_existing(token, selected_target, ACTION_TYPE)
        if is_skipped:
            res_msg = "[ CACHE HIT ] ALREADY INJECTED"
            success_count += 1
            print(f" -> ⏭️ SKIPPED: Node #{real_idx + 1} ({token_preview}) already executed this target.")
            status_header = "🟡 <b>[ CACHE HIT ] ASSET VERIFIED</b>"
        else:
            success, info = perform_api_action(token, selected_target, ACTION_TYPE)
            if success: success_count += 1
            res_msg = info
            print(f" -> {res_msg} [Executed by Node #{real_idx + 1} | {token_preview}]")
            status_header = "🟢 <b>[ AUTHORIZED ] ASSET SECURED</b>" if success else "🔴 <b>[ DENIED ] BREACH FAILED</b>"

        final_pct = int(((step_i + 1) / len(tokens_to_use)) * 100)
        final_bar = "▓" * (final_pct // 10) + "░" * (10 - (final_pct // 10))
        
        # 3. NOTIFIKASI SELESAI EKSESKUSI 1 NODE (SUCCESS/FAILED)
        msg_done = (f"{B}\n"
                    f"{status_header}\n"
                    f"{B}\n"
                    f"🛡️ <b>VALIDATION:</b> <code>{res_msg}</code>\n"
                    f"🎯 <b>ASSET ID  :</b> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f"🤖 <b>UNIT      :</b> <code>Operative-#{real_idx + 1}</code>\n"
                    f"🔑 <b>KEYCARD   :</b> <code>{token_preview}</code>\n"
                    f"🔋 <b>SYS LOAD  :</b> <code>[{final_bar}] {final_pct}%</code>\n"
                    f"🕒 <b>TIMESTAMP :</b> <code>{get_now_wib().strftime('%H:%M:%S WIB')}</code>\n"
                    f"{FOOTER}\n"
                    f"<i>Transaction logged in corporate database.</i>\n"
                    f"<code>ADMIN@CORP-SEC:~$ verify_checksum</code>\n"
                    f"{B}")
        
        edit_telegram_notification(sent_msgs, msg_done)

        if step_i < len(tokens_to_use) - 1:
            delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
            print(f" -> Sleeping for {int(delay)} seconds...")
            time.sleep(delay)

    # 4. NOTIFIKASI REKAPITULASI (FINAL SUMMARY)
    final_report = (f"{B}\n"
                    f"🏢 <b>[ LOG OFF ] AUDIT TRAIL WIPED</b>\n"
                    f"{B}\n"
                    f"🛡️ <b>DIRECTIVE :</b> <code>[ {ACTION_TYPE}_INJECTION ]</code>\n"
                    f"🎯 <b>ASSET ID  :</b> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f"📊 <b>RESULT    :</b> <code>{success_count}/{len(tokens_to_use)} AUTHORIZED</code>\n"
                    f"{FOOTER}\n"
                    f"<i>Operation concluded. Disconnecting from mainframe...</i>\n"
                    f"<code>ADMIN@CORP-SEC:~$ wipe_logs && exit</code>\n"
                    f"{B}")
    send_telegram_notification(final_report)
    print("="*50)
    print("✅ EXECUTION COMPLETE!")

if __name__ == "__main__":
    main()