from bot_core import morning_post
import asyncio

def handler(req):
    asyncio.run(morning_post())
    return {"statusCode": 200, "body": "Morning post sent"}