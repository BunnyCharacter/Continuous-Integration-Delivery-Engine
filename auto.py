import os #WORKER
import requests
import time
import sys
import random
from datetime import datetime, timedelta, timezone

def get_now_wib():
    tz_wib = timezone(timedelta(hours=7))
    return datetime.now(tz_wib)

print("🔄 Inisialisasi Script Dimulai...")

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

ENGINE_NAME = str(os.environ.get("INPUT_ENGINE_NAME", "Unknown Engine")).strip()
INPUT_LANG = str(os.environ.get("INPUT_LANG", "id")).strip().lower()

print(f"🎯 Target: {TARGETS} | Aksi: {ACTION_TYPE} | Engine: {ENGINE_NAME}")

# ==========================================
# 🌍 PENGATURAN BAHASA (ID / EN)
# ==========================================
if INPUT_LANG == "en":
    LBL_ENG, LBL_DIR, LBL_AST, LBL_OPR, LBL_THR, LBL_QUE, LBL_SYS = "ENGINE", "DIRECTIVE", "ASSET ID", "OPERATIVE", "THROTTLE", "PROG QUEUE", "SYS LOAD"
    LBL_VAL, LBL_TIM, LBL_EXT = "VALIDATION", "TIME STAMP", "EXIT CODE"
    TXT_HRS, TXT_SUCCESS = "Hrs / Unit", "SUCCESS"
    HEAD_INIT = "🔴 <b>CORP-SEC ALERTS</b>"
    HEAD_LIVE = "🟡 <b>INJECTION PROGRESS</b>"
    HEAD_TERM = "🏁 <b>DAEMON TERMINATED</b>"
    STAT_SKIP = "🟡 <b>CACHE HIT (SKIPPED)</b>"
    STAT_SUCC = "🟢 <b>TRANSACTION LOGGED</b>"
    STAT_FAIL = "🔴 <b>TRANSACTION FAILED</b>"
    MSG_INIT_TXT = "Establishing secure uplink..."
    MSG_LIVE_TXT = "Deploying payload to target..."
    MSG_SYNC_TXT = "Checksum verified. Sync complete."
    MSG_END_TXT  = "Operation concluded. Wiping logs..."
    VAL_SKIP = "ALREADY INJECTED"
else:
    LBL_ENG, LBL_DIR, LBL_AST, LBL_OPR, LBL_THR, LBL_QUE, LBL_SYS = "MESIN", "ARAHAN", "ID ASET", "OPERATOR", "JEDA WAKTU", "ANTREAN", "BEBAN SYS"
    LBL_VAL, LBL_TIM, LBL_EXT = "VALIDASI", "WAKTU", "KODE KELUAR"
    TXT_HRS, TXT_SUCCESS = "Jam / Unit", "BERHASIL"
    HEAD_INIT = "🔴 <b>PERINGATAN CORP-SEC</b>"
    HEAD_LIVE = "🟡 <b>PROSES INJEKSI</b>"
    HEAD_TERM = "🏁 <b>DAEMON DIHENTIKAN</b>"
    STAT_SKIP = "🟡 <b>DILEWATI (SUDAH ADA)</b>"
    STAT_SUCC = "🟢 <b>TRANSAKSI BERHASIL</b>"
    STAT_FAIL = "🔴 <b>TRANSAKSI GAGAL</b>"
    MSG_INIT_TXT = "Membangun koneksi aman..."
    MSG_LIVE_TXT = "Mengirim muatan ke target..."
    MSG_SYNC_TXT = "Ceksum valid. Sinkronisasi selesai."
    MSG_END_TXT  = "Operasi selesai. Menghapus log..."
    VAL_SKIP = "SUDAH DIINJEKSI"

L_TOP = "╔════════════════════════════════╗"
L_MID = "╠════════════════════════════════╣"
L_BOT = "╚════════════════════════════════╝"

def send_telegram_notification(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_ids_raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    
    if not bot_token or not chat_ids_raw:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID kosong/tidak terbaca dari Secrets!")
        return {}

    chat_ids = [chat_id.strip() for chat_id in chat_ids_raw.split(",") if chat_id.strip()]
    sent_messages = {}
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try:
            print(f"📡 Mencoba mengirim pesan ke Telegram (Chat ID: {chat_id})...")
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                sent_messages[chat_id] = res.json()['result']['message_id']
                print(f"✅ Pesan sukses terkirim!")
            else:
                print(f"❌ TELEGRAM API ERROR ({res.status_code}): {res.text}")
        except Exception as e: 
            print(f"❌ KONEKSI GAGAL ke Telegram: {e}")
    return sent_messages

def edit_telegram_notification(sent_messages, new_message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token or not sent_messages: return
    for chat_id, msg_id in sent_messages.items():
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": msg_id, "text": new_message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try: 
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code != 200:
                print(f"❌ GAGAL EDIT PESAN: {res.text}")
        except: pass

def perform_api_action(token, target, action_type):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json", "X-GitHub-Api-Version": "2022-11-28"}
    try:
        if action_type == "FOLLOW":
            res = requests.put(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
            return (res.status_code == 204), "FOLLOW INJECTED" if res.status_code == 204 else f"FAILED ({res.status_code})"
    except: return False, "CONNECTION ERROR"
    return False, "UNKNOWN ERROR"

def main():
    print("Mempersiapkan token pekerja...")
    tokens_raw = os.environ.get("WORKER_TOKENS", "")
    all_tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]

    if not all_tokens or not TARGETS:
        print("❌ WORKER_TOKENS kosong. Script dihentikan.")
        sys.exit(1)

    if "," in RAW_START:
        indices = [int(x.strip()) - 1 for x in RAW_START.split(",") if x.strip().isdigit()]
        tokens_to_use = [(i, all_tokens[i]) for i in indices if 0 <= i < len(all_tokens)]
    else:
        start_idx = max(0, int(RAW_START) - 1)
        tokens_to_use = [(start_idx + i, all_tokens[start_idx + i]) for i in range(INPUT_QTY) if 0 <= start_idx + i < len(all_tokens)]

    if not tokens_to_use:
        print("❌ Tidak ada token yang tersisa untuk diproses. Script dihentikan.")
        sys.exit(1)

    selected_target = TARGETS[0]
    base_delay = (INPUT_DUR * 3600) / max(1, len(tokens_to_use))

    idx_list = [str(idx + 1) for idx, _ in tokens_to_use]
    if len(idx_list) > 3 and idx_list == [str(i) for i in range(int(idx_list[0]), int(idx_list[-1])+1)]:
        worker_info = f"{len(tokens_to_use)} Nodes (#{idx_list[0]}-#{idx_list[-1]})"
    else:
        worker_info = f"{len(tokens_to_use)} Nodes ({','.join(idx_list)})"

    print(f"📊 Menjalankan {len(tokens_to_use)} antrean dengan base delay {base_delay} detik.")

    bar_init = "░" * 10
    pre_msg = (f"{L_TOP}\n"
               f" {HEAD_INIT}\n"
               f"{L_MID}\n"
               f" ❖ <b>{LBL_ENG:<9}</b> : {ENGINE_NAME}\n"
               f" ❖ <b>{LBL_DIR:<9}</b> : {ACTION_TYPE}_INJECT\n"
               f" ❖ <b>{LBL_AST:<9}</b> : <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
               f" ❖ <b>{LBL_OPR:<9}</b> : {worker_info}\n"
               f" ❖ <b>{LBL_THR:<9}</b> : {INPUT_DUR} {TXT_HRS}\n"
               f" ❖ <b>{LBL_SYS:<9}</b> : <code>[{bar_init}] 0%</code>\n"
               f"{L_MID}\n"
               f" 🛡️ Engineered by Abie Haryatmo\n"
               f" 🤝 Powered by XianBee Tech Store\n"
               f"{L_MID}\n"
               f" <i>> {MSG_INIT_TXT}</i>\n"
               f" <code>root@xianbee-core:~$ init_sequence</code>\n"
               f"{L_BOT}")
    
    send_telegram_notification(pre_msg)

    success_count = 0

    for step_i, (real_idx, token) in enumerate(tokens_to_use):
        clean_token = token[4:] if token.startswith("ghp_") else token
        token_preview = f"{clean_token[:5]}...{clean_token[-4:]}"
        progress_pct = int(((step_i) / len(tokens_to_use)) * 100)
        bar = "▓" * (progress_pct // 10) + "░" * (10 - (progress_pct // 10))

        print(f"⚡ Memproses Node #{real_idx + 1} ({token_preview})")

        msg_live = (f"{L_TOP}\n"
                    f" {HEAD_LIVE}\n"
                    f"{L_MID}\n"
                    f" ❖ <b>{LBL_ENG:<9}</b> : {ENGINE_NAME}\n"
                    f" ❖ <b>{LBL_AST:<9}</b> : <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f" ❖ <b>{LBL_OPR:<9}</b> : #{real_idx + 1} (<code>{token_preview}</code>)\n"
                    f" ❖ <b>{LBL_QUE:<9}</b> : SEQ {step_i + 1}/{len(tokens_to_use)}\n"
                    f" ❖ <b>{LBL_SYS:<9}</b> : <code>[{bar}] {progress_pct}%</code>\n"
                    f"{L_MID}\n"
                    f" 🛡️ Engineered by Abie Haryatmo\n"
                    f" 🤝 Powered by XianBee Tech Store\n"
                    f"{L_MID}\n"
                    f" <i>> {MSG_LIVE_TXT}</i>\n"
                    f" <code>root@xianbee-core:~$ monitor_traffic</code>\n"
                    f"{L_BOT}")

        sent_msgs = send_telegram_notification(msg_live)

        success, info = perform_api_action(token, selected_target, ACTION_TYPE)
        if success: success_count += 1
        res_msg = info
        status_text = STAT_SUCC if success else STAT_FAIL

        print(f"Mendapatkan hasil GitHub API: {res_msg}")

        msg_done = (f"{L_TOP}\n"
                    f"{status_text}\n"
                    f"{L_MID}\n"
                    f" ❖ <b>{LBL_ENG:<9}</b> : {ENGINE_NAME}\n"
                    f" ❖ <b>{LBL_VAL:<9}</b> : {res_msg}\n"
                    f" ❖ <b>{LBL_AST:<9}</b> : <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f" ❖ <b>{LBL_OPR:<9}</b> : #{real_idx + 1} (<code>{token_preview}</code>)\n"
                    f" ❖ <b>{LBL_TIM:<9}</b> : {get_now_wib().strftime('%H:%M:%S WIB')}\n"
                    f"{L_MID}\n"
                    f" 🛡️ Engineered by Abie Haryatmo\n"
                    f" 🤝 Powered by XianBee Tech Store\n"
                    f"{L_MID}\n"
                    f" <i>> {MSG_SYNC_TXT}</i>\n"
                    f" <code>root@xianbee-core:~$ verify_hash</code>\n"
                    f"{L_BOT}")

        edit_telegram_notification(sent_msgs, msg_done)

        if step_i < len(tokens_to_use) - 1:
            delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
            print(f"⏳ Sleep selama {delay:.2f} detik...")
            time.sleep(delay)

    send_telegram_notification("SELESAI")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ CRASH FATAL: {e}")
        sys.exit(1)
