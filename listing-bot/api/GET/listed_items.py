route = "/listed/items"
from quart import current_app, jsonify
from bot.bot import Bot
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot

    accounts_query = await bot.db.fetchall(
        """
        SELECT a.uuid, a.username, a.price, a.listed_by, a.profile, a.payment_methods, 
               a.additional_information, a.number, a.channel_id, a.message_id, a.show_username,
               s.skill_average, s.catacombs_level, s.zombie_slayer_level, s.spider_slayer_level,
               s.wolf_slayer_level, s.enderman_slayer_level, s.blaze_slayer_level, 
               s.vampire_slayer_level, s.skyblock_level, s.total_networth, s.soulbound_networth,
               s.liquid_networth, s.heart_of_the_mountain_level, s.mithril_powder, 
               s.gemstone_powder, s.glaciate_powder
        FROM accounts a
        LEFT JOIN account_stats s ON a.uuid = s.uuid
        WHERE s.uuid IS NOT NULL
        """
    )
    
    alts_query = await bot.db.fetchall(
        """
        SELECT a.uuid, a.username, a.price, a.listed_by, a.profile, a.payment_methods, 
               a.additional_information, a.number, a.channel_id, a.message_id, a.show_username,
               a.farming, a.mining,
               s.skill_average, s.catacombs_level, s.zombie_slayer_level, s.spider_slayer_level,
               s.wolf_slayer_level, s.enderman_slayer_level, s.blaze_slayer_level, 
               s.vampire_slayer_level, s.skyblock_level, s.total_networth, s.soulbound_networth,
               s.liquid_networth, s.heart_of_the_mountain_level, s.mithril_powder, 
               s.gemstone_powder, s.glaciate_powder
        FROM alts a
        LEFT JOIN account_stats s ON a.uuid = s.uuid
        WHERE s.uuid IS NOT NULL
        """
    )
    
    profiles_query = await bot.db.fetchall(
        """
        SELECT p.uuid, p.username, p.price, p.listed_by, p.profile, p.payment_methods, 
               p.additional_information, p.number, p.channel_id, p.message_id, p.show_username,
               s.total_networth, s.soulbound_networth, s.liquid_networth, s.minion_slots,
               s.minion_bonus_slots, s.maxed_collections, s.unlocked_collections
        FROM profiles p
        LEFT JOIN profile_stats s ON p.uuid = s.uuid AND p.profile = s.profile
        WHERE s.uuid IS NOT NULL AND s.profile IS NOT NULL
        """
    )
    
    accounts_data = []
    for row in accounts_query:
        account = {
            "type": "account",
            "uuid": row[0],
            "username": row[1],
            "price": row[2],
            "listed_by": str(row[3]) if row[3] else None,
            "profile": row[4],
            "payment_methods": row[5],
            "additional_information": row[6],
            "number": row[7],
            "channel_id": str(row[8]) if row[8] else None,
            "message_id": str(row[9]) if row[9] else None,
            "show_username": row[10],
            "stats": {
                "skill_average": row[11],
                "catacombs_level": row[12],
                "zombie_slayer_level": row[13],
                "spider_slayer_level": row[14],
                "wolf_slayer_level": row[15],
                "enderman_slayer_level": row[16],
                "blaze_slayer_level": row[17],
                "vampire_slayer_level": row[18],
                "skyblock_level": row[19],
                "total_networth": row[20],
                "soulbound_networth": row[21],
                "liquid_networth": row[22],
                "heart_of_the_mountain_level": row[23],
                "mithril_powder": row[24],
                "gemstone_powder": row[25],
                "glaciate_powder": row[26]
            }
        }
        accounts_data.append(account)
    
    alts_data = []
    for row in alts_query:
        alt = {
            "type": "alt",
            "uuid": row[0],
            "username": row[1],
            "price": row[2],
            "listed_by": str(row[3]) if row[3] else None,
            "profile": row[4],
            "payment_methods": row[5],
            "additional_information": row[6],
            "number": row[7],
            "channel_id": str(row[8]) if row[8] else None,
            "message_id": str(row[9]) if row[9] else None,
            "show_username": row[10],
            "farming": row[11],
            "mining": row[12],
            "stats": {
                "skill_average": row[13],
                "catacombs_level": row[14],
                "zombie_slayer_level": row[15],
                "spider_slayer_level": row[16],
                "wolf_slayer_level": row[17],
                "enderman_slayer_level": row[18],
                "blaze_slayer_level": row[19],
                "vampire_slayer_level": row[20],
                "skyblock_level": row[21],
                "total_networth": row[22],
                "soulbound_networth": row[23],
                "liquid_networth": row[24],
                "heart_of_the_mountain_level": row[25],
                "mithril_powder": row[26],
                "gemstone_powder": row[27],
                "glaciate_powder": row[28]
            }
        }
        alts_data.append(alt)
    
    profiles_data = []
    for row in profiles_query:
        profile = {
            "type": "profile",
            "uuid": row[0],
            "username": row[1],
            "price": row[2],
            "listed_by": str(row[3]) if row[3] else None,
            "profile": row[4],
            "payment_methods": row[5],
            "additional_information": row[6],
            "number": row[7],
            "channel_id": str(row[8]) if row[8] else None,
            "message_id": str(row[9]) if row[9] else None,
            "show_username": row[10],
            "stats": {
                "total_networth": row[11],
                "soulbound_networth": row[12],
                "liquid_networth": row[13],
                "minion_slots": row[14],
                "minion_bonus_slots": row[15],
                "maxed_collections": row[16],
                "unlocked_collections": row[17]
            }
        }
        profiles_data.append(profile)
    
    all_items = accounts_data + alts_data + profiles_data
    
    return jsonify({
        "success": True,
        "data": {
            "accounts": accounts_data,
            "alts": alts_data,
            "profiles": profiles_data,
        },
        "counts": {
            "total": len(all_items),
            "accounts": len(accounts_data),
            "alts": len(alts_data),
            "profiles": len(profiles_data)
        }
    }), 200
