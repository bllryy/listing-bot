route = "/seller"

from bot.bot import Bot
from quart import current_app, request
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot

    user_id = request.args.get("user_id")

    main_guild = await bot.db.get_config("main_guild")
    guild = bot.get_guild(main_guild)

    if not guild:
        return {"response": False}, 404
    
    member = guild.get_member(int(user_id))
    if not member:
        return {"response": False}, 404
    
    seller_role = await bot.db.get_config("seller_role")
    role = guild.get_role(seller_role)
    if not role:
        return {"response": False}, 404
    
    if role in member.roles:
        return {"response": True}, 200
    
    return {"response": False}, 403
