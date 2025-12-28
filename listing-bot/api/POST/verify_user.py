route = "/verify/user"
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
    
    action_id = data.get("action_id")

    if not action_id:
        return jsonify({
            "success": False,
            "error": "action_id is required"
        }), 400
    
    try:
        action_id = int(action_id)
    except ValueError:
        return jsonify({
            "success": False,
            "error": "action_id must be a valid integer"
        }), 400
    
    action = await bot.db.fetchone(
        "SELECT user_id FROM auth_actions WHERE action_id = ?",
        action_id
    )
    if not action:
        return jsonify({
            "success": False,
            "error": "No action found with the specified action_id"
        }), 404

    user_id = action[0]

    guild_id = await bot.db.get_config("main_guild")
    guild = bot.get_guild(guild_id)
    if not guild:
        return {"error": "Failed to get guild"}, 404
    
    member = await guild.fetch_member(user_id)
    if not member:
        return {"error": "Failed to get member"}, 404
    
    role_id = await bot.db.get_config("regular_role")
    role = guild.get_role(role_id)
    if not role:
        return {"error": "Failed to get role"}, 404
    
    if role in member.roles:

        await bot.db.execute(
            "UPDATE auth_actions SET resolved = ? WHERE action_id = ?",
            1, action_id
        )
        
        return jsonify({
            "success": True,
            "message": "User is already verified"
        }), 200
    
    try:
        await member.add_roles(role, reason="User verification via API")
        
        try:
            embed = discord.Embed(
                title="✅ Account Verified",
                description="Your account has been manually verified by the bot owner. You now have access to the server!",
                color=discord.Color.green()
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass
        
        await bot.db.execute(
            "UPDATE auth_actions SET resolved = ? WHERE action_id = ?",
            1, action_id
        )
        return jsonify({
            "success": True,
            "message": "User has been successfully verified"
        }), 200
    
    except discord.Forbidden:
        return jsonify({
            "success": False,
            "error": "Bot does not have permission to manage roles"
        }), 403
    
    except discord.HTTPException as e:
        return jsonify({
            "success": False,
            "error": f"Failed to add role: {str(e)}"
        }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500



