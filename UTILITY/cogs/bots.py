# cogs/bots.py
import discord
from discord import SlashCommandGroup, option
from discord.ext import commands

import subprocess

from util.copy_files import copy_gathered_files
from util.get_bot_names import get_bot_names
from util.update_files import update_files

import base64

import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Bots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    listing = SlashCommandGroup(name="listing", description="Manages listing bots.", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    bots = listing.create_subgroup(name="bots", description="Manage listing bots.")

    @bots.command(
        name="restart",
        description="Restarts all listing bots",
    )
    @commands.is_owner()
    async def restart_bots(self, ctx: discord.ApplicationContext):
        try:
            await ctx.defer(ephemeral=True)
        except:
            pass

        bots = get_bot_names()
        to_restart = []

        for bot in bots:
            to_restart.append(f'v2-{bot}')

        subprocess.run(f"/root/.nvm/versions/node/v20.17.0/bin/pm2 restart {' '.join(to_restart)}", shell=True)
        await ctx.respond(f"Restarted bots: {', '.join(to_restart)}", ephemeral=True) #Respond after restarting

    @bots.command(name="update")
    @commands.is_owner()
    async def update_bots(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        success = update_files()
        if not success:
            return await ctx.respond("An error occurred while updating the files.", ephemeral=True)

        parent_dir = os.path.dirname(base_dir)
        
        bots = get_bot_names()
        for bot in bots:
            bot_path = os.path.join(parent_dir, bot)
            print(f"Updating bot at: {bot_path}")
            copy_gathered_files(bot_path)

        await self.restart_bots(ctx)

    @bots.command(
        name="create",
        description="Create a listing bot.",
    )
    @commands.is_owner()
    @option(name="token", description="The token of the bot.", type=str, required=True)
    @option(name="name", description="The name of the bot.", type=str, required=True)
    async def create_bot(self, ctx: discord.ApplicationContext, token: str, name: str):
        await ctx.defer(ephemeral=True)

        if os.path.exists(f"../{name}"):
            return await ctx.respond("A bot with that name already exists.", ephemeral=True)

        try:
            client_id = base64.b64decode(token.split(".")[0]+"==").decode("utf-8")
            int(client_id)
        except:
            return await ctx.respond("Invalid token.", ephemeral=True)

        url = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions=8"
        view = discord.ui.View()  # Corrected:  Create an instance, don't reference the class
        view.add_item(discord.ui.Button(label="Invite", url=url))


        copy_gathered_files(f"../{name}", token) #Correct call.
        bot_dir = os.path.join("..", name)
        original_dir = os.getcwd()
        try:
            os.chdir(bot_dir)
            subprocess.run(f"/root/.nvm/versions/node/v20.17.0/bin/pm2 start main.py --name=v2-{name} --interpreter=python3", shell=True)
            await ctx.respond(f"Created and started bot: {name}", view=view, ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Created bot: {name}, but failed to start it. Error: {e}", view=view, ephemeral=True)
        finally:
            os.chdir(original_dir)

def setup(bot):
    bot.add_cog(Bots(bot))