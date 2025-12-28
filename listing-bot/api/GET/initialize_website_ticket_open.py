route = "/initialize/website/ticket/open"

from bot.bot import Bot
from quart import current_app
from api.auth_utils import require_api_key
import random
from auth.auth import Auth

@require_api_key
async def func():
    bot: Bot = current_app.bot

    bot_data = await bot.db.fetchall("SELECT * FROM auth_bots")
    bot_data = random.choice(bot_data) if bot_data else None

    if bot_data:
        auth = Auth(bot_data[0], bot)
        await auth.init()

        url = auth.get_url()
        return {
            "url": url,
        }, 200

    else:
        return {"error": "No bot data found"}, 404
