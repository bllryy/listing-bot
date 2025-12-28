route = "/bot/ai-credits"

from bot.bot import Bot
from quart import current_app
from datetime import datetime, timezone
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    ai_config = await bot.db.fetchone(
        "SELECT monthly_limit, remaining_credits_free, remaining_credits_paid, last_reset FROM ai_config LIMIT 1"
    )
    
    if not ai_config:
        return {
            "monthly_limit": 0,
            "remaining_free": 0,
            "remaining_paid": 0,
            "last_reset": None,
            "next_reset": None
        }, 200
    
    monthly_limit, remaining_free, remaining_paid, last_reset = ai_config
    
    # Calculate next reset date (first of next month)
    last_reset_date = datetime.fromisoformat(last_reset.replace(' ', 'T')) if last_reset else datetime.now(timezone.utc)
    next_month = last_reset_date.month + 1 if last_reset_date.month < 12 else 1
    next_year = last_reset_date.year + 1 if last_reset_date.month == 12 else last_reset_date.year
    next_reset = datetime(next_year, next_month, 1, tzinfo=timezone.utc)
    
    return {
        "monthly_limit": monthly_limit,
        "remaining_free": remaining_free,
        "remaining_paid": remaining_paid,
        "total_remaining": remaining_free + remaining_paid,
        "last_reset": last_reset,
        "next_reset": next_reset.isoformat()
    }, 200