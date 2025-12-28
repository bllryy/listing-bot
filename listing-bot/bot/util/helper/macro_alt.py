import discord
from bot.util.formatting import format_number
from bot.bot import Bot
from bot.util.emoji import get_hotm_emojis

class AltObject:
    def __init__(self, uuid, username, profile, payment_methods, additional_info, price, number, channel_id=None, message_id=None, listed_by=None, show_username='true', farming='true', mining='false'):
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
        self.farming = self.string_to_bool(farming)
        self.mining = self.string_to_bool(mining)
        self.owner_mention = f"<@{listed_by}>"
        self.additional_information = str(additional_info)

    def string_to_bool(self, string):
        return str(string).lower() == "true"

    def to_tuple(self):
        return (self.uuid, self.username, self.profile, self.payment_methods, self.additional_info, self.price, self.number, self.channel_id, self.message_id, self.listed_by, str(self.show_username), str(self.farming), str(self.mining))

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
            "show_username": self.show_username,
            "farming": self.farming,
            "mining": self.mining
        }

    def to_embed(self, bot: Bot):
        embed = discord.Embed(
            title=f"Alt Account Listing #{self.number}",
            description=f"""
                **Username:** {self.username}
                `{self.uuid}`
                **Profile Name:** {self.profile}
                **Price:** ${self.price:,}
                **Payment Methods:** {self.payment_methods}
                **Additional Info:**
                ```{self.additional_info}```

                **Farming:** {self.farming}
                **Mining:** {self.mining}
            """,
            color=discord.Color.blue()
        )
        listed_by = bot.get_user(self.listed_by)
        embed.set_thumbnail(url=f"https://vzge.me/bust/{self.uuid}.png?y=-40")

        if listed_by:
            embed.set_author(name=f"{listed_by}", icon_url=listed_by.avatar.url if listed_by.avatar else listed_by.default_avatar.url)

        return embed

def create_embed_alt_listing(profile_data, cute_name, price, payment_methods, bot: Bot, listed_by, mining, farming):

    embeds = []

    profile_items = []
    networth_data = profile_data.get("networth", {})
    networth_types = networth_data.get("types", {})
    for key in networth_types:
        type_key_data = networth_types[key]
        items = type_key_data.get("items", [])
        profile_items.extend(items)

    skill_data = profile_data.get("skills", {})

    if mining:
        mining_data = profile_data.get("mining", {})
        hotM_tree = mining_data.get("hotM_tree", {})

        hotM_Level = hotM_tree.get("level", 0)

        perks = hotM_tree.get("perks", [])
        pickaxe_ability = hotM_tree.get("pickaxe_ability", "")
        if not pickaxe_ability:
            pickaxe_ability = ""

        for perk in perks:
            if perk.get("name", "") == "Peak of the Mountain":
                peak = perk
                break
        else:
            peak = {}

        mithril_powder = mining_data.get("mithril_powder", {}).get("total", 0)
        gemstone_powder = mining_data.get("gemstone_powder", {}).get("total", 0)
        glacite_powder = mining_data.get("glacite_powder", {}).get("total", 0)

        embed_description = f"{bot.get_emoji('HEART_OF_THE_MOUNTAIN')} HOTM: **Tier {hotM_Level}**\n"
        embed_description += f"{bot.get_emoji('GREEN_DYE')} **{format_number(mithril_powder)}** / {bot.get_emoji('PINK_DYE')} **{format_number(gemstone_powder)}** / {bot.get_emoji('LIGHT_BLUE_DYE')} **{format_number(glacite_powder)}**\n\n"
        embed_description += get_hotm_emojis(perks, pickaxe_ability, bot)
        embed_description += f"\nPeak of the Mountain: **{peak.get('level', 0)}**"          

        mining_embed = discord.Embed(
            color=discord.Color.blue(),
            description=embed_description
        )

        mining_skill = skill_data.get("mining", {})
        mining_skill_level = round(mining_skill.get("levelWithProgress", 0), 2)
        mining_skill_xp = format_number(mining_skill.get("totalXp", 0))  

        mining_embed.add_field(
            name=f"{bot.get_emoji('STONE_PICKAXE')} Mining Skill",
            value=f"""
Level: **{mining_skill_level}**
XP: **{mining_skill_xp}**"""
        )

        armor = ""
        mining_armor_sets = {
            "divan": [
                "divan_helmet",
                "divan_chestplate",
                "divan_leggings",
                "divan_boots"
            ],
            "sorrow": [
                "sorrow_helmet",
                "sorrow_chestplate",
                "sorrow_leggings",
                "sorrow_boots"
            ],
            "yog": [
                "armor_of_yog_helmet",
                "armor_of_yog_chestplate",
                "armor_of_yog_leggings",
                "armor_of_yog_boots"
            ],
            "glacite": [
                "glacite_helmet",
                "glacite_chestplate",
                "glacite_leggings",
                "glacite_boots"
            ],
            "goblin": [
                "goblin_helmet",
                "goblin_chestplate",
                "goblin_leggings",
                "goblin_boots"
            ],
        }

        armor_strings = {}
        for armor_set in mining_armor_sets:
            found = []
            for piece in mining_armor_sets[armor_set]:
                for item in profile_items:
                    if item["id"] == piece:
                        found.append(item)
                        break

            armor_strings[armor_set] = {"text": f"{len(found)}/4 {bot.get_emoji(mining_armor_sets[armor_set][1].upper())} **{armor_set.capitalize()}**\n", "count": len(found)}
            found = []

        for armor_set_data in armor_strings:
            armor += armor_strings[armor_set_data]["text"]
            if armor_strings[armor_set_data]["count"] == 4:
                break
        
        mining_embed.add_field(
            name=f"{bot.get_emoji('IRON_CHESTPLATE')} Mining Armor",
            value=armor
        )

        mining_embed.add_field(
            name="\u200b",
            value="\u200b"
        )

        drill_hierarchy = [
            "divan_drill", "titanium_drill_4",
            "titanium_drill_3", "titanium_drill_2",
            "titanium_drill_1", "mithril_drill_2",
            "mithril_drill_1"
        ]

        mappings = {
            "royal_pigeon": "Royal Pigeon",
            "gemstone_gauntlet": "Gemstone Gauntlet",
            "divan_pendant": "Pendant of Divan",
        }

        extra = ["royal_pigeon", "gemstone_gauntlet", "divan_pendant"]

        has_extra_items = {}

        drill = ""
        for drill_id in drill_hierarchy:
            for item in profile_items:
                if item["id"] == drill_id:
                    drill = item.get("name", "Failed to get drill name.")
                    break

                if item["id"] in extra:
                    has_extra_items[item["id"]] = True

            if drill:
                break

        else:
            drill = "No Drill found."
        
        mining_embed.add_field(
            name=f"{bot.get_emoji('PRISMARINE_SHARD')} Mining Tools",
            value=f"Best Drill: **{drill}**",
            inline=False
        )

        additional_items_string = ""
        for item in mappings:

            if item not in has_extra_items:
                prefix = suffix = "~~"
            else:
                prefix = suffix = "**"

            additional_items_string += f"{prefix}{mappings[item]}{suffix}, "

        mining_embed.add_field(
            name="Additional Mining Items",
            value=additional_items_string[:-2],
            inline=False
        )

        embeds.append(mining_embed)

    if farming:

        farming_embed = discord.Embed(
            color=discord.Color.blue()
        )

        farming_data = profile_data.get("farming", {})

        farming_skill = skill_data.get("farming", {})
        farming_skill_level = round(farming_skill.get("levelWithProgress", 0), 2)
        farming_skill_xp = format_number(farming_skill.get("totalXp", 0))  

        trapper_quest = farming_data.get("trapper_quest")
        if not trapper_quest:
            trapper_quest = {}

        jacobs = farming_data.get("jacob")
        if not jacobs:
            jacobs = {}

        contests = jacobs.get("contests")
        if not contests:
            contests = {}

        medals_current = jacobs.get("medals")
        if not medals_current:
            medals_current = {
                "gold": 0,
                "silver": 0,
                "bronze": 0
            }

        medals_total = jacobs.get("total_badges")
        if not medals_total:
            medals_total = {
                "gold": 0,
                "silver": 0,
                "bronze": 0
            }

        crops = jacobs.get("crops")
        if not crops:
            crops = {}

        crop_string = ""

        for crop in crops:
            crop_data = crops.get(crop)
            if not crop_data:
                crop_data = {}

            crop_name = crop_data.get("name")
            if not crop_name:
                continue

            crop_emoji_name = crop_name.lower().replace(" ", "_")
            _map = {
                "MELON": "MELON_BLOCK",
                "MUSHROOM": "RED_MUSHROOM",
                "PUMPKIN": "PUMPKIN_BLOCK",
            }
            crop_emoji = bot.get_emoji(_map.get(crop_emoji_name.upper(), crop_emoji_name.upper()))

            medals = crop_data.get("badges")
            if not medals:
                continue

            if medals.get("gold", 0) > 0:
                crop_string += f"{crop_emoji} {crop_name}\n"

        crop_string = crop_string[:-1]

        farming_embed.add_field(
            name="Medals",
            value=f"""
{bot.get_emoji('GOLD_INGOT')} Gold: **{medals_total['gold']}**  (**{medals_current['gold']}**)
{bot.get_emoji('IRON_INGOT')} Silver: **{medals_total['silver']}**  (**{medals_current['silver']}**)
{bot.get_emoji('BRICK')} Bronze: **{medals_total['bronze']}**  (**{medals_current['bronze']}**)"""
        )

        farming_embed.add_field(
            name=f"Unique Golds ({len(crop_string.splitlines())})",
            value=crop_string
        )

        perk_string = ""
        perks = jacobs.get("perks")
        farming_level_cap = 0
        if not perks:
            perk_string = f"""
{bot.get_emoji('HAY_BALE_ICON')} Farming Level Cap: **0** / 10
{bot.get_emoji('WHEAT')} Extra Farming Drops: ☘ **0** / ☘ 60"""

        else:
            farming_level_cap = perks.get("farming_level_cap", 0)
            perk_string += f"""
{bot.get_emoji('HAY_BALE_ICON')} Farming Level Cap: **{farming_level_cap}** / 10
{bot.get_emoji('WHEAT')} Extra Farming Drops: **☘ {perks.get("double_drops", 0)*4}** / ☘ 60"""

        farming_embed.add_field(
            name="Perks",
            value=perk_string,
            inline=False
        )

        attended_contests = contests.get("attended_contests", 0)

        actual = None
        if farming_skill_level > 50:
            if 50+farming_level_cap < farming_skill_level:
                actual = farming_skill_level
                farming_skill_level = 50+farming_level_cap

        farming_embed.description = f"""
{bot.get_emoji('GOLDEN_HOE')} Level: **{farming_skill_level} {f'({actual})' if actual else ''} ({farming_skill_xp} XP)**
{bot.get_emoji('JACOBS_MEDAL')} Contests: **{attended_contests}**"""

        embeds.append(farming_embed)

    embeds[0].title = "Macro-Ready Account"
    embeds[0].set_thumbnail(url=f"https://mc-heads.net/body/640a5372780b4c2ab7e78359d2f9a6a8/left")
    embeds[-1].set_footer(text="Made by noemt | https://noemt.dev", icon_url="https://bots.noemt.dev/avatars/nom.png")
    embeds[-1].add_field(name="💸 Price", value=f"{price}$", inline=True)
    embeds[-1].add_field(name="💳 Payment Methods", value=payment_methods, inline=True)
    embeds[-1].add_field(name="Listed By", value=listed_by, inline=True)

    return embeds
