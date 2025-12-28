import discord
from discord.ext import commands
from discord import SlashCommandGroup, option

from bot.util.constants import is_authorized_to_use_bot

from bot.bot import Bot


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    tags = SlashCommandGroup("tags", description="Commands related to automatic responses")

    @tags.command(
        name="create",
        description="Create a new tag"
    )
    @option(
        "name",
        "The name of the tag",
        type=str,
        required=True
    )
    @option(
        "content",
        "The content of the tag",
        type=str,
        required=True
    )
    @is_authorized_to_use_bot()
    async def tags_create(self, ctx: discord.ApplicationContext, name: str, content: str):
        await ctx.defer(ephemeral=True)
        await self.bot.db.execute("INSERT INTO tags (name, content, created_by) VALUES (?, ?, ?)", name, content, ctx.author.id)

        embed = discord.Embed(
            title="Tag Created",
            description=f"Tag `{name}` created.",
            color=discord.Color.green()
        )

        await ctx.respond(embed=embed)

    @tags.command(
        name="delete",
        description="Delete a tag"
    )
    @option(
        "name",
        "The name of the tag",
        type=str,
        required=True
    )
    @is_authorized_to_use_bot()
    async def tags_delete(self, ctx: discord.ApplicationContext, name: str):
        await ctx.defer(ephemeral=True)
        await self.bot.db.execute("DELETE FROM tags WHERE name = ?", name)

        embed = discord.Embed(
            title="Tag Deleted",
            description=f"Tag `{name}` deleted if it existed before.",
            color=discord.Color.green()
        )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Tags(bot))