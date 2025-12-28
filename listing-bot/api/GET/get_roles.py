route = "/roles"
from quart import current_app, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key
import discord

@require_api_key
async def func():
    bot: Bot = current_app.bot

    # Get the main guild
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

    excluded_role_name = "𝔟𝔬𝔱𝔰.𝔫𝔬𝔢𝔪𝔱.𝔡𝔢𝔳 | 𝔪𝔞𝔡𝔢 𝔟𝔶 𝔫𝔬𝔪"
    
    roles_data = []
    
    for role in guild.roles:
        if role.name == excluded_role_name:
            continue
            
        color_hex = f"#{role.color.value:06x}" if role.color.value != 0 else "#000000"
        
        role_data = {
            "id": str(role.id),
            "name": role.name,
            "position": role.position,
            "color": color_hex,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
            "managed": role.managed,
            "is_default": role.is_default(),
            "member_count": len(role.members),
            "permissions": role.permissions.value
        }
        
        roles_data.append(role_data)
    
    roles_data.sort(key=lambda x: x["position"], reverse=True)

    return jsonify({
        "success": True,
        "guild_id": str(guild.id),
        "guild_name": guild.name,
        "roles": roles_data,
        "total_roles": len(roles_data),
        "excluded_role": excluded_role_name
    })
