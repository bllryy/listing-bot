route = "/channels"
from quart import current_app, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key
import discord

@require_api_key
async def func():
    bot: Bot = current_app.bot

    guild_id = await bot.db.get_config("main_guild")
    if not guild_id:
        return jsonify({
            "success": False,
            "error": "Main guild not configured"
        }), 400
    
    guild = bot.get_guild(guild_id)
    if not guild:
        return jsonify({
            "success": False,
            "error": "Guild not found"
        }), 404

    channels_data = []
    categories_data = []

    for channel in guild.channels:
        if isinstance(channel, discord.CategoryChannel):
            category_data = {
                "id": str(channel.id),
                "name": channel.name,
                "type": "category",
                "position": channel.position,
                "channels": []
            }
            
            for child_channel in channel.channels:
                channel_type = "unknown"
                if isinstance(child_channel, discord.TextChannel):
                    channel_type = "text"
                elif isinstance(child_channel, discord.VoiceChannel):
                    channel_type = "voice"
                elif isinstance(child_channel, discord.StageChannel):
                    channel_type = "stage"
                elif isinstance(child_channel, discord.ForumChannel):
                    channel_type = "forum"
                
                category_data["channels"].append({
                    "id": str(child_channel.id),
                    "name": child_channel.name,
                    "type": channel_type,
                    "position": child_channel.position
                })
            
            category_data["channels"].sort(key=lambda x: x["position"])
            categories_data.append(category_data)
            
        else:
            if channel.category is None:
                channel_type = "unknown"
                if isinstance(channel, discord.TextChannel):
                    channel_type = "text"
                elif isinstance(channel, discord.VoiceChannel):
                    channel_type = "voice"
                elif isinstance(channel, discord.StageChannel):
                    channel_type = "stage"
                elif isinstance(channel, discord.ForumChannel):
                    channel_type = "forum"
                
                channels_data.append({
                    "id": str(channel.id),
                    "name": channel.name,
                    "type": channel_type,
                    "position": channel.position
                })

    channels_data.sort(key=lambda x: x["position"])
    
    categories_data.sort(key=lambda x: x["position"])

    return jsonify({
        "success": True,
        "guild_id": str(guild.id),
        "guild_name": guild.name,
        "data": {
            "standalone_channels": channels_data,
            "categories": categories_data
        },
        "counts": {
            "standalone_channels": len(channels_data),
            "categories": len(categories_data),
            "total_channels": len([ch for ch in guild.channels if not isinstance(ch, discord.CategoryChannel)])
        }
    })
