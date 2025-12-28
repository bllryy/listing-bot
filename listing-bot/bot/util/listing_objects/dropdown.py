import discord
from discord.ui import Select
from discord import SelectOption
from bot.util.helper.account import AccountObject
from bot.util.helper.profile import ProfileObject
from bot.util.helper.macro_alt import AltObject
from bot.util.fetch import fetch_profile_data
from bot.util.transform import abbreviate, get_progress_bar
from bot.util.constants import (
    class_emoji_mappings, slayer_emoji_mappings, 
    slayer_names, skill_emoji_mappings, garden_plot_mappings, 
    networth_categories, hotm_tree_mapping, special_hotm_types
)
from bot.util.helper.kuudra import Kuudra
from bot.util.networth import generate_embed_networth_field, process_items
import aiohttp
import asyncio

from bot.bot import Bot

class Dropdown(Select):
    def __init__(self, bot: Bot, account_type: str = "accounts", *args, **kwargs):

        options = [
            SelectOption(label="Catacombs", value="Dungeons", emoji=bot.get_emoji("MORT")),
            SelectOption(label="Slayers", value="Slayers", emoji=bot.get_emoji("BEHEADED_HORROR")),
            SelectOption(label="Skills", value="Skills", emoji=bot.get_emoji("JUNGLE_SAPLING")),
            SelectOption(label="Unsoulbound Networth", value="Unsoulbound Networth", emoji=bot.get_emoji("BANK_ITEM")),
            SelectOption(label="Soulbound Networth", value="Soulbound Networth", emoji=bot.get_emoji("BANK_ITEM")),
            SelectOption(label="Mining", value="Mining", emoji=bot.get_emoji("STONE_PICKAXE")),
            SelectOption(label="Farming", value="Farming", emoji=bot.get_emoji("GOLDEN_HOE")),
            SelectOption(label="Kuudra", value="Kuudra", emoji=bot.get_emoji("KUUDRA_KEY_BASIC")),
            SelectOption(label="Minion Slots", value="Minions", emoji=bot.get_emoji("COBBLESTONE_MINION")),
            SelectOption(label="Garden", value="Garden", emoji=bot.get_emoji("GARDEN_VISITOR")),
        ]

        super().__init__(custom_id="breakdown:stats:"+account_type, options=options, placeholder="Click a stat to view it!", *args, **kwargs)

        self.account_type = account_type
        self.bot = bot
        self.send_response = True

    def base(self, cute_name: str, stat: str):
        embed = discord.Embed(
            title=f"{stat} on {cute_name.title()} Profile",
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text="Made by noemt | https://bots.noemt.dev",
            icon_url="https://bots.noemt.dev/avatars/nom.png"
        )
        embed.set_thumbnail(
            url="https://mc-heads.net/avatar/640a5372780b4c2ab7e78359d2f9a6a8"
        )
        return embed
    
    def recursing_view(self):
        view = discord.ui.View(timeout=None)
        dropdown = Dropdown(self.bot, self.account_type)
        dropdown.send_response = False
        view.add_item(self)
        return view

    async def callback(self, interaction: discord.Interaction):
        data = await self.bot.db.fetchone(f"SELECT * FROM {self.account_type} WHERE channel_id = ?", interaction.channel.id)
        if not data:
            await interaction.respond("This account was not found in the database, deleting in `5` Seconds.", ephemeral=True)
            await asyncio.sleep(5)
            return await interaction.channel.delete()

        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            return
        
        match self.account_type:
            case "accounts":
                account = AccountObject(*data)
            case "profiles":
                account = ProfileObject(*data)
            case "alts":
                account = AltObject(*data)
            case _:
                raise ValueError("Invalid account type")
            
        async with aiohttp.ClientSession() as session:
            try:
                profile_data, profile = await fetch_profile_data(session, account.uuid, self.bot, account.profile, False)
            except asyncio.TimeoutError:
                await interaction.respond("The request to Hypixel's API timed out, please try again later.", ephemeral=True)
                return
            if not profile_data:
                await interaction.respond("Failed to fetch profile data, please try again later.", ephemeral=True)
                return
            
        embed = self.base(profile, self.values[0])
        match self.values[0]:
            case "Dungeons":
                dungeon_data = profile_data.get("dungeons", {})
                if not dungeon_data:
                    dungeon_data = {}

                catacombs_data = dungeon_data.get("catacombs", {})
                catacombs_skill = catacombs_data.get("skill", {})

                cata_level = catacombs_skill.get("level", 0)
                cata_xp = catacombs_skill.get("xpCurrent", 0)
                cata_xp_for_next = catacombs_skill.get("xpForNext", 0)

                cata_string = (
                    f"**MAX LEVEL** (**50**)" if cata_xp_for_next == 0 and cata_xp != 0 else 
                    f"**{abbreviate(cata_xp)}** / {abbreviate(cata_xp_for_next)} XP (**{cata_level}**)"
                )

                selected_class = dungeon_data.get("selected_class", "None")
                secrets_found = dungeon_data.get("secrets_found", 0)
                dungeon_classes = dungeon_data.get("classes", {})

                class_levels_total = sum(dungeon_class_data.get("level", 0) for dungeon_class_data in dungeon_classes.values())
                class_xp_total = sum(dungeon_class_data.get("xpCurrent", 0) for dungeon_class_data in dungeon_classes.values())

                for dungeon_class, dungeon_class_data in dungeon_classes.items():
                    level = dungeon_class_data.get("level", 0)
                    xp = dungeon_class_data.get("xpCurrent", 0)
                    xp_for_next = dungeon_class_data.get("xpForNext", 0)

                    exp_string = f"**MAX LEVEL**" if xp_for_next == 0 else f"**XP**: {format(xp, ',d')}/{format(xp_for_next, ',d')}"
                    progress_string = get_progress_bar(dungeon_class_data["progress"], self.bot, xp_for_next)

                    embed.add_field(
                        name=f"{self.bot.get_emoji(class_emoji_mappings[dungeon_class])} {dungeon_class.capitalize()} {'(selected)' if dungeon_class.capitalize() == selected_class else ''}",
                        value=f"**Level**: {level}\n{exp_string}\n{progress_string}",
                        inline=False
                    )

                class_average = class_levels_total / len(dungeon_classes) if dungeon_classes else 0

                floors = catacombs_data.get('floors', {})
                mmfloors = catacombs_data.get('master_mode_floors', {})

                total_runs = sum(floor_data.get('times_played', 0) for floor_data in floors.values()) + sum(floor_data.get('times_played', 0) for floor_data in mmfloors.values())

                secrets_per_run = secrets_found / total_runs if total_runs != 0 else 0

                embed.description = f"""
{self.bot.get_emoji("WITHER_CATALYST")} Catacombs XP: {cata_string}
{self.bot.get_emoji("CHEST")} Secrets Found: **{format(secrets_found, ',d')}** (**{round(secrets_per_run, 2)}** per run)
{self.bot.get_emoji("NETHER_STAR")} Class Average: **{round(class_average, 2)}**
:man_running: Total Runs: **{format(total_runs, ',d')}**
{self.bot.get_emoji(class_emoji_mappings[selected_class.lower()])} Total Class XP: **{abbreviate(class_xp_total)}**"""
                
            case "Slayers":
                slayer_data = profile_data.get("slayer")
                if not slayer_data:
                    slayer_data = {}

                levels_string = "/".join(str(slayer_data[slayer]["level"]) for slayer in slayer_data)
                embed.description = levels_string

                for slayer, data_specific_slayer in slayer_data.items():
                    level = data_specific_slayer["level"]
                    exp = data_specific_slayer["xp"]
                    exp_for_next = data_specific_slayer.get("xpForNext", 0)
                    progress = data_specific_slayer.get("progress", 0)

                    if exp_for_next == None:
                        exp_for_next = 0

                    if progress == None:
                        progress = 1

                    progress = get_progress_bar(progress, self.bot, exp_for_next, 9)
                    kills = data_specific_slayer.get("kills", {})

                    emoji = self.bot.get_emoji(slayer_emoji_mappings[slayer])
                    slayer_name = slayer_names[slayer]

                    kills_text = "\n\n**Boss Kills**:" + "".join(f"\nTier {kill}: {count}" for kill, count in kills.items()) if kills else ""

                    exp_string = f"**Exp**: {format(exp, ',d')}/{format(exp_for_next, ',d')}\n{progress}"
                    if exp_for_next == 0:
                        exp_string = f"**MAX LEVEL**\n{progress}"

                    embed.add_field(
                        name=f"{emoji} {slayer_name}",
                        value=f"**Level**: {level}\n{exp_string}{kills_text}\n\u200b",
                        inline=True
                    )

                    if slayer_name in ["Tarantula Broodmother", "Voidgloom Seraph", "Riftstalker Bloodfiend"]:
                        embed.add_field(name="\u200b", value="\u200b", inline=True)

                embed.fields[-1].value = embed.fields[-1].value[:-2]

            case "Skills":
                skill_data = profile_data.get("skills", {})
                if not skill_data:
                    skill_data = {}

                skill_levels_total = sum(skill_data[skill]["level"] for skill in skill_data if skill not in ["runecrafting", "social"])
                skill_xp_total = sum(skill_data[skill]["totalXp"] for skill in skill_data)

                for skill, skill_data_specific in skill_data.items():
                    level = skill_data_specific["level"]
                    xp_current = skill_data_specific["xpCurrent"]
                    xp_for_next = skill_data_specific["xpForNext"]

                    emoji = self.bot.get_emoji(skill_emoji_mappings[skill])

                    skill_string = "**MAX LEVEL**\n\u200b" if xp_for_next == 0 else f"**{abbreviate(xp_current)}** / {abbreviate(xp_for_next)} XP\n\u200b"

                    embed.add_field(
                        name=f"{emoji} {skill.capitalize()} {level}",
                        value=skill_string,
                    )

                dungeon_data = profile_data.get("dungeons", {})
                if not dungeon_data:
                    dungeon_data = {}
                catacombs_data = dungeon_data.get("catacombs", {})
                catacombs_skill = catacombs_data.get("skill", {})

                cata_level = catacombs_skill.get("level", 0)
                cata_xp = catacombs_skill.get("xpCurrent", 0)
                cata_xp_for_next = catacombs_skill.get("xpForNext", 0)

                cata_string = "**MAX LEVEL**" if cata_xp_for_next == 0 and cata_xp != 0 else f"**{abbreviate(cata_xp)}** / {abbreviate(cata_xp_for_next)} XP"

                embed.add_field(
                    name=f"{self.bot.get_emoji('WITHER_CATALYST')} Catacombs {cata_level}",
                    value=cata_string,
                )

                embed.fields[-2].value = embed.fields[-2].value[:-2]
                embed.fields[-3].value = embed.fields[-3].value[:-2]

                skill_average = skill_levels_total / (len(skill_data) - 2)
                embed.description = f"Skill Average: **{round(skill_average, 2)}**\nTotal Skill XP: **{abbreviate(skill_xp_total)}**"

            case "Unsoulbound Networth":
                networth_data = profile_data.get("networth", {})
                if not networth_data:
                    networth_data = {}

                unsoulbound_networth_total = networth_data.get("unsoulboundNetworth", 0)
                embed.description = f"Networth: **{format(int(unsoulbound_networth_total), ',d')}** (**{abbreviate(unsoulbound_networth_total)}**)"

                purse = networth_data.get("purse", 0)
                bank = networth_data.get("bank", 0)
                personal_bank = networth_data.get("personalBank", 0)

                networth_types = networth_data.get("types", {})
                sacks = networth_types.get("sacks", {}).get("unsoulboundTotal", 0)
                essence = networth_types.get("essence", {}).get("unsoulboundTotal", 0)

                embed.add_field(
                    name=f"{self.bot.get_emoji('GOLD_INGOT')} Coins",
                    value=abbreviate(purse + bank + personal_bank),
                )

                embed.add_field(
                    name=f"{self.bot.get_emoji('SACKS')} Sacks",
                    value=abbreviate(sacks),
                )

                embed.add_field(
                    name=f"{self.bot.get_emoji('WITHER_ESSENCE')} Essence",
                    value=abbreviate(essence),
                )

                for category in networth_categories:
                    data_structure = {"total": 0, "items": []}
                    process_items(networth_types, category["keys"], data_structure, False)
                    data_structure["items"] = sorted(data_structure["items"], key=lambda item: item["price"], reverse=True)
                    field = generate_embed_networth_field(data_structure["items"], data_structure["total"], category["title"], self.bot)
                    embed.add_field(**field)

            case "Soulbound Networth":
                networth_data = profile_data.get("networth")
                if not networth_data:
                    networth_data = {}

                soulbound_networth_total = networth_data.get("networth", 0) - networth_data.get("unsoulboundNetworth", 0)
                embed.description = f"Networth: **{format(int(soulbound_networth_total), ',d')}** (**{abbreviate(soulbound_networth_total)}**)"
                purse = networth_data.get("purse", 0)
                bank = networth_data.get("bank", 0)

                networth_types = networth_data.get("types")
                if not networth_types:
                    networth_types = {}

                sacks = networth_types.get("sacks", 0)
                essence = networth_types.get("essence", 0)

                embed.add_field(
                    name=f"{self.bot.get_emoji('GOLD_INGOT')} Coins",
                    value="Not Soulbound",
                )

                embed.add_field(
                    name=f"{self.bot.get_emoji('SACKS')} Sacks",
                    value="Not Soulbound",
                )

                embed.add_field(
                    name=f"{self.bot.get_emoji('WITHER_ESSENCE')} Essence",
                    value="Not Soulbound",
                )

                for category in networth_categories:
                    data_structure = {
                        "total": 0,
                        "items": []
                    }
                    process_items(networth_types, category["keys"], data_structure, True)
                    data_structure["items"] = sorted(data_structure["items"], key=lambda item: item["price"], reverse=True)
                    items = data_structure["items"]
                    value = data_structure["total"]
                    field = generate_embed_networth_field(items, value, category["title"], self.bot)
                    embed.add_field(**field)

            case "Mining":
                mining_data = profile_data.get("mining", {})
                if not mining_data:
                    mining_data = {}

                hotM_tree = mining_data.get("hotM_tree", {})
                tokens = hotM_tree.get("tokens", {"current": 0, "total": 0})
                mithril_powder = mining_data.get("mithril_powder", {"total": 0, "current": 0})
                gemstone_powder = mining_data.get("gemstone_powder", {"total": 0, "current": 0})
                glacite_powder = mining_data.get("glacite_powder", {"total": 0, "current": 0})
                level = hotM_tree.get("level", 0)
                experience = hotM_tree.get("experience", 0)
                perks = hotM_tree.get("perks", [])
                selected_ability = hotM_tree.get("pickaxe_ability", "")
                last_reset = f"<t:{int(hotM_tree.get('last_reset', 0) / 1000)}:R>" if hotM_tree.get("last_reset") else "Never"

                hotm_tree_emojis = {
                    "empty": self.bot.get_emoji("VOID"),
                    "selected_ability": self.bot.get_emoji("EMERALD_BLOCK"),
                    "ability": self.bot.get_emoji("EMERALD_BLOCK"),
                    "unlocked_path": self.bot.get_emoji("EMERALD"),
                    "peak": self.bot.get_emoji("BLOCK_OF_REDSTONE"),
                    "maxed_path": self.bot.get_emoji("DIAMOND"),
                    "locked_path": self.bot.get_emoji("COAL"),
                    "locked_ability": self.bot.get_emoji("BLOCK_OF_COAL")
                }

                mining_emojis = {
                    "hotm": self.bot.get_emoji("HEART_OF_THE_MOUNTAIN"),
                    "tokens": self.bot.get_emoji("IRON_NUGGET"),
                    "mithril_powder": self.bot.get_emoji("GREEN_DYE"),
                    "gemstone_poweder": self.bot.get_emoji("PINK_DYE"),
                    "pigeon": self.bot.get_emoji("ROYAL_PIGEON"),
                    "reset": ":x:",
                    "pick": self.bot.get_emoji("STONE_PICKAXE"),
                    "glacite": self.bot.get_emoji("LIGHT_BLUE_DYE"),
                }

                def get_hotm_emojis(perks_data_raw: list, selected_ability: str):
                    perks = []
                    for item in perks_data_raw:
                        if item.get("id"):
                            perks.append(item["id"])

                    perks_data = {}
                    for item in perks_data_raw:
                        if item.get("id"):
                            perks_data[item["id"]] = item

                    hotm_string = ""
                    for row in hotm_tree_mapping:
                        for cell in row:

                            if cell["type"] == "empty":
                                hotm_string += hotm_tree_emojis["empty"]

                            elif cell["type"] not in perks and cell["type"] not in special_hotm_types:
                                hotm_string += hotm_tree_emojis["locked_path"]

                            elif cell["type"] not in special_hotm_types:
                                perk_data = perks_data[cell["type"]]
                                if perk_data["maxLevel"] == perk_data["level"]:
                                    hotm_string += hotm_tree_emojis["maxed_path"]
                                else:
                                    hotm_string += hotm_tree_emojis["unlocked_path"]

                            else:
                                if cell["type"] == "special_0":
                                    hotm_string += hotm_tree_emojis["peak"]

                                else:

                                    if cell["type"] not in perks_data:
                                        hotm_string += hotm_tree_emojis["locked_ability"]

                                    elif cell["type"] in perks_data and perks_data[cell["type"]]["name"] == selected_ability:
                                        hotm_string += hotm_tree_emojis["selected_ability"]

                                    else:
                                        hotm_string += hotm_tree_emojis["ability"]

                        hotm_string += "\n"

                    return hotm_string

                embed.description = f"""
{mining_emojis['hotm']} Level: **{level}** (**{format(experience, ',d')}** XP)
{mining_emojis['tokens']} Tokens: **{tokens['total'] - tokens['current']}** / **{tokens['total']}** used
{mining_emojis['mithril_powder']} Mithril Powder: **{abbreviate(mithril_powder['total'])}**
{mining_emojis['gemstone_poweder']} Gemstone Powder: **{abbreviate(gemstone_powder['total'])}**
{mining_emojis['glacite']} Glacite Powder: **{abbreviate(glacite_powder['total'])}**
:x: **Last Reset**: {last_reset}

{get_hotm_emojis(perks, selected_ability)}"""
            case "Farming":
                farming_data = profile_data.get("farming", {})
                if not farming_data:
                    farming_data = {}

                skill_data = profile_data.get("skills", {})
                farming_skill = skill_data.get("farming", {})
                farming_level = farming_skill.get("level", 0)

                trapper_quest = farming_data.get("trapper_quest", {})
                pelt_count = trapper_quest.get("pelt_count", 0)

                jacobs = farming_data.get("jacob", {})
                contests = jacobs.get("contests", {})
                medals_current = jacobs.get("medals", {"gold": 0, "silver": 0, "bronze": 0})
                medals_total = jacobs.get("total_badges", {"gold": 0, "silver": 0, "bronze": 0})
                crops = jacobs.get("crops", {})

                farming_emojis = {
                    "level": self.bot.get_emoji("GOLDEN_HOE"),
                    "contests": self.bot.get_emoji("JACOBS_MEDAL"),
                    "pelts": self.bot.get_emoji("RABBIT_HIDE"),
                    "gold_medal": self.bot.get_emoji("GOLD_INGOT"),
                    "silver_medal": self.bot.get_emoji("IRON_INGOT"),
                    "bronze_medal": self.bot.get_emoji("BRICK"),
                    "wheat": self.bot.get_emoji("WHEAT"),
                    "carrot": self.bot.get_emoji("CARROT"),
                    "potato": self.bot.get_emoji("POTATO"),
                    "melon": self.bot.get_emoji("MELON_BLOCK"),
                    "pumpkin": self.bot.get_emoji("PUMPKIN_BLOCK"),
                    "cocoa_beans": self.bot.get_emoji("COCOA_BEANS"),
                    "mushroom": self.bot.get_emoji("RED_MUSHROOM"),
                    "cactus": self.bot.get_emoji("CACTUS"),
                    "sugar_cane": self.bot.get_emoji("SUGAR_CANE"),
                    "nether_wart": self.bot.get_emoji("NETHER_WART"),
                    "farming_level_cap": self.bot.get_emoji("HAY_BALE_ICON")
                }

                crop_string = "".join(
                    f"{farming_emojis.get(crop_data.get('name', '').lower().replace(' ', '_'), '')} {crop_data.get('name')}\n"
                    for crop_data in crops.values()
                    if crop_data.get("badges", {}).get("gold", 0) > 0
                ).strip()

                embed.add_field(
                    name="Medals",
                    value=f"""
{farming_emojis['gold_medal']} Gold: **{medals_total['gold']}**  (**{medals_current['gold']}**)
{farming_emojis['silver_medal']} Silver: **{medals_total['silver']}**  (**{medals_current['silver']}**)
{farming_emojis['bronze_medal']} Bronze: **{medals_total['bronze']}**  (**{medals_current['bronze']}**)"""
                )

                embed.add_field(
                    name=f"Unique Golds ({len(crop_string.splitlines())})",
                    value=crop_string
                )

                perks = jacobs.get("perks", {})
                perk_string = f"""
{farming_emojis['farming_level_cap']} Farming Level Cap: **{perks.get("farming_level_cap", 0)}** / 10
{farming_emojis['wheat']} Extra Farming Drops: **☘ {perks.get("double_drops", 0) * 4}** / ☘ 60"""

                embed.add_field(
                    name="Perks",
                    value=perk_string,
                    inline=False
                )

                attended_contests = contests.get("attended_contests", 0)

                embed.description = f"""
{farming_emojis['level']} Level: **{farming_level}**
{farming_emojis['contests']} Contests: **{attended_contests}**
{farming_emojis['pelts']} Pelts: **{pelt_count}**"""
                
            case "Kuudra":
                kuudra = Kuudra(self.bot)

                crimson_data = kuudra.get_data_or_default(profile_data, "crimson")
                kuudra_data = kuudra.get_data_or_default(crimson_data, "kuudra")
                kuudra_runs = kuudra.get_kuudra_runs(kuudra_data)
                factions = kuudra.get_data_or_default(crimson_data, "factions", {})
                _faction, faction_emoji, mage_reputation, barbarian_reputation = kuudra.get_faction_info(factions)

                embed.description = f"""
Current Faction: **{_faction[0]}** {faction_emoji}
{kuudra.faction_emojis["Mages"]} Mages Reputation: **{format(mage_reputation, ',d')}**
{kuudra.faction_emojis["Barbarians"]} Barbarians Reputation: **{format(barbarian_reputation, ',d')}**"""

                kuudra_string = kuudra.generate_kuudra_string(kuudra_runs)
                embed.add_field(
                    name="Kuudra Completions",
                    value=kuudra_string,
                    inline=False
                )

            case "Minions":
                minion_data = profile_data.get("minions", {})
                if not minion_data:
                    minion_data = {}

                unique_minions = minion_data.get("uniqueMinions", 0)
                minion_slots = minion_data.get("minionSlots", 0)
                bonus_slots = minion_data.get("bonusSlots", 0)

                max_minions = {category: 0 for category in ["mining", "combat", "fishing", "farming", "foraging"]}

                for minion in minion_data.get("unlockedMinions", []):
                    if minion["tier"] >= minion.get("maxLevel", 11):
                        max_minions[minion["category"]] += 1

                max_minions_string = "\n".join(
                    f"{self.bot.get_emoji(skill_emoji_mappings[category])} {category.capitalize()}: **{count}**"
                    for category, count in sorted(max_minions.items(), key=lambda item: item[1], reverse=True)
                )

                embed.description = f"""
{self.bot.get_emoji('COBBLESTONE_MINION')} Minion Slots: **{minion_slots + bonus_slots}** (of which **{bonus_slots}** are bonus slots)
{self.bot.get_emoji('IRON_NUGGET')} Unique Minion Crafts: **{unique_minions}**

**Amount of Maxed Minions**:
{max_minions_string}"""

            case "Garden":
                garden_data = profile_data.get("garden", {})
                if not garden_data:
                    garden_data = {}

                unlocked_plots = garden_data.get("unlocked_plots_ids", [])
                unlocked_plots.append("unlocked")

                green_pane = self.bot.get_emoji("GREEN_DYE")
                red_pane = self.bot.get_emoji("RED_DYE")
                empty = self.bot.get_emoji("VOID")

                unlocked_plot_lists = [[None for _ in range(5)] for _ in range(5)]

                for i, row in enumerate(garden_plot_mappings):
                    for j, plot in enumerate(row):


                        if plot in unlocked_plots:
                            unlocked_plot_lists[i][j] = green_pane

                            if plot == "unlocked":
                                unlocked_plot_lists[i][j] = empty

                        else:
                            unlocked_plot_lists[i][j] = red_pane

                garden_string = "\n".join("".join(plot for plot in row) for row in unlocked_plot_lists)

                commission_data = garden_data.get("commission_data", {})
                total_completed = commission_data.get("total_completed", 0)
                unique_npcs_served = commission_data.get("unique_npcs_served", 0)

                garden_experience = garden_data.get("garden_experience", 0)

                experience_threshold_per_level = [0, 70, 140, 280, 520, 1120, 2620, 4620, 7120, 10120, 20120, 30120, 40120, 50120, 60120]

                level = 0
                for i in range(1, len(experience_threshold_per_level)):
                    if garden_experience < experience_threshold_per_level[i]:
                        level += (garden_experience - experience_threshold_per_level[i - 1]) / (experience_threshold_per_level[i] - experience_threshold_per_level[i - 1])
                        break
                    level += 1

                garden_level = round(level+1, 2)

                embed.description = f'''
Garden Level: **{garden_level}** (**{format(garden_experience, ',d')}** XP)
Visitors Served: **{total_completed}** / 1,055
Unique Visitors: **{unique_npcs_served}** / 83
        
**Unlocked Plots:**\n{garden_string}'''
                
        if self.send_response:
            return await interaction.respond(embed=embed, view=self.recursing_view(), ephemeral=True)
        
        return await interaction.edit_original_response(embed=embed)
