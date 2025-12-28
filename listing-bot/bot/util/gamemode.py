def gamemode_to_string(gamemode):
    if gamemode == "island":
        return "🏝"

    elif gamemode in ["normal", None]:
        return ""

    elif gamemode == "ironman":
        return "♻"

    elif gamemode == "bingo":
        return "🎲"
    else:
        return "Unknown"
