from bot.util.constants import rarity_emoji_mappings, networth_embed_field_emoji_mappings
from bot.bot import Bot
from bot.util.transform import abbreviate, count

def process_items(networth_types, keys, data_structure, soulbound):
    for key in keys:
        items_data = networth_types.get(key, {"total": 0, "unsoulboundTotal": 0, "items": []})
        data_structure["total"] += (items_data["total"] - items_data["unsoulboundTotal"]) if soulbound else items_data["unsoulboundTotal"]
        for item in items_data.get("items", []):
            if item["soulbound"] == soulbound:
                data_structure["items"].append(item)

def generate_embed_networth_field(items, total_value, name, bot: Bot):
    items_string = ""
    for item in enumerate(items):
        if item[0] == 5:
            items_string += f"**... {len(items) - 5} more**"
            break

        suffix = ""
        for calc in item[1]["calculation"]:
            if calc["id"] == "RECOMBOBULATOR_3000":
                suffix += bot.get_emoji(rarity_emoji_mappings["recomb"])

        items_string += f"→ {count(item[1])} {suffix} (**{abbreviate(item[1]['price'])}**)\n"

    return {
        "name": f"{bot.get_emoji(networth_embed_field_emoji_mappings[name])} {name} ({abbreviate(total_value)})",
        "value": items_string,
        "inline": False
    }