route = "/seller/list/item"

from bot.bot import Bot
from quart import current_app, request, jsonify
from api.auth_utils import require_api_key
from bot.util.list import list_account, list_profile, list_alt
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

    # Validate required fields
    user_id = data.get("user_id")
    item_type = data.get("type")
    item_data = data.get("item")

    if not user_id:
        return jsonify({
            "success": False,
            "error": "user_id is required"
        }), 400

    if not item_type:
        return jsonify({
            "success": False,
            "error": "type is required (account, profile, or alt)"
        }), 400

    if not item_data or not isinstance(item_data, dict):
        return jsonify({
            "success": False,
            "error": "item data is required and must be an object"
        }), 400

    # Validate item_type
    if item_type not in ["account", "profile", "alt"]:
        return jsonify({
            "success": False,
            "error": "type must be 'account', 'profile', or 'alt'"
        }), 400

    try:
        user_id = str(user_id)
    except:
        return jsonify({
            "success": False,
            "error": "user_id must be a valid string"
        }), 400

    # Validate user permissions
    main_guild = await bot.db.get_config("main_guild")
    guild = bot.get_guild(main_guild)
    
    if not guild:
        return jsonify({
            "success": False,
            "error": "Main guild not configured or not found"
        }), 404
    
    member = guild.get_member(int(user_id))
    if not member:
        return jsonify({
            "success": False,
            "error": "User not found in guild"
        }), 404

    seller_role = await bot.db.get_config("seller_role")
    role = guild.get_role(seller_role)
    if not role:
        return jsonify({
            "success": False,
            "error": "Seller role not configured"
        }), 404

    if role not in member.roles:
        return jsonify({
            "success": False,
            "error": "User is not a seller"
        }), 403

    # Extract common fields from item data
    try:
        username = item_data.get("username")
        price = item_data.get("price")
        payment_methods = item_data.get("payment_methods", "")
        ping = item_data.get("ping", False)
        additional_information = item_data.get("additional_information", "")
        show_ign = item_data.get("show_username", True)
        profile = item_data.get("profile", "")
        number = item_data.get("number")

        # Validate required fields
        if not username:
            return jsonify({
                "success": False,
                "error": "username is required in item data"
            }), 400

        # Validate and convert price
        if price is None:
            return jsonify({
                "success": False,
                "error": "price is required"
            }), 400
        
        try:
            price = float(price)  # Convert to float first to handle string numbers
            if price < 0:
                return jsonify({
                    "success": False,
                    "error": "price must be non-negative"
                }), 400
            price = int(price)  # Convert to integer for storage
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "price must be a valid number"
            }), 400

        # Convert boolean fields properly
        if isinstance(ping, str):
            ping = ping.lower() == "true"
        else:
            ping = bool(ping)
            
        if isinstance(show_ign, str):
            show_ign = show_ign.lower() == "true"
        else:
            show_ign = bool(show_ign)


        class Icon:
            def __init__(self):
                self.url = "https://noemt.dev"
    
        class Guild:
            def __init__(self):
                self.name = "API Listing Bot"
                self.icon = Icon()

        class Context:
            def __init__(self):
                self.guild = Guild()

        ctx = Context()

        farming = True
        mining = False
        
        if item_type == "alt":
            farming = item_data.get("farming", True)
            mining = item_data.get("mining", False)
            
            # Convert boolean fields properly for alt-specific fields
            if isinstance(farming, str):
                farming = farming.lower() == "true"
            else:
                farming = bool(farming)
                
            if isinstance(mining, str):
                mining = mining.lower() == "true"
            else:
                mining = bool(mining)

        # Create a unique task ID for tracking
        import uuid
        task_id = str(uuid.uuid4())

        # Execute listing directly (synchronous approach)
        try:
            result_embed = None
            
            if item_type == "account":
                result_embed = await list_account(
                    bot=bot,
                    username=username,
                    price=price,
                    payment_methods=payment_methods,
                    ping=ping,
                    additional_information=additional_information,
                    show_ign=show_ign,
                    profile=profile,
                    number=number,
                    ctx=ctx,
                    listed_by=user_id
                )

            elif item_type == "profile":
                result_embed = await list_profile(
                    bot=bot,
                    username=username,
                    price=price,
                    payment_methods=payment_methods,
                    ping=ping,
                    additional_information=additional_information,
                    show_ign=show_ign,
                    profile=profile,
                    number=number,
                    listed_by=user_id
                )

            elif item_type == "alt":
                result_embed = await list_alt(
                    bot=bot,
                    username=username,
                    price=price,
                    payment_methods=payment_methods,
                    farming=farming,
                    mining=mining,
                    ping=ping,
                    additional_information=additional_information,
                    show_ign=show_ign,
                    profile=profile,
                    number=number,
                    listed_by=user_id
                )

            # Debug: Log what we got back
            if hasattr(bot, 'logger'):
                bot.logger.info(f"Listing result for {username}: {result_embed}")
                bot.logger.info(f"Result color: {result_embed.color if result_embed else 'None'}")
                bot.logger.info(f"Result description: {result_embed.description if result_embed else 'None'}")

            # Check if listing was successful
            if result_embed and hasattr(result_embed, 'color'):
                if result_embed.color == discord.Color.green():
                    return jsonify({
                        "success": True,
                        "type": item_type,
                        "message": result_embed.description,
                        "username": username,
                        "price": price,
                        "user_id": user_id,
                        "task_id": task_id
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": result_embed.description if hasattr(result_embed, 'description') else "Listing failed",
                        "type": item_type,
                        "username": username,
                        "task_id": task_id
                    }), 400
            else:
                return jsonify({
                    "success": False,
                    "error": f"No valid result returned from list_{item_type} function",
                    "type": item_type,
                    "username": username,
                    "task_id": task_id
                }), 500
                
        except Exception as e:
            # Log the full traceback for debugging
            import traceback
            error_details = traceback.format_exc()
            if hasattr(bot, 'logger'):
                bot.logger.error(f"Error in list_{item_type} for {username}: {error_details}")
            
            return jsonify({
                "success": False,
                "error": f"Error while listing {item_type}: {str(e)}",
                "type": item_type,
                "username": username,
                "task_id": task_id,
                "debug_info": str(e)
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An error occurred while listing the {item_type}: {str(e)}"
        }), 500
