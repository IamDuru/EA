from pyrogram import Client
from fastapi import FastAPI
from .console import *

class Bot(Client):
    def __init__(self):
        super().__init__(
            "EraApi",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            in_memory=True,  # Use in-memory session to avoid database locks
        )

    async def start(self):
        await super().start()
        print("✅ Bot Started❗")
        try:
            await self.send_message(console.owner_id, "✅ Bot Successfully Started!")
        except Exception as e:
            print(f"Failed to send start message: {e}")

    async def stop(self, *args):
        await super().stop()
        print("✅ Bot Stopped❗")


bot = Bot()
app = FastAPI(title="EraApi")