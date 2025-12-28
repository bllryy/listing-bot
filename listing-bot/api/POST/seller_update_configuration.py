route = "/seller/update/configuration"

from bot.bot import Bot
from quart import current_app, request, jsonify
from api.auth_utils import require_api_key

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

    # Validate required user_id field
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({
            "success": False,
            "error": "user_id is required"
        }), 400

    try:
        user_id = str(user_id)
    except:
        return jsonify({
            "success": False,
            "error": "user_id must be a valid string"
        }), 400

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

    results = {}
    errors = []

    if "sellauth" in data:
        sellauth_data = data["sellauth"]
        if isinstance(sellauth_data, dict):
            try:
                store_id = sellauth_data.get("store_id")
                store_name = sellauth_data.get("store_name")
                product_id = sellauth_data.get("product_id")
                variant_id = sellauth_data.get("variant_id")

                await bot.db.execute("DELETE FROM sellauth_config WHERE user_id = ?", user_id)
                
                if any([store_id, store_name, product_id, variant_id]):
                    await bot.db.execute(
                        "INSERT INTO sellauth_config (user_id, shop_id, shop_name, product_id, variant_id) VALUES (?, ?, ?, ?, ?)",
                        user_id, store_id, store_name, product_id, variant_id
                    )
                
                results["sellauth"] = {"status": "updated"}
            except Exception as e:
                errors.append(f"Failed to update sellauth configuration: {str(e)}")

    if "payment_methods" in data:
        payment_methods = data["payment_methods"]
        try:
            if isinstance(payment_methods, str):
                payment_methods = [payment_methods] if payment_methods else []
            elif not isinstance(payment_methods, list):
                payment_methods = []

            existing_seller = await bot.db.fetchone("SELECT user_id FROM sellers WHERE user_id = ?", user_id)
            
            if existing_seller:
                await bot.db.execute("UPDATE sellers SET payment_methods = ? WHERE user_id = ?", 
                                   "/".join(payment_methods), user_id)
            else:
                await bot.db.execute("INSERT INTO sellers (user_id, payment_methods) VALUES (?, ?)", 
                                   user_id, "/".join(payment_methods))
            
            results["payment_methods"] = {"status": "updated", "value": payment_methods}
        except Exception as e:
            errors.append(f"Failed to update payment methods: {str(e)}")

    if "payment_details" in data:
        payment_details = data["payment_details"]
        if isinstance(payment_details, dict):
            try:
                paypal_email = payment_details.get("paypal_email")
                business_name = payment_details.get("business_name")
                currency = payment_details.get("currency")
                bitcoin_address = payment_details.get("bitcoin_address")
                ethereum_address = payment_details.get("ethereum_address")
                litecoin_address = payment_details.get("litecoin_address")

                existing_seller = await bot.db.fetchone("SELECT user_id FROM payment_details WHERE user_id = ?", user_id)
                
                if not existing_seller:
                    await bot.db.execute("INSERT INTO payment_details (user_id, paypal_email, business_name, currency, bitcoin_address, ethereum_address, litecoin_address) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                       user_id, paypal_email, business_name, currency, bitcoin_address, ethereum_address, litecoin_address)

                await bot.db.execute("""
                    INSERT OR REPLACE INTO payment_details 
                    (user_id, paypal_email, business_name, currency, bitcoin_address, ethereum_address, litecoin_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, user_id, paypal_email, business_name, currency, bitcoin_address, ethereum_address, litecoin_address)
                
                results["payment_details"] = {"status": "updated"}
            except Exception as e:
                errors.append(f"Failed to update payment details: {str(e)}")

    response_data = {
        "success": len(errors) == 0,
        "results": results,
        "updated_sections": len(results),
        "user_id": user_id
    }

    if errors:
        response_data["errors"] = errors
        response_data["error_count"] = len(errors)

    status_code = 200 if len(errors) == 0 else 207
    return jsonify(response_data), status_code
