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

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUP_CHAT_ID_ENV = os.getenv("GROUP_CHAT_ID")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set")

if not GROUP_CHAT_ID_ENV:
    raise ValueError("GROUP_CHAT_ID not set")

GROUP_CHAT_ID = int(GROUP_CHAT_ID_ENV)

client: Optional[OpenAI] = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
bot = Bot(token=TELEGRAM_TOKEN)


def fetch_news(limit: int = 8) -> str:
    """Fetch raw news titles + links from RSS feeds."""
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
                summary = getattr(entry, "summary", "")[:300]
                items.append(f"Заголовок: {title}\nКраткое описание: {summary}\nСсылка: {link}")
        except Exception as e:
            logger.warning(f"Feed error {url}: {e}")
            continue
        if len(items) >= limit:
            break
    return "\n\n".join(items) if items else ""


def fetch_memes(limit: int = 2) -> list:
    subreddits = [
        "ProgrammerHumor",
        "ProgrammerMemes",
        "MachineLearningMemes",
    ]
    memes = []
    for sub in subreddits:
        if len(memes) >= limit:
            break
        try:
            url = f"https://meme-api.com/gimme/{sub}/{limit}"
            r = requests.get(url, timeout=10).json()
            if isinstance(r, dict) and "memes" in r:
                for m in r["memes"]:
                    if not m.get("nsfw", False):
                        memes.append(m["url"])
            elif "url" in r and not r.get("nsfw", False):
                memes.append(r["url"])
        except Exception as e:
            logger.warning(f"Meme API error for {sub}: {e}")
            continue

    random.shuffle(memes)
    return memes[:limit]


async def call_gpt(prompt: str, max_tokens: int = 800) -> str:
    if not client:
        return ""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"GPT error: {e}")
        return ""


async def generate_morning_post() -> str:
    """Fetch fresh news and ask GPT to rewrite them into a digest."""
    raw_news = fetch_news(limit=8)

    if raw_news:
        prompt = (
            "Ты редактор Telegram-канала про ИИ, ML и программирование.\n"
            "Вот свежие новости из RSS-лент:\n\n"
            f"{raw_news}\n\n"
            "Задача: составь утренний дайджест на русском языке.\n"
            "Формат:\n"
            "— Одна строка-заголовок с эмодзи (например: ☀️ Утренний дайджест)\n"
            "— 5 новостей. Каждая — 2 коротких предложения своими словами + ссылка в конце в виде [читать](ссылка)\n"
            "— 2 вопроса для обсуждения в конце\n"
            "Требования: без жирного текста, без markdown-заголовков (#), только русский язык."
        )
        gpt = await call_gpt(prompt, max_tokens=1100)
        if gpt:
            return gpt

    fallback_news = fetch_news(limit=6)
    return f"☀️ Утренний дайджест\n\n{fallback_news}" if fallback_news else "Новости временно недоступны"


async def generate_afternoon_post() -> str:
    """3-4 interesting facts, no bold, Russian only."""
    count = random.randint(3, 4)
    prompt = (
        f"Ты редактор Telegram-канала про ИИ, ML и программирование.\n"
        f"Напиши {count} интересных и малоизвестных факта на тему ИИ, машинного обучения или разработки ПО.\n"
        "Каждый факт — 2–3 предложения, понятно и увлекательно.\n"
        "В самом конце добавь 1 практический совет разработчику или исследователю.\n"
        "Требования: без жирного текста, без markdown-заголовков (#), только русский язык."
    )
    gpt = await call_gpt(prompt, max_tokens=900)
    return gpt if gpt else "Интересные факты временно недоступны"


async def morning_post():
    content = await generate_morning_post()
    try:
        await bot.send_message(GROUP_CHAT_ID, content, parse_mode="HTML")
        logger.info("Morning post sent")
    except Exception as e:
        logger.error(f"Failed to send morning post: {e}")
    finally:
        await bot.session.close()


async def afternoon_post():
    content = await generate_afternoon_post()
    try:
        await bot.send_message(GROUP_CHAT_ID, content, parse_mode="HTML")
        logger.info("Afternoon post sent")
    except Exception as e:
        logger.error(f"Failed to send afternoon post: {e}")
    finally:
        await bot.session.close()


async def evening_memes():
    limit = random.randint(1, 2)
    urls = fetch_memes(limit)
    sent = 0

    for url in urls:
        try:
            await bot.send_photo(GROUP_CHAT_ID, url, caption="😂")
            sent += 1
            await asyncio.sleep(random.uniform(1.0, 2.5))
        except Exception as e:
            logger.warning(f"Failed to send meme {url}: {e}")
            continue

    if sent == 0:
        try:
            await bot.send_message(GROUP_CHAT_ID, "Сегодня без мемов 🙂")
        except Exception as e:
            logger.error(f"Failed to send fallback message: {e}")

    logger.info(f"Evening memes sent: {sent}")
    await bot.session.close()