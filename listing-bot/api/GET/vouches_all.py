from quart import request, jsonify
from api.auth_utils import require_api_key
from quart import current_app
from bot.bot import Bot

route = "/vouches/all"

@require_api_key
async def func():
    """Get all vouches from this bot's database"""
    try:
        bot: Bot = current_app.bot

        if not bot or not bot.db:
            return jsonify({"error": "Bot not available"}), 500
        
        # Get all vouches from database
        vouches = await bot.db.fetchall("SELECT user_id, message, avatar, username FROM vouches")
        
        vouch_data = []
        for user_id, message, avatar, username in vouches:
            # Extract amount from vouch message
            amount = extract_amount_from_message(message)
            
            # Extract mentioned user ID (person being vouched for)
            mentioned_user_id = extract_mentioned_user_from_message(message)
            
            vouch_data.append({
                "user_id": user_id,  # Person who sent the vouch
                "mentioned_user_id": mentioned_user_id,  # Person being vouched for
                "message": message,
                "avatar": avatar,
                "username": username,
                "amount": amount
            })
        
        # Get shop info if available
        shop_info = await bot.db.fetchone("SELECT shop_id, shop_name FROM sellauth_config LIMIT 1")
        shop_data = {
            "shop_id": shop_info[0] if shop_info else None,
            "shop_name": shop_info[1] if shop_info else None,
            "bot_name": bot.bot_name
        }
        
        return jsonify({
            "success": True,
            "shop_info": shop_data,
            "vouches": vouch_data,
            "total_vouches": len(vouch_data)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_amount_from_message(message):
    """Extract dollar amount from vouch message"""
    import re
    
    if not message:
        return 0.0
    
    # Patterns to match: $50, 50$, 50 bucks, etc.
    patterns = [
        r'(\d+(?:\.\d{2})?)\$',  # 50$ or 50.99$
        r'\$(\d+(?:\.\d{2})?)',  # $50 or $50.99
        r'(\d+(?:\.\d{2})?)\s?(?:bucks?|dollars?)',  # 50 bucks, 50 dollars
        r'(\d+(?:\.\d{2})?)\s?(?:usd|USD)',  # 50 USD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                continue
    
    return 0.0

def extract_mentioned_user_from_message(message):
    """Extract mentioned user ID from vouch message using regex"""
    import re
    
    if not message:
        return None
    
    # Look for Discord mention pattern: <@userid> or <@!userid>
    pattern = r'<@!?(\d+)>'
    match = re.search(pattern, message)
    
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    return None
