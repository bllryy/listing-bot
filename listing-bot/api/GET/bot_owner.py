route = "/bot/owner"

from bot.bot import Bot
from quart import current_app
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    owner_id = bot.owner_ids[0]
    owner = bot.get_user(owner_id)
    
    if not owner:
        try:
            owner = await bot.fetch_user(owner_id)
        except:
            return {
                "id": owner_id,
                "name": "Unknown",
                "discriminator": "0000",
                "avatar_url": None,
                "created_at": None
            }, 200
    
    return {
        "id": owner.id,
        "name": owner.name,
        "display_name": owner.display_name if hasattr(owner, "display_name") else owner.name,
        "discriminator": owner.discriminator if hasattr(owner, "discriminator") else "0",
        "avatar_url": str(owner.avatar.url) if owner.avatar else None,
        "created_at": owner.created_at.isoformat() if hasattr(owner, "created_at") else None
    }, 200