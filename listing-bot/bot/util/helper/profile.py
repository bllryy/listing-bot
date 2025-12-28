from bot.util.gamemode import gamemode_to_string
import discord
from bot.util.formatting import format_number
from bot.bot import Bot

class ProfileObject:
    def __init__(self, uuid, username, profile, payment_methods, additional_info, price, number, channel_id=None, message_id=None, listed_by=None, show_username='true'):
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

    def string_to_bool(self, string):
        return str(string).lower() == "true"
    
    def set_discord_data(self, channel_id, message_id, listed_by):
        self.channel_id = channel_id
        self.message_id = message_id
        self.listed_by = listed_by

    def to_tuple(self):
        return (self.uuid, self.username, self.profile, self.payment_methods, self.additional_info, self.price, self.number, self.channel_id, self.message_id, self.listed_by, str(self.show_username))

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
            "show_username": self.show_username
        }

    def to_embed(self, bot: Bot):
        embed = discord.Embed(
            title=f"Profile Listing #{self.number}",
            description=f"""
                **Username:** {self.username}
                `{self.uuid}`
                **Profile Name:** {self.profile}
                **Price:** ${self.price:,}
                **Payment Methods:** {self.payment_methods}
                **Additional Info:**
                ```{self.additional_info}```
            """,
            color=discord.Color.blue()
        )
        listed_by = bot.get_user(self.listed_by)
        embed.set_thumbnail(url=f"https://vzge.me/bust/{self.uuid}.png?y=-40")

        if listed_by:
            embed.set_author(name=f"{listed_by}", icon_url=listed_by.avatar.url if listed_by.avatar else listed_by.default_avatar.url)

        return embed

def create_embed_profile_listing(profile_data, cute_name, price, payment_methods, bot, listed_by):
    p_type = gamemode_to_string(profile_data.get('gamemode'))

    embed = discord.Embed(
        title=f"HIDDEN's Profile on " +
        cute_name+(f" {p_type}" if p_type != " " else ""),
        color=discord.Color.blue(),
    ).set_footer(text="Made by noemt | https://noemt.dev", icon_url="https://bots.noemt.dev/avatars/nom.png")
    embed.set_thumbnail(
        url="https://visage.surgeplay.com/full/640a5372780b4c2ab7e78359d2f9a6a8")
    
    networth_data = profile_data.get("networth", {})
    
    embed.add_field(
        name=f"{bot.get_emoji('BANK_ITEM')} Networth",
        value=f"""
Networth: `{format_number(networth_data.get('networth', 0))}`
Soulbound: `{format_number(networth_data.get('networth', 0)-networth_data.get('unsoulboundNetworth', 0))}`
Liquid: `{format_number(networth_data.get('purse', 0)+networth_data.get('bank', 0)+networth_data.get('personalBank', 0))}`"""
    )

    minion_data = profile_data.get("minions", {})
    slots = minion_data.get("minionSlots", 0)
    bonus = minion_data.get("bonusSlots", 0)

    embed.add_field(
        name=f"{bot.get_emoji('COBBLESTONE_MINION')} Minions",
        value=f"""
Slots: `{slots+bonus}`
Bonus: `{bonus}`
Base: `{slots}`"""

    )

    collection_data = profile_data.get("collections", [])
    total_collections = len(collection_data)
    maxed_collections = len([c for c in collection_data if c["tier"] == c["maxTiers"]])
    unlocked_collections = len([c for c in collection_data if c["amount"] > 0])

    embed.add_field(
        name=f"{bot.get_emoji('PAINTING')} Collections",
        value=f"""
Maxed: `{maxed_collections}/{total_collections}`
Unlocked: `{unlocked_collections}/{total_collections}`"""

    )

    embed.add_field(name="💸 Price",
                        value=f"{price}$",
                        inline=True)

    embed.add_field(name="💳 Payment Method(s)",
                        value=f"{payment_methods}",
                        inline=False)
    
    return embed