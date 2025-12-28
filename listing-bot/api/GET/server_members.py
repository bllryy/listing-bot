route = "/server/members"

from bot.bot import Bot
from quart import current_app
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    main_guild_id = await bot.db.get_config("main_guild")
    guild = bot.get_guild(main_guild_id)
    
    if not guild:
        return {
            "member_count": 0,
            "online_count": 0,
            "bot_count": 0,
            "human_count": 0
        }, 404
    
    # Calculate different member counts
    total_members = guild.member_count
    bot_count = len([m for m in guild.members if m.bot])
    human_count = total_members - bot_count
    online_count = len([m for m in guild.members if m.status != "offline" and not m.bot])
    
    return {
        "member_count": total_members,
        "online_count": online_count,
        "bot_count": bot_count,
        "human_count": human_count
    }, 200