import asyncio
import httpx
import json
import os
from datetime import datetime
import jdatetime

TOKEN = TOKEN = "1217217814:r7Sj41AZB4LJo9USK3xkWululeRBtY6ydAI"
API = f"https://tapi.bale.ai/bot{TOKEN}"
DB_FILE = "valves.json"

# ------------------ دیتابیس ساده ------------------
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# ------------------ توابع کمکی ------------------
async def send_msg(client, chat_id, text):
    await client.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text})

# ------------------ چک کردن یادآورها ------------------
async def check_reminders(client):
    db = load_db()
    today = jdatetime.date.today()
    
    for chat_id, valves in db.items():
        for v in valves:
            try:
                # تبدیل تاریخ به شمسی
                y, m, d = map(int, v["next_cal"].split("/"))
                next_date = jdatetime.date(y, m, d)
                days_left = (next_date - today).days
                
                # اگه ۷ روز یا کمتر مونده بود
                if 0 <= days_left <= 7:
                    msg = f"⚠️ یادآور:\nسیفتی ولو {v['tag']}\nتاریخ کالیبراسیون: {v['next_cal']}\nفقط {days_left} روز مونده!"
                    await send_msg(client, int(chat_id), msg)
                    print(f"🔔 یادآور فرستاده شد برای {v['tag']} (چت {chat_id})")
            except Exception as e:
                print(f"خطا در چک تاریخ: {e}")

# ------------------ حلقه اصلی ------------------
async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{API}/getMe")
        print(f"✅ وصل شدم به: @{r.json()['result']['username']}")
        
        # پاک کردن پیام‌های قدیمی
        r = await client.get(f"{API}/getUpdates")
        offset = 0
        if r.json().get("ok") and r.json()["result"]:
            offset = r.json()["result"][-1]["update_id"] + 1
        
        print("⏳ ربات آماده است. منتظر پیام...")
        
        # حالت‌های کاربر (برای ثبت مرحله‌به‌مرحله)
        user_states = {}
        last_reminder_check = datetime.now()

        while True:
            try:
                # ۱. چک کردن یادآورها (هر ۱ دقیقه)
                if (datetime.now() - last_reminder_check).seconds > 60:
                    await check_reminders(client)
                    last_reminder_check = datetime.now()

                # ۲. گرفتن پیام‌های جدید از بله
                r = await client.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 10})
                data = r.json()
                
                if data.get("ok") and data["result"]:
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        if "message" not in update: continue
                        
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "").strip()
                        
                        # ---------------- دستور /start ----------------
                        if text == "/start":
                            await send_msg(client, chat_id, "سلام 👋\nمن ربات یادآور کالیبراسیون هستم.\n\nدستورات:\n/add - افزودن شیر جدید\n/list - لیست شیرها")
                        
                        # ---------------- دستور /list ----------------
                        elif text == "/list":
                            db = load_db()
                            my_valves = db.get(str(chat_id), [])
                            if not my_valves:
                                await send_msg(client, chat_id, "📭 هیچ شیری ثبت نکردی.")
                            else:
                                txt = "📋 لیست شیرهای شما:\n\n"
                                for v in my_valves:
                                    txt += f"🔹 تگ: {v['tag']}\n📅 کالیبراسیون بعدی: {v['next_cal']}\n\n"
                                await send_msg(client, chat_id, txt)
                        
                        # ---------------- دستور /add ----------------
                        elif text == "/add":
                            user_states[chat_id] = {"step": "waiting_tag"}
                            await send_msg(client, chat_id, "🏷️ شماره تگ شیر (مثلاً 10001) را وارد کنید:")
                        
                        # ---------------- دریافت مراحل ثبت ----------------
                        elif chat_id in user_states:
                            state = user_states[chat_id]
                            
                            if state["step"] == "waiting_tag":
                                state["tag"] = text
                                state["step"] = "waiting_date"
                                await send_msg(client, chat_id, "📅 تاریخ کالیبراسیون بعدی را وارد کنید (مثلاً 1406/08/01):")
                            
                            elif state["step"] == "waiting_date":
                                # ذخیره در دیتابیس
                                db = load_db()
                                cid = str(chat_id)
                                if cid not in db: db[cid] = []
                                
                                db[cid].append({
                                    "tag": state["tag"],
                                    "next_cal": text
                                })
                                save_db(db)
                                
                                await send_msg(client, chat_id, f"✅ شیر {state['tag']} با تاریخ {text} ثبت شد.")
                                del user_states[chat_id]
                        
                        # ---------------- دستور ناشناخته ----------------
                        else:
                            await send_msg(client, chat_id, "دستور نامشخص. از /start استفاده کنید.")
            
            except Exception as e:
                print(f"❌ خطا: {e}")
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())