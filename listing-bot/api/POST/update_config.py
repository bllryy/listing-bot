route = "/config"
from quart import current_app, request, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key
from bot.util.constants import config_options
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
    
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Request body must be a JSON object"
        }), 400
    
    results = {}
    errors = []
    
    for config_key, config_data in data.items():
        try:
            if config_key not in config_options:
                errors.append(f"Unknown configuration option: {config_key}")
                continue
            
            if not isinstance(config_data, dict) or "value" not in config_data or "type" not in config_data:
                errors.append(f"Invalid data structure for {config_key}. Must contain 'value' and 'type'")
                continue
            
            value_str = config_data["value"]
            type_name = config_data["type"]
            
            if value_str is None:
                try:
                    await bot.db.execute("DELETE FROM config WHERE key = ?", config_key)
                    results[config_key] = {"status": "deleted", "value": None}
                    continue
                except Exception as e:
                    errors.append(f"Failed to delete {config_key}: {str(e)}")
                    continue
            
            converted_value = None
            
            if type_name == "int":
                try:
                    converted_value = int(value_str)
                except ValueError:
                    errors.append(f"Invalid integer value for {config_key}: {value_str}")
                    continue
                    
            elif type_name == "float":
                try:
                    converted_value = float(value_str)
                except ValueError:
                    errors.append(f"Invalid float value for {config_key}: {value_str}")
                    continue
                    
            elif type_name == "bool":
                if isinstance(value_str, bool):
                    converted_value = value_str
                elif str(value_str).lower() in ['true', '1', 'yes', 'on']:
                    converted_value = True
                elif str(value_str).lower() in ['false', '0', 'no', 'off']:
                    converted_value = False
                else:
                    errors.append(f"Invalid boolean value for {config_key}: {value_str}")
                    continue
                    
            elif type_name == "str":
                converted_value = str(value_str)
                
            elif type_name in ["TextChannel", "CategoryChannel", "Role"]:
                try:
                    converted_value = int(value_str)
                    
                    guild_id = await bot.db.get_config("main_guild")
                    if guild_id:
                        guild = bot.get_guild(guild_id)
                        if guild:
                            if type_name == "TextChannel":
                                channel = guild.get_channel(converted_value)
                                if not channel or not isinstance(channel, discord.TextChannel):
                                    errors.append(f"Invalid TextChannel ID for {config_key}: {value_str}")
                                    continue
                            elif type_name == "CategoryChannel":
                                channel = guild.get_channel(converted_value)
                                if not channel or not isinstance(channel, discord.CategoryChannel):
                                    errors.append(f"Invalid CategoryChannel ID for {config_key}: {value_str}")
                                    continue
                            elif type_name == "Role":
                                role = guild.get_role(converted_value)
                                if not role:
                                    errors.append(f"Invalid Role ID for {config_key}: {value_str}")
                                    continue
                        
                except ValueError:
                    errors.append(f"Invalid ID format for {config_key}: {value_str}")
                    continue
            else:
                errors.append(f"Unsupported type '{type_name}' for {config_key}")
                continue
            
            try:
                success = await bot.db.update_config(config_key, converted_value)
                if success:
                    # Return string format for Discord IDs for consistency
                    return_value = converted_value
                    if type_name in ["TextChannel", "CategoryChannel", "Role"]:
                        return_value = str(converted_value)
                    
                    results[config_key] = {
                        "status": "updated",
                        "value": return_value,
                        "type": type_name
                    }
                else:
                    errors.append(f"Database update failed for {config_key}")
            except Exception as e:
                errors.append(f"Error updating {config_key}: {str(e)}")
                
        except Exception as e:
            errors.append(f"Unexpected error processing {config_key}: {str(e)}")
    
    response_data = {
        "success": len(errors) == 0,
        "results": results,
        "updated_count": len(results),
        "total_sent": len(data)
    }
    
    if errors:
        response_data["errors"] = errors
        response_data["error_count"] = len(errors)
    
    status_code = 200 if len(errors) == 0 else 207
    return jsonify(response_data), status_code
