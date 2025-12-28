route = "/bot/listings"

from bot.bot import Bot
from quart import current_app
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    accounts_count = await bot.db.fetchone("SELECT COUNT(*) FROM accounts")
    profiles_count = await bot.db.fetchone("SELECT COUNT(*) FROM profiles")
    alts_count = await bot.db.fetchone("SELECT COUNT(*) FROM alts")
    
    # Extract first element from each tuple (the count)
    accounts = accounts_count[0] if accounts_count else 0
    profiles = profiles_count[0] if profiles_count else 0
    alts = alts_count[0] if alts_count else 0
    
    return {
        "accounts": accounts,
        "profiles": profiles,
        "alts": alts,
        "total": accounts + profiles + alts
    }, 200