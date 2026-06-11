import os
import json
import asyncio
from aiohttp import web, ClientSession

# 1. Fetch Environment Variable from Render Dashboard
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

async def send_message(session, chat_id, text):
    url = f"{API_URL}sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        async with session.post(url, data=payload) as resp:
            await resp.read()
    except Exception as e:
        print(f"Error sending message: {e}")

# 2. Text Counting Engine
def calculate_metrics(text):
    char_with_spaces = len(text)
    char_no_spaces = len(text.replace(" ", "").replace("\n", ""))
    
    words_list = text.split()
    word_count = len(words_list)
    
    if word_count == 0:
        return "⚠️ Please send a message containing actual text or sentences to analyze!"
        
    paragraphs_list = [p for p in text.split("\n") if p.strip()]
    paragraph_count = len(paragraphs_list) if paragraphs_list else 1
    
    # Calculate reading time (200 words/min)
    reading_seconds = int((word_count / 200) * 60)
    if reading_seconds < 60:
        reading_time = f"{reading_seconds} sec"
    else:
        minutes = reading_seconds // 60
        seconds = reading_seconds % 60
        reading_time = f"{minutes} min {seconds} sec"

    return (
        f"📝 **WordCounter Dashboard Report**\n"
        f"--- \n"
        f"🔢 **Total Words:** `{word_count}`\n\n"
        f"🔤 **Characters (with spaces):** `{char_with_spaces}`\n"
        f"🚫 **Characters (no spaces):** `{char_no_spaces}`\n\n"
        f"📉 **Paragraphs:** `{paragraph_count}`\n"
        f"⏱️ **Est. Reading Time:** `{reading_time}`\n"
        f"--- \n"
        f"💡 _Tip: Paste your draft or homework essays here to monitor limits instantly!_"
    )

# 3. Continuous Polling Loop
async def bot_polling(app):
    offset = 0
    print("WordCounter Pro background worker is active...")
    
    async with ClientSession() as session:
        while True:
            try:
                url = f"{API_URL}getUpdates"
                params = {"offset": offset, "timeout": 30}
                
                async with session.get(url, params=params, timeout=35) as response:
                    res_json = await response.json()
                    
                    if res_json.get("ok") and res_json.get("result"):
                        for update in res_json["result"]:
                            offset = update["update_id"] + 1
                            message = update.get("message", {})
                            chat_id = message.get("chat", {}).get("id")
                            text = message.get("text", "").strip()
                            
                            if not chat_id or not text:
                                continue
                                
                            if text.startswith("/start"):
                                welcome = (
                                    "📝 **Welcome to WordCounter Pro!**\n\n"
                                    "Simply send or paste any text or document here, and I will compile an instant metrics dashboard for you!"
                                )
                                await send_message(session, chat_id, welcome)
                            else:
                                report_results = calculate_metrics(text)
                                await send_message(session, chat_id, report_results)
                                
            except Exception as e:
                print(f"Polling loop stutter: {e}")
            await asyncio.sleep(1)

# 4. Render Web Server Bridge Setup
async def handle_health(request):
    return web.Response(text="WordCounter Pro Engine Running Successfully")

async def start_background_tasks(app):
    app['bot_task'] = asyncio.create_task(bot_polling(app))

async def cleanup_background_tasks(app):
    app['bot_task'].cancel()
    await app['bot_task']

def make_app():
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app

if __name__ == "__main__":
    app = make_app()
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host='0.0.0.0', port=port)
