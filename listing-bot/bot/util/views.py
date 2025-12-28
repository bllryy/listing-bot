from bot.util.listing_objects.fairness import FairnessView
from bot.util.listing_objects.ticket import OpenedTicket
from bot.util.listing_objects.account import Account
from bot.util.listing_objects.profile import Profile
from bot.util.listing_objects.alt import Alt
from bot.util.panels.account import AccountSale
from bot.util.panels.profile import ProfileSale
from bot.util.panels.alt import AltSale
from bot.util.panels.coin import CoinSale
from bot.util.panels.mfa import MFASale
from bot.util.panels.middleman import Middleman
from bot.util.ticket import LowballView, get_default_overwrites
from bot.trolls.captcha.view import CaptchaView

import discord
from discord.ui import View, button, Button
from bot.bot import Bot
from auth.auth import Auth
import random
import base64
import ujson

import random
import datetime

class ModalOverwrite(discord.ui.Modal):
    def __init__(self, button_label: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button_label = button_label

async def hylist_lookup(user_id: int) -> discord.Embed:   
    # goodbye the hylist lookup (I might bring back some other feature referencing this function later)
    return None

class AuthorizeView(View):
    def __init__(self, bot: Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

    @button(
        label="Initialize Authorization Process",
        style=discord.ButtonStyle.grey,
        custom_id="auth:panel:init"
    )
    async def authorize(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        data = await self.bot.db.fetchone("SELECT * FROM auth WHERE user_id = ?", interaction.user.id)
        if data:
            bot_id = data[3]
            bot_data = await self.bot.db.fetchone("SELECT * FROM auth_bots WHERE client_id = ?", bot_id)
        else:
            bot_data = await self.bot.db.fetchall("SELECT * FROM auth_bots")
            bot_data = random.choice(bot_data) if bot_data else None

        if bot_data:
            auth = Auth(bot_data[0], self.bot)
            await auth.init()

            url = auth.get_url()
            embed = discord.Embed(
                title="Authorization",
                description=f"Click the button below to authorize the application.\n*You don't need to log in to Discord in your Browser*\n\nAlternatively, if Discord broke *again*, as it always does, you can click [this](https://{await self.bot.get_domain()}/redirect?url={base64.b64encode(url.encode()).decode()}). However, this requires you to log in to your Discord account in your browser.",
                color=discord.Color.green()
            )
            view = View()
            view.add_item(Button(label="Authorize", style=discord.ButtonStyle.link, url=url))
            await interaction.respond(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(
                title="No Authorization Bots Available",
                description="No authorization bots available currently. DM nom for assistance.",
                color=discord.Color.red()
            )
            await interaction.respond(embed=embed, ephemeral=True)

class CustomView(View):
    def __init__(self, bot: Bot, data: str, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

        self.data = ujson.loads(base64.b64decode(data).decode("utf-8"))

        for i, button in enumerate(self.data["buttons"]):
            button_color = getattr(discord.ButtonStyle, button["style"])

            button_object = Button(label=button["label"], style=button_color, custom_id=f"{data[-90:] if len(data) > 90 else data}:{i}")
            modal_data = self.data["modals"][i]
            modal_components = modal_data["components"]

            children = []

            for component in modal_components:
                length = getattr(discord.InputTextStyle, component["length"])

                component_object = discord.ui.InputText(
                    label=component["label"],
                    placeholder=component["placeholder"],
                    style=length,
                    required=True if component.get("required", False) else False
                )
                children.append(component_object)

            modal = ModalOverwrite(
                button['label'],
                *children,
                title=modal_data["title"],
                timeout=None
            )

            async def modal_callback(interaction: discord.Interaction, modal: ModalOverwrite=modal, children=children):
                response = await self.bot.db.fetchone("SELECT * FROM custom_mappings WHERE message_id = ?", interaction.message.id)
                if not response:
                    await interaction.response.send_message("This message is no longer valid.", ephemeral=True)
                    return
                        
                _, channel_id, role_id, name = response

                response_embed = discord.Embed(
                    color=discord.Color.red()
                )

                open_tickets_user = await self.bot.db.fetchone("SELECT * FROM tickets WHERE opened_by = ?", interaction.user.id)
                if open_tickets_user:
                    response_embed.title = "An Error Occurred"
                    response_embed.description = "You already have an open ticket, please close that ticket before opening a new one."
                    await interaction.respond(embed=response_embed, ephemeral=True)
                    return

                category: discord.CategoryChannel = self.bot.get_channel(channel_id)
                if not category:
                    response_embed.title = "An Error Occurred"
                    response_embed.description = "The category associated with the panel no longer exists."
                    await interaction.respond(embed=response_embed, ephemeral=True)
                    return
                
                ticket_role = interaction.guild.get_role(role_id)
                if not ticket_role:
                    response_embed.title = "An Error Occurred"
                    response_embed.description = "The role associated with the panel no longer exists."
                    await interaction.respond(embed=response_embed, ephemeral=True)
                    return

                overwrites, role, tos_agreed = await get_default_overwrites(self.bot, interaction.guild.id, interaction.user.id, ticket_type=name[7:])
                seller_role = await self.bot.db.get_config("seller_role")
                if seller_role:
                    seller_role = interaction.guild.get_role(seller_role)
                    if seller_role:
                        if seller_role in overwrites:
                            del overwrites[seller_role]

                overwrites[ticket_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

                channel = await category.create_text_channel(name=name, overwrites=overwrites)
                response_embed.color = discord.Color.green()

                await interaction.user.add_roles(role)
                response_embed.title = "Ticket Created"
                response_embed.description = f"Your ticket has been created, go to {channel.mention}!"

                await interaction.respond(embed=response_embed, ephemeral=True)

                embed = discord.Embed(
                    title="Ticket Opened",
                    description=f"Thank you for opening a ticket, a member of our team will be with you shortly.",
                    color=discord.Color.red()
                )

                initial_message = await channel.send(
                    embed=embed,
                    content=f"<@&{role_id}>, <@{interaction.user.id}>",
                    view=OpenedTicket(self.bot)
                )
                await initial_message.pin()
                # Extract ticket_type from name (format: "ticket-{type}")
                ticket_type = name[7:] if name.startswith("ticket-") else None
                await self.bot.db.execute(
                    "INSERT INTO tickets (opened_by, channel_id, initial_message_id, role_id, is_open, claimed, ticket_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    interaction.user.id, channel.id, initial_message.id, role.id, 1, 0, ticket_type
                )

                embed = discord.Embed(
                    color=discord.Color.red(),
                    description=f"""# Disclaimer
### We will only deal within this ticket\nso if anyone pretending to be one of us messages you, please ignore them."""
                )
                embed.set_footer(text="Made by noemt | https://bots.noemt.dev", icon_url="https://noemt.dev/assets/icon.webp")
                await channel.send(embed=embed)

                modal_inputs_embed = discord.Embed(
                    title="Ticket Info",
                    description=f"The following data was submitted:\nButton: **{modal.button_label}** was used to open this ticket.",
                    color=discord.Color.red()
                )
                for i, component in enumerate(children):
                    modal_inputs_embed.add_field(name=modal.children[i].label, value=modal.children[i].value, inline=False)

                await channel.send(embed=modal_inputs_embed)

                hylist_embed = await hylist_lookup(interaction.user.id)
                if hylist_embed:
                    await channel.send(embed=hylist_embed)
                    await channel.edit(name=f'❌-{channel.name}')

                if tos_agreed is False:
                    await channel.send(
                        embed=discord.Embed(
                            title="Terms of Service",
                            description=f"We require you to agree to our Terms of Service before you can buy something.\nRefer to {self.bot.get_command_link('terms view')}.",
                            color=discord.Color.red()
                        ))

            modal = discord.ui.Modal(
                *children,
                title=modal_data["title"],
                timeout=None
            )
            modal.callback = modal_callback

            async def button_callback(interaction: discord.Interaction, modal=modal):
                await interaction.response.send_modal(modal)

            button_object.callback = button_callback

            self.add_item(button_object)

class TermsView(View):
    def __init__(self, bot: Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

    @button(
        label="Accept Terms",
        style=discord.ButtonStyle.green,
        custom_id="terms:accept"
    )
    async def accept_terms(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        already_accepted = await self.bot.db.fetchone("SELECT * FROM tos_agreed WHERE user_id = ?", interaction.user.id)
        if already_accepted:
            embed = discord.Embed(
                title="Terms Already Accepted",
                description="You have already accepted the terms of service. You will no longer be prompted in this server unless it is changed.",
                color=discord.Color.red()
            )
            return await interaction.respond(embed=embed, ephemeral=True)

        await self.bot.db.execute("INSERT INTO tos_agreed (user_id, agreed_at) VALUES (?, ?)", interaction.user.id, datetime.datetime.now().timestamp())
        
        embed = discord.Embed(
            title="Terms Accepted",
            description="You have accepted the terms of service. You will no longer be prompted in this server unless it is changed.",
            color=discord.Color.green()
        )
        await interaction.respond(embed=embed, ephemeral=True)

        is_ticket = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id = ?", interaction.channel.id)
        if is_ticket:
            embed = discord.Embed(
                title="Terms of Service",
                description="Thank you for accepting the terms of service.",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=embed, content=interaction.user.mention)

views = [OpenedTicket, Account, FairnessView, Profile, Alt, AccountSale, ProfileSale, AltSale, AuthorizeView, CoinSale, MFASale, Middleman, LowballView, TermsView, CaptchaView]
