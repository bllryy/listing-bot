import discord
from discord.ext import commands
from discord import option, SlashCommandGroup
import asyncio

from discord.ui import View, Button

from bot.util.value import old_value, old_lowball
from bot.util.constants import is_authorized_to_use_bot
from bot.util.selector import profile_selector

class MassView(View):
    def __init__(self, embeds: list[discord.Embed], views: list[discord.ui.View]):
        super().__init__()
        self.embeds = embeds
        self.views = views
        self.index = 0

        self.update_buttons()

    def update_buttons(self):

        self.clear_items()

        start = self.index * 5
        end = start + 5

        first_views = self.views[start:end]

        # Add account buttons (max 5 per view page)
        for i, view in enumerate(first_views):
            child: discord.ui.Button = view.children[-1]
            child.custom_id = f"overwrite_{i}"
            child.callback = self.overwrite_button
            child.style = discord.ButtonStyle.gray
            child.label = view.username
            child.row = i  # Put each button on its own row (rows 0-4)

            self.add_item(child)

        # Add navigation buttons on the last row (row 4 if we have 5 account buttons, or the next available row)
        nav_row = min(len(first_views), 4)
        
        previous_button = Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous", row=nav_row)
        next_button = Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next", row=nav_row)

        previous_button.callback = self.previous
        next_button.callback = self.next

        self.add_item(previous_button)
        self.add_item(next_button)

    async def overwrite_button(self, interaction: discord.Interaction):
        button = interaction.data["custom_id"]
        index = int(button.split("_")[-1])

        start = self.index * 5
        view_at_index = self.views[start+index]

        embed = await view_at_index.update_embed(interaction=interaction, return_embed=True)

        await interaction.respond(embed=embed, view=view_at_index.reset_buttons(), ephemeral=True)

    async def next(self, interaction: discord.Interaction):
        self.index += 1
        max_index = (len(self.embeds) - 1) // 5
        if self.index > max_index:
            self.index = max_index
            return await interaction.response.defer()

        await self.handle_button_click(interaction)

    async def previous(self, interaction: discord.Interaction):
        self.index -= 1
        if self.index < 0:
            self.index = 0
            return await interaction.response.defer()

        await self.handle_button_click(interaction)

    async def handle_button_click(self, interaction: discord.Interaction):
        start = self.index * 5
        end = start + 5

        accounts_to_display = self.embeds[start:end]
        self.update_buttons()
        await interaction.response.edit_message(embeds=accounts_to_display, view=self)


class Value(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    bulk = SlashCommandGroup(
        name="bulk",
        description="Bulk commands",
    )

    @commands.slash_command(name="value", description="Get the account value of an account.")
    @option(name="username", description="Name of the Account", type=str, required=True)
    @option(name="profile", description="Profile to check", type=str, required=False, autocomplete=profile_selector)
    @is_authorized_to_use_bot()
    async def value_singular(self, ctx: discord.ApplicationContext, username: str, profile: str = None):
        await old_value(ctx, self.bot, username, profile)

    @commands.slash_command(name="lowball", description="Get the lowball value of an account.")
    @option(name="username", description="Name of the Account", type=str, required=True)
    @option(name="profile", description="Profile to check", type=str, required=False, autocomplete=profile_selector)
    @is_authorized_to_use_bot()
    async def lowball_singular(self, ctx: discord.ApplicationContext, username: str, profile: str = None):
        await old_lowball(ctx, self.bot, username, profile)

    @bulk.command(name="lowballs", description="Get the lowball value of MANY accounts.")
    @option(name="usernames", description="The usernames to check (separate by commas)", type=str, required=False)
    @option(name="file", description="The file to check (txt file with one username per line)", type=discord.Attachment, required=False)
    @is_authorized_to_use_bot()
    async def bulk_lowball(self, ctx: discord.ApplicationContext, usernames: str = None, file: discord.Attachment = None):

        if not usernames and not file:
            embed = discord.Embed(
                title="Input Error",
                description="You must provide either usernames or a file.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        if usernames and file:
            embed = discord.Embed(
                title="Input Error",
                description="You must provide either usernames or a file, not both.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        await ctx.defer(ephemeral=True)
        
        if file:
            file_content = await file.read()
            usernames = file_content.decode("utf-8").split("\n")
        else:
            usernames = usernames.split(",")

        embeds = []
        views = []

        failed_usernames = []

        for i, username in enumerate(usernames):
            embed, view = await old_lowball(ctx, self.bot, username, just_embed=True)

            if embed is None:
                failed_usernames.append(username)
                continue

            embeds.append(embed)
            views.append(view)

            if i != len(usernames) - 1:
                await asyncio.sleep(1)

        view = MassView(embeds, views)

        if failed_usernames:
            embed = discord.Embed(
                title="Some Accounts Failed to fetch",
                description=f"**Failed usernames**: `{'`, `'.join(failed_usernames)}`",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed)

        await ctx.respond(embeds=embeds[:5], view=view, ephemeral=True)

    @bulk.command(name="values", description="Get the account value of MANY accounts.")
    @option(name="usernames", description="The usernames to check (separate by commas)", type=str, required=False)
    @option(name="file", description="The file to check (txt file with one username per line)", type=discord.Attachment, required=False)
    @is_authorized_to_use_bot()
    async def bulk_value(self, ctx: discord.ApplicationContext, usernames: str = None, file: discord.Attachment = None):

        if not usernames and not file:
            embed = discord.Embed(
                title="Input Error",
                description="You must provide either usernames or a file.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        if usernames and file:
            embed = discord.Embed(
                title="Input Error",
                description="You must provide either usernames or a file, not both.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        await ctx.defer(ephemeral=True)
        
        if file:
            file_content = await file.read()
            usernames = file_content.decode("utf-8").split("\n")
        else:
            usernames = usernames.split(",")

        embeds = []
        views = []

        failed_usernames = []

        for i, username in enumerate(usernames):
            embed, view = await old_value(ctx, self.bot, username, just_embed=True)

            if embed is None:
                failed_usernames.append(username)
                continue

            embeds.append(embed)
            views.append(view)

            if i != len(usernames) - 1:
                await asyncio.sleep(1)

        view = MassView(embeds, views)

        if failed_usernames:
            embed = discord.Embed(
                title="Some Accounts Failed to fetch",
                description=f"**Failed usernames**: `{'`, `'.join(failed_usernames)}`",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed)

        if not failed_usernames == usernames:
            await ctx.respond(embeds=embeds[:5], view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(Value(bot))
