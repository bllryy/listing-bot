route = "/bot/payment"

from bot.bot import Bot
from quart import current_app
from datetime import datetime, timezone
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    hosting_data = await bot.db.fetchone(
        "SELECT paid_until, paid_by, last_payment, last_payment_amount, last_payment_method FROM hosting LIMIT 1"
    )
    
    if not hosting_data or not hosting_data[0]:
        return {
            "is_paid": False,
            "expires_at": None,
            "days_remaining": 0,
            "paid_by": None,
            "last_payment": None,
            "last_payment_amount": None,
            "last_payment_method": None
        }, 200
    
    paid_until, paid_by, last_payment, last_payment_amount, last_payment_method = hosting_data
    paid_until_date = datetime.fromisoformat(paid_until.replace(' ', 'T'))
    current_time = datetime.now(timezone.utc)
    
    is_paid = current_time < paid_until_date
    days_remaining = (paid_until_date - current_time).days if is_paid else 0
    
    return {
        "is_paid": is_paid,
        "expires_at": paid_until,
        "days_remaining": days_remaining,
        "paid_by": paid_by,
        "last_payment": last_payment,
        "last_payment_amount": last_payment_amount,
        "last_payment_method": last_payment_method
    }, 200