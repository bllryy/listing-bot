route = "/seller/get/accounts"

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
        "accounts": [],
        "profiles": [],
        "alts": []
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
        
        # Get accounts with stats
        accounts = await bot.db.fetchall("""
            SELECT a.uuid, a.username, a.profile, a.payment_methods, a.additional_information, 
                   a.price, a.number, a.channel_id, a.message_id, a.listed_by, a.show_username,
                   s.skill_average, s.catacombs_level, s.zombie_slayer_level, s.spider_slayer_level,
                   s.wolf_slayer_level, s.enderman_slayer_level, s.blaze_slayer_level, 
                   s.vampire_slayer_level, s.skyblock_level, s.total_networth, s.soulbound_networth,
                   s.liquid_networth, s.heart_of_the_mountain_level, s.mithril_powder, 
                   s.gemstone_powder, s.glaciate_powder
            FROM accounts a
            LEFT JOIN account_stats s ON a.uuid = s.uuid
            WHERE a.listed_by = ?
        """, user_id)
        
        data["accounts"] = []
        for account in accounts:
            try:
                # Create AccountObject from basic fields
                account_obj = AccountObject(*account[:11])  # First 11 fields for AccountObject
                account_dict = account_obj.to_dict()
                
                # Add stats if available
                if account[11] is not None:  # skill_average exists
                    account_dict["stats"] = {
                        "skill_average": account[11],
                        "catacombs_level": account[12],
                        "zombie_slayer_level": account[13],
                        "spider_slayer_level": account[14],
                        "wolf_slayer_level": account[15],
                        "enderman_slayer_level": account[16],
                        "blaze_slayer_level": account[17],
                        "vampire_slayer_level": account[18],
                        "skyblock_level": account[19],
                        "total_networth": account[20],
                        "soulbound_networth": account[21],
                        "liquid_networth": account[22],
                        "heart_of_the_mountain_level": account[23],
                        "mithril_powder": account[24],
                        "gemstone_powder": account[25],
                        "glaciate_powder": account[26]
                    }
                else:
                    account_dict["stats"] = None
                
                data["accounts"].append(account_dict)
            except Exception as e:
                # Skip problematic entries and log if needed
                if hasattr(bot, 'logger'):
                    bot.logger.warning(f"Error processing account for user {user_id}: {e}")
        
        # Get profiles with stats
        profiles = await bot.db.fetchall("""
            SELECT p.uuid, p.username, p.profile, p.payment_methods, p.additional_information, 
                   p.price, p.number, p.channel_id, p.message_id, p.listed_by, p.show_username,
                   s.total_networth, s.soulbound_networth, s.liquid_networth, s.minion_slots,
                   s.minion_bonus_slots, s.maxed_collections, s.unlocked_collections
            FROM profiles p
            LEFT JOIN profile_stats s ON p.uuid = s.uuid AND p.profile = s.profile
            WHERE p.listed_by = ?
        """, user_id)
        
        data["profiles"] = []
        for profile in profiles:
            try:
                # Create ProfileObject from basic fields
                profile_obj = ProfileObject(*profile[:11])  # First 11 fields for ProfileObject
                profile_dict = profile_obj.to_dict()
                
                # Add stats if available
                if profile[11] is not None:  # total_networth exists
                    profile_dict["stats"] = {
                        "total_networth": profile[11],
                        "soulbound_networth": profile[12],
                        "liquid_networth": profile[13],
                        "minion_slots": profile[14],
                        "minion_bonus_slots": profile[15],
                        "maxed_collections": profile[16],
                        "unlocked_collections": profile[17]
                    }
                else:
                    profile_dict["stats"] = None
                
                data["profiles"].append(profile_dict)
            except Exception as e:
                # Skip problematic entries and log if needed
                if hasattr(bot, 'logger'):
                    bot.logger.warning(f"Error processing profile for user {user_id}: {e}")
        
        # Get alts with stats
        alts = await bot.db.fetchall("""
            SELECT a.uuid, a.username, a.profile, a.payment_methods, a.additional_information, 
                   a.price, a.number, a.channel_id, a.message_id, a.listed_by, a.show_username,
                   a.farming, a.mining,
                   s.skill_average, s.catacombs_level, s.zombie_slayer_level, s.spider_slayer_level,
                   s.wolf_slayer_level, s.enderman_slayer_level, s.blaze_slayer_level, 
                   s.vampire_slayer_level, s.skyblock_level, s.total_networth, s.soulbound_networth,
                   s.liquid_networth, s.heart_of_the_mountain_level, s.mithril_powder, 
                   s.gemstone_powder, s.glaciate_powder
            FROM alts a
            LEFT JOIN account_stats s ON a.uuid = s.uuid
            WHERE a.listed_by = ?
        """, user_id)
        
        data["alts"] = []
        for alt in alts:
            try:
                # Create AltObject from all alt-specific fields
                alt_obj = AltObject(*alt[:13])  # First 13 fields for AltObject (includes farming/mining)
                alt_dict = alt_obj.to_dict()
                
                # Add stats if available
                if alt[13] is not None:  # skill_average exists
                    alt_dict["stats"] = {
                        "skill_average": alt[13],
                        "catacombs_level": alt[14],
                        "zombie_slayer_level": alt[15],
                        "spider_slayer_level": alt[16],
                        "wolf_slayer_level": alt[17],
                        "enderman_slayer_level": alt[18],
                        "blaze_slayer_level": alt[19],
                        "vampire_slayer_level": alt[20],
                        "skyblock_level": alt[21],
                        "total_networth": alt[22],
                        "soulbound_networth": alt[23],
                        "liquid_networth": alt[24],
                        "heart_of_the_mountain_level": alt[25],
                        "mithril_powder": alt[26],
                        "gemstone_powder": alt[27],
                        "glaciate_powder": alt[28]
                    }
                else:
                    alt_dict["stats"] = None
                
                data["alts"].append(alt_dict)
            except Exception as e:
                # Skip problematic entries and log if needed
                if hasattr(bot, 'logger'):
                    bot.logger.warning(f"Error processing alt for user {user_id}: {e}")
        
        return data, 200

    return data, 403
