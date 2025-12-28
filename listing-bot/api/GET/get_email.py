route = "/get/email"

from quart import current_app
from bot.bot import Bot
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot

    lookup = await bot.db.fetchone(
        "SELECT * FROM config WHERE key = 'email_address' LIMIT 1"
    )
    if not lookup:
        return {"success": False, "error": "Email not found"}, 404
    
    email = lookup[1]  # Assuming the email is in the second column
    if not email:
        return {"success": False, "error": "Email not set"}, 404
    
    return {"success": True, "email": email}, 200
