import os
import json

def commas(number):
    return "{:,.0f}".format(number)

def count(count):
    return f"`{count}x` " if count > 1 else ""

def format_number(number):
    thresholds = [
        (1_000_000_000_000, 'T'),
        (1_000_000_000, 'B'),
        (1_000_000, 'M'),
        (1_000, 'K')
    ]
    for threshold, suffix in thresholds:
        if number >= threshold:
            return f"{round(number / threshold, 2)}{suffix}"
    return int(number)

def star(star):
    if star not in [0, 1]:
        raise ValueError("Star must be 0 or 1")
    return "⭐" if star == 1 else ""

def star_convert(star):
    if star not in ["Yes", "No"]:
        raise ValueError("Star must be Yes or No")
    return 1 if star == "Yes" else 0

def slayer_levels(levels):
    return "/".join(map(str, levels))

def unabbreviate(amount):
    if isinstance(amount, (int, float)):
        return amount

    lookup = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
        "t": 1_000_000_000_000,
        "q": 1_000_000_000_000_000,
        "Q": 1_000_000_000_000_000_000
    }
    abbreviation = amount[-1].lower()
    multiplier = lookup.get(abbreviation, 1)

    try:
        amount = float(amount[:-1]) * multiplier if abbreviation in lookup else float(amount)
    except ValueError:
        return "invalid"

    return amount

def get_channel_name(type, price, number, a=""):
    types = {
        "accounts": "account",
        "profiles": "profile",
        "bedwars": "bedwars",
        "fortnite": "fortnite",
        "alts": "alts"
    }
    default_cname = f"💲{price}┃{types.get(type, '')}-{number}{a}"

    if os.path.exists("./data/channel_names.json"):
        with open("./data/channel_names.json", "r") as f:
            channel_names = json.load(f)
            accounts_cname = channel_names.get(type)
            if accounts_cname:
                return accounts_cname.format(price=price, number=number)

    return default_cname