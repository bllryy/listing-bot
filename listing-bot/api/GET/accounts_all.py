route = "/api/accounts/all"
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

    sellers_query = await bot.db.fetchall(
        """
        SELECT user_id, payment_methods
        FROM sellers
        """
    )
    
    sellers_data = {}
    for seller in sellers_query:
        user_id, payment_methods = seller
        member = guild.get_member(user_id)
        
        sellers_data[str(user_id)] = {
            "user_id": str(user_id),
            "payment_methods": payment_methods,
            "discord_member": {
                "display_name": member.display_name if member else None,
                "avatar_url": str(member.avatar.url) if member and member.avatar else None,
                "joined_at": member.joined_at.isoformat() if member and member.joined_at else None,
                "is_online": member.status != discord.Status.offline if member else False
            } if member else None
        }

    vouches_query = await bot.db.fetchall(
        """
        SELECT message
        FROM vouches
        """
    )
    
    # Count vouches by scanning message content for seller mentions
    vouch_counts = {}
    for vouch_row in vouches_query:
        message = vouch_row[0]
        if message:
            # Look for user ID mentions in the message content
            for seller_id in sellers_data.keys():
                if seller_id in message:
                    vouch_counts[seller_id] = vouch_counts.get(seller_id, 0) + 1
    
    # Add vouch counts to sellers data
    for seller_id, vouch_count in vouch_counts.items():
        if seller_id in sellers_data:
            sellers_data[seller_id]["vouches"] = {
                "count": vouch_count
            }

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

    def get_channel_info(channel_id):
        """Helper function to get channel information"""
        if not channel_id:
            return {"name": None, "url": None, "category": None}
        
        channel = bot.get_channel(int(channel_id))
        if channel:
            category_info = None
            if channel.category:
                category_info = {
                    "id": str(channel.category.id),
                    "name": channel.category.name
                }
            
            return {
                "name": channel.name,
                "url": str(channel.jump_url) if hasattr(channel, 'jump_url') else None,
                "category": category_info
            }
        else:
            return {"name": "Unknown Channel", "url": None, "category": None}

    accounts_data = []
    for row in accounts_query:
        channel_info = get_channel_info(row[8])
        seller_info = sellers_data.get(str(row[3])) if row[3] else None
        
        account = {
            "type": "account",
            "uuid": row[0],
            "price": row[2],
            "listed_by": str(row[3]) if row[3] else None,
            "seller": seller_info,
            "profile": row[4],
            "payment_methods": row[5],
            "additional_information": row[6],
            "number": row[7],
            "channel": {
                "id": str(row[8]) if row[8] else None,
                "name": channel_info["name"],
                "url": channel_info["url"],
                "category": channel_info["category"]
            },
            "message_id": str(row[9]) if row[9] else None,
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
        channel_info = get_channel_info(row[8])
        seller_info = sellers_data.get(str(row[3])) if row[3] else None
        
        alt = {
            "type": "alt",
            "uuid": row[0],
            "price": row[2],
            "listed_by": str(row[3]) if row[3] else None,
            "seller": seller_info,
            "profile": row[4],
            "payment_methods": row[5],
            "additional_information": row[6],
            "number": row[7],
            "channel": {
                "id": str(row[8]) if row[8] else None,
                "name": channel_info["name"],
                "url": channel_info["url"],
                "category": channel_info["category"]
            },
            "message_id": str(row[9]) if row[9] else None,
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
        channel_info = get_channel_info(row[8])
        seller_info = sellers_data.get(str(row[3])) if row[3] else None
        
        profile = {
            "type": "profile",
            "uuid": row[0],
            "price": row[2],
            "listed_by": str(row[3]) if row[3] else None,
            "seller": seller_info,
            "profile": row[4],
            "payment_methods": row[5],
            "additional_information": row[6],
            "number": row[7],
            "channel": {
                "id": str(row[8]) if row[8] else None,
                "name": channel_info["name"],
                "url": channel_info["url"],
                "category": channel_info["category"]
            },
            "message_id": str(row[9]) if row[9] else None,
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
    
    return jsonify({
        "invite": bot.invite,
        "listings": {
            "accounts": accounts_data,
            "alts": alts_data,
            "profiles": profiles_data
        },
        "success": True
    }), 200
