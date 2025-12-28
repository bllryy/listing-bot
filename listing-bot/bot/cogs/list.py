import discord
from discord import SlashCommandGroup, option
from discord.ext import commands
from bot.util.constants import is_authorized_to_use_bot
from bot.bot import Bot
from bot.util.list import list_account, list_profile, list_alt
from bot.util.selector import profile_selector
from bot.util.fetch import fetch_profile_data
from bot.util.get_payment_methods import get_payment_methods
from bot.util.convert_payment_methods import convert_payment_methods

from bot.util.helper.account import AccountObject, create_embed_account_listing
from bot.util.helper.profile import ProfileObject, create_embed_profile_listing
from bot.util.helper.macro_alt import AltObject, create_embed_alt_listing

class List(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    list = SlashCommandGroup(name="list", description="Listing related commands.")
    update = SlashCommandGroup(name="update", description="Updating related commands.")
    restore = SlashCommandGroup(name="restore", description="Restoration related commands.")

    @list.command(name="account", description="List an account")
    @option(name="username", description="Name of the Account", type=str, required=True)
    @option(name="price", description="Price of the Account (IN USD)", type=int, required=True)
    @option(name="ping", description="Ping?", type=bool, required=False)
    @option(name="additional_information", description="Additional Account Information", type=str, required=False)
    @option(name="show_ign", description="Show IGN on ticket creation?", type=bool, required=False)
    @option(name="profile", description="Profile you want to list.", type=str, required=False, autocomplete=profile_selector)
    @option(name="number", description="Account Number", type=int, required=False)
    @is_authorized_to_use_bot()
    async def accounts_list(
        self, ctx: discord.ApplicationContext,
        username: str, price: int, ping: bool = False,
        additional_information: str = "No Information Provided",
        show_ign: bool = True, profile: str = None,
        number: int = None
    ):
        await ctx.defer(ephemeral=True)
        payment_methods = await get_payment_methods(self.bot, ctx.author.id)
        if not payment_methods:
            embed = discord.Embed(
                title="No Payment Methods Found",
                description=f"You haven't set your payment methods yet. Use {self.bot.get_command_link('methods set')} to do so.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        embed = await list_account(self.bot, username, price, payment_methods, ping, additional_information, show_ign, profile, number, ctx, ctx.author.id)
        await ctx.respond(embed=embed)

    @update.command(name="accounts", description="Update an account")
    @option(name="number", description="Account Number", type=int, required=False)
    @is_authorized_to_use_bot()
    async def accounts_update(self, ctx: discord.ApplicationContext, number: int=None):
        await ctx.defer(ephemeral=True)

        query = "SELECT * FROM accounts" + (" WHERE number=?" if number else "")
        params = (number,) if number else ()
        accounts = await self.bot.db.fetchall(query, *params)

        if not accounts:
            response_embed = discord.Embed(
                title="No Accounts Found",
                description="No accounts found with the specified criteria.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=response_embed)


        response_embed = discord.Embed(
            title="Accounts Found",
            description=f"Found {len(accounts)} account(s) matching the given criteria.",
            color=discord.Color.green()
        )
        for i, account in enumerate(accounts):
            if i < 24:
                account = AccountObject(*account)
                response_embed.add_field(name=account.username, value=f"🔴")
            else:
                response_embed.add_field(name=f"And {len(accounts)-24} more", value="🔴", inline=False)
                break

        response: discord.WebhookMessage = await ctx.respond(embed=response_embed)

        for i, account in enumerate(accounts):
            if i < 24:
                account = AccountObject(*account)
                profile_data, profile = await fetch_profile_data(self.bot.session, account.uuid, self.bot, account.profile)
                embed = create_embed_account_listing(profile_data, profile, account.uuid, account.username, account.price, account.additional_info, convert_payment_methods(self.bot, account.payment_methods), ctx, self.bot, f"<@{account.listed_by}>")
                response_embed.fields[i].value = f"🟢"

                channel = self.bot.get_channel(account.channel_id)
                if not channel:
                    continue
                message = await channel.fetch_message(account.message_id)
                if not message:
                    continue

                await message.edit(embed=embed)
                await response.edit(embed=response_embed)

        response_embed.fields[-1].value = "🟢"
        await response.edit(embed=response_embed)
    
    @restore.command(name="accounts", description="Restore all accounts")
    @is_authorized_to_use_bot()
    async def accounts_restore(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        accounts = await self.bot.db.fetchall("SELECT * FROM accounts WHERE channel_id IS NOT NULL")

        if not accounts:
            response_embed = discord.Embed(
                title="No Accounts Found",
                description="No accounts found with the specified criteria.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=response_embed)

        response_embed = discord.Embed(
            title="Accounts Found",
            description=f"Found {len(accounts)} account(s) matching the given criteria.",
            color=discord.Color.green()
        )
        for i, account in enumerate(accounts):
            if i < 24:
                account = AccountObject(*account)
                response_embed.add_field(name=account.username, value=f"🔴")
            else:
                response_embed.add_field(name=f"And {len(accounts)-24} more", value="🔴", inline=False)
                break

        response: discord.WebhookMessage = await ctx.respond(embed=response_embed)

        for i, account in enumerate(accounts):
            account = AccountObject(*account)

            channel = self.bot.get_channel(account.channel_id)
            if channel:
                await channel.delete()
            
            await self.bot.db.execute("DELETE FROM accounts WHERE number=?", account.number)
            await list_account(self.bot, account.username, account.price, account.payment_methods, False, account.additional_info, account.show_username, account.profile, account.number, ctx, account.listed_by)
            
            if i < 24:
                response_embed.fields[i].value = f"🟢"
                await response.edit(embed=response_embed)

        response_embed.fields[-1].value = "🟢"
        await response.edit(embed=response_embed)

    @list.command(name="profile", description="List a profile")
    @option(name="username", description="Name of the Account", type=str, required=True)
    @option(name="price", description="Price of the Account (IN USD)", type=int, required=True)
    @option(name="ping", description="Ping?", type=bool, required=False)
    @option(name="additional_information", description="Additional Account Information", type=str, required=False)
    @option(name="show_ign", description="Show IGN on ticket creation?", type=bool, required=False)
    @option(name="profile", description="Profile you want to list.", type=str, required=False, autocomplete=profile_selector)
    @option(name="number", description="Account Number", type=int, required=False)
    @is_authorized_to_use_bot()
    async def profiles_list(
        self, ctx: discord.ApplicationContext,
        username: str, price: int, ping: bool = False,
        additional_information: str = "No Information Provided",
        show_ign: bool = True, profile: str = None,
        number: int = None
    ):
        await ctx.defer(ephemeral=True)
        payment_methods = await get_payment_methods(self.bot, ctx.author.id)
        if not payment_methods:
            embed = discord.Embed(
                title="No Payment Methods Found",
                description=f"You haven't set your payment methods yet. Use {self.bot.get_command_link('methods set')} to do so.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        embed = await list_profile(self.bot, username, price, payment_methods, ping, additional_information, show_ign, profile, number, ctx.author.id)
        await ctx.respond(embed=embed)

    @update.command(name="profiles", description="Update a profile")
    @option(name="number", description="Account Number", type=int, required=False)
    @is_authorized_to_use_bot()
    async def profiles_update(self, ctx: discord.ApplicationContext, number: int=None):
        await ctx.defer(ephemeral=True)

        query = "SELECT * FROM profiles" + (" WHERE number=?" if number else "")
        params = (number,) if number else ()
        profiles = await self.bot.db.fetchall(query, *params)

        if not profiles:
            response_embed = discord.Embed(
                title="No Profiles Found",
                description="No profiles found with the specified criteria.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=response_embed)

        response_embed = discord.Embed(
            title="Profiles Found",
            description=f"Found {len(profiles)} profile(s) matching the given criteria.",
            color=discord.Color.green()
        )
        for i, profile in enumerate(profiles):
            if i < 24:
                profile = ProfileObject(*profile)
                response_embed.add_field(name=profile.username, value=f"🔴")
            else:
                response_embed.add_field(name=f"And {len(profiles)-24} more", value="🔴", inline=False)
                break

        response: discord.WebhookMessage = await ctx.respond(embed=response_embed)

        for i, profile in enumerate(profiles):
            if i < 24:
                account = ProfileObject(*profile)
                profile_data, profile = await fetch_profile_data(self.bot.session, account.uuid, self.bot, account.profile)
                embed = create_embed_profile_listing(profile_data, profile, account.price, convert_payment_methods(self.bot, account.payment_methods), self.bot, f"<@{account.listed_by}>")
                response_embed.fields[i].value = f"🟢"

                channel = self.bot.get_channel(account.channel_id)
                if not channel:
                    continue
                message = await channel.fetch_message(account.message_id)
                if not message:
                    continue

                await message.edit(embed=embed)
                await response.edit(embed=response_embed)

        response_embed.fields[-1].value = "🟢"
        await response.edit(embed=response_embed)

    @restore.command(name="profiles", description="Restore all profiles")
    @is_authorized_to_use_bot()
    async def profiles_restore(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        profiles = await self.bot.db.fetchall("SELECT * FROM profiles WHERE channel_id IS NOT NULL")

        if not profiles:
            response_embed = discord.Embed(
                title="No Profiles Found",
                description="No profiles found with the specified criteria.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=response_embed)

        response_embed = discord.Embed(
            title="Profiles Found",
            description=f"Found {len(profiles)} profile(s) matching the given criteria.",
            color=discord.Color.green()
        )
        for i, profile in enumerate(profiles):
            if i < 24:
                profile = ProfileObject(*profile)
                response_embed.add_field(name=profile.username, value=f"🔴")
            else:
                response_embed.add_field(name=f"And {len(profiles)-24} more", value="🔴", inline=False)
                break

        response: discord.WebhookMessage = await ctx.respond(embed=response_embed)

        for i, profile in enumerate(profiles):
            profile = ProfileObject(*profile)

            channel = self.bot.get_channel(profile.channel_id)
            if channel:
                await channel.delete()
            
            await self.bot.db.execute("DELETE FROM profiles WHERE number=?", profile.number)
            await list_profile(self.bot, profile.username, profile.price, profile.payment_methods, False, profile.additional_info, profile.show_username, profile.profile, profile.number, profile.listed_by)

            if i < 24:
                response_embed.fields[i].value = f"🟢"
                await response.edit(embed=response_embed)

        response_embed.fields[-1].value = "🟢"
        await response.edit(embed=response_embed)

    @list.command(name="alt", description="List an alt")
    @option(name="username", description="Name of the Account", type=str, required=True)
    @option(name="price", description="Price of the Account (IN USD)", type=int, required=True)
    @option(name="farming", description="Is this a farming alt?", type=bool, required=True)
    @option(name="mining", description="Is this a mining alt?", type=bool, required=True)
    @option(name="ping", description="Ping?", type=bool, required=False)
    @option(name="additional_information", description="Additional Account Information", type=str, required=False)
    @option(name="show_ign", description="Show IGN on ticket creation?", type=bool, required=False)
    @option(name="profile", description="Profile you want to list.", type=str, required=False, autocomplete=profile_selector)
    @option(name="number", description="Account Number", type=int, required=False)
    @is_authorized_to_use_bot()
    async def alts_list(
        self, ctx: discord.ApplicationContext,
        username: str, price: int, farming: bool,
        mining: bool, ping: bool = False,
        additional_information: str = "No Information Provided",
        show_ign: bool = True, profile: str = None,
        number: int = None
    ):
        await ctx.defer(ephemeral=True)
        payment_methods = await get_payment_methods(self.bot, ctx.author.id)
        if not payment_methods:
            embed = discord.Embed(
                title="No Payment Methods Found",
                description=f"You haven't set your payment methods yet. Use {self.bot.get_command_link('methods set')} to do so.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        embed = await list_alt(self.bot, username, price, payment_methods, farming, mining, ping, additional_information, show_ign, profile, number, ctx.author.id)
        await ctx.respond(embed=embed)

    @update.command(name="alts", description="Update an Alt Account")
    @option(name="number", description="Account Number", type=int, required=False)
    @is_authorized_to_use_bot()
    async def alts_update(self, ctx: discord.ApplicationContext, number: int=None):
        await ctx.defer(ephemeral=True)

        query = "SELECT * FROM alts" + (" WHERE number=?" if number else "")
        params = (number,) if number else ()
        alts = await self.bot.db.fetchall(query, *params)

        if not alts:
            response_embed = discord.Embed(
                title="No Alt Accounts Found",
                description="No Alt Accounts found with the specified criteria.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=response_embed)

        response_embed = discord.Embed(
            title="Alt Accounts Found",
            description=f"Found {len(alts)} Alt Account(s) matching the given criteria.",
            color=discord.Color.green()
        )
        for i, profile in enumerate(alts):
            if i < 24:
                profile = AltObject(*profile)
                response_embed.add_field(name=profile.username, value=f"🔴")
            else:
                response_embed.add_field(name=f"And {len(alts)-24} more", value="🔴", inline=False)
                break

        response: discord.WebhookMessage = await ctx.respond(embed=response_embed)

        for i, profile in enumerate(alts):
            if i < 24:
                account = AltObject(*profile)
                profile_data, profile = await fetch_profile_data(self.bot.session, account.uuid, self.bot, account.profile)
                embeds = create_embed_alt_listing(profile_data, profile, account.price, convert_payment_methods(self.bot, account.payment_methods), self.bot, f"<@{account.listed_by}>", account.mining, account.farming)
                response_embed.fields[i].value = f"🟢"

                channel = self.bot.get_channel(account.channel_id)
                if not channel:
                    continue
                message = await channel.fetch_message(account.message_id)
                if not message:
                    continue

                await message.edit(embeds=embeds)
                await response.edit(embed=response_embed)

        response_embed.fields[-1].value = "🟢"
        await response.edit(embed=response_embed)

    @restore.command(name="alts", description="Restore all alt accounts")
    @is_authorized_to_use_bot()
    async def alts_restore(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        alts = await self.bot.db.fetchall("SELECT * FROM alts WHERE channel_id IS NOT NULL")

        if not alts:
            response_embed = discord.Embed(
                title="No Alt Accounts Found",
                description="No Alt Accounts found with the specified criteria.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=response_embed)
        
        response_embed = discord.Embed(
            title="Alt Accounts Found",
            description=f"Found {len(alts)} Alt Account(s) matching the given criteria.",
            color=discord.Color.green()
        )

        for i, profile in enumerate(alts):
            if i < 24:
                profile = AltObject(*profile)
                response_embed.add_field(name=profile.username, value=f"🔴")
            else:
                response_embed.add_field(name=f"And {len(alts)-24} more", value="🔴", inline=False)
                break

        response: discord.WebhookMessage = await ctx.respond(embed=response_embed)

        for i, profile in enumerate(alts):
            profile = AltObject(*profile)

            channel = self.bot.get_channel(profile.channel_id)
            if channel:
                await channel.delete()
            
            await self.bot.db.execute("DELETE FROM alts WHERE number=?", profile.number)
            await list_alt(self.bot, profile.username, profile.price, profile.payment_methods, profile.farming, profile.mining, False, profile.additional_info, profile.show_username, profile.profile, profile.number, profile.listed_by)

            if i < 24:
                response_embed.fields[i].value = f"🟢"
                await response.edit(embed=response_embed)

        response_embed.fields[-1].value = "🟢"
        await response.edit(embed=response_embed)

def setup(bot):
    bot.add_cog(List(bot))