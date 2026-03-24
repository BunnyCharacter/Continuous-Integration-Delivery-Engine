import os #auto.py
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

print(f"🎯 Target: {TARGETS} | Aksi: {ACTION_TYPE} | Engine: {ENGINE_NAME}")

# ==========================================
# 🌍 PENGATURAN BAHASA (FULL ENGLISH)
# ==========================================
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

L_TOP = "╔═════════════════════════╗"
L_MID = "╠═════════════════════════╣"
L_BOT = "╚═════════════════════════╝"

# 🟢 FIX: TAMBAH PARAMETER SKIP_GROUP AGAR TIDAK DOUBLE DI AKHIR PESAN
def send_telegram_notification(message, skip_group=False):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_ids_raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    group_ids_raw = os.environ.get("TELEGRAM_GROUP_ID", "").strip()

    if not bot_token or not chat_ids_raw:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID kosong/tidak terbaca dari Secrets!")
        return {}

    # LIVE IDS (Channel + Buyer) - Untuk dapetin ID pesan buat diedit
    chat_ids = [chat_id.strip() for chat_id in chat_ids_raw.split(",") if chat_id.strip()]
    buyer_id = os.environ.get("BUYER_ID", "").strip()
    if buyer_id and buyer_id not in chat_ids:
        chat_ids.append(buyer_id)

    sent_messages = {}
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try:
            print(f"📡 Mencoba mengirim pesan AWAL ke Telegram Live (Chat ID: {chat_id})...")
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                sent_messages[chat_id] = res.json()['result']['message_id']
                print(f"✅ Pesan AWAL Live sukses terkirim!")
            else:
                print(f"❌ TELEGRAM API ERROR ({res.status_code}): {res.text}")
        except Exception as e: 
            print(f"❌ KONEKSI GAGAL ke Telegram: {e}")

    if not skip_group:
        # STATIC IDS (Group Admin) - Cuma dikirim saat AWAL dan AKHIR, tidak disimpan untuk diedit
        group_ids = [gid.strip() for gid in group_ids_raw.split(",") if gid.strip()]
        for gid in group_ids:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": gid, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
            try:
                print(f"📡 Mencoba mengirim pesan Statis ke Grup Admin (Chat ID: {gid})...")
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    # 🟢 FIX: SIMPAN ID GRUP AGAR BISA IKUTAN DI-EDIT SECARA ADIL!
                    sent_messages[gid] = res.json()['result']['message_id']
                    print(f"✅ Pesan Statis sukses terkirim!")
                else:
                    print(f"❌ TELEGRAM API ERROR GRUP ({res.status_code}): {res.text}")
            except Exception as e: 
                print(f"❌ KONEKSI GAGAL ke Telegram Grup: {e}")

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
                print(f"❌ GAGAL EDIT PESAN di {chat_id}: {res.text}")
            else:
                print(f"✅ Berhasil mengedit pesan di {chat_id}!")
        except Exception as e:
            print(f"❌ KONEKSI GAGAL edit pesan: {e}")

# 🟢 FUNGSI INI KEMBALI 100% UTUH SESUAI STRUKTUR ASLI LU
def send_telegram_static_only(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    group_ids_raw = os.environ.get("TELEGRAM_GROUP_ID", "").strip()
    if not bot_token or not group_ids_raw: return
    group_ids = [gid.strip() for gid in group_ids_raw.split(",") if gid.strip()]
    for gid in group_ids:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": gid, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        try:
            requests.post(url, json=payload, timeout=15)
        except: pass

# 🚀 FITUR BARU: RADAR TRIPLE CHECK (ANTI GHOSTING & ALREADY USED)
def perform_api_action(token, target, action_type):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json", "X-GitHub-Api-Version": "2022-11-28"}
    try:
        if action_type == "FOLLOW":
            # 1. CEK STATUS SEBELUMNYA (Mencegah laporan palsu kalau udah follow)
            cek_res = requests.get(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
            if cek_res.status_code == 204:
                return False, "ALREADY FOLLOWING"
            
            # 2. EKSEKUSI INJEKSI
            res = requests.put(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
            if res.status_code == 204:
                # 3. DOUBLE CHECK (Radar pendeteksi Shadowban/Ghosting dari GitHub)
                time.sleep(1.5) # Jeda agar database GitHub sinkron
                cek_lagi = requests.get(f"https://api.github.com/user/following/{target}", headers=headers, timeout=10)
                if cek_lagi.status_code == 404:
                    return False, "GHOSTED / SHADOWBANNED"
                return True, "FOLLOW INJECTED"
            return False, f"FAILED ({res.status_code})"

        elif action_type == "STARS":
            cek_res = requests.get(f"https://api.github.com/user/starred/{target}", headers=headers, timeout=10)
            if cek_res.status_code == 204:
                return False, "ALREADY STARRED"
                
            res = requests.put(f"https://api.github.com/user/starred/{target}", headers=headers, timeout=10)
            if res.status_code == 204:
                time.sleep(1.5)
                cek_lagi = requests.get(f"https://api.github.com/user/starred/{target}", headers=headers, timeout=10)
                if cek_lagi.status_code == 404:
                    return False, "GHOSTED / SHADOWBANNED"
                return True, "STAR INJECTED"
            return False, f"FAILED ({res.status_code})"

        elif action_type == "FORKS":
            res = requests.post(f"https://api.github.com/repos/{target}/forks", headers=headers, timeout=10)
            return (res.status_code in [200, 201, 202]), "FORK INJECTED" if res.status_code in [200, 201, 202] else f"FAILED ({res.status_code})"

        elif action_type == "WATCH":
            cek_res = requests.get(f"https://api.github.com/repos/{target}/subscription", headers=headers, timeout=10)
            if cek_res.status_code == 200:
                return False, "ALREADY WATCHING"
                
            payload = {"subscribed": True}
            res = requests.put(f"https://api.github.com/repos/{target}/subscription", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                time.sleep(1.5)
                cek_lagi = requests.get(f"https://api.github.com/repos/{target}/subscription", headers=headers, timeout=10)
                if cek_lagi.status_code != 200:
                    return False, "GHOSTED / SHADOWBANNED"
                return True, "WATCH INJECTED"
            return False, f"FAILED ({res.status_code})"

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
    
    # Inisialisasi counter di awal
    success_count = 0
    skipped_count = 0
    failed_count = 0
    dead_nodes_list = []
    dead_message_ids = {} 
    
    pre_msg = (f"{L_TOP}\n"
               f" {HEAD_INIT}\n"
               f"{L_MID}\n"
               f" ❖ <code>{LBL_ENG:<10} :</code> {ENGINE_NAME}\n"
               f" ❖ <code>{LBL_DIR:<10} :</code> {ACTION_TYPE}_INJECT\n"
               f" ❖ <code>{LBL_AST:<10} :</code> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
               f" ❖ <code>{LBL_OPR:<10} :</code> {worker_info}\n"
               f" ❖ <code>{LBL_THR:<10} :</code> {INPUT_DUR} {TXT_HRS}\n"
               f" ❖ <code>{LBL_SYS:<10} :</code> <code>[{bar_init}] 0%</code>\n"
               f"{L_MID}\n"
               f" 🛡️ Engineered by Abie Haryatmo\n"
               f" 🤝 Powered by XianBee Tech Store\n"
               f"{L_MID}\n"
               f" <i>> {MSG_INIT_TXT}</i>\n"
               f" <code>root@xianbee-core:~$ init_sequence</code>\n"
               f"{L_BOT}")

    # 🟢 GELEMBUNG 1: PESAN AWAL (STATIS)
    send_telegram_notification(pre_msg)

    # 🟢 GELEMBUNG 2: PESAN PROGRESS BAR (DISIMPAN UNTUK DIEDIT)
    msg_live_initial = (f"{L_TOP}\n"
                        f" {HEAD_LIVE}\n"
                        f"{L_MID}\n"
                        f" ❖ <code>{LBL_ENG:<10} :</code> {ENGINE_NAME}\n"
                        f" ❖ <code>{LBL_AST:<10} :</code> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                        f" ❖ <code>{LBL_OPR:<10} :</code> {worker_info}\n"
                        f" ❖ <code>{LBL_QUE:<10} :</code> INITIATING...\n"
                        f" ❖ <code>{LBL_SYS:<10} :</code> <code>[{bar_init}] 0%</code>\n"
                        f"{L_MID}\n"
                        f" 🟢 <code>{'SUCCESS':<10} :</code> {success_count}\n"
                        f" 🟡 <code>{'SKIPPED':<10} :</code> {skipped_count}\n"
                        f" 🔴 <code>{'FAILED':<10} :</code> {failed_count}\n"
                        f"{L_MID}\n"
                        f" 🛡️ Engineered by Abie Haryatmo\n"
                        f" 🤝 Powered by XianBee Tech Store\n"
                        f"{L_MID}\n"
                        f" <i>> Warming up injectors...</i>\n"
                        f" <code>root@xianbee-core:~$ monitor_traffic</code>\n"
                        f"{L_BOT}")

    live_message_ids = send_telegram_notification(msg_live_initial)

    # Menyaring ID agar grup dan channel/buyer bisa diedit secara terpisah
    group_ids_raw = os.environ.get("TELEGRAM_GROUP_ID", "")

    for step_i, (real_idx, token) in enumerate(tokens_to_use):
        clean_token = token[4:] if token.startswith("ghp_") else token
        token_preview = f"{clean_token[:5]}...{clean_token[-4:]}"

        progress_pct = int(((step_i + 1) / len(tokens_to_use)) * 100)
        bar = "▓" * (progress_pct // 10) + "░" * (10 - (progress_pct // 10))

        print(f"⚡ Memproses Node #{real_idx + 1} ({token_preview})")

        msg_live = (f"{L_TOP}\n"
                    f" {HEAD_LIVE}\n"
                    f"{L_MID}\n"
                    f" ❖ <code>{LBL_ENG:<10} :</code> {ENGINE_NAME}\n"
                    f" ❖ <code>{LBL_AST:<10} :</code> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f" ❖ <code>{LBL_OPR:<10} :</code> #{real_idx + 1} (<code>{token_preview}</code>)\n"
                    f" ❖ <code>{LBL_QUE:<10} :</code> SEQ {step_i + 1}/{len(tokens_to_use)}\n"
                    f" ❖ <code>{LBL_SYS:<10} :</code> <code>[{bar}] {progress_pct}%</code>\n"
                    f"{L_MID}\n"
                    f" 🟢 <code>{'SUCCESS':<10} :</code> {success_count}\n"
                    f" 🟡 <code>{'SKIPPED':<10} :</code> {skipped_count}\n"
                    f" 🔴 <code>{'FAILED':<10} :</code> {failed_count}\n"
                    f"{L_MID}\n"
                    f" 🛡️ Engineered by Abie Haryatmo\n"
                    f" 🤝 Powered by XianBee Tech Store\n"
                    f"{L_MID}\n"
                    f" <i>> {MSG_LIVE_TXT}</i>\n"
                    f" <code>root@xianbee-core:~$ monitor_traffic</code>\n"
                    f"{L_BOT}")

        # 🟢 EDIT GELEMBUNG 2 SAAT PROSES BERJALAN (Channel/Klien diedit tiap step)
        chat_buyer_ids = {k: v for k, v in live_message_ids.items() if str(k) not in group_ids_raw}
        edit_telegram_notification(chat_buyer_ids, msg_live)

        # 🟢 GRUP ADMIN DIEDIT TIAP KELIPATAN 5 EKSEKUSI
        if step_i % 5 == 0:
            group_only_ids = {k: v for k, v in live_message_ids.items() if str(k) in group_ids_raw}
            edit_telegram_notification(group_only_ids, msg_live)

        success, info = perform_api_action(token, selected_target, ACTION_TYPE)
        res_msg = info
        status_text = STAT_SUCC if success else STAT_FAIL

        if success: 
            success_count += 1
        elif "ALREADY" in res_msg:
            skipped_count += 1
            status_text = STAT_SKIP
        else:
            failed_count += 1
            # 🟢 GELEMBUNG 3 (+1 OPTIONAL): TRACKER DEAD NODES (Hanya untuk yang benar-benar error/banned)
            dead_nodes_list.append(f"#{real_idx + 1} (<code>{token_preview}</code>) - {res_msg}")

            dead_msg = (f"{L_TOP}\n"
                        f" 🔴 <b>DEAD NODES TRACKER</b>\n"
                        f"{L_MID}\n"
                        f" ❖ <code>{LBL_ENG:<10} :</code> {ENGINE_NAME}\n"
                        f" ❖ <code>{'TOTAL FAIL':<10} :</code> {len(dead_nodes_list)} Nodes\n"
                        f"{L_MID}\n")

            for d in dead_nodes_list[-100:]:
                dead_msg += f"  ❌ {d}\n"

            if len(dead_nodes_list) > 100:
                dead_msg += f"  ... (+{len(dead_nodes_list)-100} lainnya hidden)\n"

            dead_msg += f"{L_BOT}"

            if not dead_message_ids:
                dead_message_ids = send_telegram_notification(dead_msg)
            else:
                edit_telegram_notification(dead_message_ids, dead_msg)

        print(f"Mendapatkan hasil GitHub API: {res_msg}")

        msg_done = (f"{L_TOP}\n"
                    f" {status_text}\n"
                    f"{L_MID}\n"
                    f" ❖ <code>{LBL_ENG:<10} :</code> {ENGINE_NAME}\n"
                    f" ❖ <code>{LBL_VAL:<10} :</code> {res_msg}\n"
                    f" ❖ <code>{LBL_AST:<10} :</code> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                    f" ❖ <code>{LBL_OPR:<10} :</code> #{real_idx + 1} (<code>{token_preview}</code>)\n"
                    f" ❖ <code>{LBL_TIM:<10} :</code> {get_now_wib().strftime('%H:%M:%S WIB')}\n"
                    f" ❖ <code>{LBL_SYS:<10} :</code> <code>[{bar}] {progress_pct}%</code>\n"
                    f"{L_MID}\n"
                    f" 🟢 <code>{'SUCCESS':<10} :</code> {success_count}\n"
                    f" 🟡 <code>{'SKIPPED':<10} :</code> {skipped_count}\n"
                    f" 🔴 <code>{'FAILED':<10} :</code> {failed_count}\n"
                    f"{L_MID}\n"
                    f" 🛡️ Engineered by Abie Haryatmo\n"
                    f" 🤝 Powered by XianBee Tech Store\n"
                    f"{L_MID}\n"
                    f" <i>> {MSG_SYNC_TXT}</i>\n"
                    f" <code>root@xianbee-core:~$ verify_hash</code>\n"
                    f"{L_BOT}")

        # 🟢 Ngedit Gelembung 2: LIVE PROGRESS (Setelah Node Kelar)
        edit_telegram_notification(chat_buyer_ids, msg_done)

        if step_i < len(tokens_to_use) - 1:
            delay = random.uniform(base_delay * 0.8, base_delay * 1.2)
            print(f"⏳ Sleep selama {delay:.2f} detik...")
            time.sleep(delay)

    dead_info = ""
    if dead_nodes_list:
        dead_info = f" ❖ <code>{'DEAD NODES':<10} :</code>\n"
        for d in dead_nodes_list[:10]:
            dead_info += f"     - {d}\n"
        if len(dead_nodes_list) > 10:
            dead_info += f"     - ... (+{len(dead_nodes_list)-10} lainnya hidden)\n"
        dead_info += f"{L_MID}\n"

    msg_final = (f"{L_TOP}\n"
                 f" {HEAD_TERM}\n"
                 f"{L_MID}\n"
                 f" ❖ <code>{LBL_ENG:<10} :</code> {ENGINE_NAME}\n"
                 f" ❖ <code>{LBL_DIR:<10} :</code> {ACTION_TYPE}_INJECT\n"
                 f" ❖ <code>{LBL_AST:<10} :</code> <a href='https://github.com/{selected_target}'>{selected_target}</a>\n"
                 f" ❖ <code>{'STATUS':<10} :</code> ROUTINE COMPLETE\n"
                 f" ❖ <code>{TXT_SUCCESS:<10} :</code> {success_count}/{len(tokens_to_use)} Nodes\n"
                 f"{L_MID}\n"
                 f" 🟢 <code>{'SUCCESS':<10} :</code> {success_count}\n"
                 f" 🟡 <code>{'SKIPPED':<10} :</code> {skipped_count}\n"
                 f" 🔴 <code>{'FAILED':<10} :</code> {failed_count}\n"
                 f"{L_MID}\n"
                 f"{dead_info}"
                 f" 🛡️ Engineered by Abie Haryatmo\n"
                 f" 🤝 Powered by XianBee Tech Store\n"
                 f"{L_MID}\n"
                 f" <i>> {MSG_END_TXT}</i>\n"
                 f" <code>root@xianbee-core:~$ exit 0</code>\n"
                 f"{L_BOT}")

    # ===============================================
    # 🟢 GELEMBUNG 4 (PALING BAWAH): TERMINATED
    # ===============================================
    # Bikin bubble baru untuk Channel & Buyer (Skip grup biar tidak double)
    send_telegram_notification(msg_final, skip_group=True)

    # 🟢 EDIT PESAN TERAKHIR KALI DI CHANNEL/KLIEN
    # (Kode dipertahankan, kita ubah progress bar jadi 100% final agar tidak berubah jadi Terminated)
    edit_telegram_notification(live_message_ids, msg_done)

    # 🟢 KIRIM PESAN BARU KE GRUP ADMIN SEBAGAI PENUTUP
    # (Kode lu tetap utuh dan dipanggil sesuai aslinya!)
    send_telegram_static_only(msg_final)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ CRASH FATAL: {e}")
        sys.exit(1)
