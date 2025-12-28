import discord
import aiohttp
from bot.util.selector import handle_selection
from bot.util.number import get_available_number
from bot.util.fetch import fetch_profile_data, fetch_mojang_api
from bot.util.listing_objects.account import Account
from bot.util.listing_objects.profile import Profile
from bot.util.listing_objects.alt import Alt
from bot.util.convert_payment_methods import convert_payment_methods
from bot.util.helper.account import create_embed_account_listing, AccountObject
from bot.util.helper.profile import create_embed_profile_listing, ProfileObject
from bot.util.helper.macro_alt import create_embed_alt_listing, AltObject
from bot.bot import Bot
from bot.util.calcs import calc_skill_avg
from numerize import numerize


async def list_account(bot: Bot, username: str, price: int, payment_methods: str, ping: bool, additional_information: str, show_ign: bool, profile: str, number: int, ctx, listed_by) -> discord.Embed:
    if profile:
        profile = handle_selection(profile)

    if not number:
        number = await get_available_number(bot, "accounts")

    response_embed = discord.Embed(color=discord.Color.red())

    async with aiohttp.ClientSession() as session:
        response, status = await fetch_mojang_api(session, username)
        if status != 200:
            response_embed.title = "An Error Occurred"
            response_embed.description = "Invalid Username Provided!"
            return response_embed
        
        uuid = response.get("id")
        username = response.get("name")

        query = "SELECT * FROM accounts WHERE number = ? OR uuid = ?"
        result = await bot.db.fetchone(query, number, uuid)

        if result:
            data = AccountObject(*result)
            response_embed.title = "An Error Occurred"
            response_embed.description = f"An Account with this {'number' if data.number == number else 'username'} is already listed <#{data.channel_id}>!"
            return response_embed

        profile_data, profile = await fetch_profile_data(session, uuid, bot, profile)
        embed = create_embed_account_listing(profile_data, profile, uuid, username, price, additional_information, convert_payment_methods(bot, payment_methods), ctx, bot, f'<@{listed_by}>')

        if not embed:
            response_embed.title = "An Error Occurred"
            response_embed.description = "An error occurred while creating the embed."
            return response_embed
        
        category_id = await bot.db.get_config("accounts_category")
        category: discord.CategoryChannel = bot.get_channel(category_id)
        if not category:
            response_embed.title = "An Error Occurred"
            response_embed.description = "An error occurred while fetching the category."
            return response_embed
        
        if len(category.channels) >= 50:
            overflow_category_id = await bot.db.get_config("listing_overflow_category")
            overflow_category: discord.CategoryChannel = bot.get_channel(overflow_category_id)
            if overflow_category:
                category = overflow_category

        if len(category.channels) >= 50:
            response_embed.title = "An Error Occurred"
            response_embed.description = "Both the primary and overflow listing categories are full. How in the actual fuck did you achieve this?"
            return response_embed
        
        channel = await category.create_text_channel(name=f"⭐｜💲{price}｜listing-{number}")
        initial_message = await channel.send(embed=embed, view=Account(bot))

        response_embed.color = discord.Color.green()
        response_embed.title = "Account Listed"
        response_embed.description = f"Your account has been listed in {channel.mention}!"

        skill_data = profile_data.get("skills", {})

        dungeons = profile_data.get("dungeons", {})
        if dungeons is None:
            dungeons = {}        
        catacombs = dungeons.get("catacombs", {})
        catacombs_skill = catacombs.get("skill", {})

        slayer_data = profile_data.get("slayer", {})
        zombie = slayer_data.get("zombie", {})
        spider = slayer_data.get("spider", {})
        wolf = slayer_data.get("wolf", {})
        enderman = slayer_data.get("enderman", {})
        blaze = slayer_data.get("blaze", {})
        vampire = slayer_data.get("vampire", {})

        networth_data = profile_data.get("networth", {})

        mining_stats = profile_data.get("mining", {})
        hotm = mining_stats.get("hotM_tree", {})
        mithril_powder = mining_stats.get("mithril_powder", {})
        gemstone_powder = mining_stats.get("gemstone_powder", {})
        glacite_powder = mining_stats.get("glacite_powder", {})

        data = (
            uuid,
            calc_skill_avg([v.get("level", 0) for k, v in skill_data.items() if not k == "carpentry" and not k == "runecrafting" and not k == "social"]),
            catacombs_skill.get("level", 0),
            zombie.get("level", 0),
            spider.get("level", 0),
            wolf.get("level", 0),
            enderman.get("level", 0),
            blaze.get("level", 0),
            vampire.get("level", 0),
            profile_data.get('sbLevel'),
            numerize.numerize(networth_data.get("networth", 0)),
            numerize.numerize(networth_data.get("networth", 0)-networth_data.get("unsoulboundNetworth", 0)),
            numerize.numerize(networth_data.get("purse", 0) + networth_data.get("bank", 0) + networth_data.get("personalBank", 0)),
            hotm.get("level", 0),
            numerize.numerize(mithril_powder.get("total", 0)),
            numerize.numerize(gemstone_powder.get("total", 0)),
            numerize.numerize(glacite_powder.get("total", 0)),
        )
        await bot.db.execute(
            "DELETE FROM account_stats WHERE uuid = ?", uuid
        )
        await bot.db.execute(
            """
            INSERT INTO account_stats 
            (
                uuid, skill_average, catacombs_level, 
                zombie_slayer_level, spider_slayer_level, 
                wolf_slayer_level, enderman_slayer_level, 
                blaze_slayer_level, vampire_slayer_level, 
                skyblock_level, total_networth, 
                soulbound_networth, liquid_networth, 
                heart_of_the_mountain_level, 
                mithril_powder, gemstone_powder, glaciate_powder
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            *data
        )

        if ping:
            ping_role = await bot.db.get_config("ping_role")
            if ping_role:
                (await channel.send(f"<@&{ping_role}>")).delete()

        await bot.db.execute(
            "INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            *(
                uuid, username, profile,
                payment_methods, additional_information,
                price, number, channel.id,
                initial_message.id, listed_by,
                str(show_ign).lower()
            )
        )

        logs_channel_id = await bot.db.get_config("logs_channel")
        logs_channel = bot.get_channel(logs_channel_id)
        if logs_channel:
            await logs_channel.send(f"**<@{listed_by}>** listed {channel.mention}. ({username})", allowed_mentions=discord.AllowedMentions.none())

    return response_embed

async def list_profile(bot: Bot, username: str, price: int, payment_methods: str, ping: bool, additional_information: str, show_ign: bool, profile: str, number: int, listed_by) -> discord.Embed:
    if profile:
        profile = handle_selection(profile)

    if not number:
        number = await get_available_number(bot, "profiles")

    response_embed = discord.Embed(color=discord.Color.red())

    async with aiohttp.ClientSession() as session:
        response, status = await fetch_mojang_api(session, username)
        if status != 200:
            response_embed.title = "An Error Occurred"
            response_embed.description = "Invalid Username Provided!"
            return response_embed
        
        uuid = response.get("id")
        username = response.get("name")

        query = "SELECT * FROM profiles WHERE number = ? OR (uuid = ? AND profile = ?)"
        result = await bot.db.fetchone(query, number, uuid, str(profile))

        if result:
            data = ProfileObject(*result)
            response_embed.title = "An Error Occurred"
            if data.number == number:
                response_embed.description = f"A Profile with this number is already listed <#{data.channel_id}>!"
            else:
                response_embed.description = f"A Profile with this username and profile is already listed <#{data.channel_id}>!"
            return response_embed

        profile_data, profile = await fetch_profile_data(session, uuid, bot, profile)
        embed = create_embed_profile_listing(profile_data, profile, price, convert_payment_methods(bot, payment_methods), bot, f'<@{listed_by}>')

        if not embed:
            response_embed.title = "An Error Occurred"
            response_embed.description = "An error occurred while creating the embed."
            return response_embed
        
        category_id = await bot.db.get_config("profiles_category")
        category: discord.CategoryChannel = bot.get_channel(category_id)
        if not category:
            response_embed.title = "An Error Occurred"
            response_embed.description = "An error occurred while fetching the category."
            return response_embed
        
        if len(category.channels) >= 50:
            overflow_category_id = await bot.db.get_config("listing_overflow_category")
            overflow_category: discord.CategoryChannel = bot.get_channel(overflow_category_id)
            if overflow_category:
                category = overflow_category

        if len(category.channels) >= 50:
            response_embed.title = "An Error Occurred"
            response_embed.description = "Both the primary and overflow listing categories are full. How in the actual fuck did you achieve this?"
            return response_embed
        
        channel = await category.create_text_channel(name=f"⭐｜💲{price}｜island-{number}")
        initial_message = await channel.send(embed=embed, view=Profile(bot))

        response_embed.color = discord.Color.green()
        response_embed.title = "Profile Listed"
        response_embed.description = f"Your profile has been listed in {channel.mention}!"

        networth_data = profile_data.get("networth", {})
        minion_data = profile_data.get("minions", {})
        slots = minion_data.get("minionSlots", 0)
        bonus = minion_data.get("bonusSlots", 0)

        collection_data = profile_data.get("collections", [])
        maxed_collections = len([c for c in collection_data if c["tier"] == c["maxTiers"]])
        unlocked_collections = len([c for c in collection_data if c["amount"] > 0])

        data = (
            uuid,
            profile,
            numerize.numerize(networth_data.get("networth", 0)),
            numerize.numerize(networth_data.get("networth", 0)-networth_data.get("unsoulboundNetworth", 0)),
            numerize.numerize(networth_data.get("purse", 0) + networth_data.get("bank", 0) + networth_data.get("personalBank", 0)),
            slots,
            bonus,
            maxed_collections,
            unlocked_collections
        )
        await bot.db.execute(
            "DELETE FROM profile_stats WHERE uuid = ? AND profile = ?", uuid, profile
        )
        await bot.db.execute(
            "INSERT INTO profile_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            *data
        )

        if ping:
            ping_role = await bot.db.get_config("ping_role")
            if ping_role:
                (await channel.send(f"<@&{ping_role}>")).delete()

        await bot.db.execute(
            "INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            *(
                uuid, username, profile,
                payment_methods, additional_information,
                price, number, channel.id,
                initial_message.id, listed_by,
                str(show_ign).lower()
            )
        )

        logs_channel_id = await bot.db.get_config("logs_channel")
        logs_channel = bot.get_channel(logs_channel_id)
        if logs_channel:
            await logs_channel.send(f"**<@{listed_by}>** listed {channel.mention}. ({username})", allowed_mentions=discord.AllowedMentions.none())

    return response_embed

async def list_alt(bot: Bot, username: str, price: int, payment_methods: str, farming: bool, mining: bool, ping: bool, additional_information: str, show_ign: bool, profile: str, number: int, listed_by) -> discord.Embed:
    if profile:
        profile = handle_selection(profile)

    if not number:
        number = await get_available_number(bot, "alts")

    response_embed = discord.Embed(color=discord.Color.red())

    async with aiohttp.ClientSession() as session:
        response, status = await fetch_mojang_api(session, username)
        if status != 200:
            response_embed.title = "An Error Occurred"
            response_embed.description = "Invalid Username Provided!"
            return response_embed
        
        uuid = response.get("id")
        username = response.get("name")

        query = "SELECT * FROM alts WHERE number = ? OR uuid = ?"
        result = await bot.db.fetchone(query, number, uuid)

        if result:
            data = AltObject(*result)
            response_embed.title = "An Error Occurred"
            if data.number == number:
                response_embed.description = f"An Alt Account with this number is already listed <#{data.channel_id}>!"
            else:
                response_embed.description = f"A Alt Account with this username and profile is already listed <#{data.channel_id}>!"
            return response_embed

        profile_data, profile = await fetch_profile_data(session, uuid, bot, profile)
        embeds = create_embed_alt_listing(profile_data, profile, price, convert_payment_methods(bot, payment_methods), bot, f'<@{listed_by}>', mining, farming)

        if not embeds:
            response_embed.title = "An Error Occurred"
            response_embed.description = "An error occurred while creating the embeds."
            return response_embed
        
        category_id = await bot.db.get_config("alts_category")
        category: discord.CategoryChannel = bot.get_channel(category_id)
        if not category:
            response_embed.title = "An Error Occurred"
            response_embed.description = "An error occurred while fetching the category."
            return response_embed
        
        if len(category.channels) >= 50:
            overflow_category_id = await bot.db.get_config("listing_overflow_category")
            overflow_category: discord.CategoryChannel = bot.get_channel(overflow_category_id)
            if overflow_category:
                category = overflow_category

        if len(category.channels) >= 50:
            response_embed.title = "An Error Occurred"
            response_embed.description = "Both the primary and overflow listing categories are full. How in the actual fuck did you achieve this?"
            return response_embed

        channel = await category.create_text_channel(name=f"⭐｜💲{price}｜alt-{number}")
        initial_message = await channel.send(embeds=embeds, view=Alt(bot))

        response_embed.color = discord.Color.green()
        response_embed.title = "Alt Account Listed"
        response_embed.description = f"Your Alt Account has been listed in {channel.mention}!"

        skill_data = profile_data.get("skills", {})

        dungeons = profile_data.get("dungeons", {})
        if dungeons is None:
            dungeons = {}        
        catacombs = dungeons.get("catacombs", {})
        catacombs_skill = catacombs.get("skill", {})

        slayer_data = profile_data.get("slayer", {})
        zombie = slayer_data.get("zombie", {})
        spider = slayer_data.get("spider", {})
        wolf = slayer_data.get("wolf", {})
        enderman = slayer_data.get("enderman", {})
        blaze = slayer_data.get("blaze", {})
        vampire = slayer_data.get("vampire", {})

        networth_data = profile_data.get("networth", {})

        mining_stats = profile_data.get("mining", {})
        hotm = mining_stats.get("hotM_tree", {})
        mithril_powder = mining_stats.get("mithril_powder", {})
        gemstone_powder = mining_stats.get("gemstone_powder", {})
        glacite_powder = mining_stats.get("glacite_powder", {})

        data = (
            uuid,
            calc_skill_avg([v.get("level", 0) for k, v in skill_data.items() if not k == "carpentry" and not k == "runecrafting" and not k == "social"]),
            catacombs_skill.get("level", 0),
            zombie.get("level", 0),
            spider.get("level", 0),
            wolf.get("level", 0),
            enderman.get("level", 0),
            blaze.get("level", 0),
            vampire.get("level", 0),
            profile_data.get('sbLevel'),
            numerize.numerize(networth_data.get("networth", 0)),
            numerize.numerize(networth_data.get("networth", 0)-networth_data.get("unsoulboundNetworth", 0)),
            numerize.numerize(networth_data.get("purse", 0) + networth_data.get("bank", 0) + networth_data.get("personalBank", 0)),
            hotm.get("level", 0),
            numerize.numerize(mithril_powder.get("total", 0)),
            numerize.numerize(gemstone_powder.get("total", 0)),
            numerize.numerize(glacite_powder.get("total", 0)),
        )
        await bot.db.execute(
            "DELETE FROM account_stats WHERE uuid = ?", uuid
        )
        await bot.db.execute(
            """
            INSERT INTO account_stats 
            (
                uuid, skill_average, catacombs_level, 
                zombie_slayer_level, spider_slayer_level, 
                wolf_slayer_level, enderman_slayer_level, 
                blaze_slayer_level, vampire_slayer_level, 
                skyblock_level, total_networth, 
                soulbound_networth, liquid_networth, 
                heart_of_the_mountain_level, 
                mithril_powder, gemstone_powder, glaciate_powder
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            *data
        )

        if ping:
            ping_role = await bot.db.get_config("ping_role")
            if ping_role:
                (await channel.send(f"<@&{ping_role}>")).delete()

        await bot.db.execute(
            "INSERT INTO alts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            *(
                uuid, username, profile,
                payment_methods, additional_information,
                price, number, channel.id,
                initial_message.id, listed_by,
                str(show_ign).lower(), str(farming).lower(), 
                str(mining).lower()
            )
        )

        logs_channel_id = await bot.db.get_config("logs_channel")
        logs_channel = bot.get_channel(logs_channel_id)
        if logs_channel:
            await logs_channel.send(f"**<@{listed_by}>** listed {channel.mention}. ({username})", allowed_mentions=discord.AllowedMentions.none())

    return response_embed
