route = "/auth/bots"
from quart import current_app, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot

    query = await bot.db.fetchall(
        """
        SELECT client_id FROM auth_bots
        """
    )
    
    # Format the data as a proper JSON response
    bots_data = []
    for (client_id,) in query:
        bots_data.append({
            "client_id": str(client_id)
        })
    
    return jsonify({
        "success": True,
        "data": bots_data,
        "count": len(bots_data)
    })
