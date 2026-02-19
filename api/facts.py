from bot_core import afternoon_post
import asyncio

def handler(req):
    asyncio.run(afternoon_post())
    return {"statusCode": 200, "body": "Facts post sent"}