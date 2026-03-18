import os
import requests
import time
import sys
import random

# Mengambil parameter dari environment variables (Kiriman Telegram -> GitHub YAML)
TARGET_REPO = os.environ.get("TARGET_REPOS", "").strip()
INPUT_QTY = int(os.environ.get("INPUT_QTY", 0))
INPUT_DUR = float(os.environ.get("INPUT_DUR", 0))
INPUT_START = int(os.environ.get("INPUT_START", 1))

def send_telegram_notification(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_ids_raw: return
    chat_ids = [c.strip() for c in chat_ids_raw.split(",") if c.strip()]
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try: requests.post(url, json=payload, timeout=10)
        except: pass

def do_star(token, repo):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        s_res = requests.put(f"https://api.github.com/user/starred/{repo}", headers=headers, timeout=10)
        if s_res.status_code == 204: return True, "⭐ <b>STAR SUCCESS</b>"
        return False, f"❌ <b>FAILED</b> ({s_res.status_code})"
    except: return False, "❌ <b>ERROR</b>"

def main():
    if not TARGET_REPO or INPUT_QTY == 0:
        print("Parameter tidak lengkap. Hibernasi...")
        sys.exit(0)

    # 1. Ambil semua token dari Secrets GitHub
    tokens_raw = os.environ.get("WORKER_TOKENS", "")
    all_tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]

    # 2. SLICING: Pilih token berdasarkan urutan yang lu minta di Telegram
    start_idx = INPUT_START - 1 # Karena array python mulai dari 0
    end_idx = start_idx + INPUT_QTY
    
    # Amankan kalau lu minta token lebih banyak dari sisa stok di secrets
    tokens_to_use = all_tokens[start_idx:end_idx]
    
    if not tokens_to_use:
        send_telegram_notification(f"❌ <b>EXECUTION ABORTED</b>\nToken habis atau urutan {INPUT_START} tidak tersedia di Secrets.")
        sys.exit(1)

    # 3. MATEMATIKA PACING (Menghitung delay agar pas dengan durasi jam lu)
    # Total Detik = Durasi (Jam) * 3600
    base_delay = (INPUT_DUR * 3600) / len(tokens_to_use)

    pre_msg = (f"╔════════════════════╗\n"
               f" ⚙️ <b>CLOUD WORKER AWAKE</b>\n"
               f"╚════════════════════╝\n\n"
               f"<i>Mode: DYNAMIC STARS INJECTION</i>\n"
               f"🎯 <b>Target:</b> <a href='https://github.com/{TARGET_REPO}'>{TARGET_REPO}</a>\n"
               f"🤖 <b>Tokens:</b> Memakai urutan #{INPUT_START} s/d #{start_idx + len(tokens_to_use)}\n"
               f"⏳ <b>Pacing:</b> {INPUT_DUR} Jam (~{int(base_delay)} dtk/node)\n\n"
               f"🛡️ <i>Engineered by Abie Haryatmo</i>")
    send_telegram_notification(pre_msg)

    success_count = 0
    for i, token in enumerate(tokens_to_use):
        token_preview = f"{token[:8]}...{token[-4:]}"
        print(f"Deploying Node (Secrets Index #{start_idx + i + 1}): {token_preview}")
        
        is_success, msg = do_star(token, TARGET_REPO)
        if is_success: success_count += 1
        print(f"Result: {msg}")
        
        # Delay aman sesuai request lu di telegram
        if i < len(tokens_to_use) - 1:
            actual_delay = random.uniform(base_delay * 0.8, base_delay * 1.2) # Tambah Jitter 20%
            print(f"Stealth Pacing: Delaying {int(actual_delay)} seconds...")
            time.sleep(actual_delay)

    final_msg = (f"╔════════════════════╗\n"
                 f" ✅ <b>MISSION ACCOMPLISHED</b>\n"
                 f"╚════════════════════╝\n\n"
                 f"<b>Action:</b> STARS INJECTION\n"
                 f"<b>Target:</b> <a href='https://github.com/{TARGET_REPO}'>{TARGET_REPO}</a>\n"
                 f"<b>Success:</b> {success_count}/{len(tokens_to_use)} Nodes\n\n"
                 f"🛡️ <i>Engineered by Abie Haryatmo</i>")
    send_telegram_notification(final_msg)

if __name__ == "__main__":
    main()
