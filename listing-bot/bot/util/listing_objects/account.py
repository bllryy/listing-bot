import discord
from discord.ui import View, button
from bot.bot import Bot
import asyncio

from bot.util.helper.account import AccountObject, create_embed_account_listing
from .ticket import OpenedTicket
from bot.util.ticket import get_default_overwrites
from bot.util.listing_objects.dropdown import Dropdown

from bot.util.fetch import fetch_profile_data
from bot.util.convert_payment_methods import convert_payment_methods


class Account(View):
    def __init__(self, bot:Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot
        self.children.insert(-1, Dropdown(bot, "accounts"))

    @button(
        label="Toggle Ping",
        custom_id="toggle:ping",
        style=discord.ButtonStyle.grey,
        emoji="🔔",
        row=2
    )
    async def toggle_ping(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        ping_role = await self.bot.db.get_config("ping_role")
        if not ping_role:
            return await interaction.respond("Account Notification role not found. Aborting..", ephemeral=True)
        
        role = interaction.guild.get_role(ping_role)
        if not role:
            return await interaction.respond("Account Notification role not found. Aborting..", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.respond("You will no longer be pinged about new accounts being listed.", ephemeral=True)

        else:
            await interaction.user.add_roles(role)
            await interaction.respond("You will now be pinged about new accounts being listed.", ephemeral=True)

    @button(
        label="Listing Owner",
        custom_id="accounts:owner",
        style=discord.ButtonStyle.grey,
        emoji="👤",
        row=2,
    )
    async def account_owner(self, button: discord.ui.Button, interaction: discord.Interaction):

        account = await self.bot.db.fetchone("SELECT * FROM accounts WHERE channel_id = ?", interaction.channel.id)
        if not account:
            await interaction.respond("This account was not found in the database, deleting in `5` Seconds.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete()
            return
        
        account = AccountObject(*account)
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="Account Owner",
            description=f"This Account is owned by <@{account.listed_by}>",
            color=discord.Color.blue()
        )
        await interaction.respond(embed=embed, ephemeral=True)


    @button(
        label="Extra Information",
        custom_id="accounts:information",
        style=discord.ButtonStyle.grey,
        row=2,
        emoji="📊"
    )
    async def extra_information(self, button: discord.ui.Button, interaction: discord.Interaction):

        account = await self.bot.db.fetchone("SELECT * FROM accounts WHERE channel_id = ?", interaction.channel.id)
        if not account:
            await interaction.respond("This account was not found in the database, deleting in `5` Seconds.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete()
            return
        
        account = AccountObject(*account)
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="Account Information",
            description=account.additional_info,
            color=discord.Color.blue()
        )
        await interaction.respond(embed=embed, ephemeral=True)

    @button(
        label="Buy",
        custom_id="accounts:buy",
        style=discord.ButtonStyle.blurple,
        emoji="💸",
        row=3
    )
    async def buy_account(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(BuyAccountModal(self.bot, title="Buy an Account", channel=interaction.channel.id))

    @button(
        label="Update Stats",
        custom_id="accounts:update",
        style=discord.ButtonStyle.blurple,
        row=3,
        emoji="🔄"
    )
    async def update_info(self, button: discord.ui.Button, interaction: discord.Interaction):
        account = await self.bot.db.fetchone("SELECT * FROM accounts WHERE channel_id = ?", interaction.channel.id)
        if not account:
            await interaction.respond("This account was not found in the database, deleting in `5` Seconds.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete()
            return
        
        role_id = await self.bot.db.get_config("seller_role")
        if not role_id:
            return
        role = interaction.guild.get_role(role_id)
        if not role:
            return
        if role not in interaction.user.roles and not interaction.user.id in self.bot.owner_ids:
            return await interaction.respond("You are not authorized to use this button.", ephemeral=True)
        
        account = AccountObject(*account)
        await interaction.response.defer(ephemeral=True)

        profile_data, profile = await fetch_profile_data(self.bot.session, account.uuid, self.bot, account.profile)
        embed = create_embed_account_listing(profile_data, profile, account.uuid, account.username, account.price, account.additional_info, convert_payment_methods(self.bot, account.payment_methods), interaction, self.bot, f"<@{account.listed_by}>")
        await interaction.message.edit(embed=embed)

    @button(
        label="Unlist",
        custom_id="unlist:item",
        style=discord.ButtonStyle.red,
        row=3
    )
    async def unlist_account(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        role_id = await self.bot.db.get_config("seller_role")
        if not role_id:
            return
        role = interaction.guild.get_role(role_id)
        if not role:
            return
        if role not in interaction.user.roles and not interaction.user.id in self.bot.owner_ids:
            return await interaction.respond("You are not authorized to unlist accounts.", ephemeral=True)
        await interaction.channel.delete()

class BuyAccountModal(discord.ui.Modal):
    def __init__(self, bot: Bot, channel: int, *args, **kwargs):
        super().__init__(discord.ui.InputText(label="Payment Method", placeholder="Crypto"), *args, **kwargs)
        self.bot = bot
        self.channel_id = channel

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        response_embed = discord.Embed(
            color=discord.Color.red()
        )

        open_tickets_user = await self.bot.db.fetchone("SELECT * FROM tickets WHERE opened_by = ?", interaction.user.id)
        if open_tickets_user:
            response_embed.title = "An Error Occurred"
            response_embed.description = "You already have an open ticket, please close that ticket before opening a new one."
            await interaction.respond(embed=response_embed, ephemeral=True)
            return

        payment_methods = self.children[0].value

        account_info = await self.bot.db.fetchone("SELECT * FROM accounts WHERE channel_id = ?", self.channel_id)
        if not account_info:
            await interaction.response.send_message("This account was not found in the database, deleting in `5` Seconds.", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete()
            return
        
        category = await self.bot.db.get_config("buy_accounts_category")
        category: discord.CategoryChannel = self.bot.get_channel(category)
        if not category:
            response_embed.title = "An Error Occurred"
            response_embed.description = "An error occurred while fetching the category."
            await interaction.respond(embed=response_embed, ephemeral=True)
            return
        
        account = AccountObject(*account_info)
        overwrites, role, tos_agreed = await get_default_overwrites(self.bot, interaction.guild.id, interaction.user.id, ticket_type=f"buy-account")
        
        channel = await category.create_text_channel(name=f"listing-{account.number}⭐-buy", overwrites=overwrites)
        response_embed.color = discord.Color.blue()

        await interaction.user.add_roles(role)
        response_embed.title = "Ticket Created"
        response_embed.description = f"Your ticket has been created, go to {channel.mention}!"

        await interaction.respond(embed=response_embed, ephemeral=True)

        embed = discord.Embed(
            title="Account Purchase",
            description=f"""
### <#{account.channel_id}>
This ticket will be handled by <@{account.listed_by}>.
Once the payment has been confirmed, the seller will provide you with the account details.""",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Payment Method",
            value=payment_methods
        )
        embed.add_field(
            name="Price",
            value=f"{account.price}$"
        )
        embed.add_field(
            name="Account Owner",
            value=f"<@{account.listed_by}>"
        )
        initial_message = await channel.send(
            embed=embed, 
            content=f"<@{account.listed_by}>, {interaction.user.mention} is interested in purchasing your account.", 
            view=OpenedTicket(self.bot)
        )
        await initial_message.pin()
        await self.bot.db.execute("INSERT INTO tickets (opened_by, channel_id, initial_message_id, role_id) VALUES (?, ?, ?, ?)", interaction.user.id, channel.id, initial_message.id, role.id)
        if account.show_username:
            await channel.send(f'https://sky.shiiyu.moe/stats/{account.uuid}/{account.profile}')

        if tos_agreed is False:
            await channel.send(
                embed=discord.Embed(
                    title="Terms of Service",
                    description=f"We require you to agree to our Terms of Service before you can buy something.\nRefer to {self.bot.get_command_link('terms view')}.",
                    color=discord.Color.red()
                ))
