from typing import Tuple

def get_cata_lvl(exp):
    levels = {
        '0': 0, '1': 50, '2': 125, '3': 235, '4': 395, '5': 625, '6': 955, '7': 1425, '8': 2095, '9': 3045,
        '10': 4385, '11': 6275, '12': 8940, '13': 12700, '14': 17960, '15': 25340, '16': 35640,
        '17': 50040, '18': 70040, '19': 97640, '20': 135640, '21': 188140, '22': 259640, '23': 356640,
        '24': 488640, '25': 668640, '26': 911640, '27': 1239640, '28': 1684640, '29': 2284640,
        '30': 3084640, '31': 4149640, '32': 5559640, '33': 7459640, '34': 9959640, '35': 13259640,
        '36': 17559640, '37': 23159640, '38': 30359640, '39': 39559640, '40': 51559640, '41': 66559640,
        '42': 85559640, '43': 109559640, '44': 139559640, '45': 177559640, '46': 225559640,
        '47': 285559640, '48': 360559640, '49': 453559640, '50': 569809640
    }
    for level in levels:
        if exp >= levels["50"]:
            return 50
        if levels[level] > exp:
            lowexp = levels[str(int(level) - 1)]
            highexp = levels[level]
            difference = highexp - lowexp
            extra = exp - lowexp
            percentage = (extra / difference)
            return (int(level) - 1) + percentage


SKILL_MAX_LEVELS = {
    "mining": {
        "maxLevel": 60,
    },

    "foraging": {
        "maxLevel": 50,
    },

    "enchanting": {
        "maxLevel": 60,
    },

    "farming": {
        "maxLevel": 60,
    },

    "combat": {
        "maxLevel": 60,
    },

    "fishing": {
        "maxLevel": 50,
    },

    "alchemy": {
        "maxLevel": 50,
    },

    "taming": {
        "maxLevel": 50,
    }
}


def get_slayer_level(slayer_type, exp):
    revenant = {"0": 0, "1": 5, "2": 15, "3": 200, "4": 1000,
                "5": 5000, "6": 20000, "7": 100000, "8": 400000, "9": 1000000}
    spider = {"0": 0, "1": 5, "2": 15, "3": 200, "4": 1000,
              "5": 5000, "6": 20000, "7": 100000, "8": 400000, "9": 1000000}
    sven = {"0": 0, "1": 10, "2": 30, "3": 250, "4": 1500, "5": 5000,
            "6": 20000, "7": 100000, "8": 400000, "9": 1000000}
    enderman = {"0": 0, "1": 10, "2": 30, "3": 250, "4": 1500,
                "5": 5000, "6": 20000, "7": 100000, "8": 400000, "9": 1000000}
    blaze = {"0": 0, "1": 10, "2": 30, "3": 250, "4": 1500,
             "5": 5000, "6": 20000, "7": 100000, "8": 400000, "9": 1000000}

    if slayer_type in ["revenant", "zombie"]:
        levels = revenant
    elif slayer_type in ["spider", "tarantula"]:
        levels = spider
    elif slayer_type in ["sven", "wolf"]:
        levels = sven
    elif slayer_type in ["enderman", "voidgloom"]:
        levels = enderman
    elif slayer_type in ["blaze", "demonlord"]:
        levels = blaze

    for level in levels:
        if exp >= levels["9"]:
            return 9
        if levels.get(level) > exp:
            lowexp = levels[str(int(level) - 1)]
            highexp = levels.get(level)
            difference = highexp - lowexp
            extra = exp - lowexp
            percentage = (extra / difference)
            return (int(level) - 1) + percentage


skill_levels = {
    "0": 0, "1": 50, "2": 175, "3": 375, "4": 675, "5": 1175, "6": 1925, "7": 2925, "8": 4425, "9": 6425,
    "10": 9925, "11": 14925, "12": 22425, "13": 32425, "14": 47425, "15": 67425, "16": 97425, "17": 147425,
    "18": 222425, "19": 322425, "20": 522425, "21": 822425, "22": 1222425, "23": 1722425, "24": 2322425,
    "25": 3022425, "26": 3822425, "27": 4722425, "28": 5722425, "29": 6822425, "30": 8022425, "31": 9322425,
    "32": 10722425, "33": 12222425, "34": 13822425, "35": 15522425, "36": 17322425, "37": 19222425,
    "38": 21222425, "39": 23322425, "40": 25522425, "41": 27822425, "42": 30222425, "43": 32722425,
    "44": 35322425, "45": 38072425, "46": 40972425, "47": 44072425, "48": 47472425, "49": 51172425,
    "50": 55172425, "51": 59472425, "52": 64072425, "53": 68972425, "54": 74172425, "55": 79672425,
    "56": 85472425, "57": 91572425, "58": 97972425, "59": 104672425, "60": 111672425

}


def get_skill_lvl(skill_type, exp):
    levels = {
        "0": 0, "1": 50, "2": 175, "3": 375, "4": 675, "5": 1175, "6": 1925, "7": 2925, "8": 4425, "9": 6425,
        "10": 9925, "11": 14925, "12": 22425, "13": 32425, "14": 47425, "15": 67425, "16": 97425, "17": 147425,
        "18": 222425, "19": 322425, "20": 522425, "21": 822425, "22": 1222425, "23": 1722425, "24": 2322425,
        "25": 3022425, "26": 3822425, "27": 4722425, "28": 5722425, "29": 6822425, "30": 8022425, "31": 9322425,
        "32": 10722425, "33": 12222425, "34": 13822425, "35": 15522425, "36": 17322425, "37": 19222425,
        "38": 21222425, "39": 23322425, "40": 25522425, "41": 27822425, "42": 30222425, "43": 32722425,
        "44": 35322425, "45": 38072425, "46": 40972425, "47": 44072425, "48": 47472425, "49": 51172425,
        "50": 55172425, "51": 59472425, "52": 64072425, "53": 68972425, "54": 74172425, "55": 79672425,
        "56": 85472425, "57": 91572425, "58": 97972425, "59": 104672425, "60": 111672425
    }
    for level in levels:
        if exp >= levels[str(SKILL_MAX_LEVELS[skill_type]["maxLevel"])]:
            return SKILL_MAX_LEVELS[skill_type]["maxLevel"]
        if levels[level] > exp:
            lowexp = levels[str(int(level) - 1)]
            highexp = levels[level]
            difference = highexp - lowexp
            extra = exp - lowexp
            percentage = (extra / difference)
            return (int(level) - 1) + percentage
        

def catacombs_to_usd(data: dict) -> Tuple[float, float]:
    dungeon_data = data.get("dungeons", {})
    if not dungeon_data:
        return 0.0, 0.0
    
    cata_data = dungeon_data.get("catacombs", {})
    if not cata_data:
        return 0.0, 0.0
    
    cata_data = cata_data.get("skill", {})
    
    if not cata_data:
        return 0.0, 0.0
    
    cata_xp = cata_data.get("totalXp", 0)
    if not cata_xp:
        return 0.0, 0.0
    
    max_xp = 569809640
    cata_xp = min(cata_xp, max_xp)
    
    cata_level = get_cata_lvl(cata_xp)
    
    max_price = 100.0
    
    value_tiers = [
        (0, 0.0, 0.015),
        (20, 3.0, 0.12),
        (24, 6.0, 0.2),
        (30, 10.0, 0.35),
        (40, 35.0, 1.5),
        (45, 75.0, 5.0),
        (49, 100.0, 0.0)
    ]
    
    tier_index = 0
    for i, (tier_level, _, _) in enumerate(value_tiers):
        if cata_level < tier_level:
            break
        tier_index = i
    
    if tier_index == len(value_tiers) - 1:
        value = value_tiers[-1][1]
    else:
        current_min_level, current_base_value, current_scaling = value_tiers[tier_index]
        
        level_progress = cata_level - current_min_level
        quadratic_component = level_progress * level_progress * current_scaling
        value = current_base_value + quadratic_component
    
    if cata_level >= 42 and cata_level < 49:
        bonus = (cata_level - 42) * 0.5
        value += bonus
    
    if cata_level >= 49 and cata_level < 50:
        value += 8.0
    
    value = min(value, max_price)

    return value, value / 1.8


def slayer_to_usd(data: dict) -> Tuple[float, float]:
    slayer_data = data.get("slayer", {})
    
    rates = {
        "zombie": {
            "tiers": [100000, 3000000, float('inf')],
            "rates": [0.00001, 0.000008, 0.000007],
            "max_value": 0.005,
            "multiplier": 1.2
        },
        "spider": {
            "tiers": [100000, 3000000, float('inf')],
            "rates": [0.00001, 0.000008, 0.000007],
            "max_value": 0.004,
            "multiplier": 1.3
        },
        "wolf": {
            "tiers": [100000, 3000000, float('inf')],
            "rates": [0.000014, 0.000012, 0.00001],
            "max_value": 0.008,
            "multiplier": 1.35
        },
        "enderman": {
            "tiers": [100000, 3000000, float('inf')],
            "rates": [0.000025, 0.000022, 0.00002],
            "max_value": 0.018,
            "multiplier": 1.0
        },
        "blaze": {
            "tiers": [20000, 100000, 1000000, float('inf')],
            "rates": [0.000033, 0.000029, 0.00002, 0.0],
            "max_value": 0.018,
            "multiplier": 1.0
        }
    }
    
    total_value = 0.0
    
    for slayer_type, config in rates.items():
        xp = slayer_data.get(slayer_type, {}).get("xp", 0)
        
        if xp == 0:
            continue
        
        xp = min(xp, 1000000)
        
        tier_index = 0
        for i, threshold in enumerate(config["tiers"]):
            if xp < threshold:
                tier_index = i
                break
            if i == len(config["tiers"]) - 2 and xp >= threshold:
                tier_index = i + 1
                break
        
        if tier_index == len(config["tiers"]) - 1:
            value = config["max_value"]
        else:
            lower_bound = 0 if tier_index == 0 else config["tiers"][tier_index - 1]
            upper_bound = config["tiers"][tier_index]
            
            current_rate = config["rates"][tier_index]
            next_rate = config["rates"][tier_index + 1] if tier_index < len(config["rates"]) - 1 else current_rate
            
            progress = (xp - lower_bound) / (upper_bound - lower_bound)
            
            linear_value = xp * current_rate
            
            if current_rate >= next_rate:
                target_upper_value = upper_bound * next_rate
                
                value = linear_value * (1 - progress) + target_upper_value * progress
                
                quad_factor = (1 - progress) * progress
                value += quad_factor * (target_upper_value - linear_value) * 0.2
            else:
                upper_bound_linear = upper_bound * current_rate
                upper_bound_next_rate = upper_bound * next_rate
                
                ratio = upper_bound_next_rate / upper_bound_linear
                value = linear_value * (1 + (ratio - 1) * progress)
        
        value *= config["multiplier"]
        
        total_value += value
    
    return total_value, total_value / 1.8

def networth_to_usd(data: dict) -> Tuple[float, float]:
    coin_multiplier = 4e-8

    def process_item(item: dict) -> float:
        soulbound = item.get("soulbound", False)

        cosmetic = item.get("cosmetic", False)
        value = item.get("price", 0.0)
        calculation = item.get("calculation", [])

        def calc_multiplier(value: float) -> float:
            if value < 1e7:
                return 0.5
                
            if value >= 1e10:
                return 0.9

            t = (value - 1e7) / (1e10 - 1e7)
            return 0.5 + (0.9 - 0.5) * (t**0.9)

        multiplier = calc_multiplier(value)
        if soulbound:
            multiplier *= 0.65

        item_usd_value = value * multiplier * coin_multiplier
        
        if cosmetic and item_usd_value > 0 and calculation:
            cosmetic_deduction = (item_usd_value / 1e6) * 0.01
            item_usd_value = max(0, item_usd_value - cosmetic_deduction)

        elif cosmetic and item_usd_value > 0:
            cosmetic_deduction = (item_usd_value / 1e6) * 0.03
            item_usd_value = max(0, item_usd_value - cosmetic_deduction)

        return item_usd_value

    total_value = 0

    networth_data = data.get("networth", {})

    liquid_networth = networth_data.get("purse", 0) + networth_data.get("bank", 0) + networth_data.get("personalBank", 0)
    total_value += liquid_networth * coin_multiplier

    item_types = networth_data.get("types", {})
    for item_type in item_types:
        item_type_data = item_types[item_type]
        items = item_type_data.get("items", [])
        for item in items:
            if isinstance(item, dict):
                value = process_item(item)
                total_value += value
    
    lowball_value = max(0, total_value / 1.8)

    return total_value, lowball_value

def skills_to_usd(data: dict) -> Tuple[float, float]:
    skills_data: dict = data.get("skills", {})
    if not skills_data:
        return 0.0, 0.0
    
    conversion_rates = {
        'farming': 18 / 111672425,
        'foraging': 24 / 55172425,
        'fishing': 22 / 55172425,
        'alchemy': 2 / 55172425,
        'enchanting': 0.5 / 111672425,
        'combat': 14 / 111672425,
        'mining': 12 / 111672425,
        'taming': 0.5 / 55172425
    }
    
    total_value = 0.0
    skill_values = {}
    
    def get_max_xp(skill):
        max_level = SKILL_MAX_LEVELS.get(skill, {}).get("maxLevel", 50)
        return int(skill_levels[str(max_level)])
    
    for skill, skill_info in skills_data.items():
        if skill not in conversion_rates:
            continue
            
        xp = skill_info.get("xp", 0)
        if not xp:
            continue
            
        max_xp = get_max_xp(skill)
        capped_xp = min(xp, max_xp)
        
        rate = conversion_rates[skill]
        value = capped_xp * rate
        
        skill_values[skill] = {
            'level': get_skill_lvl(skill, xp),
            'value': round(value, 2)
        }
        
        total_value += value
    
    if skill_values:
        skill_levels_list = [info['level'] for info in skill_values.values()]
        skill_avg = sum(skill_levels_list) / len(skill_levels_list)
        
        if skill_avg > 50:
            avg_bonus = (skill_avg - 50) ** 2 * 0.02
            total_value += avg_bonus
    
    return total_value, total_value / 1.8

def mining_to_usd(data: dict) -> Tuple[float, float]:
    mining_data = data.get("mining", {})
    
    mithril_powder = mining_data.get("mithril_powder", {}).get("total", 0)
    gemstone_powder = mining_data.get("gemstone_powder", {}).get("total", 0)
    glacite_powder = mining_data.get("glacite_powder", {}).get("total", 0)

    max_mithril = 12658220
    max_gemstone = 31505666
    max_glacite = 35479533
    
    mithril_powder = min(mithril_powder, max_mithril)
    gemstone_powder = min(gemstone_powder, max_gemstone)
    glacite_powder = min(glacite_powder, max_glacite)
    
    mithril_value = min(mithril_powder / max_mithril * 20, 20)
    gemstone_value = min(gemstone_powder / max_gemstone * 20, 20)
    glacite_value = min(glacite_powder / max_glacite * 20, 20)
    
    total_value = mithril_value + gemstone_value + glacite_value
    
    return total_value, total_value / 1.8

def farming_to_usd(data: dict) -> Tuple[float, float]:

    total_value = 0.0

    farming_data = data.get("farming", {})
    jacobs_data = farming_data.get("jacob", {})
    if not jacobs_data:
        return 0.0, 0.0
    
    total_value += jacobs_data.get("unique_golds", 0) * 0.75

    perks = jacobs_data.get("perks", {})
    if perks:
        for perk in perks:
            if perk not in ["double_drops", "farming_level_cap"]:
                continue

            perk_value = perks[perk]
            total_value += perk_value * 0.126

    return total_value, total_value / 1.8

def crimson_to_usd(data: dict) -> Tuple[float, float]:

    total_value = 0.0

    crimson_data = data.get("crimson", {})

    fractions_data = crimson_data.get("factions", {})
    kuudra_data = crimson_data.get("kuudra", {})

    kuudra_tiers = {
        "none": 0.5,
        "hot": 0.7,
        "burning": 1.2,
        "fiery": 1.9,
        "infernal": 2.7
    }

    for tier in kuudra_tiers:
        if tier in kuudra_data:
            total_value += kuudra_tiers[tier]

    if not fractions_data:
        return total_value, total_value / 1.8

    try:
        highest_rep = max(value for value in fractions_data.values() if isinstance(value, int)) if fractions_data else 0
    except ValueError:
        highest_rep = 0
        
    max_rep = 12000

    reputation = min(highest_rep, max_rep)
    total_value += reputation / 500

    return total_value, total_value / 1.8

def gather_lowball_value(data: dict) -> dict:
    return {
        "catacombs": catacombs_to_usd(data)[1],
        "slayer": slayer_to_usd(data)[1],
        "networth": networth_to_usd(data)[1],
        "skills": skills_to_usd(data)[1],
        "mining": mining_to_usd(data)[1],
        "farming": farming_to_usd(data)[1],
        "crimson": crimson_to_usd(data)[1]
    }

def gather_value(data: dict) -> dict:
    return {
        "catacombs": catacombs_to_usd(data)[0],
        "slayer": slayer_to_usd(data)[0],
        "networth": networth_to_usd(data)[0],
        "skills": skills_to_usd(data)[0],
        "mining": mining_to_usd(data)[0],
        "farming": farming_to_usd(data)[0],
        "crimson": crimson_to_usd(data)[0]
    }

async def calculate_coin_price(type: str, bot, amount: int):
    base_key = f"coin_price_{type}"
    base_price_value = await bot.db.get_config(base_key)
    if base_price_value is None:
        return 0.0
    
    base_price = float(base_price_value)
    
    dynamic_tiers = []
    tier_number = 1
    while True:
        tier_key = f"{type}_coins_tier_{tier_number}"
        tier_value = await bot.db.get_config(tier_key)
        if tier_value is None:
            break
        parts = tier_value.split(';')
        if len(parts) != 2:
            break
        try:
            threshold = int(parts[0])
            price = float(parts[1])
        except ValueError:
            break

        dynamic_tiers.append({"over": threshold, "price": price})
        tier_number += 1
    
    dynamic_tiers.sort(key=lambda x: x["over"])
    
    price_to_pay = 0.0
    amount_remaining = amount
    millions = amount / 1e6
    
    if not dynamic_tiers:
        return base_price * millions
    
    first_threshold = dynamic_tiers[0]["over"]
    
    for index, tier in enumerate(dynamic_tiers):
        tier_multi = tier["price"]
        tier_threshold = tier["over"]
        millions_under_first_threshold = 0.0
        
        if index == 0:
            if amount <= tier_threshold:
                return base_price * millions
            millions_under_first_threshold = tier_threshold / 1e6
            price_to_pay += millions_under_first_threshold * base_price
            amount_remaining -= tier_threshold
        
        if index == len(dynamic_tiers) - 1:
            if len(dynamic_tiers) != 1:
                amount_remaining += tier_threshold
                amount_remaining -= (first_threshold + tier_threshold)
            price_to_pay += (amount_remaining / 1e6) * tier_multi
            break
        
        next_tier = dynamic_tiers[index + 1]
        next_tier_threshold = next_tier["over"]
        diff = next_tier_threshold - tier_threshold
        diff_millions = diff / 1e6
        
        if amount_remaining > next_tier_threshold:
            price_to_pay += diff_millions * tier_multi
            amount_remaining -= diff
        else:
            price_to_pay += (amount_remaining / 1e6) * tier_multi
            break
    
    return price_to_pay

def average(lst):
    return sum(lst) / len(lst)

def calc_skill_avg(skills: list) -> str:
    if not skills:
        return "0"
    
    return f"{round(sum(skills) / len(skills), 2)}"