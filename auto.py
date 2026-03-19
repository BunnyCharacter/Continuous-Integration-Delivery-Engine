import os
import requests
import time
import sys
import random
from datetime import datetime, timedelta, timezone

# Fungsi untuk mengambil waktu WIB untuk laporan di Telegram
def get_now_wib():
    tz_wib = timezone(timedelta(hours=7))
    return datetime.now(tz_wib)

# ==========================================
# 🎯 TAHAP 1: MENGAMBIL SINYAL DARI GITHUB ACTIONS
# ==========================================
# Menangkap sinyal ACTION_TYPE dari file .yml (Apakah ini minta STARS, FORKS, dll?)
ACTION_TYPE = os.environ.get("ACTION_TYPE", "").strip().upper()
if not ACTION_TYPE:
    print("❌ CRITICAL ERROR: Sinyal 'ACTION_TYPE' tidak ditemukan di file .yml!")
    sys.exit(1)

# Menangkap sinyal Bahasa dari Bot Telegram lu
raw_lang = os.environ.get("INPUT_LANG", "id").strip().lower()
LANG = raw_lang if raw_lang in ["id", "en"] else "id"

print("="*50)
print("🚀 XIANBEE CLOUD WORKER ENGINE STARTING")
print("="*50)
print(f"🎯 MODE OPERASI : {ACTION_TYPE}")
print(f"🗣️ BAHASA UI    : {LANG.upper()}")
print("="*50)

# ==========================================
# 🌍 TAHAP 2: KAMUS BAHASA (BILINGUAL)
# ==========================================
# Ini yang mengatur agar loading screen Telegram berubah sesuai bahasa yang dipilih Klien
UI = {
    "id": {
        "live": "EKSEKUSI LIVE",
        "checking": "Mengecek status worker...",
        "deploying": f"Mengirim protokol {ACTION_TYPE}...",
        "skipped": f"⚠️ TUGAS DILEWATI (Sudah {ACTION_TYPE.lower()} sebelumnya)",
        "target_repo": "Target Repo",
        "target_user": "Target User",
        "node": "Node",
        "progress": "Proses",
        "status": "{current} dari {total} Selesai",
        "success": "DEPLOYMENT BERHASIL",
        "time": "Waktu",
        "accomplished": "MISI SELESAI",
        "awake": "PEKERJA CLOUD AKTIF"
    },
    "en": {
        "live": "LIVE EXECUTION",
        "checking": "Checking worker status...",
        "deploying": f"Deploying {ACTION_TYPE} protocol...",
        "skipped": f"⚠️ TASK SKIPPED (Already executed {ACTION_TYPE.lower()})",
        "target_repo": "Target Repo",
        "target_user": "Target User",
        "node": "Node",
        "progress": "Progress",
        "status": "{current} of {total} Completed",
        "success": "DEPLOYMENT SUCCESS",
        "time": "Time",
        "accomplished": "MISSION ACCOMPLISHED",
        "awake": "CLOUD WORKER AWAKE"
    }
}
T = UI.get(LANG, UI["id"])

# ==========================================
# 🎯 TAHAP 3: MENYIAPKAN TARGET & KUOTA
# ==========================================
# Cek apakah ini minta Follower (Target User) atau yang lain (Target Repo)
if ACTION_TYPE == "FOLLOW":
    RAW_TARGETS = os.environ.get("TARGET_USERS", "")
    TARGET_LABEL = T["target_user"]
else:
    RAW_TARGETS = os.environ.get("TARGET_REPOS", "")
    TARGET_LABEL = T["target_repo"]

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

# ==========================================
# 📱 TAHAP 4: FUNGSI KOMUNIKASI KE TELEGRAM
# ==========================================
def send_telegram_notification(message):
    """Kirim pesan baru ke Telegram (Untuk Header Awal & Akhir)"""
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
    """Edit pesan yang sudah ada di Telegram (Untuk Update Loading Bar)"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token or not sent_messages: return
    for chat_id, msg_id in sent_messages.items():
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": msg_id, "text": new_message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try: requests.post(url, json=payload, timeout=15)
        except: pass

# ==========================================
# 🧠 TAHAP 5: FUNGSI INTI GITHUB API
# ==========================================
def check_existing(token, target, action_type):
    """Fungsi Pengecekan: Memastikan token belum pernah melakukan aksi ini ke target."""
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
    """Fungsi Penembak: Mengirim sinyal asli ke GitHub berdasarkan ACTION_TYPE."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json", "X-GitHub-Api-Version": "2022-11-28"}
    try:
        if action_type == "STARS":
            res = requests.put(f"https://api.github.com/user/starred/{target}", headers=headers, timeout=10)
            return (res.status_code == 204), f"Code: {res.status_code}"
        elif action_type == "FORKS":
            res = requests.post(f"https://api.github.com/repos/{target}/forks", headers=headers, timeout=10)
            return (res.status_code in [201, 202]), f"Code: {res.status_code}"
        elif action_type == "WATCH":
            res = requests.put(f"https://api.github.com/repos/{target}/subscription", headers=headers, json={"subscribed": True}, timeout=10)
            return (res.status_code == 200), f"Code: {res.status_code}"
        elif action_type == "FOLLOW":
            res = requests.put(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
            return (res.status_code == 204), f"Code: {res.status_code}"
    except: return False, "Error Connection"
    return False, "Unknown Error"

# ==========================================
# 🚀 TAHAP 6: FUNGSI EKSEKUSI UTAMA (MAIN)
# ==========================================
def main():
    # 1. Menarik & Memotong Token Sesuai Pesanan
    tokens_raw = os.environ.get("WORKER_TOKENS", "")
    all_tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]
    
    start_idx = INPUT_START - 1
    tokens_to_use = all_tokens[start_idx:start_idx + INPUT_QTY]
    
    if not tokens_to_use or not TARGETS:
        print("❌ ERROR: Tokens atau Target kosong. Exiting...")
        sys.exit(1)

    selected_target = TARGETS[0]
    # Rumus Delay: Total Durasi (jam) diubah ke detik, lalu dibagi jumlah aksi
    base_delay = (INPUT_DUR * 3600) / max(1, len(tokens_to_use))
    
    # 2. Mengirim Notifikasi "Mesin Bangun" ke Telegram
    pre_msg = (f"╔════════════════════╗\n"
               f" ⚙️ <b>{T['awake']}</b>\n"
               f"╚════════════════════╝\n\n"
               f"<i>Mode: {ACTION_TYPE} INJECTION</i>\n"
               f"🎯 <b>Target:</b> {selected_target}\n"
               f"🤖 <b>Nodes :</b> {len(tokens_to_use)} Workers\n"
               f"⏳ <b>Pacing:</b> {INPUT_DUR} Hours\n\n"
               f"🛡️ <i>Engineered by Abie Haryatmo</i>")
    send_telegram_notification(pre_msg)

    success_count = 0
    
    # 3. Proses Looping: Nembak target satu per satu pakai token yang beda
    for i, token in enumerate(tokens_to_use):
        token_preview = f"{token[:8]}...{token[-4:]}"
        print(f"[{i+1}/{len(tokens_to_use)}] Processing Node: {token_preview}")
        
        # --- UI LOADING SCREEN (Sedang Menyerang) ---
        progress_pct = int((i / len(tokens_to_use)) * 100)
        bar = "█" * (progress_pct // 10) + "░" * (10 - (progress_pct // 10))
        
        msg_live = (f"╔════════════════════╗\n   ⏳ <b>{T['live']}</b>\n╚════════════════════╝\n\n"
                    f"🔄 <i>{T['deploying']}</i>\n"
                    f"══════════════════════\n"
                    f"🎯 <b>{TARGET_LABEL} :</b> {selected_target}\n"
                    f"🤖 <b>{T['node']}   :</b> #{start_idx + i + 1} ({token_preview})\n"
                    f"📊 <b>{T['progress']} :</b> <code>[{bar}] {progress_pct}%</code>\n"
                    f"🔢 <b>Status :</b> {T['status'].format(current=i, total=len(tokens_to_use))}\n\n"
                    f"🛡️ <i>Engineered by Abie Haryatmo</i>")
        
        sent_msgs = send_telegram_notification(msg_live)

        # --- EKSEKUSI API GITHUB ---
        is_skipped = check_existing(token, selected_target, ACTION_TYPE)
        if is_skipped:
            res_msg = T["skipped"]
            success_count += 1 # Dihitung sukses karena tujuannya memang sudah tercapai
            print(f" -> SKIPPED (Already executed)")
        else:
            success, info = perform_api_action(token, selected_target, ACTION_TYPE)
            if success: success_count += 1
            res_msg = f"✅ SUCCESS: {info}" if success else f"❌ FAILED: {info}"
            print(f" -> {res_msg}")

        # --- UI LOADING SCREEN (Hasil Eksekusi) ---
        final_pct = int(((i + 1) / len(tokens_to_use)) * 100)
        final_bar = "█" * (final_pct // 10) + "░" * (10 - (final_pct // 10))
        selected_quote = random.choice(QUOTES) # Mengambil kata mutiara acak
        
        msg_done = (f"╔════════════════════╗\n   🚀 <b>{T['success']}</b>\n╚════════════════════╝\n\n"
                    f"{res_msg}\n"
                    f"══════════════════════\n"
                    f"🎯 <b>{TARGET_LABEL} :</b> {selected_target}\n"
                    f"🤖 <b>{T['node']}   :</b> #{start_idx + i + 1}\n"
                    f"📊 <b>{T['progress']} :</b> <code>[{final_bar}] {final_pct}%</code>\n"
                    f"⏱️ <b>{T['time']}   :</b> {get_now_wib().strftime('%H:%M:%S WIB')}\n\n"
                    f"#CloudAutomation\n"
                    f"<i>{selected_quote}</i>")
        
        edit_telegram_notification(sent_msgs, msg_done)

        # --- JEDA WAKTU (Pacing Aman) ---
        if i < len(tokens_to_use) - 1:
            delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
            print(f" -> Sleeping for {int(delay)} seconds...")
            time.sleep(delay)

    # 4. Mengirim Laporan Akhir Pesanan
    final_report = (f"╔════════════════════╗\n"
                    f" ✅ <b>{T['accomplished']}</b>\n"
                    f"╚════════════════════╝\n\n"
                    f"<b>Action:</b> {ACTION_TYPE} INJECTION\n"
                    f"<b>Target:</b> {selected_target}\n"
                    f"<b>Result:</b> {success_count}/{len(tokens_to_use)} Success\n\n"
                    f"🛡️ <i>Engineered by Abie Haryatmo</i>")
    send_telegram_notification(final_report)
    print("="*50)
    print("✅ EXECUTION COMPLETE!")

if __name__ == "__main__":
    main()
