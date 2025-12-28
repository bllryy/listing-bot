route = "/stats"

from bot.bot import Bot
from quart import current_app
from datetime import datetime, timezone
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    # Get payment info
    hosting_data = await bot.db.fetchone(
        "SELECT paid_until, paid_by, last_payment, last_payment_amount, last_payment_method FROM hosting LIMIT 1"
    )
    
    payment_info = {}
    if not hosting_data or not hosting_data[0]:
        payment_info = {
            "is_paid": False,
            "expires_at": None,
            "days_remaining": 0,
            "paid_by": None,
            "last_payment": None,
            "last_payment_amount": None,
            "last_payment_method": None
        }
    else:
        paid_until, paid_by, last_payment, last_payment_amount, last_payment_method = hosting_data
        # Fix 1: Ensure paid_until_date has timezone info
        paid_until_date = datetime.fromisoformat(paid_until.replace(' ', 'T'))
        if paid_until_date.tzinfo is None:
            paid_until_date = paid_until_date.replace(tzinfo=timezone.utc)
            
        current_time = datetime.now(timezone.utc)
        
        is_paid = current_time < paid_until_date
        days_remaining = (paid_until_date - current_time).days if is_paid else 0
        
        payment_info = {
            "is_paid": is_paid,
            "expires_at": paid_until,
            "days_remaining": days_remaining,
            "paid_by": paid_by,
            "last_payment": last_payment,
            "last_payment_amount": last_payment_amount,
            "last_payment_method": last_payment_method
        }
    
    # Get AI credits info
    ai_config = await bot.db.fetchone(
        "SELECT monthly_limit, remaining_credits_free, remaining_credits_paid, last_reset FROM ai_config LIMIT 1"
    )
    
    ai_credits = {}
    if ai_config:
        monthly_limit, remaining_free, remaining_paid, last_reset = ai_config
        
        # Fix 2: Ensure last_reset_date has timezone info
        if last_reset:
            last_reset_date = datetime.fromisoformat(last_reset.replace(' ', 'T'))
            if last_reset_date.tzinfo is None:
                last_reset_date = last_reset_date.replace(tzinfo=timezone.utc)
        else:
            last_reset_date = datetime.now(timezone.utc)
            
        # Calculate next reset date (first of next month)
        next_month = last_reset_date.month + 1 if last_reset_date.month < 12 else 1
        next_year = last_reset_date.year + 1 if last_reset_date.month == 12 else last_reset_date.year
        next_reset = datetime(next_year, next_month, 1, tzinfo=timezone.utc)
        
        ai_credits = {
            "monthly_limit": monthly_limit,
            "remaining_free": remaining_free,
            "remaining_paid": remaining_paid,
            "total_remaining": remaining_free + remaining_paid,
            "last_reset": last_reset,
            "next_reset": next_reset.isoformat()
        }
    else:
        ai_credits = {
            "monthly_limit": 0,
            "remaining_free": 0,
            "remaining_paid": 0,
            "total_remaining": 0,
            "last_reset": None,
            "next_reset": None
        }
    
    # Get owner info
    owner_id = bot.owner_ids[0]
    owner = bot.get_user(owner_id)
    
    owner_info = {}
    if not owner:
        try:
            owner = await bot.fetch_user(owner_id)
        except:
            owner_info = {
                "id": owner_id,
                "name": "Unknown",
                "discriminator": "0000",
                "avatar_url": None,
                "created_at": None
            }
    
    if not owner_info:
        owner_info = {
            "id": owner.id,
            "name": owner.name,
            "display_name": owner.display_name if hasattr(owner, "display_name") else owner.name,
            "discriminator": owner.discriminator if hasattr(owner, "discriminator") else "0",
            "avatar_url": str(owner.avatar.url) if owner.avatar else None,
            "created_at": owner.created_at.isoformat() if hasattr(owner, "created_at") else None
        }
    
    # Get listings info
    accounts_count = await bot.db.fetchone("SELECT COUNT(*) FROM accounts")
    profiles_count = await bot.db.fetchone("SELECT COUNT(*) FROM profiles")
    alts_count = await bot.db.fetchone("SELECT COUNT(*) FROM alts")
    
    # Extract first element from each tuple (the count)
    accounts = accounts_count[0] if accounts_count else 0
    profiles = profiles_count[0] if profiles_count else 0
    alts = alts_count[0] if alts_count else 0
    
    listings_info = {
        "accounts": accounts,
        "profiles": profiles,
        "alts": alts,
        "total": accounts + profiles + alts
    }
    
    # Get tickets info
    tickets_data = await bot.db.fetchall("SELECT opened_by, channel_id FROM tickets")
    total_tickets = len(tickets_data)
    
    tickets_info = {
        "total": total_tickets,
        "active": total_tickets  # Assuming all tickets are active
    }
    
    # Get server members info
    main_guild_id = await bot.db.get_config("main_guild")
    guild = bot.get_guild(main_guild_id)
    
    members_info = {}
    if guild:
        # Calculate different member counts
        total_members = guild.member_count
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        online_count = len([m for m in guild.members if m.status != "offline" and not m.bot])
        
        members_info = {
            "member_count": total_members,
            "online_count": online_count,
            "bot_count": bot_count,
            "human_count": human_count
        }
    else:
        members_info = {
            "member_count": 0,
            "online_count": 0,
            "bot_count": 0,
            "human_count": 0
        }
    
    # Combine all data
    return {
        "bot": {
            "name": bot.user.name,
            "id": bot.user.id,
            "avatar_url": str(bot.user.avatar.url) if bot.user.avatar else None,
            "uptime": bot.uptime if hasattr(bot, "uptime") else None,
            "version": "2.2.2"
        },
        "payment": payment_info,
        "ai_credits": ai_credits,
        "owner": owner_info,
        "listings": listings_info,
        "tickets": tickets_info,
        "server": members_info,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, 200