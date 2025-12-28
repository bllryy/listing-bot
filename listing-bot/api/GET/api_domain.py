route = "/api/domain"

from bot.bot import Bot
from quart import current_app
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot

    return {"domain": (await bot.get_domain())}
