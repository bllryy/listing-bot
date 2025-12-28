import discord
from discord import SlashCommandGroup, option
from discord.ext import commands

from chat_exporter.construct.transcript import Transcript
from bot.bot import Bot

from bot.util.constants import is_authorized_to_use_bot
from bot.util.listing_objects.ticket import Ticket as TicketObject
from bot.util.ticket import get_default_overwrites
from bot.util.paginator import Paginator
import os
from bot.util.attachment_handler import CustomHandler


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    ticket = SlashCommandGroup("ticket", description="Commands related to tickets")


    @ticket.command(
        name="close",
        description="Close a ticket"
    )
    @is_authorized_to_use_bot()
    async def ticket_close(self, ctx: discord.ApplicationContext): 

        try:
            await ctx.defer()
        except:
            pass

        data = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id = ?", ctx.channel.id,)
        if not data:
            embed = discord.Embed(
                title="Error",
                description="This is not a ticket channel!",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        ticket_object = TicketObject(*data)
        
        # Check if ticket is already closed
        if hasattr(ticket_object, 'is_open') and not ticket_object.is_open:
            embed = discord.Embed(
                title="Error",
                description="This ticket is already closed!",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        transcript = (
            await Transcript(
                channel=ctx.channel,
                limit=None,
                messages=None,
                pytz_timezone="UTC",
                military_time=True,
                fancy_times=True,
                before=None,
                after=None,
                support_dev=True,
                bot=self.bot,
                attachment_handler=CustomHandler()
            ).export()
        ).html

        transcript_url = f"https://{await self.bot.get_domain()}/transcript/{self.bot.bot_name}/{ctx.channel.id}-{ticket_object.opened_by}"

        transcript_embed = discord.Embed(
            description=f"**Transcript Link:** [Click]({transcript_url})",
            colour=discord.Colour.embed_background()
        )
        transcript_embed.set_author(name="Transcript", icon_url=self.bot.user.avatar.url)
        transcript_embed.set_footer(text=f"{ctx.channel.name}")
        transcript_embed.add_field(name="Closed By", value=f"{ctx.author.mention}")
        transcript_embed.add_field(name="Opened By", value=f"<@{ticket_object.opened_by}>")
        os.makedirs("./templates", exist_ok=True)

        with open(f"./templates/{self.bot.bot_name}-{ctx.channel.id}-{ticket_object.opened_by}.html", "wb") as f:
            f.write(transcript.encode())

        button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Transcript",
            url=transcript_url
        )
        view = discord.ui.View()
        view.add_item(button)

        role = ctx.guild.get_role(ticket_object.role_id)

        if not role:
            try:
                await self.bot.db.execute("DELETE FROM roles WHERE role_id = ?", ticket_object.role_id)
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
        await self.bot.db.execute("UPDATE tickets SET is_open = ? WHERE channel_id = ?", 0, ctx.channel.id)
        await self.bot.db.execute("UPDATE roles SET used = ? WHERE role_id = ?", 0, ticket_object.role_id)

        # Update channel permissions to make it read-only
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False, read_messages=False)
        if role:
            await ctx.channel.set_permissions(role, send_messages=False, read_messages=True)

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
        await ctx.respond(embed=close_embed)

    @ticket.command(
        name="delete",
        description="Permanently delete a closed ticket"
    )
    @is_authorized_to_use_bot()
    async def ticket_delete(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id = ?", ctx.channel.id)
        if not data:
            embed = discord.Embed(
                title="Error",
                description="This is not a ticket channel!",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        ticket_object = TicketObject(*data)
        
        if hasattr(ticket_object, 'is_open') and ticket_object.is_open:
            await self.ticket_close(ctx)

        await self.bot.db.execute("DELETE FROM tickets WHERE channel_id = ?", ctx.channel.id)
        await ctx.channel.delete()


    @ticket.command(
        name="add",
        description="Add a user to a ticket"
    )
    @option(
        name="user",
        description="User to add",
        type=discord.Member
    )
    @is_authorized_to_use_bot()
    async def ticket_add(self, ctx: discord.ApplicationContext, user: discord.Member):
        await ctx.defer()

        data = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id = ?", ctx.channel.id,)
        if not data:
            embed = discord.Embed(
                title="Error",
                description="This is not a ticket channel!",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
            
        ticket_object = TicketObject(*data)
        role = ctx.guild.get_role(ticket_object.role_id)
        if not role:
            _, role = await get_default_overwrites(self.bot, ctx.guild.id)

        await user.add_roles(role)

        embed = discord.Embed(
            title="Success",
            description=f"Added {user.mention} to the ticket!",
            color=discord.Color.green()
        )
        await ctx.respond(user.mention, embed=embed)
        await ctx.channel.set_permissions(role, read_messages=True, send_messages=True)

        await self.bot.db.execute("UPDATE tickets SET role_id = ? WHERE channel_id = ?", role.id, ctx.channel.id)
        await self.bot.db.execute("UPDATE roles SET used = ? WHERE role_id = ?", 0, ticket_object.role_id)
        await self.bot.db.execute("UPDATE roles SET used = ? WHERE role_id = ?", 1, role.id)

    @ticket.command(
        name="remove",
        description="Remove a user from a ticket"
    )
    @option(
        name="user",
        description="User to remove",
        type=discord.Member
    )
    @is_authorized_to_use_bot()
    async def ticket_remove(self, ctx: discord.ApplicationContext, user: discord.Member):
        await ctx.defer()

        data = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id = ?", ctx.channel.id,)
        if not data:
            embed = discord.Embed(
                title="Error",
                description="This is not a ticket channel!",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
            
        ticket_object = TicketObject(*data)
        role = ctx.guild.get_role(ticket_object.role_id)
        if not role:
            embed = discord.Embed(
                title="Error",
                description="Role not found!",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        await user.remove_roles(role)

        embed = discord.Embed(
            title="Success",
            description=f"Removed {user.mention} from the ticket!",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @ticket.command(
        name="list",
        description="Lists all active tickets"
    )
    @is_authorized_to_use_bot()
    async def ticket_list(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        tickets = await self.bot.db.fetchall("SELECT * FROM tickets")
        if not tickets:
            embed = discord.Embed(
                title="Error",
                description="No tickets found!",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        embeds = []
        
        for i, data in enumerate(tickets):
            if i % 10 == 0:

                if i != 0:
                    embeds.append(embed)

                embed = discord.Embed(
                    title="Tickets",
                    color=discord.Color.blue()
                )

            ticket = TicketObject(*data)
            status = "🟢 Open" if (hasattr(ticket, 'is_open') and ticket.is_open) else "🔴 Closed"
            embed.add_field(
                name=f"Ticket {i+1} - {status}",
                value=f"Opened by: <@{ticket.opened_by}>\nChannel: <#{ticket.channel_id}>",
                inline=False
            )

        if embed not in embeds:
            embeds.append(embed)

        paginator = Paginator(embeds=embeds)
        await ctx.respond(embed=embeds[0], view=paginator, ephemeral=True)

def setup(bot):
    bot.add_cog(Ticket(bot))
