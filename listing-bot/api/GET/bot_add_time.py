route = "/bot/extend"

from quart import current_app, request
from bot.bot import Bot
from datetime import datetime, timezone, timedelta
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    days = request.args.get("days")
    user_id = request.args.get("user_id")
    payment_method = request.args.get("payment_method", "API")
    payment_amount = request.args.get("amount")
    
    if not days:
        return {"success": False, "error": "Missing required parameter: days"}, 400
    
    try:
        days = int(days)
        if days <= 0:
            return {"success": False, "error": "Days must be a positive number"}, 400
    except ValueError:
        return {"success": False, "error": "Days must be a valid number"}, 400
    
    try:
        payment_amount = float(payment_amount) if payment_amount else days
    except ValueError:
        payment_amount = days
    
    hosting_data = await bot.db.fetchone("SELECT paid_until FROM hosting LIMIT 1")
    current_time = datetime.now(timezone.utc)
    
    if hosting_data and hosting_data[0]:
        try:
            paid_until = datetime.fromisoformat(hosting_data[0].replace(' ', 'T'))
            if paid_until.tzinfo is None:
                paid_until = paid_until.replace(tzinfo=timezone.utc)
                
            if paid_until < current_time:
                base_date = current_time
                is_expired = True
            else:
                base_date = paid_until
                is_expired = False
        except (ValueError, TypeError):
            base_date = current_time
            is_expired = True
    else:
        base_date = current_time
        is_expired = True
    
    new_expiration = base_date + timedelta(days=days)
    
    if hosting_data:
        await bot.db.execute(
            """
            UPDATE hosting 
            SET paid_until = ?, 
                paid_by = ?, 
                last_payment = CURRENT_TIMESTAMP,
                last_payment_amount = ?,
                last_payment_method = ?
            """, 
            new_expiration.isoformat(), 
            int(user_id) if user_id else None,
            payment_amount,
            payment_method
        )
    else:
        await bot.db.execute(
            """
            INSERT INTO hosting 
            (paid_until, paid_by, last_payment, last_payment_amount, last_payment_method) 
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
            """,
            new_expiration.isoformat(), 
            int(user_id) if user_id else None,
            payment_amount,
            payment_method
        )
    
    status_message = f"Successfully extended hosting by {days} days"
    if is_expired:
        status_message += " (started from current time due to expired subscription)"
    
    return {
        "success": True,
        "message": status_message,
        "previous_expiration": base_date.isoformat(),
        "new_expiration": new_expiration.isoformat(),
        "days_added": days,
        "payment_amount": payment_amount,
        "payment_method": payment_method,
        "was_expired": is_expired
    }, 200