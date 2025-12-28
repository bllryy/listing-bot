import discord
from discord.ext import commands
from discord import SlashCommandGroup, option

from bot.bot import Bot

limiting_words = {
    "account": "listing",
    "profile": "island",
    "mfa": "ranked",
    "vouches": "reputation",
}

class Limited(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    limited = SlashCommandGroup(
        name="limited",
        description="Commands that help you prevent being limited.",
    )

    @limited.command(
        name="detect",
        description="Detect if your server would be limited. (Restricted to known words)",
    )
    @option(
        name="rename",
        description="Rename channels automatically?",
        default=False,
        type=bool,
        required=False,
    )
    @commands.is_owner()
    async def detect(self, ctx: discord.ApplicationContext, rename: bool = False):
        await ctx.defer(ephemeral=True)

        affected_channels = []
        affected_categories = []
        for channel in ctx.guild.channels:
            if any(word in channel.name.lower() for word in limiting_words):
                if isinstance(channel, discord.CategoryChannel):
                    affected_categories.append(channel)
                else:
                    affected_channels.append(channel)

        if not affected_channels and not affected_categories:
            embed = discord.Embed(
                title="No Limitations Detected",
                description="Your server does not have any channels or categories that would trigger limitations.",
                color=discord.Color.green()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
            title="Limitations Detected",
            description="The following channels and categories may trigger limitations due to their names.",
            color=discord.Color.red()
        )
        if affected_channels:
            embed.add_field(
                name="Affected Channels",
                value="\n".join(channel.mention for channel in affected_channels),
                inline=False
            )
        if affected_categories:
            embed.add_field(
                name="Affected Categories",
                value="\n".join(channel.mention for channel in affected_categories),
                inline=False
            )

        await ctx.respond(embed=embed, ephemeral=True)

        updated_channels = []
        updated_categories = []

        if rename:
            await ctx.respond(
                "Renaming affected channels and categories...",
                ephemeral=True
            )

            for channel in affected_channels:
                new_name = channel.name
                for word, replacement in limiting_words.items():
                    new_name = new_name.replace(word, replacement)
                if new_name != channel.name:
                    await channel.edit(name=new_name)
                    updated_channels.append(channel)

            for category in affected_categories:
                new_name = category.name
                for word, replacement in limiting_words.items():
                    new_name = new_name.replace(word, replacement)
                if new_name != category.name:
                    await category.edit(name=new_name)
                    updated_categories.append(category)

        if updated_channels or updated_categories:
            embed = discord.Embed(
                title="Renaming Completed",
                description="The following channels and categories have been renamed to prevent limitations.",
                color=discord.Color.green()
            )
            if updated_channels:
                embed.add_field(
                    name="Updated Channels",
                    value="\n".join(channel.mention for channel in updated_channels),
                    inline=False
                )
            if updated_categories:
                embed.add_field(
                    name="Updated Categories",
                    value="\n".join(channel.mention for channel in updated_categories),
                    inline=False
                )

            await ctx.respond(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="No Changes Made",
                description="No channels or categories were renamed.",
                color=discord.Color.yellow()
            )
            await ctx.respond(embed=embed, ephemeral=True)

def setup(bot: Bot):
    bot.add_cog(Limited(bot))
