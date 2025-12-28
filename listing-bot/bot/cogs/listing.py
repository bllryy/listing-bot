import discord
from discord.ext import commands
from discord import SlashCommandGroup, option

from bot.bot import Bot
from bot.util.constants import is_authorized_to_use_bot
from bot.util.fetch import fetch_profile_data
from bot.util.convert_payment_methods import convert_payment_methods

from bot.util.helper.account import AccountObject, create_embed_account_listing
from bot.util.helper.profile import ProfileObject, create_embed_profile_listing
from bot.util.helper.macro_alt import AltObject, create_embed_alt_listing

from bot.util.paginator import Paginator
import ujson

class Listings(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    listings = SlashCommandGroup("listings", description="Commands for managing listings")
    view = listings.create_subgroup("view", "Views listings")
    update = listings.create_subgroup("update", "Updates listings")
    unlist = listings.create_subgroup("unlist", "Unlists listings")
    
    @view.command(
        name="listing",
        description="View a listing",
    )
    @option(
        name="channel",
        description="The channel of the listing",
        type=discord.TextChannel,
    )
    @is_authorized_to_use_bot()
    async def listings_view_listing(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)

        tables = {
            "accounts": AccountObject,
            "profiles": ProfileObject,
            "alts": AltObject
        }

        for table_name, object in tables.items():
            data = await self.bot.db.fetchone(f"SELECT * FROM {table_name} WHERE channel_id = ?", channel.id)
            if data:
                account = object(*data)
                embed = account.to_embed(self.bot)

                await ctx.respond(embed=embed, ephemeral=True)

    @view.command(
        name="from",
        description="View listings by a user",
    )
    @option(
        name="user",
        description="The user who listed the listing",
        type=discord.User,
        required=False
    )
    @is_authorized_to_use_bot()
    async def listings_view_from(self, ctx: discord.ApplicationContext, user: discord.User=None):
        await ctx.defer(ephemeral=True)

        if not user:
            user = ctx.author

        tables = {
            "accounts": AccountObject,
            "profiles": ProfileObject,
            "alts": AltObject
        }

        embeds = []

        for table_name, object in tables.items():
            data = await self.bot.db.fetchall(f"SELECT * FROM {table_name} WHERE listed_by = ?", user.id)
            for row in data:
                account = object(*row)
                embed = account.to_embed(self.bot)
                embeds.append(embed)

        if len(embeds) == 0:
            return await ctx.respond("No listings found for this user", ephemeral=True)

        paginator = Paginator(embeds)
        await ctx.respond(embed=embeds[0], view=paginator, ephemeral=True)

    @update.command(
        name="price",
        description="Update the price of a listing",
    )
    @option(
        name="channel",
        description="The channel of the listing",
        type=discord.TextChannel,
    )
    @option(
        name="price",
        description="The new price of the listing (this supports e.g. -10%)",
        type=str,
    )
    @is_authorized_to_use_bot()
    async def listings_update_price(self, ctx: discord.ApplicationContext, channel: discord.TextChannel, price: str):
        await ctx.defer(ephemeral=True)

        tables = {
            "accounts": AccountObject,
            "profiles": ProfileObject,
            "alts": AltObject
        }

        for table_name, object in tables.items():
            data = await self.bot.db.fetchone(f"SELECT * FROM {table_name} WHERE channel_id = ?", channel.id)
            if data:
                account = object(*data)
                used_table = table_name
                break
        else:
            return await ctx.respond("No listing found for this channel", ephemeral=True)

        original_price = account.price

        if price.endswith('%'):
            try:
                percentage = float(price.rstrip('%'))
                new_price = int(original_price * (1 + percentage/100))
            except ValueError:
                return await ctx.respond("Invalid percentage format", ephemeral=True)
        else:
            try:
                new_price = int(float(price))
            except ValueError:
                return await ctx.respond("Invalid price format", ephemeral=True)

        await self.bot.db.execute(
            f"UPDATE {table_name} SET price = ? WHERE channel_id = ?",
            new_price, channel.id
        )

        profile_data, profile = await fetch_profile_data(self.bot.session, account.uuid, self.bot, account.profile)

        if used_table == "accounts":
            embeds = [create_embed_account_listing(profile_data, profile, account.uuid, account.username, new_price, account.additional_info, convert_payment_methods(self.bot, account.payment_methods), ctx, self.bot, f"<@{account.listed_by}>")]
            channel_name = f"⭐｜💲{new_price}｜listing-{account.number}"

        elif used_table == "profiles":
            embeds = [create_embed_profile_listing(profile_data, profile, account.price, convert_payment_methods(self.bot, account.payment_methods), self.bot, f"<@{account.listed_by}>")]
            channel_name = f"⭐｜💲{new_price}｜island-{account.number}"

        else:
            embeds = create_embed_alt_listing(profile_data, profile, account.price, convert_payment_methods(self.bot, account.payment_methods), self.bot, f"<@{account.listed_by}>", account.mining, account.farming)
            channel_name = f"⭐｜💲{new_price}｜alt-{account.number}"


        channel = self.bot.get_channel(account.channel_id)
        await channel.edit(name=channel_name)
        
        message = await channel.fetch_message(account.message_id)
        await message.edit(embeds=embeds)

        embed = discord.Embed(
            title="Price Updated",
            description=f"Price updated from `${original_price:,}` to `${new_price:,}`",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @unlist.command(
        name="listing",
        description="Unlist a listing",
    )
    @option(
        name="channel",
        description="The channel of the listing",
        type=discord.TextChannel,
    )
    @is_authorized_to_use_bot()
    async def listings_unlist_listing(self, ctx: discord.ApplicationContext, channel: discord.TextChannel, log: discord.TextChannel=None):
        await ctx.defer(ephemeral=True)

        tables = {
            "accounts": AccountObject,
            "profiles": ProfileObject,
            "alts": AltObject
        }

        for table_name, object in tables.items():
            data = await self.bot.db.fetchone(f"SELECT * FROM {table_name} WHERE channel_id = ?", channel.id)
            if data:
                account = object(*data)
                used_table = table_name
                break
        else:
            return await ctx.respond("No listing found for this channel", ephemeral=True)

        await self.bot.db.execute(
            f"DELETE FROM {table_name} WHERE channel_id = ?",
            channel.id
        )

        channel = self.bot.get_channel(account.channel_id)
        
        if log:
            message = await channel.fetch_message(account.message_id)
            await log.send(embed=message.embeds[0])
        
        await channel.delete()

        embed = discord.Embed(
            title="Listing Unlisted",
            description=f"Listing unlisted",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @unlist.command(
        name="all",
        description="Unlist all listings",
    )
    @is_authorized_to_use_bot(strict=True)
    async def listings_unlist_all(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        tables = {
            "accounts": AccountObject,
            "profiles": ProfileObject,
            "alts": AltObject
        }

        for table_name, object in tables.items():
            data = await self.bot.db.fetchall(f"SELECT * FROM {table_name}")
            for row in data:
                account = object(*row)
                channel = self.bot.get_channel(account.channel_id)
                await channel.delete()

            await self.bot.db.execute(f"DELETE FROM {table_name}")

        embed = discord.Embed(
            title="All Listings Unlisted",
            description=f"All listings unlisted",
            color=discord.Color.green()
        )

        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot: Bot):
    bot.add_cog(Listings(bot))