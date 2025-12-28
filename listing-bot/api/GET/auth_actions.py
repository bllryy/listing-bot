route = "/auth/actions"
from quart import current_app, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot

    query = await bot.db.fetchall(
        """
        SELECT * FROM auth_actions
        """
    )
    
    action_data = []
    for action in query:
        action_id, user_id, action_type, timestamp, details, resolved = action
        action_data.append({
            "action_id": str(action_id),
            "user_id": str(user_id),
            "action_type": str(action_type),
            "timestamp": str(timestamp),
            "details": str(details),
            "resolved": bool(resolved)
        })
    
    return jsonify({
        "success": True,
        "data": action_data,
        "count": len(action_data)
    })
