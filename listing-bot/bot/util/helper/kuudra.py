from bot.bot import Bot
from bot.util.transform import abbreviate

class Kuudra:
    def __init__(self, bot: Bot):
        self.bot = bot

        self.faction_emojis = {
            "Mages": bot.get_emoji("MAGE_FACTION"),
            "Barbarians": bot.get_emoji("BARBARIAN_FACTION")
        }

        self.kuudra_key_emojis = {
            "burning": bot.get_emoji("KUUDRA_KEY_BURNING"),
            "fiery": bot.get_emoji("KUUDRA_KEY_FIERY"),
            "hot": bot.get_emoji("KUUDRA_KEY_HOT"),
            "infernal": bot.get_emoji("KUUDRA_KEY_INFERNAL"),
            "basic": bot.get_emoji("KUUDRA_KEY_BASIC")
        }

    def get_data_or_default(self, data, key, default={}):
        return data.get(key, default)

    def get_kuudra_runs(self, kuudra_data):
        return {
            "basic": kuudra_data.get("none", 0),
            "hot": kuudra_data.get("hot", 0),
            "burning": kuudra_data.get("burning", 0),
            "fiery": kuudra_data.get("fiery", 0),
            "infernal": kuudra_data.get("infernal", 0)
        }

    def get_faction_info(self, factions):
        mage_reputation = factions.get("mages_reputation", 0)
        barbarian_reputation = factions.get("barbarians_reputation", 0)
        current_faction = factions.get("name")
        if current_faction:
            faction_emoji = self.faction_emojis[current_faction.capitalize()]
            _faction = (current_faction.capitalize(),)
        else:
            _faction = "None",
            faction_emoji = ""
        return _faction, faction_emoji, mage_reputation, barbarian_reputation

    def generate_kuudra_string(self, kuudra_runs):
        return "\n".join(f"{self.kuudra_key_emojis[kuudra]} {kuudra.capitalize()}: **{kuudra_runs[kuudra]}**" for kuudra in kuudra_runs)

    def get_category_items(self, categories, networth_types, data_structure):
        for category in categories:
            category_data = self.get_data_or_default(networth_types, category)
            category_items = category_data.get("items", [])
            for item in category_items:
                if item["soulbound"]:
                    data_structure["items"].append(item)

    def convert_kuudra_stars(self, item_lore):
        stars_with_colorcode = item_lore.split(" ")[-1]
        twice = stars_with_colorcode.count("§b✪")
        once = stars_with_colorcode.count("§6✪")
        return twice * 2 + once

    def convert_attribute_roll_string_to_attributes(self, attribute_roll_string):
        attributes = attribute_roll_string.split("_roll_")
        attributes = [attribute.replace("_", " ") for attribute in attributes if attribute]
        return ", ".join(attributes).title()