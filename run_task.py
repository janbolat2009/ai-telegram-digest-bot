import asyncio
import sys

from bot_core import morning_post, afternoon_post, evening_memes


async def run(name: str):
    if name == "morning":
        await morning_post()
    elif name == "afternoon":
        await afternoon_post()
    else:
        print("Unknown task. Use: morning | afternoon | memes")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "morning"
    asyncio.run(run(name))
