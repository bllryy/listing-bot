import discord
from discord.ext import commands
import os
import logging
import aiohttp

from dotenv import load_dotenv
load_dotenv()


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.command_prefix = ">"
        self.load_commands()

        self.logger = logging.getLogger("discord")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
        handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        self.logger.addHandler(handler)

        self.owner_ids = []

        self.session = None

    async def on_ready(self):
        print("Connected to database")
        self.session = aiohttp.ClientSession()

        async with self.session.get("https://backup.noemt.dev/accounts") as resp:
            response = await resp.json()
            current_account = response.get("current")
            if current_account:
                self.owner_ids.append(int(current_account))

        print("Owner IDs:", self.owner_ids)

    async def on_interaction(self, interaction: discord.Interaction):
        return await super().on_interaction(interaction)

    def load_commands(self):
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                self.load_extension(f"cogs.{filename[:-3]}")

    def run(self):
        token = os.getenv("TOKEN")
        self.loop.create_task(self.start(token))
        self.loop.run_forever()

    def get_command_link(self, qualified_name: str) -> str:
        for cog in self.cogs:
            cog_commands = []
            cog_object = self.get_cog(cog)
            for cog_command in cog_object.walk_commands():
                if isinstance(cog_command, discord.SlashCommandGroup):
                    continue
                cog_commands.append(cog_command)

                for command in cog_commands:
                    if command.qualified_name == qualified_name:
                        string = f"</{command.qualified_name}:{command.qualified_id}>"
                        return string

        return "/"+qualified_name

bot = Bot(intents=discord.Intents.all())
bot.run()