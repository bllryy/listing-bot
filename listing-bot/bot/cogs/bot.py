import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from count_lines import count_lines
from discord.ui import View, Button
import aiohttp
from bot.util.constants import bot_name, is_authorized_to_use_bot
import subprocess

from bot.bot import Bot as BotObject

class Bot(commands.Cog):
    def __init__(self, bot):
        self.bot: BotObject = bot

    _bot = SlashCommandGroup("bot", description="Commands related to the bot")
    _commands = _bot.create_subgroup("commands", "Commands related to the commands")

    @_bot.command(
        name="suggest",
        description="Suggest a new feature or command for the bot"
    )
    @option(
        "suggestion",
        description="Your suggestion for the bot",
        type=str,
        required=True
    )
    @is_authorized_to_use_bot()
    async def suggest(self, ctx: discord.ApplicationContext, suggestion: str):
        await ctx.defer(ephemeral=True)

        webhook = discord.Webhook.from_url("", session=self.bot.session)
        await webhook.send(
            content=suggestion,
            username=ctx.author.display_name,
            avatar_url=ctx.author.display_avatar.url
        )

        embed = discord.Embed(
            title="Suggestion Sent",
            description="Your suggestion has been sent to the development team. Thank you for your input!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed, ephemeral=True)

    @_bot.command(
        name="information",
        description="Get information on the bot"
    )
    async def bot_stats(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get("https://backup.noemt.dev/accounts") as r:
                data: dict = await r.json()
                current_account = data.get("current", "1323257877711818753")

        invite = "t4D7Njgcgg"

        view = View()
        view.add_item(Button(label=f"nom's shop (quite reputable if I say so)", url=f'https://discord.gg/{invite}', row=1))
        view.add_item(Button(label="Buy!", url=f"https://noemt.dev", row=1))
        view.add_item(Button(label="Bot Invite", url=f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot", row=2))

        user_object: discord.User = self.bot.get_user(int(current_account))
        if not user_object:
            user_object = await self.bot.fetch_user(int(current_account))

        lines, files = count_lines()
        embed = discord.Embed(
            title="Bot Stats",
            color=discord.Color.red(),
            url="https://bots.noemt.dev"
        )
        embed.description = f"""**Listing Bot v2 (rewrite)**
Developed by: <@{current_account}> `({user_object.global_name})`

Lines of code: `{lines}`
Python Files: `{files}`"""

        embed.set_thumbnail(
            url="https://noemt.dev/assets/icon.webp"
        )
        embed.add_field(name="Uptime", value=f"*A lot*, I also fix bugs in record time as I get push notification whenever something goes wrong. If it doesn't work after you retried within 2 minutes, then, idk, maybe I'm out or something..", inline=True)
        await ctx.respond(embed=embed, view=view)

    @_bot.command(
        name="dashboard",
        description="Get the dashboard link"
    )
    @is_authorized_to_use_bot(strict=True)
    async def dashboard(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        embed = discord.Embed(
            title="Dashboard",
            description="You can manage the bot using the dashboard.",
            color=discord.Color.blue()
        )
        dashboard_link = f"https://dashboard.noemt.dev/{bot_name}"

        view = View()
        view.add_item(Button(label="Open Dashboard", url=dashboard_link, row=1))
        embed.set_thumbnail(
            url="https://noemt.dev/assets/icon.webp"
        )
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @_bot.command(
        name="restart",
        description="Restart the bot"
    )
    @is_authorized_to_use_bot(strict=True)
    async def restart(self, ctx: discord.ApplicationContext):
        await ctx.respond("Restarting the bot...", ephemeral=True)
        subprocess.run(f"/usr/local/bin/pm2 restart v2-{bot_name}", shell=True)

def setup(bot):
    bot.add_cog(Bot(bot))