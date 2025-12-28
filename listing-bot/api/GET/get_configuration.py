route = "/config"
from quart import current_app, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key
from bot.util.constants import config_options
import discord

@require_api_key
async def func():
    bot: Bot = current_app.bot

    configuration_data = {}
    
    for option_key, option_info in config_options.items():
        try:
            current_value = await bot.db.get_config(option_key)
            
            expected_type = option_info["type"]
            description = option_info["description"]
            
            if expected_type == discord.TextChannel:
                type_name = "TextChannel"
            elif expected_type == discord.CategoryChannel:
                type_name = "CategoryChannel"
            elif expected_type == discord.Role:
                type_name = "Role"
            elif expected_type == int:
                type_name = "int"
            elif expected_type == float:
                type_name = "float"
            elif expected_type == bool:
                type_name = "bool"
            elif expected_type == str:
                type_name = "str"
            else:
                type_name = str(expected_type)
            
            # Convert Discord IDs to strings for consistency
            display_value = current_value
            if current_value is not None and type_name in ["TextChannel", "CategoryChannel", "Role"]:
                display_value = str(current_value)
            
            configuration_data[option_key] = {
                "value": display_value,
                "type": type_name,
                "description": description,
                "is_set": current_value is not None
            }
            
        except Exception as e:
            configuration_data[option_key] = {
                "value": None,
                "type": option_info["type"].__name__ if hasattr(option_info["type"], "__name__") else str(option_info["type"]),
                "description": option_info["description"],
                "is_set": False,
                "error": str(e)
            }
    
    return jsonify({
        "success": True,
        "configuration": configuration_data,
        "total_options": len(config_options)
    })
