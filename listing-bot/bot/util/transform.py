from bot.bot import Bot

def abbreviate(amount: int):
    if not amount:
        return 0

    table = {
        1000000000000: "T",
        1000000000: "B",
        1000000: "M",
        1000: "K",
    }
    for num, abbrev in table.items():
        if amount >= num:
            return f"{amount // num}{abbrev}"
        
def unabbreviate(amount: str) -> int:
    if not amount:
        return 0
    
    amount = amount.upper().replace(",", "")
    multiplier = 1
    
    abbreviations = {
        'B': 1_000_000_000,
        'M': 1_000_000,
        'K': 1_000,
    }
    
    for abbrev, mult in abbreviations.items():
        if abbrev in amount:
            number_part = amount.replace(abbrev, "")
            multiplier = mult
            break
    else:
        number_part = amount
    
    try:
        if '.' in number_part:
            return int(float(number_part) * multiplier)
        return int(number_part) * multiplier
    except (ValueError, TypeError):
        return 0

def format_commas(amount):

    if isinstance(amount, str):
        return format(unabbreviate(amount), ",d")
    
    return format(int(amount), ",d")

def get_progress_bar(progress, bot: Bot, exp_for_next, panes=10):
    if exp_for_next == None:
        return bot.get_emoji("GREEN_STAINED_GLASS_PANE") * panes
    if exp_for_next == 0:
        return bot.get_emoji("GREEN_STAINED_GLASS_PANE") * panes
    return ''.join(bot.get_emoji("GREEN_STAINED_GLASS_PANE") if progress > i / (panes + 1) else bot.get_emoji("GREY_STAINED_GLASS_PANE") for i in range(1, panes + 1))

def count(item):
    if item.get("count", 1) == 1:
        return item.get("name")
    else:
        return f"`{item['count']}x` {item.get('name')}"