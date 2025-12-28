import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from bot.bot import Bot
from bot.util.constants import is_authorized_to_use_bot, cog_action_types
from bot.util.listing_objects.ticket import Ticket as TicketObject
from chat_exporter.construct.transcript import Transcript
from bot.util.attachment_handler import CustomHandler
from typing import Optional
import asyncio
import os

class CogActions(commands.Cog):
    """Cog for managing server action configurations"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    _cog_actions = SlashCommandGroup("actions", description="Configure server actions")

    @_cog_actions.command(
        name="list",
        description="List all available action types and their status"
    )
    @is_authorized_to_use_bot()
    async def list_actions(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            
            # Get current action statuses
            action_statuses = await self.bot.db.fetchall(
                "SELECT action_type, enabled FROM cog_actions WHERE guild_id = ?",
                guild_id
            )
            
            status_dict = {row[0]: bool(row[1]) for row in action_statuses}
            
            embed = discord.Embed(
                title="🛠️ Server Action Configuration",
                description="Available actions and their current status:",
                color=discord.Color.blue()
            )
            
            for action_type, config in cog_action_types.items():
                status = "🟢 Enabled" if status_dict.get(action_type, False) else "🔴 Disabled"
                embed.add_field(
                    name=f"{status} **{config['name']}**",
                    value=config['description'],
                    inline=False
                )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to load action statuses: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @_cog_actions.command(
        name="enable",
        description="Enable a specific action type"
    )
    @is_authorized_to_use_bot()
    @option("action_type", description="Action type to enable", choices=list(cog_action_types.keys()))
    async def enable_action(self, ctx: discord.ApplicationContext, action_type: str):
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            
            # Enable the action
            await self.bot.db.execute(
                "INSERT OR REPLACE INTO cog_actions (guild_id, action_type, enabled) VALUES (?, ?, 1)",
                guild_id, action_type
            )
            
            config = cog_action_types[action_type]
            embed = discord.Embed(
                title="✅ Action Enabled",
                description=f"**{config['name']}** has been enabled for this server.",
                color=discord.Color.green()
            )
            
            if 'channels' in config or 'settings' in config:
                embed.add_field(
                    name="⚠️ Configuration Required",
                    value=f"Use `/actions configure {action_type}` to set up channels and settings.",
                    inline=False
                )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to enable action: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @_cog_actions.command(
        name="disable",
        description="Disable a specific action type"
    )
    @is_authorized_to_use_bot()
    @option("action_type", description="Action type to disable", choices=list(cog_action_types.keys()))
    async def disable_action(self, ctx: discord.ApplicationContext, action_type: str):
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            
            # Disable the action
            await self.bot.db.execute(
                "INSERT OR REPLACE INTO cog_actions (guild_id, action_type, enabled) VALUES (?, ?, 0)",
                guild_id, action_type
            )
            
            config = cog_action_types[action_type]
            embed = discord.Embed(
                title="🔴 Action Disabled",
                description=f"**{config['name']}** has been disabled for this server.",
                color=discord.Color.orange()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to disable action: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @_cog_actions.command(
        name="configure",
        description="Configure channels and settings for an action"
    )
    @is_authorized_to_use_bot()
    @option("action_type", description="Action type to configure", choices=list(cog_action_types.keys()))
    async def configure_action(self, ctx: discord.ApplicationContext, action_type: str):
        await ctx.defer(ephemeral=True)
        
        try:
            config = cog_action_types[action_type]
            
            # Check if action is enabled
            is_enabled = await self.bot.db.fetchone(
                "SELECT enabled FROM cog_actions WHERE guild_id = ? AND action_type = ?",
                ctx.guild.id, action_type
            )
            
            if not is_enabled or not is_enabled[0]:
                embed = discord.Embed(
                    title="⚠️ Action Not Enabled",
                    description=f"**{config['name']}** is not enabled. Use `/actions enable {action_type}` first.",
                    color=discord.Color.orange()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            # Get current configuration
            channels = await self.bot.db.fetchall(
                "SELECT channel_type, channel_id FROM cog_action_channels WHERE guild_id = ? AND action_type = ?",
                ctx.guild.id, action_type
            )
            
            settings = await self.bot.db.fetchall(
                "SELECT setting_key, setting_value FROM cog_action_settings WHERE guild_id = ? AND action_type = ?",
                ctx.guild.id, action_type
            )
            
            embed = discord.Embed(
                title=f"⚙️ Configure {config['name']}",
                description=config['description'],
                color=discord.Color.blue()
            )
            
            # Show current channels
            if 'channels' in config:
                channel_info = []
                channel_dict = {row[0]: row[1] for row in channels}
                
                for channel_type in config['channels']:
                    channel_id = channel_dict.get(channel_type)
                    if channel_id:
                        channel = ctx.guild.get_channel(channel_id)
                        channel_info.append(f"**{channel_type}**: {channel.mention if channel else 'Unknown Channel'}")
                    else:
                        channel_info.append(f"**{channel_type}**: Not set")
                
                embed.add_field(
                    name="📍 Channels",
                    value="\n".join(channel_info) or "No channels configured",
                    inline=False
                )
            
            # Show current settings
            if 'settings' in config:
                setting_info = []
                setting_dict = {row[0]: row[1] for row in settings}
                
                for setting_key in config['settings']:
                    setting_value = setting_dict.get(setting_key, "Not set")
                    setting_info.append(f"**{setting_key}**: {setting_value}")
                
                embed.add_field(
                    name="⚙️ Settings",
                    value="\n".join(setting_info) or "No settings configured",
                    inline=False
                )
            
            embed.add_field(
                name="🛠️ Configuration Commands",
                value=f"Use `/actions set-channel` and `/actions set-setting` to configure this action.",
                inline=False
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to load configuration: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @_cog_actions.command(
        name="set-channel",
        description="Set a channel for a specific action"
    )
    @is_authorized_to_use_bot()
    @option("action_type", description="Action type", choices=list(cog_action_types.keys()))
    @option("channel_type", description="Channel type (join_channel, leave_channel, etc.)")
    @option("channel", description="Channel to set", type=discord.TextChannel)
    async def set_channel(self, ctx: discord.ApplicationContext, action_type: str, channel_type: str, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)
        
        try:
            config = cog_action_types[action_type]
            
            # Validate channel type
            if 'channels' not in config or channel_type not in config['channels']:
                embed = discord.Embed(
                    title="❌ Invalid Channel Type",
                    description=f"**{channel_type}** is not a valid channel type for **{config['name']}**.\nValid types: {', '.join(config.get('channels', []))}",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            # Set the channel
            await self.bot.db.execute(
                "INSERT OR REPLACE INTO cog_action_channels (guild_id, action_type, channel_type, channel_id) VALUES (?, ?, ?, ?)",
                ctx.guild.id, action_type, channel_type, channel.id
            )
            
            embed = discord.Embed(
                title="✅ Channel Set",
                description=f"**{channel_type}** for **{config['name']}** has been set to {channel.mention}",
                color=discord.Color.green()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to set channel: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @_cog_actions.command(
        name="set-setting",
        description="Set a setting value for a specific action"
    )
    @is_authorized_to_use_bot()
    @option("action_type", description="Action type", choices=list(cog_action_types.keys()))
    @option("setting_key", description="Setting key (join_message, leave_message, etc.)")
    @option("setting_value", description="Setting value")
    async def set_setting(self, ctx: discord.ApplicationContext, action_type: str, setting_key: str, setting_value: str):
        await ctx.defer(ephemeral=True)
        
        try:
            config = cog_action_types[action_type]
            
            # Validate setting key
            if 'settings' not in config or setting_key not in config['settings']:
                embed = discord.Embed(
                    title="❌ Invalid Setting Key",
                    description=f"**{setting_key}** is not a valid setting for **{config['name']}**.\nValid settings: {', '.join(config.get('settings', []))}",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            # Set the setting
            await self.bot.db.execute(
                "INSERT OR REPLACE INTO cog_action_settings (guild_id, action_type, setting_key, setting_value) VALUES (?, ?, ?, ?)",
                ctx.guild.id, action_type, setting_key, setting_value
            )
            
            embed = discord.Embed(
                title="✅ Setting Updated",
                description=f"**{setting_key}** for **{config['name']}** has been set to: `{setting_value}`",
                color=discord.Color.green()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to set setting: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
    
    # Action implementations
    async def is_action_enabled(self, guild_id: int, action_type: str) -> bool:
        """Check if an action is enabled for a guild"""
        result = await self.bot.db.fetchone(
            "SELECT enabled FROM cog_actions WHERE guild_id = ? AND action_type = ?",
            guild_id, action_type
        )
        return bool(result and result[0])
    
    async def get_action_channel(self, guild_id: int, action_type: str, channel_type: str) -> Optional[int]:
        """Get a channel ID for an action"""
        result = await self.bot.db.fetchone(
            "SELECT channel_id FROM cog_action_channels WHERE guild_id = ? AND action_type = ? AND channel_type = ?",
            guild_id, action_type, channel_type
        )
        return result[0] if result else None
    
    async def get_action_setting(self, guild_id: int, action_type: str, setting_key: str) -> Optional[str]:
        """Get a setting value for an action"""
        result = await self.bot.db.fetchone(
            "SELECT setting_value FROM cog_action_settings WHERE guild_id = ? AND action_type = ? AND setting_key = ?",
            guild_id, action_type, setting_key
        )
        return result[0] if result else None
    
    # Event handlers for join/leave messages
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join events"""
        try:
            if not await self.is_action_enabled(member.guild.id, "join_leave_messages"):
                return
            
            # Get join channel
            join_channel_id = await self.get_action_channel(member.guild.id, "join_leave_messages", "join_channel")
            if not join_channel_id:
                return
            
            join_channel = member.guild.get_channel(join_channel_id)
            if not join_channel:
                return
            
            # Get join message
            join_message = await self.get_action_setting(member.guild.id, "join_leave_messages", "join_message")
            if not join_message:
                join_message = "Welcome {user} to {server}! 🎉"
            
            # Replace placeholders
            message = join_message.format(
                user=member.mention,
                username=member.display_name,
                server=member.guild.name,
                member_count=member.guild.member_count
            )
            
            await join_channel.send(message)
            
        except Exception as e:
            print(f"Error in join message handler: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leave events"""
        try:
            # Handle join/leave messages
            if await self.is_action_enabled(member.guild.id, "join_leave_messages"):
                # Get leave channel
                leave_channel_id = await self.get_action_channel(member.guild.id, "join_leave_messages", "leave_channel")
                if leave_channel_id:
                    leave_channel = member.guild.get_channel(leave_channel_id)
                    if leave_channel:
                        # Get leave message
                        leave_message = await self.get_action_setting(member.guild.id, "join_leave_messages", "leave_message")
                        if not leave_message:
                            leave_message = "{username} has left {server}. 👋"
                        
                        # Replace placeholders
                        message = leave_message.format(
                            user=member.mention,
                            username=member.display_name,
                            server=member.guild.name,
                            member_count=member.guild.member_count
                        )
                        
                        await leave_channel.send(message)
            
            # Handle ticket auto close
            if await self.is_action_enabled(member.guild.id, "ticket_auto_close"):
                await self._handle_ticket_auto_close(member)
            
        except Exception as e:
            print(f"Error in member remove handler: {e}")
    
    async def _handle_ticket_auto_close(self, member: discord.Member):
        """Handle automatic ticket closing when a member leaves"""
        try:
            # Get close delay setting (default 5 minutes)
            delay_minutes = await self.get_action_setting(member.guild.id, "ticket_auto_close", "close_delay_minutes")
            delay_seconds = int(delay_minutes) * 60 if delay_minutes else 300  # Default 5 minutes
            
            # Find all tickets opened by this member
            tickets = await self.bot.db.fetchall(
                "SELECT * FROM tickets WHERE opened_by = ? AND is_open = 1",
                member.id
            )
            
            if not tickets:
                return
            
            # Wait for the specified delay
            await asyncio.sleep(delay_seconds)
            
            # Check if member rejoined during the delay
            if member.guild.get_member(member.id):
                return  # Member rejoined, don't close tickets
            
            # Close each ticket
            for ticket_data in tickets:
                try:
                    ticket_object = TicketObject(*ticket_data)
                    channel = member.guild.get_channel(ticket_object.channel_id)
                    
                    if not channel:
                        continue
                    
                    # Check if ticket is still open
                    current_ticket = await self.bot.db.fetchone(
                        "SELECT is_open FROM tickets WHERE channel_id = ?",
                        ticket_object.channel_id
                    )
                    
                    if not current_ticket or not current_ticket[0]:
                        continue  # Ticket already closed
                    
                    await self._auto_delete_ticket(channel, ticket_object, member)
                    
                except Exception as e:
                    print(f"Error closing ticket {ticket_data[0]}: {e}")
                    
        except Exception as e:
            print(f"Error in ticket auto close handler: {e}")
    
    async def _auto_delete_ticket(self, channel: discord.TextChannel, ticket_object: TicketObject, departed_member: discord.Member):
        """Automatically delete a ticket with transcript generation"""
        try:
            # Generate transcript
            transcript = (
                await Transcript(
                    channel=channel,
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

            transcript_url = f"https://{await self.bot.get_domain()}/transcript/{self.bot.bot_name}/{channel.id}-{ticket_object.opened_by}"

            transcript_embed = discord.Embed(
                description=f"**Transcript Link:** [Click]({transcript_url})",
                colour=discord.Colour.embed_background()
            )
            transcript_embed.set_author(name="Transcript (Auto-Deleted)", icon_url=self.bot.user.avatar.url)
            transcript_embed.set_footer(text=f"{channel.name}")
            transcript_embed.add_field(name="Auto-Deleted Reason", value="Member left the server")
            transcript_embed.add_field(name="Departed Member", value=f"{departed_member.mention}")
            transcript_embed.add_field(name="Opened By", value=f"<@{ticket_object.opened_by}>")
            
            # Save transcript
            os.makedirs("./templates", exist_ok=True)
            with open(f"./templates/{self.bot.bot_name}-{channel.id}-{ticket_object.opened_by}.html", "wb") as f:
                f.write(transcript.encode())

            button = discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Transcript",
                url=transcript_url
            )
            view = discord.ui.View()
            view.add_item(button)

            # Send to logs channel before deleting
            logs_channel = await self.bot.db.get_config("logs_channel")
            if logs_channel:
                logs_channel = self.bot.get_channel(logs_channel)
                if logs_channel:
                    await logs_channel.send(embed=transcript_embed, view=view)

            # Delete ticket from database
            await self.bot.db.execute("DELETE FROM tickets WHERE channel_id = ?", channel.id)
            
            # Delete role and remove from database
            role = channel.guild.get_role(ticket_object.role_id)
            if role:
                try:
                    await role.delete()
                except:
                    pass
            
            # Remove role from database
            await self.bot.db.execute("DELETE FROM roles WHERE role_id = ?", ticket_object.role_id)

            # Delete the channel
            await channel.delete()
            
        except Exception as e:
            print(f"Error auto-deleting ticket: {e}")
            # Try to at least delete the channel and database entry
            try:
                await self.bot.db.execute("DELETE FROM tickets WHERE channel_id = ?", channel.id)
                await self.bot.db.execute("DELETE FROM roles WHERE role_id = ?", ticket_object.role_id)
                
                role = channel.guild.get_role(ticket_object.role_id)
                if role:
                    try:
                        await role.delete()
                    except:
                        pass
                        
                await channel.delete()
                
            except Exception as e2:
                print(f"Error in fallback ticket deletion: {e2}")


def setup(bot: Bot):
    bot.add_cog(CogActions(bot))
