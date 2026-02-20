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
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.82,
        max_tokens=450
    )
    return response.choices[0].message.content.strip()


def get_news():
    feeds = [
        "https://arxiv.org/rss/cs.AI",
        "https://arxiv.org/rss/cs.LG",
        "https://arxiv.org/rss/cs.CV",
        "https://news.google.com/rss/search?q=ИИ+OR+машинное+обучение+OR+программирование&hl=ru&gl=RU&ceid=RU:ru",
    ]
    lines = []
    count = 0
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if count >= 6:
                    break
                title = entry.title.replace("<", "&lt;").replace(">", "&gt;")
                link = entry.get("link", "#")
                lines.append(f"• <a href='{link}'>{title}</a>")
                count += 1
            if count >= 6:
                break
        except:
            pass
    return "\n".join(lines) if lines else "<i>новости не загрузились</i>"


def get_meme_urls():
    queries = ["programming meme", "AI meme funny", "coder humor", "developer meme", "machine learning joke"]
    all_images = []
    for q in random.sample(queries, k=3):
        try:
            url = f"https://www.google.com/search?q={q.replace(' ', '+')}&tbm=isch"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src") or img.get("data-src") or ""
                if src.startswith("http") and re.search(r'\.(jpg|jpeg|png|gif)$', src, re.I):
                    all_images.append(src)
        except:
            pass
    all_images = list(set(all_images))[:8]
    random.shuffle(all_images)
    return all_images[:5]


async def morning_post():
    gpt = await generate_gpt_content("morning")
    news = get_news()
    text = f"{gpt}\n\n📰 {news}"
    await bot.send_message(GROUP_CHAT_ID, text, parse_mode="HTML", disable_web_page_preview=True)
    await bot.session.close()


async def afternoon_post():
    gpt = await generate_gpt_content("afternoon")
    await bot.send_message(GROUP_CHAT_ID, gpt, parse_mode="HTML")
    await bot.session.close()


async def evening_memes():
    urls = get_meme_urls()
    sent = 0
    for url in urls:
        if sent >= 4:
            break
        try:
            await bot.send_photo(GROUP_CHAT_ID, url, caption="😂")
            sent += 1
            await asyncio.sleep(random.uniform(1.5, 3))
        except:
            pass
    if sent == 0:
        await bot.send_message(GROUP_CHAT_ID, "🤖 мемов сегодня нет")
    await bot.session.close()