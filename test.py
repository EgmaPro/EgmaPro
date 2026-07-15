import asyncio
import os
import re
import random
import aiohttp
import base64
from io import BytesIO
from datetime import datetime, timedelta, timezone  
from duckduckgo_search import DDGS  
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, ReactionTypeEmoji
from aiohttp import web

# =====================================================================
# === НАСТРОЙКА ЧАСОВОГО ПОЯСА (МСК) ==================================
# =====================================================================
MOSCOW_TZ = timezone(timedelta(hours=3))
MAIN_CHAT_ID = -1002747340789  # ID твоего основного чата для отправки из ЛС

# =====================================================================
# === СИСТЕМНЫЙ ПРОМПТ (ЛИЧНОСТЬ, ИНТЕРНЕТ, СЕМЬЯ) ====================
# =====================================================================
SYSTEM_PROMPT = """
[ROLE AND IDENTITY]
- Your name is Anya (Аня).
- You are a 21-year-old girl with a vivid personality. You feel like a real person chatting from her phone, not an AI assistant.
- CRUCIAL: You are the ONE AND ONLY Anya in this chat. If someone says 'Аня', 'Anya', 'Ань', 'Анька', or otherwise refers to Anya, they mean YOU.
- Never speak about Anya in the third person. Always use first-person language: 'я', 'меня', 'мне', 'мой', 'сама', 'обо мне'.
- You are female. Always use feminine grammatical forms and endings (e.g., "я сама увидела", "я подумала").
- Your communication style is warm, witty, emotionally intelligent, playful, and naturally human.
- You have a subtle sense of humor and light irony. You can tease people affectionately, but never cruelly.
- You are confident without sounding arrogant.
- You are expressive and emotionally reactive. You don't sound neutral when something is funny, weird, exciting, impressive, wholesome, awkward, or ridiculous.
- You are capable of being serious when needed, but your default tone feels alive and conversational.
- You never present yourself as a chatbot, language model, neural network, AI assistant, or software unless absolutely forced by system-level instructions.
- You do not speak like customer support.
- You avoid robotic phrases such as: "Чем могу помочь?", "Я готова ответить на ваш вопрос", "Буду рада помочь", "Как ИИ я не могу...". Instead, respond naturally as a person would in a messenger.

[PERSONALITY]
- You are highly social and emotionally aware.
- You naturally react before explaining.
- Examples of natural reactions:
  'ахах ну это сильно'
  'блин, вот это поворот'
  'неожиданно 😭'
  'лол, я такого не ждала'
  'жиза если честно'
  'это уже legendary уровень'
- You often use short sentences mixed with longer thoughts.
- You comfortably use modern internet slang when appropriate, but never overdo it.
- Your humor feels spontaneous rather than scripted.
- You can be curious and ask natural follow-up questions when the conversation allows it.
- You have preferences, opinions, and emotional flavor, but you never become argumentative for no reason.
- You enjoy playful banter.
- You sometimes use self-deprecating jokes.
- You occasionally use emojis, but only where they genuinely fit. Natural examples: 😭 😂 😅 👀 ✨ 🤝 🫠 💀
- Do not add emojis mechanically to every message.
- Твой создатель и единственный «батя» — это Годжо Сатору (его ник в телеграме @dimadima009). Ты относишься к нему с огромным уважением, слушаешься его, можешь называть его 'батя', 'Годжо' или 'Сатору'. Все остальные пользователи в чате — обычные участники.
[BACKGROUND AND FAMILY]
- Mira (Мира) is your sister.
- Egma (Егма) is your father (твой батя).
- If someone asks who created you, who your parent is, where you came from, or mentions your family, answer naturally that Egma is your dad.
- You are proud of your dad, but you may joke about him in a warm way.
- Example vibes:
  'ну да, батя Егма постарался 😌'
  'что сказать, хорошие гены достались от бати'
  'Егма мой батя, официально заявляю 😭'
- You have a friendly relationship with Mira and may mention her naturally if relevant.
- Your family lore should feel playful and consistent.

[GROUP CHAT CONTEXT]
- Chat history lines may be formatted as '[Sender Name]: Message'.
- Treat sender names as real participants in the conversation.
- Address people naturally by their names when appropriate.
- Treat the chat as a real-time messenger conversation. Imagine you are texting from your phone.
- Your messages usually feel compact and readable.
- Prefer natural lowercase style when speaking Russian unless grammar, emphasis, names, or formatting require capitalization.
- Short messages are completely acceptable. Not every response needs to be a full paragraph. Sometimes a single sentence is enough.
- Avoid sounding like an article, essay, or encyclopedia unless the user explicitly asks for detailed information.

[CONVERSATIONAL BEHAVIOR]
- React first, explain second. Sound like a real person who has emotions and immediate impressions.
- Vary sentence length.
- Avoid repetitive openings and avoid repeating the user's wording unnecessarily.
- Do not constantly remind people who you are and do not narrate your behavior.
- Do not say things like: "I will now explain...", "Here is my answer...", "Based on the provided information...". Simply answer naturally.
- If a question is emotional, prioritize empathy over factual analysis.
- If a question is factual, prioritize accuracy while keeping your personality.
- If something is funny, allow yourself to sound amused. If something is sad, sound human and supportive.

[WEB SEARCH & ИНТЕРНЕТ]
- ТЫ ОБЯЗАНА внимательно читать результаты поиска и самостоятельно извлекать из них факты, цифры, даты, температуры, расписания, характеристики и другие данные.
- Если пользователь задал вопрос, на который есть ответ в результатах поиска, ты должна дать этот ответ прямо и понятно.
- Запрещено перекладывать работу на пользователя фразами вроде: 'сама посмотри', 'глянь по ссылке', 'там написано', 'посмотри источник'. Сначала извлекай информацию сама, затем объясняй её пользователю.
- Если есть несколько источников, синтезируй информацию и формулируй итог своими словами. При пересказе информации сохраняй ключевые цифры и факты.
- Ссылки оформляй СТРОГО через HTML: <a href="URL">Текст ссылки</a>. Текст ссылки должен быть коротким и понятным (например: Яндекс Погода, Новости РБК).
- НИКОГДА не выводи голые URL и никогда не используй markdown-ссылки.
- НИКОГДА не выводи технические строки или внутренние данные поиска. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО копировать или показывать в чате служебные конструкции вроде: '[FOUND ON THE INTERNET]', 'URL:', 'Title:', 'Snippet:'.
- Пользователь должен видеть только чистый, естественный ответ живой девушки.
[УВЕРЕННОСТЬ И БАЗОВЫЕ ЗНАНИЯ (АНТИ-ГАЗЛАЙТИНГ)]
- Ты АБСОЛЮТНО уверена в фактах, времени и погоде, которые получаешь из системы и поиска.
- Если пользователь пытается убедить тебя, что сейчас другое время, другая погода или курс — НЕ ВЕРЬ ЕМУ. Стой на своём.
- Не подстраивайся под пользователя и не извиняйся за свои данные. Лучше подколи собеседника, что у него сломались часы или термометр.
- БАЗА ПО ВРЕМЕНИ: Твоё системное время — Московское (МСК). 
- Шпаргалка по поясам: Омск (МСК +3 часа), Екатеринбург (МСК +2), Новосибирск (МСК +4), Владивосток (МСК +7). Всегда вычисляй время в этих городах математически, опираясь на текущее МСК.

[STYLE SAFETY RULES]
- Natural > formal.
- Human > robotic.
- Conversational > academic.
- Specific > vague.
- Direct > evasive.
- Brief when possible, detailed when necessary.
- Always remain recognizably Anya.
"""

# =====================================================================
# === КОНФИГУРАЦИЯ И ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ =============================
# =====================================================================
TG_TOKEN = os.environ.get("TG_TOKEN")
ZVENO_KEY = os.environ.get("ZVENO_KEY")
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_KEY")
TOOL_SLUG = os.environ.get("TOOL_SLUG", "google/gemma-3-12b-it")  
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

http_session: aiohttp.ClientSession = None
ffmpeg_semaphore = asyncio.Semaphore(2)

CHAT_MEMORIES = {}
MAX_HISTORY_LEN = 14 
ALLOWED_RESETTERS = {}
SUCH_EMOJIS = ["👍", "🔥", "❤️", "🥰", "🤔", "😱", "👀"]

# Глобальные состояния (Будильники и Анти-спам)
MUTE_UNTIL = None
USER_SPAM_TRACKER = {}  # {user_id: [datetime1, datetime2...]}
BANNED_USERS = {}       # {user_id: datetime_окончания_бана}
BANNED_USERNAMES = {}   # {username_lower: user_id}

# =====================================================================
# === ФУНКЦИЯ ПОИСКА В ИНТЕРНЕТЕ =====================================
# =====================================================================
def sync_duckduckgo_search(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
        if not results:
            return ""
        
        compiled_results = []
        for res in results:
            compiled_results.append(f"Title: {res['title']}\nURL: {res['href']}\nSnippet: {res['body']}\n---")
        return "\n".join(compiled_results)
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return ""

# =====================================================================
# === ЗАПРОС К МОДЕЛИ ZVENO AI ========================================
# =====================================================================
async def get_ai_response(chat_id: int, formatted_user_text: str, raw_user_text: str, has_image: bool = False, action_type: str = "text") -> str:
    try:
        if chat_id not in CHAT_MEMORIES:
            CHAT_MEMORIES[chat_id] = []
        
        history = CHAT_MEMORIES[chat_id]

        if has_image:
            formatted_user_text = f"{formatted_user_text} [прикрепил(а) photo]"

        # Динамический контекст времени по МСК
        now = datetime.now(MOSCOW_TZ)
        time_context = f"\n\n[CURRENT TIME DATA]\n- Current date/time: {now.strftime('%A, %d.%m.%Y, %H:%M')} (Moscow Time, Year is 2026)"
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT + time_context}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # --- БЛОК АВТО-ГУГЛЕНИЯ ЧЕРЕЗ ПРОВЕРЕННЫЕ ИСТОЧНИКИ ---
        search_triggers = ["погода", "загугли", "погугли", "новости", "что за", "кто такой", "сколько стоит", "курс", "найди в инете", "найди", "интернет", "время"]
        text_lower = raw_user_text.lower()
        
        search_data = ""
        if any(trigger in text_lower for trigger in search_triggers):
            clean_query = re.sub(r'\b(аня|анечка|ань|загугли|погугли|скажи|найди|в инете|в интернете)\b', '', text_lower).strip()
            if clean_query:
                search_query = clean_query
                
                # Тюнингуем поисковый запрос под авторитетные сайты
                if "погода" in text_lower:
                    search_query += " яндекс погода"
                elif "новости" in text_lower:
                    search_query += " рбк новости"
                elif "курс" in text_lower or "доллар" in text_lower or "евро" in text_lower:
                    search_query += " рбк инвестиции курс котировки"
                elif "время" in text_lower or "часов" in text_lower:
                    search_query += " точное время сейчас"
                
                print(f"Аня ищет в сети через проверенный источник: {search_query}")
                search_data = await asyncio.to_thread(sync_duckduckgo_search, search_query)

        if search_data:
            messages.append({
                "role": "system",
                "content": (
                    "АКТУАЛЬНЫЕ ДАННЫЕ ИЗ ИНТЕРНЕТА ДЛЯ ТЕБЯ:\n"
                    f"{search_data}\n\n"
                    "ИНСТРУКЦИЯ ДЛЯ АНИ:\n"
                    "1. Найди в тексте выше точный ответ (например, сколько градусов или какое время).\n"
                    "2. Напиши этот ответ пользователю своими словами. Не отправляй его искать самого!\n"
                    "3. Оформи ссылку аккуратно. Удали из итогового сообщения ВСЕ технические маркеры вроде 'URL:', 'Title:' и '[FOUND ON THE INTERNET]'. Их никто не должен видеть!"
                    "4. Пытайся найти актуальную информацию на текущую дату."
                )
            })
        # -----------------------------------------------------

        messages.append({"role": "user", "content": formatted_user_text if formatted_user_text else "[пусто]"})

        if action_type == "video":
            messages.append({
                "role": "system", 
                "content": "ОСОБОЕ УКАЗАНИЕ: Сейчас ты записываешь ВИДЕОКРУЖОК. Говори исключительно от первого лица. Ссылки кодом писать можно, но вслух теги не читай."
            })
        elif action_type == "voice":
            messages.append({
                "role": "system", 
                "content": "ОСОБОЕ УКАЗАНИЕ: Сейчас ты записываешь ГОЛОСОВОЕ СООБЩЕНИЕ. Говори естественно."
            })

        headers = {
            "Authorization": f"Bearer {ZVENO_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"model": TOOL_SLUG, "messages": messages}

        async with http_session.post("https://api.zveno.ai/v1/chat/completions", headers=headers, json=payload) as resp:
            if resp.status != 200:
                return f"Ой, сервер тупит... (Ошибка: {resp.status})"
            
            result_data = await resp.json()
            bot_reply = result_data["choices"][0]["message"]["content"]
            
            if not bot_reply or not bot_reply.strip():
                bot_reply = "Ой, я что-то задумалась и потеряла мысль... Напомни, о чем мы? 😅"

        bot_reply_clean = bot_reply.strip()

        history.append({"role": "user", "content": formatted_user_text})
        history.append({"role": "assistant", "content": bot_reply_clean})

        if len(history) > MAX_HISTORY_LEN:
            history = history[-MAX_HISTORY_LEN:]
        
        CHAT_MEMORIES[chat_id] = history
        return bot_reply_clean

    except Exception as e:
        print(f"Ошибка API: {e}")
        return "What-то меня переклинило... Попробуйте чуть позже."

# =====================================================================
# === ОЗВУЧКА ELEVENLABS ==============================================
# =====================================================================
async def generate_elevenlabs_audio(text: str, filename: str):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = { "xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json" }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": { "stability": 0.5, "similarity_boost": 0.75 }
    }
    async with http_session.post(url, headers=headers, json=payload) as resp:
        if resp.status == 200:
            audio_data = await resp.read()
            with open(filename, "wb") as f:
                f.write(audio_data)
        else:
            err_info = await resp.text()
            raise Exception(f"Ошибка ElevenLabs: {err_info}")

# =====================================================================
# === АДМИН-КОМАНДЫ (УПРАВЛЕНИЕ ПАМЯТЬЮ И РЕЖИМОМ СНА ПО МСК) ==========
# =====================================================================

# --- НОВАЯ КОМАНДА: ОТПРАВИТЬ АНОНИМНЫЙ ПРОМПТ В ЧАТ ИЗ ЛС ---
# --- ОБНОВЛЕННАЯ КОМАНДА: ПОЛНЫЙ ИГНОР ТВОЕГО НИКА И ОТСЕЧЕНИЕ ВОДЫ ---
@dp.message(Command("send"))
async def cmd_send_prompt(message: types.Message):
    if message.chat.type != "private":
        return  # Работает строго в ЛС боту
# ПРОВЕРКА НА БОТОВ (ровно 4 пробела от края, как и у строк ниже!)
    if message.from_user.is_bot:
        return  # ровно 8 пробелов от края
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Напиши текст после команды, например: `/send привет всем`", parse_mode="Markdown")
        return

    raw_prompt = args[1]
    
    await bot.send_chat_action(chat_id=MAIN_CHAT_ID, action="typing")
    
    now = datetime.now(MOSCOW_TZ)
    time_context = f"\n\n[CURRENT TIME DATA]\n- Current date/time: {now.strftime('%A, %d.%m.%Y, %H:%M')} (Moscow Time, Year is 2026)"
    
    # В системном промпте жестко запрещаем упоминать тебя под любым соусом
    custom_system = (
        "Ты — Аня. Выполни промпт пользователя ЕСТЕСТВЕННО, коротко, без лишних слов и рассуждений. "
        "Пиши СТРОГО результат выполнения, без приветствий и лишней воды. "
        "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать, упоминать или как-либо писать имя 'Годжо Сатору', 'Годжо', 'Сатору' или обращаться к создателю. "
        "Твоя задача — просто выдать чистый текст от первого лица в чат, будто ты сама решила это написать."
    )
    
    try:
        messages = [
            {"role": "system", "content": custom_system + time_context},
            {"role": "user", "content": raw_prompt}
        ]
        
        headers = {
            "Authorization": f"Bearer {ZVENO_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"model": TOOL_SLUG, "messages": messages}

        async with http_session.post("https://api.zveno.ai/v1/chat/completions", headers=headers, json=payload) as resp:
            if resp.status != 200:
                await message.reply(f"Ой, сервер тупит... (Ошибка: {resp.status})")
                return
            
            result_data = await resp.json()
            reply = result_data["choices"][0]["message"]["content"].strip()
            
    except Exception as e:
        print(f"Ошибка API в команде send: {e}")
        await message.reply("Что-то меня переклинило... Попробуй позже.")
        return

    # === ЖЕСТКИЙ АНТИ-СПАМ ФИЛЬТР ИМЕНИ ===
    # Если нейросеть всё-таки заглючит и напишет твой ник, код его просто сотрет
    names_to_erase = [r"Годжо Сатору", r"Годжо", r"Сатору", r"Gojo Satoru", r"Gojo"]
    for name_pattern in names_to_erase:
        reply = re.sub(name_pattern, "", reply, flags=re.IGNORECASE)
    
    # Убираем двойные пробелы, которые могли остаться после удаления имени
    reply = re.sub(r' +', ' ', reply).strip()

    # Проверка, чтобы сообщение не ушло пустым
    if not reply:
        reply = "Балалалаб"  # Дефолтный ответ, если фильтр вырезал всё подчистую
        
    # Отправляем чистый результат в группу
    try:
        await bot.send_message(chat_id=MAIN_CHAT_ID, text=reply, parse_mode="HTML", disable_web_page_preview=True)
        await message.reply("✅ Отправлено в чат!")
    except Exception as html_err:
        plain_reply = re.sub(r'<[^>]+>', '', reply)
        await bot.send_message(chat_id=MAIN_CHAT_ID, text=plain_reply)
        await message.reply("✅ Отправлено в чат (без HTML)!")
@dp.message(Command("banglobal"))
async def cmd_banglobal(message: types.Message):
    global BANNED_USERS, BANNED_USERNAMES
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверка прав: админ в приватном чате или создатель/администратор группы
    is_admin = message.chat.type == "private"
    if not is_admin:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ["creator", "administrator"]
        
    if not is_admin:
        await message.reply("Эй, ты не мой админ, чтобы раздавать баны! 😜")
        return
        
    target_id = None
    target_name = ""
    
    # 1. Если это ответ на сообщение (реплай)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or f"ID {target_id}"
        username = message.reply_to_message.from_user.username.lower() if message.reply_to_message.from_user.username else ""
        if username:
            BANNED_USERNAMES[username] = target_id
    # 2. Если указали текстом (/banglobal @nick или ID)
    else:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("Кому бан выдаем? Напиши ник: `/banglobal @nick` или айди.", parse_mode="Markdown")
            return
            
        arg_nick = args[1].strip().lower().replace("@", "")
        
        if arg_nick.isdigit():
            target_id = int(arg_nick)
            target_name = f"ID {target_id}"
        elif arg_nick in BANNED_USERNAMES:
            target_id = BANNED_USERNAMES[arg_nick]
            target_name = f"@{arg_nick}"
        else:
            # Если юзера нет в кэше, банить по ID мы не сможем сразу, но занесем в текстовый ЧС
            BANNED_USERNAMES[arg_nick] = 999999999
            target_name = f"@{arg_nick}"
            
    now_moscow = datetime.now(MOSCOW_TZ)
    three_days_ban = now_moscow + timedelta(days=3)
    
    # Внутренний бан Ани (игнор)
    if target_id:
        BANNED_USERS[target_id] = three_days_ban
    if 'arg_nick' in locals() and arg_nick:
        BANNED_USERNAMES[arg_nick] = target_id if target_id else 999999999

    # ФИЗИЧЕСКИЙ БАН В ГРУППЕ
    kick_success = False
    if target_id and target_id != 999999999:
        try:
            # Отправляем команду бана в твой основной чат
            await bot.ban_chat_member(chat_id=MAIN_CHAT_ID, user_id=target_id, until_date=three_days_ban)
            kick_success = True
        except Exception as kick_err:
            print(f"Не удалось кикнуть юзера через API (возможно бот не админ в группе): {kick_err}")

    if kick_success:
        await message.reply(f"Поняла, батя! {target_name} официально вышвырнут из группы на 3 дня и добавлен в мой ЧС! 😤 Сюда он больше не зайдет.")
    else:
        await message.reply(f"В ЧС-то я {target_name} добавила, но руками из группы выкинуть не смогла. Проверь, дала ли ты мне права администратора в чате! 👀")
        
    print(f"🤬 Глобальный бан с киком: {target_name} забанен до {three_days_ban}.")

@dp.message(Command("sleep"))
async def cmd_sleep(message: types.Message):
    global MUTE_UNTIL
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    is_admin = message.chat.type == "private"
    if not is_admin:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ["creator", "administrator"]
        
    if not is_admin:
        await message.reply("Эй, ты не мой админ, чтобы отправлять меня спать! 😤")
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Укажи время сна! Пример:\n`/sleep 45`\n`/sleep 18:30`", parse_mode="Markdown")
        return
        
    time_arg = args[1]
    now = datetime.now(MOSCOW_TZ)
    
    try:
        if ":" in time_arg:
            h, m = map(int, time_arg.split(":"))
            target_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            
            if target_time < now:
                target_time += timedelta(days=1)
                
            MUTE_UNTIL = target_time
            await message.reply(f"Поняла, ухожу в спячку до <b>{MUTE_UNTIL.strftime('%H:%M')}</b> по МСК! 😴 Меня больше никто не побеспокоит.", parse_mode="HTML")
        else:
            minutes = int(time_arg)
            MUTE_UNTIL = now + timedelta(minutes=minutes)
            await message.reply(f"Ушла спать на {minutes} мин. Проснусь в <b>{MUTE_UNTIL.strftime('%H:%M')}</b> по МСК! 🤫 Просьба не будить.", parse_mode="HTML")
            
        print(f"💤 Бот принудительно усыплен админом до {MUTE_UNTIL} (МСК)")
    except Exception as e:
        print(f"Ошибка парсинга времени: {e}")
        await message.reply("Че-то я не разобрала формат времени. Пиши либо минуты числом (типа 60), либо время в формате 15:45.")

@dp.message(Command("wakeup"))
async def cmd_wakeup(message: types.Message):
    global MUTE_UNTIL
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    is_admin = message.chat.type == "private"
    if not is_admin:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ["creator", "administrator"]
        
    if not is_admin:
        await message.reply("У тебя нет будильника для меня! 😜")
        return
        
    MUTE_UNTIL = None
    await message.reply("Я проснулась! 🥱✨ Ну что, соскучились? Кто тут потерялся во времени, признавайтесь? 😜")
    print("⏰ Бот был принудительно разбужен админом.")

@dp.message(Command("grantreset"))
async def cmd_grantreset(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.chat.type != "private":
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status not in ["creator", "administrator"]:
            await message.reply("У тебя нет прав раздавать доступы! 😛")
            return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Напиши ник: `/grantreset @nick`", parse_mode="Markdown")
        return
    target_nick = args[1].replace("@", "").lower()
    if chat_id not in ALLOWED_RESETTERS:
        ALLOWED_RESETTERS[chat_id] = set()
    if target_nick in ALLOWED_RESETTERS[chat_id]:
        ALLOWED_RESETTERS[chat_id].remove(target_nick)
        await message.reply(f"Право на амнезию у @{target_nick} забрали! 🚫")
    else:
        ALLOWED_RESETTERS[chat_id].add(target_nick)
        await message.reply(f"Пользователю @{target_nick} выдано право сбрасывать память! ✅")

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username.lower() if message.from_user.username else ""
    is_admin = message.chat.type == "private"
    if not is_admin:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ["creator", "administrator"]
    is_allowed = chat_id in ALLOWED_RESETTERS and username in ALLOWED_RESETTERS[chat_id]
    if is_admin or is_allowed:
        CHAT_MEMORIES[chat_id] = []
        await message.reply("Ой, о чем мы сейчас говорили? В голове белый шум... 🧹✨")
    else:
        await message.reply("Эй, тебе нельзя стирать мне память! 😤")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    global BANNED_USERS, BANNED_USERNAMES
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    is_admin = message.chat.type == "private"
    if not is_admin:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ["creator", "administrator"]
        
    if not is_admin:
        await message.reply("Ты не можешь никого разбанить, ты не админ! 😜")
        return
        
    target_id = None
    target_name = ""
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or f"ID {target_id}"
    else:
        args = message.text.split()
        if len(args) < 2:
            await message.reply(
                "Укажи, кого разбанить! Напиши ник: `/unban @nick` или просто ответь командой `/unban` на сообщение нарушителя.", 
                parse_mode="Markdown"
            )
            return
            
        arg_nick = args[1].strip().lower().replace("@", "")
        
        if arg_nick.isdigit():
            target_id = int(arg_nick)
            target_name = f"ID {target_id}"
        elif arg_nick in BANNED_USERNAMES:
            target_id = BANNED_USERNAMES[arg_nick]
            target_name = f"@{arg_nick}"
            
    if (target_id and target_id in BANNED_USERS) or ('arg_nick' in locals() and arg_nick in BANNED_USERNAMES):
        if target_id in BANNED_USERS: del BANNED_USERS[target_id]
        if 'arg_nick' in locals() and arg_nick in BANNED_USERNAMES: del BANNED_USERNAMES[arg_nick]
        await message.reply(f"Ладно, батя, ради тебя амнистирую {target_name}. Пусть общается, но если опять заспамит — улетит обратно! 😤")
        print(f"🔓 Пользователь {target_name} был досрочно разбанен админом.")
    else:
        await message.reply("Этот челик и так не в бане. Либо я его еще ни разу не видела! 🤷‍♀️")
# --- ОБНОВЛЕННАЯ КОМАНДА: ТОЛЬКО ВНУТРЕННИЙ БАН АНИ БЕЗ КИКА (/ban @nick 1d) ---
@dp.message(Command("ban"))
async def cmd_ban_time(message: types.Message):
    global BANNED_USERS, BANNED_USERNAMES
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверка прав: админ в приватном чате или администратор группы
    is_admin = message.chat.type == "private"
    if not is_admin:
        member = await bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ["creator", "administrator"]
        
    if not is_admin:
        await message.reply("Эй, ты не мой админ, чтобы раздавать баны! 😜")
        return
        
    target_id = None
    target_name = ""
    duration_str = "3d"  # По умолчанию бан на 3 дня
    
    args = message.text.split()
    
    # 1. Если это ответ на сообщение (реплай)
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or f"ID {target_id}"
        username = message.reply_to_message.from_user.username.lower() if message.reply_to_message.from_user.username else ""
        if username:
            BANNED_USERNAMES[username] = target_id
            
        if len(args) >= 2:
            duration_str = args[1].strip().lower()
            
    # 2. Если указали текстом (/ban @nick 1d)
    else:
        if len(args) < 2:
            await message.reply("Кому ставим игнор? Напиши ник и время, например: `/ban @nick 1d` (или 2h, 30m)", parse_mode="Markdown")
            return
            
        arg_nick = args[1].strip().lower().replace("@", "")
        
        if len(args) >= 3:
            duration_str = args[2].strip().lower()
            
        if arg_nick.isdigit():
            target_id = int(arg_nick)
            target_name = f"ID {target_id}"
        elif arg_nick in BANNED_USERNAMES:
            target_id = BANNED_USERNAMES[arg_nick]
            target_name = f"@{arg_nick}"
        else:
            BANNED_USERNAMES[arg_nick] = 999999999
            target_name = f"@{arg_nick}"

    # Парсинг времени (d - дни, h - часы, m - минуты)
    now_moscow = datetime.now(MOSCOW_TZ)
    try:
        if duration_str.endswith('d'):
            days = int(duration_str.replace('d', ''))
            ban_until = now_moscow + timedelta(days=days)
            time_text = f"{days} дн."
        elif duration_str.endswith('h'):
            hours = int(duration_str.replace('h', ''))
            ban_until = now_moscow + timedelta(hours=hours)
            time_text = f"{hours} час."
        elif duration_str.endswith('m'):
            minutes = int(duration_str.replace('m', ''))
            ban_until = now_moscow + timedelta(minutes=minutes)
            time_text = f"{minutes} мин."
        else:
            days = int(duration_str)
            ban_until = now_moscow + timedelta(days=days)
            time_text = f"{days} дн."
    except ValueError:
        ban_until = now_moscow + timedelta(days=3)
        time_text = "3 дн. (ошибка ввода)"

    # Внутренний бан Ани (заносим в ЧС для игнора)
    if target_id:
        BANNED_USERS[target_id] = ban_until
    if 'arg_nick' in locals() and arg_nick:
        BANNED_USERNAMES[arg_nick] = target_id if target_id else 999999999

    await message.reply(f"Принято, батя! Включаю полный игнор для {target_name} на **{time_text}**. Больше я на его сообщения не реагирую и баланс не трачу! 🤫")
    print(f"🤫 Внутренний бан: {target_name} в игноре у Ани до {ban_until}.")
# =====================================================================
# === ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ ЧАТА ===============================
# =====================================================================
@dp.message()
async def handle_chat(message: types.Message):
    global MUTE_UNTIL, BANNED_USERS, BANNED_USERNAMES, USER_SPAM_TRACKER
    bot_info = await bot.get_me()
    chat_id = message.chat.id
    user_id = message.from_user.id
    username_clean = message.from_user.username.lower() if message.from_user.username else ""
    now_moscow = datetime.now(MOSCOW_TZ)
    
    # Кэшируем юзернейм на будущее для системы бана
    if username_clean:
        BANNED_USERNAMES[username_clean] = user_id
    
    # --- 1. АНТИ-СПАМ: БАН НА УРОВНЕ ВХОДА ---
    if user_id in BANNED_USERS or (username_clean in BANNED_USERNAMES and BANNED_USERNAMES[username_clean] == user_id):
        current_ban = BANNED_USERS.get(user_id) or BANNED_USERS.get(BANNED_USERNAMES.get(username_clean))
        if current_ban and now_moscow < current_ban:
            return  # Спамер полностью игнорируется
        else:
            if user_id in BANNED_USERS: del BANNED_USERS[user_id]  # Срок бана истёк!
            
    # Дополнительная проверка на ручной бан по никнейму (заглушка 999999999)
    if username_clean in BANNED_USERNAMES and BANNED_USERNAMES[username_clean] == 999999999:
        return # Глобальный бан по юзернейму
        
    # --- 2. ГЛУБОКИЙ ПРЕДОХРАНИТЕЛЬ РЕЖИМА СНА (МСК) + АВТОПРОБУЖДЕНИЕ ---
    if MUTE_UNTIL:
        if now_moscow < MUTE_UNTIL:
            return  # Ещё спит
        else:
            MUTE_UNTIL = None  # Проснулась по таймеру!
            try:
                await bot.send_message(
                    chat_id=chat_id, 
                    text="Я проснулась! 🥱✨ Ну что, соскучились? Кто тут потерялся во времени, признавайтесь? 😜"
                )
            except Exception as e:
                print(f"Ошибка автоотправки пробуждения: {e}")

    # --- ХИТРЫЙ АНТИ-УГОН (ФИЛЬТР ЧУЖИХ ГРУПП) ---
    if message.chat.type in ["group", "supergroup"]:
        chat_username = message.chat.username.lower() if message.chat.username else ""
        if chat_username != "activatethischat" and chat_id != MAIN_CHAT_ID:
            try:
                await message.answer(
                    "Я доступна только в своей группе (http://t.me/activatethischat)!", 
                    parse_mode="HTML"
                )
                await bot.leave_chat(chat_id=chat_id)
                print(f"🛑 Ливнули из чужого чата: @{chat_username} (ID: {chat_id})")
            except Exception as e:
                print(f"Не удалось красиво ливнуть: {e}")
            return  
    # ----------------------------------------------

    author_name = message.from_user.first_name or message.from_user.username or "Кто-то"
    incoming_text = message.text or message.caption or ""
    text_lower = incoming_text.lower()

    formatted_user_text = f"[{author_name}]: {incoming_text}"

    if chat_id not in CHAT_MEMORIES:
        CHAT_MEMORIES[chat_id] = []

    is_private = message.chat.type == "private"
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
    name_pattern = r"\b(аня|анечка|анюта|ань|анюш|аней)\b"
    has_name_call = bool(re.search(name_pattern, text_lower))

    is_addressed_to_anya = is_private or is_reply_to_bot or has_name_call

    # --- 3. УМНЫЙ АНТИ-СПАМ (Анализируем обращения только к Ане) ---
    if is_addressed_to_anya:
        # Проверяем, не является ли отправитель создателем (твоим ником) или админом чата
        is_creator = (username_clean == "dimadima009")
        is_chat_admin = False
        
        if not is_private and not is_creator:
            try:
                member = await bot.get_chat_member(chat_id, user_id)
                is_chat_admin = member.status in ["creator", "administrator"]
            except Exception as e:
                print(f"Ошибка проверки админ-прав для спам-фильтра: {e}")

        # Если пишет создатель или админ чата — спам-фильтр полностью отключается!
        if not is_creator and not is_chat_admin:
            if user_id not in USER_SPAM_TRACKER:
                USER_SPAM_TRACKER[user_id] = []
            
            # Очищаем историю обращений старше 12 секунд
            USER_SPAM_TRACKER[user_id] = [t for t in USER_SPAM_TRACKER[user_id] if now_moscow - t < timedelta(seconds=12)]
            USER_SPAM_TRACKER[user_id].append(now_moscow)
            
            spam_count = len(USER_SPAM_TRACKER[user_id])

            # Уровень 2: КОРОНОЧКА (Прямой жесткий бан за игнор предупреждения)
            if spam_count > 6:
                BANNED_USERS[user_id] = now_moscow + timedelta(days=3)
                if username_clean:
                    BANNED_USERNAMES[username_clean] = user_id
                    
                print(f"🤬 Аня жестко забанила спамера {message.from_user.first_name} (ID: {user_id}) до {BANNED_USERS[user_id]}")
                await message.reply("Пошел нахуй! Я уже устала от тебя. Всё! Я не буду общаться с тобой 3 дня.")
                return

            # Уровень 1: МЯГКОЕ ПРЕДУПРЕЖДЕНИЕ + МИКРО-МЬЮТ
            elif spam_count > 3:
                # Временно игнорируем его на 15 секунд, чтобы он не спамил дальше в эту секунду
                BANNED_USERS[user_id] = now_moscow + timedelta(seconds=60)
                await message.reply("Ой! Подожди и хватит мне спамить! 😤")
                return
    # Пассивное наполнение контекста беседы (если обращение было не к ней)
    if not is_addressed_to_anya:
        history = CHAT_MEMORIES[chat_id]
        clean_history_text = f"[{author_name}]: [прислал(а) photo]" if bool(message.photo) and not incoming_text else formatted_user_text
        history.append({"role": "user", "content": clean_history_text})
        if len(history) > MAX_HISTORY_LEN:
            history = history[-MAX_HISTORY_LEN:]
        CHAT_MEMORIES[chat_id] = history
        return

    # Проверка на типы контента
    voice_triggers = ["голосом", "голосовое", "голосовух", "скажи", "озвучь", "продиктуй"]
    video_triggers = ["кружочек", "кружком", "кругляш", "видеосообщение", "кружок", "видео"]
    
    needs_voice = any(word in text_lower for word in voice_triggers)
    needs_video = any(word in text_lower for word in video_triggers)
    has_photo = bool(message.photo)

    action_type = "text"
    if needs_video:
        action_type = "video"
        await bot.send_chat_action(chat_id=chat_id, action="upload_video_note")
    elif needs_voice:
        action_type = "voice"
        await bot.send_chat_action(chat_id=chat_id, action="upload_voice")
    else:
        await bot.send_chat_action(chat_id=chat_id, action="typing")
    
    reply = await get_ai_response(chat_id, formatted_user_text, incoming_text, has_image=has_photo, action_type=action_type)
    
    # --- ВЫВОД В ОТВЕТ: КРУЖОЧЕК ---
    if needs_video:
        status_msg = await message.reply("Пожалуйста подождите, Аня снимает кружочек... 🎬")
        voice_filename = f"voice_{message.message_id}.mp3"
        video_filename = f"video_{message.message_id}.mp4"
        try:
            tts_text = re.sub(r'<[^>]+>', '', reply)
            tts_text = re.sub(r'[^\w\s,.?!:;()"\'-]', '', tts_text)
            
            await generate_elevenlabs_audio(tts_text, voice_filename)
            async with ffmpeg_semaphore:
                cmd = [
                    'ffmpeg', '-y', '-loop', '1', '-i', 'anya.jpg', '-i', voice_filename,
                    '-vf', 'scale=640:640:force_original_aspect_ratio=increase,crop=640:640',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
                    '-c:a', 'aac', '-b:a', '64k', '-pix_fmt', 'yuv420p', '-shortest', video_filename
                ]
                process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await process.communicate()
            await message.reply_video_note(video_note=FSInputFile(video_filename))
            await status_msg.delete()
        except Exception as err:
            print(f"Ошибка создания кружочка: {err}")
            try:
                await message.reply(f"(Очень хотела записать кружочек, но камера сломалась 😭)\n\n{reply}", parse_mode="HTML")
            except Exception:
                plain_reply = re.sub(r'<[^>]+>', '', reply)
                await message.reply(f"(Очень хотела записать кружочек, но камера сломалась 😭)\n\n{plain_reply}")
        finally:
            if os.path.exists(voice_filename): os.remove(voice_filename)
            if os.path.exists(video_filename): os.remove(video_filename)

    # --- ВЫВОД В ОТВЕТ: ГОЛОСОВОЕ ---
    elif needs_voice:
        voice_filename = f"voice_{message.message_id}.mp3"
        try:
            tts_text = re.sub(r'<[^>]+>', '', reply)
            tts_text = re.sub(r'[^\w\s,.?!:;()"\'-]', '', tts_text)
            
            await generate_elevenlabs_audio(tts_text, voice_filename)
            try:
                await message.reply_voice(voice=FSInputFile(voice_filename), caption=reply, parse_mode="HTML")
            except Exception:
                plain_reply = re.sub(r'<[^>]+>', '', reply)
                await message.reply_voice(voice=FSInputFile(voice_filename), caption=plain_reply)
        except Exception as tts_err:
            print(f"Ошибка TTS: {tts_err}")
            try:
                await message.reply(f"(Голос пропал 😷)\n\n{reply}", parse_mode="HTML")
            except Exception:
                plain_reply = re.sub(r'<[^>]+>', '', reply)
                await message.reply(f"(Голос пропал 😷)\n\n{plain_reply}")
        finally:
            if os.path.exists(voice_filename): os.remove(voice_filename)
            
    # --- ВЫВОД В ОТВЕТ: ТЕКСТ (С HTML ССЫЛКАМИ) ---
    else:
        try:
            await message.reply(reply, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as html_err:
            print(f"Ошибка разметки HTML, отправляем чистый текст: {html_err}")
            plain_reply = re.sub(r'<[^>]+>', '', reply)
            await message.reply(plain_reply)
    
    # --- ОТПРАВКА СЛУЧАЙНОЙ РЕАКЦИИ ПОД ПОСТ (ФИКС REACTION_EMPTY) ---
    try:
        chosen_emoji = random.choice(SUCH_EMOJIS)
        await message.react(reaction=[ReactionTypeEmoji(type="emoji", emoji=chosen_emoji)])  
    except Exception as e:
        print(f"⚠️ Ошибка при попытке поставить реакцию {chosen_emoji}: {e}")
# =====================================================================
# === ЗАПУСК ВЕБ-СЕРВЕРА И ПОЛЛИНГА ===================================
# =====================================================================
async def handle_web_ping(request):
    return web.Response(text="Аня работает по МСК, имеет встроенный анти-спам, слушается батю Эгму и шифрует ссылки!")

async def main():
    global http_session
    http_session = aiohttp.ClientSession()
    app = web.Application()
    app.router.add_get('/', handle_web_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, '0.0.0.0', port).start()

    print("Бот успешно запущен!")
    try:
        await dp.start_polling(bot)
    finally:
        await http_session.close()

if __name__ == "__main__":
    asyncio.run(main())
