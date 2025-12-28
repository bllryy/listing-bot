import aiohttp
import discord

import discord.ext
import discord.ext.commands
from bot.bot import Bot

from .calcs import *
from .fetch import fetch_mojang_api, fetch_profile_data
from .gamemode import gamemode_to_string

from bot.util.list import list_account, list_profile
from bot.util.get_payment_methods import get_payment_methods


def create_embed(
        value_type: str, value_data: dict,
        username: str, cute_name: str,
        profile_type: str, bot: Bot,
        coop: bool,
        uuid: str = None,
        disabled_values: list = []
    ):

    adjusted_data = value_data.copy()
    if coop:
        for key in adjusted_data:
            if key == "catacombs":
                adjusted_data[key] /= 2.5
            elif key == "networth":
                adjusted_data[key] /= 1.3
            else:
                adjusted_data[key] /= 1.7

    embed = discord.Embed(
        color=discord.Color.embed_background(),
        title=f"{value_type.title()} for {username} on {cute_name}" +
        (f" {profile_type}" if profile_type != " " else ""),
        url=f"https://sky.shiiyu.moe/stats/{username}/{cute_name}",
    )

    value_emojis = {
        "networth": "BANK_ITEM", 
        "catacombs": "MORT",
        "skills": "JUNGLE_SAPLING",
        "slayer": "BEHEADED_HORROR",
        "mining": "HEART_OF_THE_MOUNTAIN",
        "farming": "HAY_BALE_ICON",
        "crimson": "MAGMA_CREAM"
    }
    
    total_value = 0
    for value_type_key, emoji_key in value_emojis.items():
        if value_type_key in adjusted_data:
            value_amount = adjusted_data[value_type_key]
            if value_type_key not in disabled_values:
                total_value += value_amount
                embed.add_field(
                    name=f"{bot.item_emojis.get(emoji_key, '💰')} {value_type_key.title()}",
                    value=f"${round(value_amount, 2)}",
                    inline=True
                )
            else:
                embed.add_field(
                    name=f"{bot.item_emojis.get(emoji_key, '💰')} {value_type_key.title()}",
                    value=f"~~${round(value_amount, 2)}~~",
                    inline=True
                )
    
    embed.add_field(
        name=f"{bot.item_emojis.get('BLOCK_OF_GOLD', '💰')} Total",
        value=f"${round(total_value, 2)}",
        inline=True
    )
    
    embed.set_thumbnail(url=f"https://mc-heads.net/avatar/{uuid}")

    if value_type == "Value":
        embed.add_field(inline=False, name="You can list this for:", value=f"{int(total_value)}$")

    footer_text = []
    if coop:
        footer_text.append("Co-op adjustments applied")
    if footer_text:
        embed.set_footer(text=" | ".join(footer_text))

    view = ToggleView(
        bot=bot,
        username=username,
        cute_name=cute_name,
        profile_type=profile_type,
        value_data=adjusted_data,
        original_data=value_data,
        uuid=uuid,
        value_type=value_type,
        disabled_values=disabled_values
    )

    return embed, view

class ToggleView(discord.ui.View):
    def __init__(self, bot, username, cute_name, profile_type, value_data, original_data, uuid, value_type, disabled_values=None):
        super().__init__(disable_on_timeout=True)
        self.bot = bot
        self.username = username
        self.cute_name = cute_name
        self.profile_type = profile_type
        self.value_data = value_data
        self.original_data = original_data
        self.uuid = uuid
        self.value_type = value_type
        self.disabled_values = disabled_values or []
        self.coop = False

        self.coop_button = discord.ui.Button(label="Toggle Co-op", style=discord.ButtonStyle.red)
        self.value_type_button = discord.ui.Button(label="Toggle Value Type", style=discord.ButtonStyle.blurple)

        self.value_buttons = {}
        value_types = ["networth", "catacombs", "skills", "slayer", "mining", "farming", "crimson"]

        for i, value_type in enumerate(value_types):
            row = 1 if i < 4 else 2
            if value_type in self.value_data:
                button = discord.ui.Button(
                    label=f"Toggle {value_type.title()}",
                    style=discord.ButtonStyle.green if value_type not in self.disabled_values else discord.ButtonStyle.red,
                    row=row,
                )
                button.callback = self.create_toggle_callback(value_type)
                self.value_buttons[value_type] = button
                self.add_item(button)

        self.coop_button.callback = self.toggle_coop
        self.value_type_button.callback = self.toggle_value_type

        self.add_item(self.coop_button)
        self.add_item(self.value_type_button)

        options = [
            discord.SelectOption(label="List as Account ❌🔔", value="account_no_ping", description="This lists the account without pinging."),
            discord.SelectOption(label="List as Account 🔔🔔", value="account_yes_ping", description="This lists the account with pinging."),
            discord.SelectOption(label="List as Profile ❌🔔", value="profile_no_ping", description="This lists the profile without pinging."),
            discord.SelectOption(label="List as Profile 🔔🔔", value="profile_yes_ping", description="This lists the profile with pinging.")
        ]

        select_menu = discord.ui.Select(
            placeholder="Select an option to list directly.",
            options=options,
            row=3
        )

        async def select_callback(interaction: discord.Interaction):
            selected_option = select_menu.values[0]
            if selected_option == "account_no_ping":
                await self.list_account_no_ping(interaction)
            elif selected_option == "account_yes_ping":
                await self.list_account_ping(interaction)
            elif selected_option == "profile_no_ping":
                await self.list_profile_no_ping(interaction)
            elif selected_option == "profile_yes_ping":
                await self.list_profile_ping(interaction)
    
        select_menu.callback = select_callback
        self.add_item(select_menu)

    def create_toggle_callback(self, value_type):
        async def toggle_callback(interaction: discord.Interaction):
            if value_type in self.disabled_values:
                self.disabled_values.remove(value_type)
                self.value_buttons[value_type].style = discord.ButtonStyle.green
            else:
                self.disabled_values.append(value_type)
                self.value_buttons[value_type].style = discord.ButtonStyle.red
            
            await self.update_embed(interaction)
        
        return toggle_callback

    async def toggle_coop(self, interaction: discord.Interaction):
        self.coop = not self.coop
        self.coop_button.style = discord.ButtonStyle.green if self.coop else discord.ButtonStyle.red
        await self.update_embed(interaction)

    async def toggle_value_type(self, interaction: discord.Interaction, return_embed: bool = False):
        if self.value_type == "Value":
            self.value_type = "Lowball"
            self.value_data = {
                key: self.original_data.get(key, 0) * (1 / 1.8)
                for key in self.original_data
            }
        else:
            self.value_type = "Value"
            self.value_data = {
                key: self.original_data.get(key, 0)
                for key in self.original_data
            }

        await self.update_embed(interaction, return_embed=return_embed)

    async def list_account_no_ping(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass

        if self.value_type == "Lowball":
            await self.toggle_value_type(interaction)

        payment_methods = await get_payment_methods(self.bot, interaction.user.id)
        if not payment_methods:
            embed = discord.Embed(
                title="Error",
                description=f"You haven't set your payment methods yet. Use {self.bot.get_command_link('methods set')} to do so.",
                color=discord.Color.red()
            )
            return await interaction.respond(embed=embed, ephemeral=True)

        total_value = sum(self.value_data[key] for key in self.value_data if key not in self.disabled_values)
        
        embed = await list_account(
            self.bot, self.username, 
            int(total_value), 
            payment_methods, False,
            "No Information Provided", True, self.cute_name, None, interaction, interaction.user.id
        )
        await super().on_timeout()
        await interaction.respond(embed=embed, ephemeral=True)
        await interaction.followup.edit_message(view=self, message_id=interaction.message.id)

    async def list_account_ping(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass

        if self.value_type == "Lowball":
            await self.toggle_value_type(interaction)

        payment_methods = await get_payment_methods(self.bot, interaction.user.id)
        if not payment_methods:
            embed = discord.Embed(
                title="Error",
                description=f"You haven't set your payment methods yet. Use {self.bot.get_command_link('methods set')} to do so.",
                color=discord.Color.red()
            )
            return await interaction.respond(embed=embed, ephemeral=True)

        total_value = sum(self.value_data[key] for key in self.value_data if key not in self.disabled_values)
        
        embed = await list_account(
            self.bot, self.username, 
            int(total_value), 
            payment_methods, True,
            "No Information Provided", True, self.cute_name, None, interaction, interaction.user.id
        )
        await super().on_timeout()
        await interaction.respond(embed=embed, ephemeral=True)
        await interaction.followup.edit_message(view=self, message_id=interaction.message.id)
    
    async def list_profile_no_ping(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass

        if self.value_type == "Lowball":
            await self.toggle_value_type(interaction)

        payment_methods = await get_payment_methods(self.bot, interaction.user.id)
        if not payment_methods:
            embed = discord.Embed(
                title="Error",
                description=f"You haven't set your payment methods yet. Use {self.bot.get_command_link('methods set')} to do so.",
                color=discord.Color.red()
            )
            return await interaction.respond(embed=embed, ephemeral=True)
        
        total_value = self.data_value["networth"]
            
        embed = await list_profile(
            self.bot, self.username, 
            int(total_value), 
            payment_methods, False,
            "No Information Provided", True, self.cute_name, None, interaction.user.id
        )
        await super().on_timeout()
        await interaction.respond(embed=embed, ephemeral=True)
        await interaction.followup.edit_message(view=self, message_id=interaction.message.id)

    async def list_profile_ping(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass
        
        if self.value_type == "Lowball":
            await self.toggle_value_type(interaction)

        payment_methods = await get_payment_methods(self.bot, interaction.user.id)
        if not payment_methods:
            embed = discord.Embed(
                title="Error",
                description=f"You haven't set your payment methods yet. Use {self.bot.get_command_link('methods set')} to do so.",
                color=discord.Color.red()
            )
            return await interaction.respond(embed=embed, ephemeral=True)

        total_value = self.data_value["networth"]
            
        embed = await list_profile(
            self.bot, self.username, 
            int(total_value), 
            payment_methods, True,
            "No Information Provided", True, self.cute_name, None, interaction.user.id
        )
        await super().on_timeout()
        await interaction.respond(embed=embed, ephemeral=True)
        await interaction.followup.edit_message(view=self, message_id=interaction.message.id)

    async def update_embed(self, interaction: discord.Interaction, return_embed: bool=False):
        embed, view = create_embed(
            value_type=self.value_type,
            value_data=self.value_data,
            username=self.username,
            cute_name=self.cute_name,
            profile_type=self.profile_type,
            bot=self.bot,
            coop=self.coop,
            uuid=self.uuid,
            disabled_values=self.disabled_values
        )

        if return_embed:
            return embed
        
        await interaction.response.edit_message(embed=embed, view=self)

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    def reset_buttons(self):
        self.coop = False
        self.coop_button.style = discord.ButtonStyle.red
        for value_type, button in self.value_buttons.items():
            if value_type in self.disabled_values:
                button.style = discord.ButtonStyle.red
            else:
                button.style = discord.ButtonStyle.green

async def old_lowball(ctx, bot, username: str, profile: str=None, uuid: str=None, just_embed: bool=False):
    if isinstance(ctx, discord.ApplicationContext) and not just_embed:
        await ctx.defer(ephemeral=True)

    async with aiohttp.ClientSession() as session:
        if not uuid:
            mojang_api, status = await fetch_mojang_api(session, username)
        else:
            mojang_api = {"id": uuid, "name": username}

        if mojang_api.get("id") is None:
            if not just_embed:
                embed = discord.Embed(
                    title="Error",
                    description="This username doesn't exist",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            return None, None
    
        profile_data, cute_name = await fetch_profile_data(session, mojang_api['id'], bot, profile, allow_error_handler=False if just_embed else True)

    if not profile_data:
        return None, None

    # Get both value types
    standard_values = gather_value(profile_data)  # Get standard values first
    lowball_values = gather_lowball_value(profile_data)  # Get lowball values

    embed, view = create_embed(
        value_type="Lowball",
        value_data=lowball_values,
        username=mojang_api['name'],
        cute_name=profile_data['name'],
        profile_type=gamemode_to_string(profile_data['gamemode']),
        bot=bot,
        coop=False,
        uuid=mojang_api['id'],
        disabled_values=[]
    )

    # Now we need to modify the view's original_data to be the standard values
    view.original_data = standard_values

    if just_embed:
        return embed, view

    await ctx.respond(embed=embed, ephemeral=True, view=view)
    return embed, view

async def old_value(ctx, bot, username: str, profile: str=None, just_embed: bool=False, return_profile_information=False):  # type: ignore

    if isinstance(ctx, discord.ApplicationContext) and not just_embed:
        await ctx.defer(ephemeral=True)

    async with aiohttp.ClientSession() as session:
        
        mojang_api, status = await fetch_mojang_api(session, username)
        if mojang_api.get("id") is None:
            if not just_embed:
                embed = discord.Embed(
                    title="Error",
                    description="This username doesn't exist",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            return None, None
    
        profile_data, cute_name  = await fetch_profile_data(session, mojang_api['id'], bot, profile, allow_error_handler=False if just_embed else True)

    if not profile_data:
        return None, None
    
    value_data = gather_value(profile_data)

    embed, view = create_embed(
        value_type="Value",
        value_data=value_data,
        username=mojang_api['name'],
        cute_name=profile_data['name'],
        profile_type=gamemode_to_string(profile_data['gamemode']),
        bot=bot,
        coop=False,
        uuid=mojang_api['id']
    )

    if just_embed:
        if return_profile_information:
            return embed, view, profile_data
        
        return embed, view

    await ctx.respond(embed=embed, ephemeral=True, view=view)
    return embed, view


async def old_inticket(mojang_obj, profile_data, p_type):
    lowball_values = gather_lowball_value(profile_data)
    
    total_value = sum(lowball_values.values())
    
    return 1, total_value