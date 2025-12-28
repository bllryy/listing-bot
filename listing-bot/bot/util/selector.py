import discord
import aiohttp

from .gamemode import gamemode_to_string
from .constants import api_key
from .fetch import fetch_mojang_api
from discord import OptionChoice


async def profile_selector(ctx: discord.AutocompleteContext):
    """
    Returns a list of profiles for the given username input
    """
    username = getattr(ctx, "value", None)
    if not username:
        opts = getattr(ctx, "options", None)
        if isinstance(opts, dict):
            username = opts.get("username")

    if not username:
        return []

    async with aiohttp.ClientSession() as session:
        try:
            uuid_result, status = await fetch_mojang_api(session, username)
        except Exception:
            return ["Something went wrong."]

        uuid = None
        if isinstance(uuid_result, dict):
            uuid = uuid_result.get("id")
        elif isinstance(uuid_result, str):
            if uuid_result == "Invalid username.":
                return ["Invalid username."]
            uuid = uuid_result

        if not uuid:
            return ["Invalid username."]

        try:
            async with session.get(f"https://api.hypixel.net/v2/skyblock/profiles?key={api_key}&uuid={uuid}") as resp:
                data = await resp.json()
        except Exception:
            return ["Something went wrong."]

        if not data or data.get("success") is False:
            return ["Something went wrong."]

        profiles = data.get("profiles")
        if not profiles:
            return ["No profiles found."]

        strings = []
        for profile in profiles:
            cute = profile.get("cute_name", "Unknown")
            gm = gamemode_to_string(profile.get("game_mode"))
            string = f"{cute} {gm}"
            if profile.get("selected", False):
                strings.insert(0, string)
            else:
                strings.append(string)

        choices = []
        for s in strings[:25]:
            try:
                choices.append(OptionChoice(name=s, value=handle_selection(s)))
            except Exception:
                choices.append(handle_selection(s))

        return choices
            
def handle_selection(selection: str):
    """
    Returns the cute name of the selected profile.
    """

    if any(icon in selection for icon in ["🎲", "♻", "🏝"]):
        return selection[:-2].strip()

    return selection.strip()
