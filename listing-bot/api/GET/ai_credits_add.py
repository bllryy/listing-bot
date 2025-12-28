route = "/ai/credits/add"

from quart import current_app, request
from bot.bot import Bot
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    credits = request.args.get("credits")
    
    if not credits:
        return {"success": False, "error": "Missing required parameter: credits"}, 400
    
    try:
        credits = int(credits)
        if credits <= 0:
            return {"success": False, "error": "Credits must be a positive number"}, 400
    except ValueError:
        return {"success": False, "error": "Credits must be a valid number"}, 400
    
    ai_config = await bot.db.fetchone("SELECT monthly_limit, remaining_credits_free, remaining_credits_paid FROM ai_config LIMIT 1")
    
    if not ai_config:
        await bot.db.execute(
            """
            INSERT INTO ai_config 
            (monthly_limit, remaining_credits_free, remaining_credits_paid, last_reset) 
            VALUES (2000, 2000, ?, CURRENT_TIMESTAMP)
            """,
            credits
        )
        
        current_free = 150
        current_paid = 0
    else:
        monthly_limit, current_free, current_paid = ai_config
        current_paid = current_paid or 0
        
        await bot.db.execute(
            "UPDATE ai_config SET remaining_credits_paid = remaining_credits_paid + ?",
            credits
        )
    
    updated_config = await bot.db.fetchone("SELECT monthly_limit, remaining_credits_free, remaining_credits_paid FROM ai_config LIMIT 1")
    if updated_config:
        monthly_limit, updated_free, updated_paid = updated_config
    else:
        updated_free, updated_paid = current_free, current_paid + credits
    
    return {
        "success": True,
        "message": f"Successfully added {credits} premium AI credits",
        "previous_credits": {
            "free": current_free,
            "paid": current_paid,
            "total": current_free + current_paid
        },
        "updated_credits": {
            "free": updated_free,
            "paid": updated_paid,
            "total": updated_free + updated_paid
        },
        "credits_added": credits
    }, 200