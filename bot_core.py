import asyncio
import logging
import os
import random
import re
from datetime import datetime

from aiogram import Bot
from dotenv import load_dotenv
from openai import OpenAI
import feedparser
import requests
from bs4 import BeautifulSoup

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUP_CHAT_ID_ENV = os.getenv("GROUP_CHAT_ID")
if GROUP_CHAT_ID_ENV is None:
    raise ValueError("GROUP_CHAT_ID environment variable is not set")
GROUP_CHAT_ID = int(GROUP_CHAT_ID_ENV)

client = OpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

async def generate_gpt_content(style="morning"):
    if style == "morning":
        prompt = (
            "Сгенерируй короткий ценный пост для Telegram-группы по ИИ, машинному обучению, графическому дизайну и программированию.\n"
            "Формат:\n"
            "Сначала 1 короткий энергичный заголовок с эмодзи\n"
            "Потом 3–4 самых интересных свежих факта или новинки (каждый факт — 1 строка, с эмодзи, без нумерации, без жирного текста, без звёздочек)\n"
            "Потом 1–2 сильных вопроса для обсуждения (каждый вопрос — отдельная строка)\n"
            "Не используй ** или __ для жирного текста — Telegram их не показывает корректно. Пиши обычным текстом. Стиль: лаконичный, цепляющий."
        )
    elif style == "afternoon":
        prompt = (
            "Сгенерируй очень короткий пост (4–6 строк) с 3–4 самыми неожиданными и крутыми фактами по ИИ/ML/дизайну/программированию.\n"
            "Каждый факт — одна строка, с эмодзи в начале, без нумерации, без жирного текста, без ** и __.\n"
            "Без заголовка, без вопросов. Только факты. Стиль энергичный и цепляющий."
        )
    else:
        prompt = "Сгенерируй 1 очень крутой вопрос или инсайт по ИИ/ML/дизайну/программированию (1–2 предложения, с эмодзи)."
import asyncio
import logging
import os
import random
from typing import Optional

from aiogram import Bot
from dotenv import load_dotenv
from openai import OpenAI
import feedparser
import requests
from bs4 import BeautifulSoup

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUP_CHAT_ID_ENV = os.getenv("GROUP_CHAT_ID")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set")

if GROUP_CHAT_ID_ENV is None:
    raise ValueError("GROUP_CHAT_ID environment variable is not set")

GROUP_CHAT_ID = int(GROUP_CHAT_ID_ENV)

client: Optional[OpenAI] = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY not set — GPT content will be unavailable and fallback will be used")

bot = Bot(token=TELEGRAM_TOKEN)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}


def _fetch_top_feeds(limit: int = 6) -> str:
    feeds = [
        "https://arxiv.org/rss/cs.AI",
        "https://arxiv.org/rss/cs.LG",
        "https://arxiv.org/rss/cs.CV",
        "https://news.google.com/rss/search?q=AI+OR+machine+learning+OR+programming&hl=en-US&gl=US&ceid=US:en",
    ]
    items = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries:
                if len(items) >= limit:
                    break
                title = getattr(entry, "title", "(no title)")
                link = getattr(entry, "link", "#")
                summary = getattr(entry, "summary", "")
                # Shorten summary
                if summary:
                    summary = summary.split("\n")[0]
                items.append((title, link, summary))
        except Exception:
            continue
        if len(items) >= limit:
            break

    if not items:
        return "(Не удалось загрузить новости)"

    out_lines = []
    for title, link, summary in items:
        # Use simple HTML link to keep Telegram rendering fine
        out_lines.append(f"• <a href=\"{link}\">{title}</a> — {summary}")
    return "\n".join(out_lines)


def _fetch_meme_urls(limit: int = 4):
    queries = ["programming meme", "AI meme", "coder meme"]
    images = []
    for q in queries:
        try:
            url = f"https://www.google.com/search?q={q.replace(' ', '+')}&tbm=isch"
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src") or img.get("data-src") or ""
                if src.startswith("http") and src.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    images.append(src)
        except Exception:
            continue
    # Deduplicate and limit
    images = list(dict.fromkeys(images))
    random.shuffle(images)
    return images[:limit]


async def _call_gpt(prompt: str, max_tokens: int = 700) -> str:
    """Call OpenAI and return text. If client absent or call fails, raise or return empty string."""
    if not client:
        return ""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=max_tokens,
        )
        # Compatible with older/newer simple response structure
        if hasattr(resp, "choices") and resp.choices:
            msg = resp.choices[0].message
            if hasattr(msg, "content"):
                return msg.content.strip()
            # fallback
            return str(resp.choices[0])
        return str(resp)
    except Exception as e:
        logger.exception("OpenAI request failed: %s", e)
        return ""


async def generate_gpt_content(style: str = "morning") -> str:
    """Generate a richer, multi-part post for morning and afternoon styles."""
    if style == "morning":
        prompt = (
            "Ты — редактор утреннего дайджеста для Telegram-группы про ИИ, ML, графический дизайн и разработку. "
            "Составь содержательный утренний пост:\n"
            "1) Одна короткая энергичная строка-заголовок с эмодзи.\\n"
            "2) 5 главных новостей/историй (каждая новость — 2–3 предложения: заголовок, 1 предлож. сводка, 1 предлож. почему это важно/что дальше).\\n"
            "3) Короткий раздел \"Что почитать\" — 2 ссылки (по одной строке каждая) с короткой подсказкой зачем читать.\\n"
            "4) 2 вопроса для обсуждения в группе (по одной строке).\\n"
            "Язык — русский. Не используй жирный текст. Сделай пост живым и полезным, длина ~8–12 абзацев." 
        )
        # Provide fetched news as context to improve factuality
        news_context = _fetch_top_feeds(limit=6)
        prompt = f"Контекст новостей:\n{news_context}\n\n" + prompt
        out = await _call_gpt(prompt, max_tokens=900)
        if out:
            return out
        # fallback: simple aggregated list
        return f"Утренний дайджест:\n\n{news_context}\n\n(Подробнее — включите OPENAI_API_KEY для расширенных постов)"

    if style == "afternoon":
        prompt = (
            "Ты — писатель для коротких, но глубоких Afternoon-facts постов для Telegram: "
            "Составь 6 увлекательных фактов по ИИ/ML/дизайну/программированию. Каждый факт — заголовок (с эмодзи) и 2–3 предложения объяснения и почему это важно."
            "Закончи 1 практическим советом для читателей. Язык — русский. Пост должен быть увлекательным и подробным."
        )
        out = await _call_gpt(prompt, max_tokens=800)
        if out:
            return out
        return "(Afternoon facts temporary unavailable — включите OPENAI_API_KEY для расширенных постов)"

    # default small insight
    prompt = "Дай 1 короткий интересный инсайт по ИИ или программированию (2 предложения)."
    return await _call_gpt(prompt, max_tokens=200)


async def morning_post():
    """Prepare and send the morning digest to the chat."""
    logger.info("Preparing morning post")
    content = await generate_gpt_content("morning")
    try:
        await bot.send_message(GROUP_CHAT_ID, content, parse_mode="HTML", disable_web_page_preview=False)
    except Exception:
        logger.exception("Failed to send morning post")
    finally:
        await bot.session.close()


async def afternoon_post():
    logger.info("Preparing afternoon post")
    content = await generate_gpt_content("afternoon")
    try:
        await bot.send_message(GROUP_CHAT_ID, content, parse_mode="HTML")
    except Exception:
        logger.exception("Failed to send afternoon post")
    finally:
        await bot.session.close()


async def evening_memes():
    logger.info("Preparing evening memes")
    urls = _fetch_meme_urls(limit=6)
    sent = 0
    for url in urls:
        if sent >= 4:
            break
        try:
            await bot.send_photo(GROUP_CHAT_ID, url, caption="😂")
            sent += 1
            await asyncio.sleep(random.uniform(1.0, 2.5))
        except Exception:
            continue
    if sent == 0:
        try:
            await bot.send_message(GROUP_CHAT_ID, "🤖 Сегодня мемов не нашлось — завтра повезёт!")
        except Exception:
            logger.exception("Failed to send fallback message for memes")
    await bot.session.close()