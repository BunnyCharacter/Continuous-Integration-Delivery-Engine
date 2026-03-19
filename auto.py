import os
import requests
import time
import sys
import random
import re
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
# 🎨 FUNGSI AUTO-PADDING (BOX MAKER)
# ==========================================
W = 38 # Lebar dalam kotak
TOP = f"╔{'═'*W}╗"
MID = f"╠{'═'*W}╣"
BOT = f"╚{'═'*W}╝"

def bl(text):
    """Fungsi untuk membuat baris kotak dengan spasi otomatis (biar ujung kanan rata)"""
    # Menghapus tag HTML sementara untuk menghitung panjang karakter asli
    clean_text = re.sub(r'<[^>]+>', '', text)
    pad_len = max(0, W - len(clean_text))
    return f"║ {text}{' ' * pad_len} ║"

# ==========================================
# ⚙️ FUNGSI TELEGRAM & API
# ==========================================
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
    # Memotong string agar kotak tidak jebol
    disp_target = selected_target if len(selected_target) <= 18 else selected_target[:16] + ".."
    
    base_delay = (INPUT_DUR * 3600) / max(1, len(tokens_to_use))
    
    idx_list = [str(idx + 1) for idx, _ in tokens_to_use]
    if len(idx_list) > 3 and idx_list == [str(i) for i in range(int(idx_list[0]), int(idx_list[-1])+1)]:
        info_str = f"{len(tokens_to_use)} Nodes (#{idx_list[0]}-#{idx_list[-1]})"
    else:
        info_str = f"{len(tokens_to_use)} Nodes ({','.join(idx_list)})"
    
    worker_info = info_str if len(info_str) <= 20 else info_str[:18] + ".."
    
    # 1. PESAN AWAL (INIT) - FULL BOX
    msg1 = [
        TOP,
        bl("🔴 <b>RESTRICTED CORP-SEC</b>"),
        MID,
        bl(f"❖ <b>DIRECTIVE</b>: {ACTION_TYPE}_INJECT"),
        bl(f"❖ <b>ASSET ID</b> : <a href='https://github.com/{selected_target}'>{disp_target}</a>"),
        bl(f"❖ <b>OPERATIVE</b>: {worker_info}"),
        bl(f"❖ <b>THROTTLE</b> : {INPUT_DUR} Hrs/Unit"),
        MID,
        bl("🛡️ <i>Eng. by Abie Haryatmo</i>"),
        bl("🤝 <b>XianBee Tech Store</b>"),
        MID,
        bl("<i>> Bypassing ICE...</i>"),
        bl("<code>ADMIN@CORP-SEC:~$ auth</code>"),
        BOT
    ]
    pre_msg = "\n".join(msg1)
    send_telegram_notification(pre_msg)

    success_count = 0
    
    for step_i, (real_idx, token) in enumerate(tokens_to_use):
        clean_token = token[4:] if token.startswith("ghp_") else token
        token_preview = f"{clean_token[:5]}...{clean_token[-4:]}"
        print(f"[{step_i+1}/{len(tokens_to_use)}] Processing Node #{real_idx + 1}: {token_preview}")
        
        progress_pct = int((step_i / len(tokens_to_use)) * 100)
        bar = "▓" * (progress_pct // 10) + "░" * (10 - (progress_pct // 10))
        
        # 2. PESAN PROGRESS (LIVE) - FULL BOX
        msg2 = [
            TOP,
            bl("🟡 <b>OPERATION IN PROGRESS</b>"),
            MID,
            bl(f"❖ <b>ASSET ID</b>: <a href='https://github.com/{selected_target}'>{disp_target}</a>"),
            bl(f"❖ <b>UNIT</b>    : #{real_idx + 1} ({token_preview})"),
            bl(f"❖ <b>QUEUE</b>   : SEQ {step_i}/{len(tokens_to_use)}"),
            bl(f"❖ <b>SYS LOAD</b>: [{bar}] {progress_pct}%"),
            MID,
            bl("🛡️ <i>Eng. by Abie Haryatmo</i>"),
            bl("🤝 <b>XianBee Tech Store</b>"),
            MID,
            bl("<i>> Deploying payload...</i>"),
            bl("<code>ADMIN@CORP-SEC:~$ monitor</code>"),
            BOT
        ]
        msg_live = "\n".join(msg2)
        sent_msgs = send_telegram_notification(msg_live)

        is_skipped = check_existing(token, selected_target, ACTION_TYPE)
        if is_skipped:
            res_msg = "ALREADY INJECTED"
            success_count += 1
            print(f" -> ⏭️ SKIPPED: Node #{real_idx + 1} ({token_preview}) already executed this target.")
            status_text = "🟡 <b>CACHE HIT (SKIPPED)</b>"
        else:
            success, info = perform_api_action(token, selected_target, ACTION_TYPE)
            if success: success_count += 1
            res_msg = info
            print(f" -> {res_msg} [Executed by Node #{real_idx + 1} | {token_preview}]")
            status_text = "🟢 <b>TRANSACTION LOGGED</b>" if success else "🔴 <b>TRANSACTION FAILED</b>"

        final_pct = int(((step_i + 1) / len(tokens_to_use)) * 100)
        final_bar = "▓" * (final_pct // 10) + "░" * (10 - (final_pct // 10))
        disp_info = res_msg if len(res_msg) <= 18 else res_msg[:16] + ".."
        
        # 3. PESAN SELESAI 1 NODE - FULL BOX
        msg3 = [
            TOP,
            bl(status_text),
            MID,
            bl(f"❖ <b>VALIDATION</b>: {disp_info}"),
            bl(f"❖ <b>ASSET ID</b>  : <a href='https://github.com/{selected_target}'>{disp_target}</a>"),
            bl(f"❖ <b>UNIT</b>      : #{real_idx + 1} ({token_preview})"),
            bl(f"❖ <b>SYS LOAD</b>  : [{final_bar}] {final_pct}%"),
            bl(f"❖ <b>TIMESTAMP</b> : {get_now_wib().strftime('%H:%M:%S')}"),
            MID,
            bl("🛡️ <i>Eng. by Abie Haryatmo</i>"),
            bl("🤝 <b>XianBee Tech Store</b>"),
            MID,
            bl("<i>> Sync complete.</i>"),
            bl("<code>ADMIN@CORP-SEC:~$ verify</code>"),
            BOT
        ]
        msg_done = "\n".join(msg3)
        edit_telegram_notification(sent_msgs, msg_done)

        if step_i < len(tokens_to_use) - 1:
            delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
            print(f" -> Sleeping for {int(delay)} seconds...")
            time.sleep(delay)

    # 4. PESAN REKAPITULASI AKHIR - FULL BOX
    msg4 = [
        TOP,
        bl("🏁 <b>DAEMON TERMINATED</b>"),
        MID,
        bl(f"❖ <b>JOB NAME</b> : {ACTION_TYPE}_INJECT"),
        bl(f"❖ <b>ASSET ID</b> : <a href='https://github.com/{selected_target}'>{disp_target}</a>"),
        bl(f"❖ <b>EXIT CODE</b>: {success_count}/{len(tokens_to_use)} SUCCESS"),
        MID,
        bl("🛡️ <i>Eng. by Abie Haryatmo</i>"),
        bl("🤝 <b>XianBee Tech Store</b>"),
        MID,
        bl("<i>> Shutting down uplink...</i>"),
        bl("<code>ADMIN@CORP-SEC:~$ exit 0</code>"),
        BOT
    ]
    final_report = "\n".join(msg4)
    send_telegram_notification(final_report)
    print("="*50)
    print("✅ EXECUTION COMPLETE!")

if __name__ == "__main__":
    main()