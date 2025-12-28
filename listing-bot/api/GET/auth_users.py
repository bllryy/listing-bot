route = "/auth/users"
from quart import current_app, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot

    query = await bot.db.fetchall(
        """
        SELECT user_id, ip_address, bot_id FROM auth
        """
    )
    
    # Format the data as a proper JSON response
    users_data = []
    for user_id, ip_address, bot_id in query:
        users_data.append({
            "user_id": str(user_id),
            "ip_address": str(ip_address),
            "bot_id": str(bot_id)
        })
    
    return jsonify({
        "success": True,
        "data": users_data,
        "count": len(users_data)
    })
