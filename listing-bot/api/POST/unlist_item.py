route = "/unlist/item"
from quart import current_app, request, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key
import discord

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    try:
        data = await request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body must contain JSON data"
            }), 400
    except Exception:
        return jsonify({
            "success": False,
            "error": "Invalid JSON in request body"
        }), 400
    
    channel_id = data.get("channel_id")
    message_id = data.get("message_id")
    
    if not channel_id or not message_id:
        return jsonify({
            "success": False,
            "error": "Both channel_id and message_id are required"
        }), 400
    
    try:
        channel_id = int(channel_id)
        message_id = int(message_id)
    except ValueError:
        return jsonify({
            "success": False,
            "error": "channel_id and message_id must be valid integers"
        }), 400
    
    account_item = await bot.db.fetchone(
        "SELECT uuid, username, type FROM (SELECT uuid, username, 'account' as type FROM accounts WHERE channel_id = ? AND message_id = ?) as result",
        channel_id, message_id
    )
    
    alt_item = await bot.db.fetchone(
        "SELECT uuid, username, type FROM (SELECT uuid, username, 'alt' as type FROM alts WHERE channel_id = ? AND message_id = ?) as result",
        channel_id, message_id
    )
    
    profile_item = await bot.db.fetchone(
        "SELECT uuid, username, profile, type FROM (SELECT uuid, username, profile, 'profile' as type FROM profiles WHERE channel_id = ? AND message_id = ?) as result",
        channel_id, message_id
    )
    
    found_item = None
    item_type = None
    
    if account_item:
        found_item = account_item
        item_type = "account"
    elif alt_item:
        found_item = alt_item
        item_type = "alt"
    elif profile_item:
        found_item = profile_item
        item_type = "profile"
    
    if not found_item:
        return jsonify({
            "success": False,
            "error": "No item found with the specified channel_id and message_id"
        }), 404
    
    try:
        if item_type == "account":
            await bot.db.execute("DELETE FROM accounts WHERE channel_id = ? AND message_id = ?", channel_id, message_id)
        elif item_type == "alt":
            await bot.db.execute("DELETE FROM alts WHERE channel_id = ? AND message_id = ?", channel_id, message_id)
        elif item_type == "profile":
            await bot.db.execute("DELETE FROM profiles WHERE channel_id = ? AND message_id = ?", channel_id, message_id)
        
        channel_deleted = False
        try:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.delete(reason="Item unlisted via API")
                channel_deleted = True
        except discord.NotFound:
            channel_deleted = True
        except discord.Forbidden:
            pass
        except Exception as e:
            pass
        
        response_data = {
            "uuid": found_item[0],
            "username": found_item[1],
            "type": item_type,
            "channel_id": str(channel_id),
            "message_id": str(message_id),
            "channel_deleted": channel_deleted
        }
        
        if item_type == "profile":
            response_data["profile"] = found_item[2]
        
        return jsonify({
            "success": True,
            "message": f"Successfully unlisted {item_type}",
            "data": response_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to delete item from database: {str(e)}"
        }), 500
