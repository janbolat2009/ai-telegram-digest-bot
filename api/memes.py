from bot_core import evening_memes
import asyncio

def handler(req):
    asyncio.run(evening_memes())
    return {"statusCode": 200, "body": "Memes sent"}