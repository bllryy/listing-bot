import discord
from discord.ext import commands
from discord import slash_command, option
from bot.util.paginator import Paginator
from bot.util.constants import is_authorized_to_use_bot
import ai

from bot.bot import Bot

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @slash_command(
        name='help',
        description='Displays a help message.'
    )
    async def help(self, ctx: discord.ApplicationContext):
        pages = []
        initial_page = discord.Embed(color=discord.Color.blurple(), description=f"Use the Buttons Below to navigate through the modules.\n\n")

        for cog in self.bot.cogs:
            
            cog_commands = []
            cog_object = self.bot.get_cog(cog)
            for cog_command in cog_object.walk_commands():
                if isinstance(cog_command, discord.SlashCommandGroup):
                    continue
                cog_commands.append(cog_command)

            if len(cog_commands) != 0:
                initial_page.description += f"{cog.capitalize()}: (**{len(cog_commands)}** Command{'s' if len(cog_commands) != 1 else ''})\n"

                page_embed = discord.Embed(color=discord.Color.blurple(), title=f"{cog.capitalize()}'{'s' if not cog.endswith('s') else ''} Commands", description="")
                for command in cog_commands:

                    string = f"</{command.qualified_name}:{command.qualified_id}> "
                    for option in command.options:
                        string += f"`[{option.name}]` " if option.required else f"`<{option.name}>` "

                    string += "\n"

                    page_embed.description += string

                pages.append(page_embed)

        pages.insert(0, initial_page)
        paginator = Paginator(embeds=pages)

        await ctx.respond(embed=pages[0], view=paginator, ephemeral=True)

    @slash_command(
        name="find",
        description="Find a feature by describing it."
    )
    @option(
        name="description",
        description="The description of the feature you want to use.",
    )
    @is_authorized_to_use_bot()
    async def find(self, ctx: discord.ApplicationContext, description: str):
        await ctx.defer(ephemeral=True)

        command_lookup = {}
        for cog in self.bot.cogs:
            cog_object = self.bot.get_cog(cog)
            for command in cog_object.walk_commands():
                if isinstance(command, discord.SlashCommandGroup):
                    continue
                command_lookup[command.qualified_name] = (command.description, command)

        if not command_lookup:
            await ctx.respond("No commands found.", ephemeral=True)
            return

        ai_query = await ai.ask_ai(
            self.bot,
            f"Which of these commands would be most suitable for '{description}'?\nAvailable options: {str({k: v[0] for k, v in command_lookup.items()})}.\n"
            'Respond in the following format: [<command_name>], even if none are found.',
            return_json=True
        )

        commands: list[dict[str, str]] = ai_query.parse()

        embed = discord.Embed(
            title="Command Search Results",
            description="The following commands **could** match your search:\n\n",
            color=discord.Color.red()
        ).set_footer(text="Made by noemt | https://noemt.dev", icon_url="https://noemt.dev/assets/icon.webp")

        if not commands:
            embed.description = "No commands found. Try rephrasing your description, looking manually or asking the developer."
        else:
            for command in commands:
                command_link = self.bot.get_command_link(command)
                desc = command_lookup.get(command, ("No description found.", None))[0]
                embed.description += f"{command_link} - `{desc}`\n"

        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Help(bot))
