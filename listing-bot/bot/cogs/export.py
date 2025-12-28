import discord
from discord.ext import commands
from discord import SlashCommandGroup, option

from bot.util.constants import is_authorized_to_use_bot
from bot.util.list import list_account, list_profile, list_alt
from bot.bot import Bot
from bot.util.number import get_available_number

def convert_str_bool(value: str) -> bool:
    return value.lower() == "true"

class Export(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    export = SlashCommandGroup("export", description="Commands related to exporting account data")
    _import = SlashCommandGroup("import", description="Commands related to importing account data")

    @export.command(name="account", description="Export your account data")
    @is_authorized_to_use_bot()
    async def export_account(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        accounts = await self.bot.db.fetchall("SELECT username, profile, price, payment_methods, additional_information, show_username FROM accounts WHERE listed_by = ?", ctx.author.id)
        if not accounts:
            embed = discord.Embed(
                title="No Accounts Found",
                description="You have no accounts to export.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        account_data = ""
        for username, profile, price, payment_methods, additional_information, show_username in accounts:
            account_data += f"{username},{profile},{price},{payment_methods},{additional_information},{show_username};"

        account_data = account_data.rstrip(";")
        embed = discord.Embed(
            title="Account Data Exported",
            description=f"```{account_data}```",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @export.command(name="profile", description="Export your profile data")
    @is_authorized_to_use_bot()
    async def export_profile(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        profiles = await self.bot.db.fetchall("SELECT username, profile, price, payment_methods, additional_information, show_username FROM profiles WHERE listed_by = ?", ctx.author.id)
        if not profiles:
            embed = discord.Embed(
                title="No Profiles Found",
                description="You have no profiles to export.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        profile_data = ""
        for username, profile, price, payment_methods, additional_information, show_username in profiles:
            profile_data += f"{username},{profile},{price},{payment_methods},{additional_information},{show_username};"

        profile_data = profile_data.rstrip(";")

        embed = discord.Embed(
            title="Profile Data Exported",
            description=f"```{profile_data}```",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

        for username, profile, price, payment_methods in profiles:
            profile_data += f"{username}:{profile}:{price}:{payment_methods};"

        embed = discord.Embed(
            title="Profile Data Exported",
            description=f"```{profile_data}```",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @export.command(name="alt", description="Export your alt data")
    @is_authorized_to_use_bot()
    async def export_alt(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        alts = await self.bot.db.fetchall("SELECT username, profile, price, payment_methods, additional_information, show_username, farming, mining FROM alts WHERE listed_by = ?", ctx.author.id)
        if not alts:
            embed = discord.Embed(
                title="No Alts Found",
                description="You have no alts to export.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        alt_data = ""
        for username, profile, price, payment_methods, additional_information, show_username, farming, mining in alts:
            alt_data += f"{username},{profile},{price},{payment_methods},{additional_information},{show_username},{farming},{mining};"

        embed = discord.Embed(
            title="Alt Data Exported",
            description=f"```{alt_data}```",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @_import.command(name="accounts", description="Import account data")
    @is_authorized_to_use_bot()
    @option(
        "account_data",
        description="The account data to import (from export command)",
        type=str,
        required=True
    )
    async def import_account(self, ctx: discord.ApplicationContext, account_data: str):
        await ctx.defer(ephemeral=True)

        accounts = account_data.split(";")
        for account in accounts:
            if not account:
                continue

            username, profile, price, payment_methods, additional_information, show_username = account.split(",")
            try:
                embed = await list_account(
                    self.bot, username, int(price), payment_methods, 
                    False, additional_information, convert_str_bool(show_username), 
                    profile, await get_available_number(self.bot, "accounts"), ctx,
                    ctx.author.id
                )
            except Exception as e:
                embed = discord.Embed(
                    title="Import Error",
                    description=f"Failed to import account `{username}`: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
            finally:
                if embed:
                    await ctx.respond(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="Account Data Imported",
            description="Your account data has been imported successfully.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @_import.command(name="profiles", description="Import profile data")
    @is_authorized_to_use_bot()
    @option(
        "profile_data",
        description="The profile data to import (from export command)",
        type=str,
        required=True
    )
    async def import_profile(self, ctx: discord.ApplicationContext, profile_data: str):
        await ctx.defer(ephemeral=True)

        profiles = profile_data.split(";")
        for profile in profiles:
            if not profile:
                continue

            username, profile, price, payment_methods, additional_information, show_username = profile.split(",")
            try:
                embed = await list_profile(
                    self.bot, username, int(price), payment_methods, 
                    False, additional_information, convert_str_bool(show_username), 
                    profile, await get_available_number(self.bot, "profiles"), ctx.author.id
                )
            except Exception as e:
                embed = discord.Embed(
                    title="Import Error",
                    description=f"Failed to import profile `{username}`: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
            finally:
                if embed:
                    await ctx.respond(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="Profile Data Imported",
            description="Your profile data has been imported successfully.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @_import.command(name="alts", description="Import alt data")
    @is_authorized_to_use_bot()
    @option(
        "alt_data",
        description="The alt data to import (from export command)",
        type=str,
        required=True
    )
    async def import_alt(self, ctx: discord.ApplicationContext, alt_data: str):
        await ctx.defer(ephemeral=True)

        alts = alt_data.split(";")
        for alt in alts:
            if not alt:
                continue

            username, profile, price, payment_methods, additional_information, show_username, farming, mining = alt.split(",")
            try:
                embed = await list_alt(
                    self.bot, username, int(price), payment_methods, 
                    convert_str_bool(farming), convert_str_bool(mining),
                    False, additional_information, convert_str_bool(show_username), 
                    profile, await get_available_number(self.bot, "alts"), ctx.author.id
                )
            except Exception as e:
                embed = discord.Embed(
                    title="Import Error",
                    description=f"Failed to import alt `{username}`: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
            finally:
                if embed:
                    await ctx.respond(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="Alt Data Imported",
            description="Your alt data has been imported successfully.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(Export(bot))