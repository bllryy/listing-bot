route = "/seller/get/configuration"

from bot.bot import Bot
from quart import current_app, request
from api.auth_utils import require_api_key
from bot.util.helper.account import AccountObject
from bot.util.helper.profile import ProfileObject
from bot.util.helper.macro_alt import AltObject

@require_api_key
async def func():
    bot: Bot = current_app.bot

    user_id = request.args.get("user_id")

    main_guild = await bot.db.get_config("main_guild")
    guild = bot.get_guild(main_guild)

    data = {
        "seller": False,
        "sellauth": {
            "store_id": None,
            "store_name": None,
            "product_id": None,
            "variant_id": None
        },
        "payment_methods": [],
        "payment_details": {
            "paypal_email": None,
            "business_name": None,
            "currency": None,
            "bitcoin_address": None,
            "ethereum_address": None,
            "litecoin_address": None
        }
    }

    if not guild:
        return data, 404
    
    member = guild.get_member(int(user_id))
    if not member:
        return data, 404

    seller_role = await bot.db.get_config("seller_role")
    role = guild.get_role(seller_role)
    if not role:
        return data, 404

    if role in member.roles:
        data["seller"] = True

        sellauth_info = await bot.db.fetchone("SELECT shop_id, shop_name, product_id, variant_id FROM sellauth_config WHERE user_id = ?", user_id)
        if sellauth_info:
            data["sellauth"] = {
                "store_id": sellauth_info[0],
                "store_name": sellauth_info[1],
                "product_id": sellauth_info[2],
                "variant_id": sellauth_info[3]
            }

        payment_methods = await bot.db.fetchone("SELECT payment_methods FROM sellers WHERE user_id = ?", user_id)
        if payment_methods and payment_methods[0]:
            try:
                # payment_methods[0] is a string representation of a list
                import ast
                data["payment_methods"] = ast.literal_eval(payment_methods[0])
            except (ValueError, SyntaxError):
                # If it's not a valid list string, treat it as a single method or split by delimiter
                methods_str = payment_methods[0]
                if '/' in methods_str:
                    data["payment_methods"] = methods_str.split('/')
                elif methods_str:
                    data["payment_methods"] = [methods_str]
                else:
                    data["payment_methods"] = []
        else:
            data["payment_methods"] = []

        payment_details = await bot.db.fetchone("SELECT paypal_email, business_name, currency, bitcoin_address, ethereum_address, litecoin_address FROM payment_details WHERE user_id = ?", user_id)
        if payment_details:
            data["payment_details"] = {
                "paypal_email": payment_details[0],
                "business_name": payment_details[1],
                "currency": payment_details[2],
                "bitcoin_address": payment_details[3],
                "ethereum_address": payment_details[4],
                "litecoin_address": payment_details[5]
            }

        return data, 200

    return data, 403
