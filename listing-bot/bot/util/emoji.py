from bot.bot import Bot

special_hotm_types = ["mining_speed_boost", "vein_seeker", "maniac_miner",
                      "pickaxe_toss", "special_0", "gifts_from_the_departed", "hazardous_miner"]

hotm_tree_mapping = [
    [
        {
            "type": "gemstone_infusion",
            "maxLevel": 3,
            "name": "Gemstone Infusion"
        },
        {
            "type": "gifts_from_the_departed",
            "maxLevel": 100,
            "name": "Gifts From The Departed"
        },
        {
            "type": "frozen_solid",
            "maxLevel": 1,
            "name": "Frozen Solid"
        },
        {
            "type": "hungry_for_more",
            "maxLevel": 50,
            "name": "Dead Man's Chest"
        },
        {
            "type": "excavator",
            "maxLevel": 50,
            "name": "Excavator"
        },
        {
            "type": "rags_of_riches",
            "maxLevel": 50,
            "name": "Rags to Riches"
        },
        {
            "type": "hazardous_miner",
            "maxLevel": 3,
            "name": "Hazardous Miner"
        }
    ],
    [
        {"type": "empty"},
        {
            "type": "surveyor",
            "maxLevel": 20,
            "name": "Surveyor"
        },
        {"type": "empty"},
        {
            "type": "subzero_mining",
            "maxLevel": 100,
            "name": "SubZero Mining"

        },
        {"type": "empty"},
        {
            "type": "eager_adventurer",
            "maxLevel": 100,
            "name": "Eager Adventurer"
        },
        {"type": "empty"}
    ],
    [
        {"name": 'Keen Eye', "maxLevel": 1, "type": "keen_eye"},
        {"name": 'Warm Hearted', "maxLevel": 50, "type": "warm_hearted"},
        {"name": 'Dust Collector', "maxLevel": 20, "type": "dust_collector"},
        {"name": 'Daily Grind', "maxLevel": 100, "type": "daily_grind"},
        {"name": 'Strong Arm', "maxLevel": 100, "type": "strong_arm"},
        {"name": 'No Stone Unturned', "maxLevel": 50,
         "type": "no_stone_unturned"},
        {"name": 'Mineshaft Mayhem', "maxLevel": 1,
         "type": "mineshaft_mayhem"}
    ],
    [
        {"type": "empty"},
        {
            "type": "mining_speed_2",
            "maxLevel": 50,
            "name": "Mining Speed II"
        },
        {"type": "empty"},
        {
            "type": "powder_buff",
            "maxLevel": 50,
            "name": "Powder Buff"
        },
        {"type": "empty"},
        {
            "type": "mining_fortune_2",
            "maxLevel": 50,
            "name": "Mining Fortune II"
        },
        {"type": "empty"}
    ],
    [
        {
            "type": "vein_seeker",
            "maxLevel": 1,
            "name": "Vein Seeker"
        },
        {
            "type": "lonesome_miner",
            "maxLevel": 45,
            "name": "Lonesome Miner"
        },
        {
            "type": "professional",
            "maxLevel": 140,
            "name": "Professional"
        },
        {
            "type": "mole",
            "maxLevel": 190,
            "name": "Mole"
        },
        {
            "type": "fortunate",
            "maxLevel": 20,
            "name": "Fortunate"
        },
        {
            "type": "great_explorer",
            "maxLevel": 20,
            "name": "Great Explorer"
        },
        {
            "type": "maniac_miner",
            "maxLevel": 1,
            "name": "Maniac Miner"
        }
    ],
    [
        {"type": "empty"},
        {
            "type": "goblin_killer",
            "maxLevel": 1,
            "name": "Goblin Killer"
        },
        {"type": "empty"},
        {
            "type": "special_0",
            "maxLevel": 7,
            "name": "Peak Of The Mountain"
        },
        {"type": "empty"},
        {
            "type": "star_powder",
            "maxLevel": 1,
            "name": "Star Powder"
        },
        {"type": "empty"}
    ],
    [
        {
            "type": "daily_effect",
            "maxLevel": 1,
            "name": "Sky Mall"
        },
        {
            "type": "mining_madness",
            "maxLevel": 1,
            "name": "Mining madness"
        },
        {
            "type": "mining_experience",
            "maxLevel": 100,
            "name": "Seasoned Mineman"
        },
        {
            "type": "efficient_miner",
            "maxLevel": 100,
            "name": "Efficient Miner"
        },
        {
            "type": "experience_orbs",
            "maxLevel": 80,
            "name": "Orbiter"
        },
        {
            "type": "front_loaded",
            "maxLevel": 1,
            "name": "Front Loaded"
        },
        {
            "type": "precision_mining",
            "maxLevel": 1,
            "name": "Precision Mining"
        }
    ],
    [
        {"type": "empty"},
        {
            "type": "random_event",
            "maxLevel": 45,
            "name": "Luck Of The Cave"
        },
        {"type": "empty"},
        {
            "type": "daily_powder",
            "maxLevel": 100,
            "name": "Daily Powder"
        },
        {"type": "empty"},
        {
            "type": "fallen_star_bonus",
            "maxLevel": 30,
            "name": "Crystallized"
        },
        {"type": "empty"}
    ],
    [
        {"type": "empty"},
        {
            "type": "mining_speed_boost",
            "maxLevel": 1,
            "name": "Mining Speed Boost"
        },
        {
            "type": "titanium_insanium",
            "maxLevel": 50,
            "name": "Titanium Insanium"
        },
        {
            "type": "mining_fortune",
            "maxLevel": 50,
            "name": "Mining Fortune"
        },
        {
            "type": "forge_time",
            "maxLevel": 20,
            "name": "Quick Forge"
        },
        {
            "type": "pickaxe_toss",
            "maxLevel": 1,
            "name": "Pickobulus"
        },
        {"type": "empty"}
    ],
    [
        {"type": "empty"},
        {"type": "empty"},
        {"type": "empty"},
        {
            "type": "mining_speed",
            "maxLevel": 50,
            "name": "Mining Speed"
        },
        {"type": "empty"},
        {"type": "empty"},
        {"type": "empty"}
    ]
]

profile_emojis = {
    "apple": "\uD83C\uDF4E",
    "banana": "\uD83C\uDF4C",
    "blueberry": "\uD83E\uDED0",
    "coconut": "\uD83E\uDD65",
    "cucumber": "\uD83E\uDD52",
    "grapes": "\uD83C\uDF47",
    "kiwi": "\uD83E\uDD5D",
    "lemon": "\uD83C\uDF4B",
    "lime": "<:LIME:1328096434238656632>",
    "mango": "\uD83E\uDD6D",
    "orange": "\uD83C\uDF4A",
    "papaya": "<:PAPAYA:1328096646147604520>",
    "peach": "\uD83C\uDF51",
    "pear": "\uD83C\uDF50",
    "pineapple": "\uD83C\uDF4D",
    "pomegranate": "<:POMEGRANATE:1328096686131904594>",
    "raspberry": "<:RASPBERRY:1328096746282291321>",
    "strawberry": "\uD83C\uDF53",
    "tomato": "\uD83C\uDF45",
    "watermelon": "\uD83C\uDF49",
    "zucchini": "<:ZUCCHINI:1328097122695778334>",
    "unknown": "?"
}

hotm_tree_emojis = {
    "empty": "VOID",
    "selected_ability": "EMERALD_BLOCK",
    "ability": "EMERALD_BLOCK",
    "unlocked_path": "EMERALD",
    "peak": "BLOCK_OF_REDSTONE",
    "maxed_path": "DIAMOND",
    "locked_path": "COAL",
    "locked_ability": "BLOCK_OF_COAL"
}


def get_hotm_emojis(perks_data_raw: list, selected_ability: str, bot: Bot):
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
                hotm_string += bot.get_emoji(hotm_tree_emojis["empty"])

            elif cell["type"] not in perks and cell["type"] not in special_hotm_types:
                hotm_string += bot.get_emoji(hotm_tree_emojis["locked_path"])

            elif cell["type"] not in special_hotm_types:
                perk_data = perks_data[cell["type"]]
                if perk_data["maxLevel"] == perk_data["level"]:
                    hotm_string += bot.get_emoji(hotm_tree_emojis["maxed_path"])
                else:
                    hotm_string += bot.get_emoji(hotm_tree_emojis["unlocked_path"])

            else:
                if cell["type"] == "special_0":
                    hotm_string += bot.get_emoji(hotm_tree_emojis["peak"])

                else:

                    if cell["type"] not in perks_data:
                        hotm_string += bot.get_emoji(hotm_tree_emojis["locked_ability"])

                    elif cell["type"] in perks_data and perks_data[cell["type"]]["name"] == selected_ability:
                        hotm_string += bot.get_emoji(hotm_tree_emojis["selected_ability"])

                    else:
                        hotm_string += bot.get_emoji(hotm_tree_emojis["ability"])

        hotm_string += "\n"

    return hotm_string
