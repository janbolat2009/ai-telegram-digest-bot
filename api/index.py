from bot_core import bot
from aiogram.types import Update
from aiogram import Dispatcher
import asyncio
import json

dp = Dispatcher()

@dp.message()
async def echo(message):
    await message.reply("Echo")

async def webhook_handler(update: dict):
    update_obj = Update(**update)
    await dp.feed_update(bot, update_obj)

def handler(req):
    if req['method'] == 'POST':
        update = json.loads(req['body'])
        asyncio.run(webhook_handler(update))
        return {"statusCode": 200}
    return {"statusCode": 405, "body": "Method Not Allowed"}