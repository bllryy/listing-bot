import discord
from discord.ui import View, button
from bot.bot import Bot

from chat_exporter.construct.transcript import Transcript
from bot.util.attachment_handler import CustomHandler
from bot.util.get_default_overwrites import get_role_config_name
import os

class Ticket:
    def __init__(self, opened_by, channel_id, initial_message_id, role_id, is_open=True, claimed:int=None, ticket_type:str=None):
        self.opened_by = opened_by
        self.channel_id = channel_id
        self.initial_message_id = initial_message_id
        self.role_id = role_id
        self.is_open = is_open
        self.ticket_type = ticket_type
        self.claimed = claimed

class OpenedTicket(View):
    def __init__(self, bot: Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

    async def _get_staff_roles_for_ticket(self, guild: discord.Guild, ticket_type: str | None):
        """Return the set of staff roles that should see this ticket."""
        roles: set[discord.Role] = set()

        seller_role_obj: discord.Role | None = None
        seller_role_id = await self.bot.db.get_config("seller_role")
        if seller_role_id:
            seller_role_obj = guild.get_role(int(seller_role_id))

        role_config_name = get_role_config_name(ticket_type) if ticket_type else "seller_role"
        if role_config_name:
            configured_role_id = await self.bot.db.get_config(role_config_name)
            if configured_role_id:
                configured_role = guild.get_role(int(configured_role_id))
                if configured_role:
                    roles.add(configured_role)

        custom_role_objs: list[discord.Role] = []
        if ticket_type:
            additional_roles = await self.bot.db.fetchall(
                "SELECT role_id FROM ticket_roles WHERE ticket_type = ?",
                ticket_type,
            )
            for (role_id,) in additional_roles:
                if role_id:
                    role_obj = guild.get_role(int(role_id))
                    if role_obj:
                        custom_role_objs.append(role_obj)

        if custom_role_objs:
            roles.update(custom_role_objs)
            if seller_role_obj in roles and seller_role_obj not in custom_role_objs:
                roles.discard(seller_role_obj)

        if not roles and seller_role_obj:
            roles.add(seller_role_obj)

        return roles

    async def _resolve_ticket_state(
        self,
        channel: discord.TextChannel,
    ) -> tuple[Ticket | None, int | None, set[discord.Role]]:
        """Fetch ticket info, determine staff roles and claimer, syncing the database if needed."""
        ticket_row = await self.bot.db.fetchone(
            "SELECT opened_by, channel_id, initial_message_id, role_id, is_open, claimed, ticket_type FROM tickets WHERE channel_id = ?",
            channel.id,
        )
        if not ticket_row:
            return None, None, set()

        ticket = Ticket(*ticket_row)
        staff_roles = await self._get_staff_roles_for_ticket(channel.guild, ticket.ticket_type)

        if not staff_roles:
            inferred_roles: set[discord.Role] = set()
            ticket_specific_role = channel.guild.get_role(ticket.role_id)
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Role):
                    if target == channel.guild.default_role:
                        continue
                    if ticket_specific_role and target.id == ticket_specific_role.id:
                        continue
                    if overwrite.read_messages or overwrite.view_channel:
                        inferred_roles.add(target)

            if inferred_roles:
                seller_role_id = await self.bot.db.get_config("seller_role")
                seller_role_obj = channel.guild.get_role(int(seller_role_id)) if seller_role_id else None
                if seller_role_obj in inferred_roles and len(inferred_roles) > 1:
                    inferred_roles.discard(seller_role_obj)
                    staff_roles = inferred_roles  # Ensure staff_roles is set even when inferred from overwrites

        claimer_id = None
        for target, overwrite in channel.overwrites.items():
            if not isinstance(target, discord.Member):
                continue
            if overwrite.read_messages and (overwrite.send_messages is True or overwrite.send_messages is None):
                if not staff_roles or any(role in target.roles for role in staff_roles):
                    claimer_id = target.id
                    break

        desired_claim_state = claimer_id if claimer_id else 0
        if ticket.claimed != desired_claim_state:
            await self.bot.db.execute(
                "UPDATE tickets SET claimed = ? WHERE channel_id = ?",
                desired_claim_state,
                channel.id,
            )

        return ticket, claimer_id, staff_roles

    async def update_button_states(
        self,
        channel: discord.TextChannel,
        *,
        ticket: Ticket | None = None,
        claimer_id: int | None = None,
        staff_roles: set[discord.Role] | None = None,
    ) -> tuple[Ticket | None, int | None, set[discord.Role]]:
        """Ensure the claim/unclaim buttons reflect the latest claim status."""

        if ticket is None or claimer_id is None or staff_roles is None:
            ticket, claimer_id, staff_roles = await self._resolve_ticket_state(channel)

        claim_button = self.children[1]  # Claim button
        unclaim_button = self.children[2]  # Unclaim button

        if ticket is None:
            claim_button.disabled = True
            unclaim_button.disabled = True
            return None, None, set()

        is_claimed = bool(claimer_id)
        claim_button.disabled = is_claimed
        unclaim_button.disabled = not is_claimed

        return ticket, claimer_id, staff_roles

    @button(
        label="Close Ticket",
        style=discord.ButtonStyle.red, 
        custom_id="tickets:close"
    )
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        seller_role = await self.bot.db.get_config("seller_role")
        if not seller_role:
            embed = discord.Embed(
                title="Error",
                description="Seller Role not found in the database.",
                color=discord.Color.red()
            )
            return await interaction.respond(embed=embed, ephemeral=True)

        config = await self.bot.db.get_config("let_customers_close_tickets")
        if not config:                
            role = interaction.guild.get_role(seller_role)
            if role not in interaction.user.roles and interaction.user.id not in self.bot.owner_ids:
                embed = discord.Embed(
                    title="Error",
                    description="You can't close this ticket!",
                    color=discord.Color.red()
                )
                return await interaction.respond(embed=embed, ephemeral=True)

        transcript = (
            await Transcript(
                channel=interaction.channel, limit=None,
                messages=None, pytz_timezone="UTC",
                military_time=True, fancy_times=True,
                before=None, after=None, support_dev=True,
                bot=self.bot, attachment_handler=CustomHandler()
            ).export()
        ).html

        ticket = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id = ?", interaction.channel.id)
        if not ticket:
            return await interaction.response.send_message("An error occurred while fetching the ticket information. (You should manually delete it.)", ephemeral=True)
        
        ticket = Ticket(*ticket)
        await interaction.channel.send("Generating Transcript...")
        os.makedirs("./templates", exist_ok=True)

        with open(f"./templates/{self.bot.bot_name}-{interaction.channel.id}-{ticket.opened_by}.html", "wb") as f:
            f.write(transcript.encode())

        transcript_url = f"https://{await self.bot.get_domain()}/transcript/{self.bot.bot_name}/{interaction.channel.id}-{ticket.opened_by}"
        transcript_embed = discord.Embed(
            description=f"**Transcript Link:** [Click]({transcript_url})",
            colour=discord.Colour.embed_background()
        )
        transcript_embed.set_author(name="Transcript", icon_url=self.bot.user.avatar.url)
        transcript_embed.set_footer(text=f"{interaction.channel.name}")
        transcript_embed.add_field(name="Closed By", value=f"{interaction.user.mention}")
        transcript_embed.add_field(name="Opened By", value=f"<@{ticket.opened_by}>")

        button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Transcript",
            url=transcript_url
        )
        view = discord.ui.View()
        view.add_item(button)

        role = interaction.guild.get_role(ticket.role_id)

        if not role:
            try:
                await self.bot.db.execute("DELETE FROM roles WHERE role_id = ?", ticket.role_id)
            except:
                pass
        else:
            # Remove all members from the role instead of deleting the channel
            for member in role.members:
                try:
                    await member.remove_roles(role)
                except:
                    pass 

        # Mark ticket as closed in database instead of deleting
        await self.bot.db.execute("UPDATE tickets SET is_open = ? WHERE channel_id = ?", 0, interaction.channel.id)
        await self.bot.db.execute("UPDATE roles SET used = ? WHERE role_id = ?", 0, ticket.role_id)

        # Update channel permissions to make it read-only
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False, read_messages=False)
        if role:
            await interaction.channel.set_permissions(role, send_messages=False, read_messages=True)

        logs_channel = await self.bot.db.get_config("logs_channel")
        if logs_channel:
            logs_channel = self.bot.get_channel(logs_channel)
            if logs_channel:
                await logs_channel.send(embed=transcript_embed, view=view)

        # Send confirmation message
        close_embed = discord.Embed(
            title="Ticket Closed",
            description="This ticket has been closed. Use `/ticket delete` to permanently delete it.",
            color=discord.Color.orange()
        )
        try:
            await interaction.followup.send(embed=close_embed)
        except discord.HTTPException:
            pass

    @button(
        label="Claim",
        style=discord.ButtonStyle.grey,
        custom_id="tickets:claim"
    )
    async def claim_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            # Interaction already responded to or expired
            return

        ticket, claimed_by, staff_roles = await self._resolve_ticket_state(interaction.channel)
        if not ticket:
            embed = discord.Embed(
                title="Error",
                description="Ticket data could not be found in the database.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Check if ticket is already claimed
        if claimed_by:
            claimer = interaction.guild.get_member(claimed_by)
            claimer_mention = claimer.mention if claimer else f"<@{claimed_by}>"
            embed = discord.Embed(
                title="Error",
                description=f"This ticket is already claimed by {claimer_mention}!",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if not staff_roles:
            embed = discord.Embed(
                title="Error",
                description="No staff roles were configured for this ticket type.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if not any(role in interaction.user.roles for role in staff_roles):
            embed = discord.Embed(
                title="Error",
                description="You can't claim this ticket!",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Remove access for staff roles while claimed
        staff_deny = discord.PermissionOverwrite(view_channel=False, read_messages=False, send_messages=False)
        try:
            for role in staff_roles:
                await interaction.channel.set_permissions(role, overwrite=staff_deny)

            claimer_overwrite = discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                send_messages=True,
            )
            await interaction.channel.set_permissions(interaction.user, overwrite=claimer_overwrite)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="I don't have permission to modify channel permissions!",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to update channel permissions: {str(e)}",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        await self.bot.db.execute(
            "UPDATE tickets SET claimed = ? WHERE channel_id = ?",
            interaction.user.id,
            interaction.channel.id,
        )

        await self.update_button_states(
            interaction.channel,
            ticket=ticket,
            claimer_id=interaction.user.id,
            staff_roles=staff_roles,
        )

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass  # Message might have been deleted

        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"This ticket has been claimed by {interaction.user.mention}",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed)

    @button(
        label="Unclaim",
        style=discord.ButtonStyle.secondary,
        custom_id="tickets:unclaim",
        disabled=True
    )
    async def unclaim_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.NotFound:
            # Interaction already responded to or expired
            return

        ticket, claimed_by, staff_roles = await self._resolve_ticket_state(interaction.channel)
        if not ticket:
            embed = discord.Embed(
                title="Error",
                description="Ticket data could not be found in the database.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Check if the user is the one who claimed the ticket
        if not claimed_by:
            embed = discord.Embed(
                title="Error",
                description="This ticket is not currently claimed!",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if claimed_by != interaction.user.id:
            claimer = interaction.guild.get_member(claimed_by)
            claimer_mention = claimer.mention if claimer else f"<@{claimed_by}>"
            embed = discord.Embed(
                title="Error",
                description=f"You can only unclaim tickets that you have claimed! This ticket is claimed by {claimer_mention}.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        try:
            staff_allow = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
            for role in staff_roles:
                await interaction.channel.set_permissions(role, overwrite=staff_allow)

            # Remove specific permissions for the user who claimed it
            await interaction.channel.set_permissions(interaction.user, overwrite=None)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="I don't have permission to modify channel permissions!",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to update channel permissions: {str(e)}",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        await self.bot.db.execute(
            "UPDATE tickets SET claimed = ? WHERE channel_id = ?",
            0,
            interaction.channel.id,
        )

        await self.update_button_states(
            interaction.channel,
            ticket=ticket,
            claimer_id=0,
            staff_roles=staff_roles,
        )

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass  # Message might have been deleted

        embed = discord.Embed(
            title="Ticket Unclaimed",
            description=f"This ticket has been unclaimed by {interaction.user.mention} and is now available for other sellers.",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=embed)