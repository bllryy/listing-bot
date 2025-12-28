from bot.util.gamemode import gamemode_to_string
from bot.util.constants import color_codes
import json
from numerize import numerize
from bot.util.calcs import calc_skill_avg
import discord

from bot.bot import Bot

class AccountObject:
    def __init__(self, uuid, username, profile, payment_methods, additional_info, price, number, channel_id=None, message_id=None, listed_by=None, show_username='true'):
        self.uuid = uuid
        self.username = username
        self.profile = profile
        self.payment_methods = payment_methods
        self.additional_info = additional_info
        self.price = price
        self.number = number
        self.channel_id = channel_id
        self.message_id = message_id
        self.listed_by = listed_by
        self.show_username = self.string_to_bool(show_username)

    def string_to_bool(self, string):
        return str(string).lower() == "true"
    
    def set_discord_data(self, channel_id, message_id, listed_by):
        self.channel_id = channel_id
        self.message_id = message_id
        self.listed_by = listed_by

    def to_tuple(self):
        return (self.uuid, self.username, self.profile, self.payment_methods, self.additional_info, self.price, self.number, self.channel_id, self.message_id, self.listed_by, str(self.show_username))

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "username": self.username,
            "profile": self.profile,
            "payment_methods": self.payment_methods,
            "additional_info": self.additional_info,
            "price": self.price,
            "number": self.number,
            "channel_id": self.channel_id,
            "message_id": self.message_id,
            "listed_by": self.listed_by,
            "show_username": self.show_username
        }

    def to_embed(self, bot: Bot):
        embed = discord.Embed(
            title=f"Account Listing #{self.number}",
            description=f"""
                **Username:** {self.username}
                `{self.uuid}`
                **Profile Name:** {self.profile}
                **Price:** ${self.price:,}
                **Payment Methods:** {self.payment_methods}
                **Additional Info:**
                ```{self.additional_info}```
            """,
            color=discord.Color.blue()
        )
        listed_by = bot.get_user(self.listed_by)
        embed.set_thumbnail(url=f"https://vzge.me/bust/{self.uuid}.png?y=-40")

        if listed_by:
            embed.set_author(name=f"{listed_by}", icon_url=listed_by.avatar.url if listed_by.avatar else listed_by.default_avatar.url)

        return embed

def create_embed_account_listing(profile_data, cute_name, uuid, username, price, additional_information, payment_methods, ctx, bot: Bot, listed_by):
    p_type = gamemode_to_string(profile_data.get('gamemode'))

    skill_data = profile_data.get("skills", {})

    farming = skill_data.get("farming", {})
    mining = skill_data.get("mining", {})
    combat = skill_data.get("combat", {})
    taming = skill_data.get("taming", {})
    foraging = skill_data.get("foraging", {})
    enchanting = skill_data.get("enchanting", {})
    alchemy = skill_data.get("alchemy", {})
    fishing = skill_data.get("fishing", {})
    carpentry = skill_data.get("carpentry", {})
    social = skill_data.get("social", {})
    runecrafting = skill_data.get("runecrafting", {})

    dungeons = profile_data.get("dungeons", {})
    if dungeons is None:
        dungeons = {}        
    classes = dungeons.get("classes", {})
    catacombs = dungeons.get("catacombs", {})
    catacombs_skill = catacombs.get("skill", {})

    networth_data = profile_data.get("networth", {})

    weight_data = profile_data.get("weight", {})
    senither = weight_data.get("senither", {})
    lily = weight_data.get("lily", {})

    slayer_data = profile_data.get("slayer", {})
    zombie = slayer_data.get("zombie", {})
    spider = slayer_data.get("spider", {})
    wolf = slayer_data.get("wolf", {})
    enderman = slayer_data.get("enderman", {})
    blaze = slayer_data.get("blaze", {})
    vampire = slayer_data.get("vampire", {})

    mining_stats = profile_data.get("mining", {})
    hotm = mining_stats.get("hotM_tree", {})
    mithril_powder = mining_stats.get("mithril_powder", {})
    gemstone_powder = mining_stats.get("gemstone_powder", {})
    glacite_powder = mining_stats.get("glacite_powder", {})
    hotm_level = hotm.get("level", 0)

    minions = profile_data.get("minions", {})
    slots = minions.get("minionSlots", 0)
    bonus = minions.get("bonusSlots", 0)
    total_slots = slots + bonus

    rank = profile_data.get("rank", "")
    if not rank:
        rank = ""
    for color in color_codes:
        rank = rank.replace(color, "")

    if rank == "":
        rank = "Non"
    
    rank_emojies = {
        "[non]": f"{bot.get_emoji('NON_LEFT')}{bot.get_emoji('NON_RIGHT')}",
        "non": f"{bot.get_emoji('NON_LEFT')}{bot.get_emoji('NON_RIGHT')}",
        "[vip]": f"{bot.get_emoji('VIP_LEFT')}{bot.get_emoji('VIP_RIGHT')}",
        "vip": f"{bot.get_emoji('VIP_LEFT')}{bot.get_emoji('VIP_RIGHT')}",
        "[vip+]": f"{bot.get_emoji('VIP_LEFT')}{bot.get_emoji('VIPPLUS_RIGHT')}",
        "vip_plus": f"{bot.get_emoji('VIP_LEFT')}{bot.get_emoji('VIPPLUS_RIGHT')}",
        "[mvp]": f"{bot.get_emoji('MVP_LEFT')}{bot.get_emoji('MVP_RIGHT')}",
        "mvp": f"{bot.get_emoji('MVP_LEFT')}{bot.get_emoji('MVP_RIGHT')}",
        "[mvp+]": f"{bot.get_emoji('MVP_LEFT')}{bot.get_emoji('MVP_PLUS_RIGHT')}",
        "mvp_plus": f"{bot.get_emoji('MVP_LEFT')}{bot.get_emoji('MVP_PLUS_RIGHT')}",
        "[mvp++]": f"{bot.get_emoji('MVP_PLUS_PLUS_LEFT')}{bot.get_emoji('MVP_PLUS_PLUS_MIDDLE')}{bot.get_emoji('MVP_PLUS_PLUS_RIGHT')}",
        "superstar": f"{bot.get_emoji('MVP_PLUS_PLUS_LEFT')}{bot.get_emoji('MVP_PLUS_PLUS_MIDDLE')}{bot.get_emoji('MVP_PLUS_PLUS_RIGHT')}",
        "[youtube]": f"{bot.get_emoji('YOUTUBE_LEFT')}{bot.get_emoji('YOUTUBE_CENTER')}{bot.get_emoji('YOUTUBE_RIGHT')}",
        "youtube": f"{bot.get_emoji('YOUTUBE_LEFT')}{bot.get_emoji('YOUTUBE_CENTER')}{bot.get_emoji('YOUTUBE_RIGHT')}",
    }

    rank = rank_emojies.get(rank.lower())

    keys_dict = {
        "bot_avatar": bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url,
        "bot_name": bot.user.name,
        "guild_icon": ctx.guild.icon.url if hasattr(ctx.guild, "icon") else "https://bots.noemt.dev/avatars/nom.png",
        "guild_name": ctx.guild.name,
        "price": price,
        "uuid": uuid,
        "username": username,
        "payment_methods": payment_methods,
        "listed_by": listed_by,
        "rank_emoji": rank,
        "extra_information": additional_information,
        "skills_skill_average": calc_skill_avg([v.get("level", 0) for k, v in skill_data.items() if not k == "carpentry" and not k == "runecrafting" and not k == "social"]),
        "skills_farming_level": farming.get("level", 0),
        "skills_mining_level": mining.get("level", 0),
        "skills_combat_level": combat.get("level", 0),
        "skills_taming_level": taming.get("level", 0),
        "skills_foraging_level": foraging.get("level", 0),
        "skills_enchanting_level": enchanting.get("level", 0),
        "skills_alchemy_level": alchemy.get("level", 0),
        "skills_fishing_level": fishing.get("level", 0),
        "skills_carpentry_level": carpentry.get("level", 0),
        "skills_social_level": social.get("level", 0),
        "skills_runecrafting_level": runecrafting.get("level", 0),
        "skills_farming_exp": numerize.numerize(farming.get("totalXp", 0)),
        "skills_mining_exp": numerize.numerize(mining.get("totalXp", 0)),
        "skills_combat_exp": numerize.numerize(combat.get("totalXp", 0)),
        "skills_taming_exp": numerize.numerize(taming.get("totalXp", 0)),
        "skills_foraging_exp": numerize.numerize(foraging.get("totalXp", 0)),
        "skills_enchanting_exp": numerize.numerize(enchanting.get("totalXp", 0)),
        "skills_alchemy_exp": numerize.numerize(alchemy.get("totalXp", 0)),
        "skills_fishing_exp": numerize.numerize(fishing.get("totalXp", 0)),
        "skills_carpentry_exp": numerize.numerize(carpentry.get("totalXp", 0)),
        "skills_social_exp": numerize.numerize(social.get("totalXp", 0)),
        "skills_runecrafting_exp": numerize.numerize(runecrafting.get("totalXp", 0)),

        "mining_hotm_level": hotm_level,
        "mining_mithril_powder": numerize.numerize(mithril_powder.get("total", 0)),
        "mining_gemstone_powder": numerize.numerize(gemstone_powder.get("total", 0)),
        "mining_glacite_powder": numerize.numerize(glacite_powder.get("total", 0)),

        "catacombs_skill_level": catacombs_skill.get("level", 0),
        "catacombs_class_average": calc_skill_avg([v.get("level", 0) for k, v in dungeons.get('classes', {}).items()]),

        "catacombs_healer_level": classes.get("healer", {}).get("level", 0),
        "catacombs_mage_level": classes.get("mage", {}).get("level", 0),
        "catacombs_archer_level": classes.get("archer", {}).get("level", 0),
        "catacombs_berserker_level": classes.get("berserker", {}).get("level", 0),
        "catacombs_tank_level": classes.get("tank", {}).get("level", 0),

        "catacombs_skill_exp": numerize.numerize(catacombs_skill.get("totalXp", 0)),
        "catacombs_healer_exp": numerize.numerize(classes.get("healer", {}).get("totalXp", 0)),
        "catacombs_mage_exp": numerize.numerize(classes.get("mage", {}).get("totalXp", 0)),
        "catacombs_archer_exp": numerize.numerize(classes.get("archer", {}).get("totalXp", 0)),
        "catacombs_berserker_exp": numerize.numerize(classes.get("berserker", {}).get("totalXp", 0)),
        "catacombs_tank_exp": numerize.numerize(classes.get("tank", {}).get("totalXp", 0)),

        "minions_slots_total": total_slots,
        "minions_slots_bonus": bonus,
        "minions_slots_base": slots,

        "networth_purse": numerize.numerize(networth_data.get("purse", 0)),
        "networth_bank": numerize.numerize(networth_data.get("bank", 0)),
        "networth_personal_bank": numerize.numerize(networth_data.get("personalBank", 0)),
        "networth_total": numerize.numerize(networth_data.get("networth", 0)),
        "networth_soulbound": numerize.numerize(networth_data.get("networth", 0)-networth_data.get("unsoulboundNetworth", 0)),
        "networth_unsoulbound": numerize.numerize(networth_data.get("unsoulboundNetworth", 0)),

        "weight_senither": format(int(senither.get("total", 0)), ',d'),

        "stats_skyblock_level": profile_data.get('sbLevel'),
        "stats_profile_type": p_type,

        "slayer_zombie_level": zombie.get("level", 0),
        "slayer_spider_level": spider.get("level", 0),
        "slayer_wolf_level": wolf.get("level", 0),
        "slayer_enderman_level": enderman.get("level", 0),
        "slayer_blaze_level": blaze.get("level", 0),
        "slayer_vampire_level": vampire.get("level", 0),

        "slayer_zombie_exp": numerize.numerize(zombie.get("xp", 0)),
        "slayer_spider_exp": numerize.numerize(spider.get("xp", 0)),
        "slayer_wolf_exp": numerize.numerize(wolf.get("xp", 0)),
        "slayer_enderman_exp": numerize.numerize(enderman.get("xp", 0)),
        "slayer_blaze_exp": numerize.numerize(blaze.get("xp", 0)),
        "slayer_vampire_exp": numerize.numerize(vampire.get("xp", 0)),
    }
    if lily.get("total", 0) is not None:
        keys_dict["weight_lily"] = format(int(lily.get("total", 0)), ',d')
    else: 
        keys_dict["weight_lily"] = "Unexpected Error"

    for emoji in bot.item_emojis:
        keys_dict[f"emojis_{emoji}"] = bot.item_emojis[emoji].strip()

    with open("./data/embeds.json", "r") as f:
        embed_data: dict = json.load(f)
        account_embeds = embed_data.get("accounts")

    embed = account_embeds[0]
    embed = {k: v for k, v in embed.items() if v != None}
    embed = discord.Embed.from_dict(embed)

    if embed.description:
        embed.description = embed.description.format(**keys_dict)

    if embed.title:
        embed.title = embed.title.format(**keys_dict)

    if embed.thumbnail:
        url = embed.thumbnail.url.format(**keys_dict)
        embed.set_thumbnail(url=url)

    if embed.image:
        url = embed.image.url.format(**keys_dict)
        embed.set_image(url=url)

    embed.set_footer(text="Made by noemt | https://noemt.dev",
                        icon_url="https://bots.noemt.dev/avatars/nom.png")

    for field in embed.fields:
        field.name = field.name.format(**keys_dict)
        field.value = field.value.format(**keys_dict)

    return embed