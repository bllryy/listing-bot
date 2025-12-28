route = "/users/info"
from quart import current_app, request, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key
import asyncio

@require_api_key
async def func():
    bot: Bot = current_app.bot

    try:
        users = await request.get_json()
        if not users or not isinstance(users, list):
            return jsonify({
                "success": False,
                "error": "Request body must contain a list of user IDs"
            }), 400
    except Exception:
        return jsonify({
            "success": False,
            "error": "Invalid JSON in request body"
        }), 400

    response = {}

    for user_id in users:
        try:
            user_info = bot.get_user(int(user_id))
            if user_info:
                response[str(user_id)] = {
                    "id": str(user_info.id),
                    "name": user_info.name,
                    "display_name": user_info.display_name,
                    "avatar": user_info.display_avatar.url,
                    "discriminator": user_info.discriminator if user_info.discriminator != "0" else None,
                    "bot": user_info.bot,
                    "created_at": user_info.created_at.isoformat()
                }
        except ValueError:
            response[str(user_id)] = {
                "error": "Invalid user ID format"
            }

    return jsonify({
        "success": True,
        "data": response,
        "requested_count": len(users),
        "found_count": len([v for v in response.values() if "error" not in v])
    })