import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, option
from bot.util.vouch import insert_vouch
from datetime import datetime
from bot.bot import Bot
import json
import os
from bot.util.constants import is_authorized_to_use_bot
import ai

sample_json = {
    "member_join": False,
    "member_leave": False,
    "message_delete": False,
    "message_edit": False,
    "reaction_add": False,
    "reaction_remove": False,
    "reaction_remove_all": False,
    "reaction_clear": False,
    "member_update": False,
    "guild_update": False,
    "guild_channel_create": False,
    "guild_channel_delete": False,
    "guild_channel_update": False,
    "guild_channel_pins_update": False,
    "guild_role_create": False,
    "guild_role_delete": False,
    "guild_role_update": False,
    "guild_emojis_update": False,
    "guild_integrations_update": False,
    "guild_member_add": False, # Duplicate of member_join, but discord.py uses on_member_join
    "guild_member_remove": False, # Duplicate of member_leave, but discord.py uses on_member_remove
    "guild_member_update": False,
    "guild_ban_add": False,
    "guild_ban_remove": False,
    "guild_webhooks_update": False,
    "guild_invite_create": False,
}

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

        if not os.path.exists("data/logging.json"):
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            with open("data/logging.json", "w") as f:
                json.dump(sample_json, f, indent=4)

    # Helper method to check if logging is enabled
    async def is_logging_enabled(self, guild_id, event_type):
        try:
            with open("data/logging.json", "r") as f:
                settings = json.load(f)
        except FileNotFoundError:
             # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            with open("data/logging.json", "w") as f:
                json.dump({}, f, indent=4) # Start with empty if file truly missing
            return False
            
        guild_id_str = str(guild_id)
        if guild_id_str not in settings:
            return False
            
        return settings[guild_id_str].get(event_type, False)
    
    # Helper method to send log messages
    async def send_log(self, guild, event_type, embed_to_send: discord.Embed):
        if not await self.is_logging_enabled(guild.id, event_type):
            return
            
        log_channel_id_str = await self.bot.db.get_config("log_channel")
        if not log_channel_id_str:
            return
        
        try:
            log_channel_id = int(log_channel_id_str)
        except (ValueError, TypeError):
            print(f"Invalid log_channel_id in DB: {log_channel_id_str}")
            return
            
        channel = guild.get_channel(log_channel_id)
        if not channel:
            return
        
        # Ensure it's a text channel before sending
        if not isinstance(channel, discord.TextChannel):
            print(f"Log channel ID {log_channel_id} is not a text channel.")
            return

        embed_to_send.timestamp = datetime.utcnow()
        embed_to_send.set_footer(text=f"Event ID: {event_type}")
        try:
            await channel.send(embed=embed_to_send)
        except discord.Forbidden:
            print(f"Missing permissions to send log message in {channel.name} ({channel.id})")
        except discord.HTTPException as e:
            print(f"Failed to send log message: {e}")
    
    # Define the logging command group
    logging = SlashCommandGroup("logging", "Commands for configuring logging settings")
    
    @logging.command(
        name="config",
        description="Configure logging settings for different events"
    )
    @is_authorized_to_use_bot()
    @option(
        name="event",
        description="The event to configure logging for",
        choices=[
            "member_join", "member_leave", "message_delete", 
            "message_edit", "reaction_add", "reaction_remove",
            "guild_channel_create", "guild_channel_delete", "guild_channel_update",
            "guild_role_create", "guild_role_delete", "guild_role_update",
            "guild_ban_add", "guild_ban_remove"
            # Removed guild_member_add/remove as they are covered by member_join/leave
        ]
    )
    @option(
        name="enabled",
        description="Enable or disable logging for this event",
        type=bool
    )
    async def logging_config(self, ctx: discord.ApplicationContext, event: str, enabled: bool):
        await ctx.defer(ephemeral=True)
        
        try:
            with open("data/logging.json", "r") as f:
                settings = json.load(f)
        except FileNotFoundError:
            os.makedirs("data", exist_ok=True)
            settings = {} # Initialize empty settings
        
        guild_id = str(ctx.guild.id)
        
        if guild_id not in settings:
            settings[guild_id] = sample_json.copy() # Use a copy of sample_json as a base
        
        # Ensure all keys from sample_json are present for the guild
        for key, value in sample_json.items():
            if key not in settings[guild_id]:
                settings[guild_id][key] = value

        if event in settings[guild_id]:
            settings[guild_id][event] = enabled
            
            with open("data/logging.json", "w") as f:
                json.dump(settings, f, indent=4)
            
            status = "enabled" if enabled else "disabled"
            await ctx.respond(f"Logging for `{event}` has been {status}.", ephemeral=True)
        else:
            # This case should ideally not be reached if choices are comprehensive
            # and sample_json is the source of truth for valid events.
            await ctx.respond(f"Event type `{event}` is not a valid configurable event.", ephemeral=True)
    
    @logging.command(
        name="channel", 
        description="Set the channel for log messages"
    )
    @is_authorized_to_use_bot()
    @option(
        name="channel",
        description="The channel to send logs to",
        type=discord.TextChannel, # This ensures it's a TextChannel
        required=True
    )
    async def logging_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)
        
        await self.bot.db.update_config("log_channel", channel.id)
        await ctx.respond(f"Log channel has been set to {channel.mention}.", ephemeral=True)
    
    @logging.command(
        name="status", 
        description="View current logging configuration"
    )
    @is_authorized_to_use_bot()
    async def logging_status(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        try:
            with open("data/logging.json", "r") as f:
                settings = json.load(f)
        except FileNotFoundError:
            os.makedirs("data", exist_ok=True)
            settings = {}
        
        guild_id = str(ctx.guild.id)
        
        if guild_id not in settings:
            settings[guild_id] = sample_json.copy()
            with open("data/logging.json", "w") as f: # Save initial settings if not present
                json.dump(settings, f, indent=4)
        
        # Ensure all keys from sample_json are present
        guild_settings = settings[guild_id]
        for key, value in sample_json.items():
            if key not in guild_settings:
                guild_settings[key] = value # Default to sample_json value if missing

        embed = discord.Embed(
            title="Logging Configuration",
            description="Current logging settings for this server:",
            color=discord.Color.blue()
        )
        
        log_channel_id_str = await self.bot.db.get_config("log_channel")
        log_channel = None
        if log_channel_id_str:
            try:
                log_channel_id = int(log_channel_id_str)
                log_channel = ctx.guild.get_channel(log_channel_id)
            except (ValueError, TypeError):
                pass # log_channel remains None

        embed.add_field(name="Log Channel", value=log_channel.mention if log_channel else "Not set", inline=False)
        
        enabled_events = []
        disabled_events = []
        
        # Use a defined list of relevant events for display to match choices
        display_events = [
            "member_join", "member_leave", "message_delete", 
            "message_edit", "reaction_add", "reaction_remove",
            "guild_channel_create", "guild_channel_delete", "guild_channel_update",
            "guild_role_create", "guild_role_delete", "guild_role_update",
            "guild_ban_add", "guild_ban_remove"
        ]

        for event in display_events:
            if guild_settings.get(event, False): # Default to False if event somehow missing
                enabled_events.append(event)
            else:
                disabled_events.append(event)
        
        if enabled_events:
            embed.add_field(name="✅ Enabled Events", value="\n".join(f"• {event.replace('_', ' ').title()}" for event in enabled_events), inline=False)
        else:
            embed.add_field(name="✅ Enabled Events", value="None", inline=False)
        
        if disabled_events:
            disabled_str = "\n".join(f"• {event.replace('_', ' ').title()}" for event in disabled_events[:10]) # Show max 10
            if len(disabled_events) > 10:
                disabled_str += f"\nAnd {len(disabled_events) - 10} more..."
            embed.add_field(name="❌ Disabled Events", value=disabled_str, inline=False)
        else:
            embed.add_field(name="❌ Disabled Events", value="None", inline=False) # Explicitly state None
        
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # Keep existing functionality
        tables = ["accounts", "alts", "profiles"]
        for table in tables:
            await self.bot.db.execute(f"DELETE FROM {table} WHERE message_id=?", message.id)

        await self.bot.db.execute("DELETE FROM tickets WHERE initial_message_id=?", message.id)
        
        # Add logging
        if not message.guild or message.author.bot:
            return
            
        log_embed = discord.Embed(
            title="Message Deleted",
            description=f"**Channel:** {message.channel.mention}\n**Author:** {message.author.mention} ({message.author})\n\n**Content:**\n```\n{message.content[:1900] if message.content else 'No text content'}\n```",
            color=discord.Color.red()
        )
        
        if message.attachments:
            attachment_list = "\n".join([f"• {attachment.filename} ({attachment.size // 1024} KB) - [Link]({attachment.url})" for attachment in message.attachments[:5]])
            if len(message.attachments) > 5:
                attachment_list += f"\nAnd {len(message.attachments) - 5} more attachments..."
            log_embed.add_field(name="Attachments", value=attachment_list, inline=False)
            
        await self.send_log(message.guild, "message_delete", log_embed)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        initiate_ai_response = False

        if isinstance(message.channel, discord.DMChannel):
            vouch_prefixes = ["+rep", "+vouch", "+ rep", "+ vouch"]
            if any(message.content.startswith(prefix) for prefix in vouch_prefixes):
                vouch_channel_id_str = await self.bot.db.get_config("vouch_channel")
                if vouch_channel_id_str:
                    try:
                        vouch_channel_id = int(vouch_channel_id_str)
                        channel: discord.TextChannel = self.bot.get_channel(vouch_channel_id)
                    except (ValueError, TypeError):
                        channel = None

                    if channel:
                        send_vouch = await insert_vouch(self.bot, message.author.id, message.content, message.author, anonymous=True)

                        if not send_vouch:
                            return # insert_vouch likely handled the reply
                        
                        await message.add_reaction("✅")

                        profile_picture = "https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDI0LTEyL3YxMTk4LWJiLWVsZW1lbnQtMTUwLXgtbTUyM3o2cjYuanBn.jpg"
                        username = "Anonymous Voucher"

                        webhooks = await channel.webhooks()
                        webhook = webhooks[0] if webhooks else await channel.create_webhook(name="Vouches")
                        await webhook.send(
                            content=message.content,
                            username=username,
                            avatar_url=profile_picture
                        )
                        await message.reply("Thank you for anonymously vouching.")

                    else:
                        await message.reply("The vouch channel is not available. Please try again later.")
                else:
                    await message.reply("The vouch channel is not configured. Please contact the server administrator.")
            else:
                initiate_ai_response = True

        is_ticket = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id=?", message.channel.id)
        if is_ticket:
            if self.bot.user in message.mentions and not message.author.bot:
                initiate_ai_response = True
                min_words = 1

        else:
            initiate_ai_response = True
            min_words = 5

        if not self.bot.user in message.mentions and not message.content.endswith("?"):
            initiate_ai_response = False

        if initiate_ai_response:
            ai_info = await self.bot.db.get_config("ai_info")
            if not ai_info:
                return
            
            word_count = len(message.content.split())
            if not (min_words < word_count < 100):
                return 
            
            query_message = f'''You are an AI assistant designed to help users with questions related to the shop you are working in.'
                {ai_info}
                The users\'s question/message is: {message.content}
                Please provide a helpful and concise response. Do not repeat the info I have given you about my server.'''
            try:
                if message.guild and message.channel:
                    query_message += f'\nSent from:{message.channel.name} in {message.guild.name}'
            except AttributeError:
                pass
            
            async with message.channel.typing():
                try:
                    query_response = await ai.ask_ai(self.bot, query_message, return_json=False)
                    reply_content = query_response.parse()
                    if '{"ban": True' in reply_content:
                        ban_info = json.loads(reply_content)
                        await message.author.ban(reason=ban_info['reason'], delete_message_seconds=0)

                    elif reply_content:
                        if "@everyone" in reply_content or "@here" in reply_content or "<@&" in reply_content:
                            reply_content = "I cannot mention everyone or here or any roles in my responses. Nice try."

                        await message.reply(reply_content)
                    else:
                        await message.reply("I couldn't generate a response for that. Please try rephrasing or ask something else.", allowed_mentions=discord.AllowedMentions.none())
                except Exception as e:
                    print(f"Error during AI processing: {e}")
                    await message.reply("Sorry, I encountered an error while processing your request.", allowed_mentions=discord.AllowedMentions.none())


        elif isinstance(message.channel, discord.TextChannel):
            vouch_channel_id_str = await self.bot.db.get_config("vouch_channel")
            if vouch_channel_id_str:
                try:
                    vouch_channel_id = int(vouch_channel_id_str)
                    vouch_channel = self.bot.get_channel(vouch_channel_id)
                except (ValueError, TypeError):
                    vouch_channel = None

                if vouch_channel and message.channel.id == vouch_channel.id:
                    inserted_vouch = await insert_vouch(self.bot, message.author.id, message.content, message.author)
                    if inserted_vouch:
                        await message.add_reaction("❤️")
                    else:
                        # insert_vouch should handle replies for invalid vouches,
                        # but if it doesn't, message.delete() might be too aggressive
                        # without user feedback. Consider if insert_vouch gives feedback.
                        try:
                            await message.delete()
                        except discord.Forbidden:
                            pass # Can't delete message

            tag = await self.bot.db.fetchone("SELECT * FROM tags WHERE name=?", message.content)
            if tag:
                await message.channel.send(tag[1], allowed_mentions=discord.AllowedMentions.none())
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot:
            return
            
        if before.content == after.content and before.embeds == after.embeds: # Also check embeds
            return # Only content change matters for this log
            
        log_embed = discord.Embed(
            title="Message Edited",
            description=f"**Channel:** {before.channel.mention}\n**Author:** {before.author.mention} ({before.author})\n**[Jump to Message]({after.jump_url})**",
            color=discord.Color.gold()
        )
        
        # Handle potential empty content
        before_content_display = before.content[:900] if before.content else "[No text content]"
        after_content_display = after.content[:900] if after.content else "[No text content]"

        log_embed.add_field(name="Before", value=f"```\n{before_content_display}\n```", inline=False)
        log_embed.add_field(name="After", value=f"```\n{after_content_display}\n```", inline=False)
        
        await self.send_log(before.guild, "message_edit", log_embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        # Keep existing functionality
        ticket = await self.bot.db.fetchone("SELECT * FROM tickets WHERE channel_id=?", channel.id)
        if ticket:
            # ticket format: (opened_by_id, channel_id, message_id, role_id, ...)
            opened_by_id = ticket[0]
            role_id = ticket[3] # Assuming role_id is at index 3

            await self.bot.db.execute("UPDATE roles SET used = ? WHERE role_id = ?", 0, role_id)
            
            member = channel.guild.get_member(opened_by_id) # Get member object
            role = channel.guild.get_role(role_id) # Get role object

            if member and role: # If member still in guild and role exists
                try:
                    await member.remove_roles(role, reason="Ticket channel deleted")
                except discord.Forbidden:
                    print(f"Failed to remove role {role_id} from member {opened_by_id} - Forbidden")
                except discord.HTTPException as e:
                    print(f"Failed to remove role {role_id} from member {opened_by_id} - HTTPException: {e}")

            if not role: # Role might have been deleted manually before channel deletion
                await self.bot.db.execute("DELETE FROM roles WHERE role_id=?", role_id)
            # If member not found, can't remove role, but role entry in DB is updated.

        tables_to_clear_by_channel_id = ["accounts", "alts", "profiles", "tickets"]
        for table in tables_to_clear_by_channel_id:
            await self.bot.db.execute(f"DELETE FROM {table} WHERE channel_id=?", channel.id)
            
        # Add logging
        log_embed = discord.Embed(
            title="Channel Deleted",
            description=f"**Name:** {channel.name}\n**ID:** `{channel.id}`\n**Type:** {str(channel.type).replace('_', ' ').title()}",
            color=discord.Color.red()
        )
        
        if hasattr(channel, 'category') and channel.category: # Check if it has category (not for CategoryChannel itself)
            log_embed.add_field(name="Category", value=channel.category.name, inline=True)
            
        await self.send_log(channel.guild, "guild_channel_delete", log_embed)
    
    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent): # Corrected type hint
        # This event is for when a member leaves or is kicked/banned.
        # on_member_remove is generally preferred unless cache is an issue.
        # This existing functionality seems tied to tickets.
        
        data = await self.bot.db.fetchone("SELECT * FROM tickets WHERE opened_by=?", payload.user.id)
        if not data:
            return

        # data format: (opened_by_id, channel_id, message_id, role_id, ...)
        ticket_channel_id = data[1] 
        channel = self.bot.get_channel(ticket_channel_id) # Use bot.get_channel
        if not channel or not isinstance(channel, discord.TextChannel): # Ensure channel exists and is text
            return

        ticket_embed = discord.Embed(
            title="User Left Server",
            description=f"{payload.user.mention} ({payload.user}) has left the server.\nThey will be added back to the ticket upon rejoining if the ticket is still open.",
            color=discord.Color.red()
        )
        ticket_embed.set_footer(text="made by nom", icon_url="https://noemt.dev/assets/icon.webp")
        try:
            await channel.send(embed=ticket_embed)
        except discord.Forbidden:
            print(f"Cannot send 'User Left' message to ticket channel {channel.id}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # --- Start of existing functionality ---
        if member.bot:
            data_auth_bot = await self.bot.db.fetchone("SELECT * FROM auth_bots WHERE client_id=?", member.id)
            if data_auth_bot:
                auth_bot_role_id_str = await self.bot.db.get_config("auth_bot_role")
                if auth_bot_role_id_str:
                    try:
                        auth_bot_role_id = int(auth_bot_role_id_str)
                        role = member.guild.get_role(auth_bot_role_id)
                        if role:
                            try:
                                await member.add_roles(role, reason="Authenticated Bot Join")
                            except discord.Forbidden:
                                print(f"Failed to add auth_bot_role to {member.name} - Forbidden")
                            except discord.HTTPException as e:
                                print(f"Failed to add auth_bot_role to {member.name} - HTTPException: {e}")
                    except (ValueError, TypeError):
                        pass # Invalid role ID in config

        data_ticket = await self.bot.db.fetchone("SELECT * FROM tickets WHERE opened_by=?", member.id)
        if data_ticket:
            # Check if ticket is open before re-adding user
            # is_open field is at index 4: (opened_by, channel_id, initial_message_id, role_id, is_open)
            is_open = bool(data_ticket[4]) if len(data_ticket) > 4 else True  # Default to True for backward compatibility
            
            if is_open:
                # data_ticket format: (opened_by_id, channel_id, message_id, role_id, is_open, ...)
                ticket_channel_id = data_ticket[1]
                ticket_role_id_from_db = data_ticket[3] # This might be None or invalid if not set properly

                channel = self.bot.get_channel(ticket_channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    role_to_add = None
                    if ticket_role_id_from_db:
                        try:
                            role_to_add = channel.guild.get_role(int(ticket_role_id_from_db))
                        except (ValueError, TypeError):
                            pass # Invalid role_id

                    if role_to_add:
                        try:
                            await member.add_roles(role_to_add, reason="Re-joined server with open ticket")
                        except discord.Forbidden:
                             print(f"Failed to re-add ticket role to {member.name} - Forbidden")
                        except discord.HTTPException as e:
                             print(f"Failed to re-add ticket role to {member.name} - HTTPException: {e}")
                    else: # Fallback to channel permissions if role not found/valid
                        try:
                            await channel.set_permissions(member, read_messages=True, send_messages=True, reason="Re-joined server with open ticket")
                        except discord.Forbidden:
                            print(f"Failed to set ticket channel permissions for {member.name} - Forbidden")
                        except discord.HTTPException as e:
                            print(f"Failed to set ticket channel permissions for {member.name} - HTTPException: {e}")

                    ticket_rejoin_embed = discord.Embed(
                        title="User Rejoined", 
                        description=f"{member.mention} has rejoined the server and has been re-added to this ticket.", 
                        color=discord.Color.green()
                    )
                    ticket_rejoin_embed.set_footer(text="made by nom", icon_url="https://noemt.dev/assets/icon.webp")
                    try:
                        await channel.send(member.mention, embed=ticket_rejoin_embed)
                    except discord.Forbidden:
                        print(f"Cannot send 'User Rejoined' message to ticket channel {channel.id}")
            # If ticket is closed, don't re-add the user
        # --- End of existing functionality ---

        # --- Start of logging logic (Moved here and fixed) ---
        # This block is now unconditional to ensure log_embed is always defined before send_log
        account_age_seconds = (datetime.utcnow().timestamp() - member.created_at.timestamp()) # Use utcnow for consistency
        account_age_days = int(account_age_seconds / 86400)
        account_age_years = account_age_days / 365.25

        log_embed = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} ({member})\nID: `{member.id}`",
            color=discord.Color.green()
        )

        if account_age_years >= 1:
            log_embed.add_field(name="Account Age", value=f"{account_age_days} days ({account_age_years:.1f} years)", inline=True)
        else:
            log_embed.add_field(name="Account Age", value=f"{account_age_days} days", inline=True)

        log_embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        log_embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
        
        if member.display_avatar:
            log_embed.set_thumbnail(url=member.display_avatar.url)
        
        await self.send_log(member.guild, "member_join", log_embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member): # This is different from on_raw_member_remove
        # This listener is for logging the member leave event.
        # The on_raw_member_remove above handles ticket-specific logic for member leaves.
        
        log_embed = discord.Embed(
            title="Member Left",
            description=f"{member.mention} ({member})\nID: `{member.id}`",
            color=discord.Color.red()
        )
        
        # Filter out @everyone role before displaying
        roles = [role.mention for role in member.roles if role.id != member.guild.id][:10]
        if roles:
            role_str = ", ".join(roles)
            if len(member.roles) -1 > 10 : # -1 for @everyone
                 role_str += f" and {len(member.roles) -1 - 10} more..."
            log_embed.add_field(name=f"Roles ({len(roles)})", value=role_str, inline=False)
        
        if member.joined_at:
            log_embed.add_field(name="Joined At", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        else:
            log_embed.add_field(name="Joined At", value="Unknown", inline=True) # Should usually be present
        log_embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
        
        if member.display_avatar:
            log_embed.set_thumbnail(url=member.display_avatar.url)
        
        await self.send_log(member.guild, "member_leave", log_embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_embed = discord.Embed(
            title="Channel Created",
            description=f"**Name:** {channel.mention} (`{channel.name}`)\n**ID:** `{channel.id}`\n**Type:** {str(channel.type).replace('_', ' ').title()}",
            color=discord.Color.green()
        )
        
        if hasattr(channel, 'category') and channel.category:
            log_embed.add_field(name="Category", value=channel.category.name, inline=True)
        if hasattr(channel, 'position'):
            log_embed.add_field(name="Position", value=str(channel.position), inline=True)
        
        await self.send_log(channel.guild, "guild_channel_create", log_embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        log_embed = discord.Embed(
            title="Channel Updated",
            description=f"**Channel:** {after.mention} (`{after.name}`)\n**ID:** `{after.id}`",
            color=discord.Color.gold()
        )
        
        changed_items = []
        if before.name != after.name:
            changed_items.append(f"**Name:** `{before.name}` → `{after.name}`")
            
        if hasattr(before, 'position') and hasattr(after, 'position') and before.position != after.position:
            changed_items.append(f"**Position:** `{before.position}` → `{after.position}`")

        if hasattr(before, 'category') and hasattr(after, 'category') and before.category != after.category:
            before_cat = before.category.name if before.category else "None"
            after_cat = after.category.name if after.category else "None"
            if before_cat != after_cat: # Ensure actual change
                changed_items.append(f"**Category:** `{before_cat}` → `{after_cat}`")

        # Topic (TextChannel, ForumChannel, StageChannel)
        if hasattr(before, "topic") and hasattr(after, "topic") and before.topic != after.topic:
            before_topic_display = f"`{before.topic[:100]}...`" if before.topic and len(before.topic) > 100 else f"`{before.topic}`" if before.topic else "`None`"
            after_topic_display = f"`{after.topic[:100]}...`" if after.topic and len(after.topic) > 100 else f"`{after.topic}`" if after.topic else "`None`"
            changed_items.append(f"**Topic:** {before_topic_display} → {after_topic_display}")

        # Slowmode (TextChannel, Thread, ForumChannel, StageChannel)
        if hasattr(before, "slowmode_delay") and hasattr(after, "slowmode_delay") and before.slowmode_delay != after.slowmode_delay:
            changed_items.append(f"**Slowmode:** `{before.slowmode_delay}s` → `{after.slowmode_delay}s`")

        # NSFW (TextChannel, VoiceChannel, StageChannel, ForumChannel)
        if hasattr(before, "nsfw") and hasattr(after, "nsfw") and before.nsfw != after.nsfw:
            changed_items.append(f"**NSFW:** `{before.nsfw}` → `{after.nsfw}`")

        # Bitrate (VoiceChannel, StageChannel)
        if hasattr(before, "bitrate") and hasattr(after, "bitrate") and before.bitrate != after.bitrate:
             changed_items.append(f"**Bitrate:** `{before.bitrate // 1000}kbps` → `{after.bitrate // 1000}kbps`")

        # User limit (VoiceChannel, StageChannel)
        if hasattr(before, "user_limit") and hasattr(after, "user_limit") and before.user_limit != after.user_limit:
             changed_items.append(f"**User Limit:** `{before.user_limit if before.user_limit > 0 else 'Unlimited'}` → `{after.user_limit if after.user_limit > 0 else 'Unlimited'}`")
        
        # Permissions (very complex to show diff, usually logged by audit log if needed deeply)
        # For simplicity, we can note if permissions changed at a high level.
        if before.overwrites != after.overwrites:
            changed_items.append("**Permissions Overwrites:** Changed (see audit log for details)")

        if not changed_items:
            return  # No meaningful changes to log from our perspective
        
        log_embed.description += "\n\n**Changes:**\n" + "\n".join(changed_items)
            
        await self.send_log(after.guild, "guild_channel_update", log_embed)
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        log_embed = discord.Embed(
            title="Role Created",
            description=f"**Name:** {role.name} ({role.mention})\n**ID:** `{role.id}`",
            color=role.color if role.color != discord.Color.default() else discord.Color.light_grey()
        )
        
        log_embed.add_field(name="Color", value=str(role.color), inline=True)
        log_embed.add_field(name="Mentionable", value=str(role.mentionable), inline=True)
        log_embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
        log_embed.add_field(name="Position", value=str(role.position), inline=True)
        log_embed.add_field(name="Managed by Integration", value=str(role.managed), inline=True)
        log_embed.add_field(name="Bot Role", value=str(role.is_bot_managed()), inline=True)
        
        await self.send_log(role.guild, "guild_role_create", log_embed)
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        log_embed = discord.Embed(
            title="Role Deleted",
            description=f"**Name:** {role.name}\n**ID:** `{role.id}`",
            color=role.color if role.color != discord.Color.default() else discord.Color.dark_grey()
        )
        
        log_embed.add_field(name="Color", value=str(role.color), inline=True)
        log_embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
        log_embed.add_field(name="Position (at deletion)", value=str(role.position), inline=True) # Position before deletion
        log_embed.add_field(name="Created At", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        
        await self.send_log(role.guild, "guild_role_delete", log_embed)
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        log_embed = discord.Embed(
            title="Role Updated",
            description=f"**Role:** {after.name} ({after.mention})\n**ID:** `{after.id}`",
            color=after.color if after.color != discord.Color.default() else discord.Color.blue()
        )
        
        changes = []
        if before.name != after.name:
            changes.append(f"**Name:** `{before.name}` → `{after.name}`")
            
        if before.color != after.color:
            changes.append(f"**Color:** `{before.color}` → `{after.color}`")
            
        if before.mentionable != after.mentionable:
            changes.append(f"**Mentionable:** `{before.mentionable}` → `{after.mentionable}`")
            
        if before.hoist != after.hoist:
            changes.append(f"**Displayed Separately (Hoisted):** `{before.hoist}` → `{after.hoist}`")
        
        if before.position != after.position: # Position changes are common, might be noisy
             changes.append(f"**Position:** `{before.position}` → `{after.position}`")

        if before.permissions != after.permissions:
            # Simplified permission change logging
            changes.append(f"**Permissions:** Changed (see audit log for details)")
            # Detailed permission diff can be very long.
            # Example for detailed (can be verbose):
            # old_perms = dict(before.permissions)
            # new_perms = dict(after.permissions)
            # added = [p for p,v in new_perms.items() if v and not old_perms.get(p)]
            # removed = [p for p,v in old_perms.items() if v and not new_perms.get(p)]
            # if added: changes.append(f"**Perms Added:** {', '.join(p.replace('_', ' ').title() for p in added)}")
            # if removed: changes.append(f"**Perms Removed:** {', '.join(p.replace('_', ' ').title() for p in removed)}")

        if not changes:
            return # No logged changes
        
        log_embed.description += "\n\n**Changes:**\n" + "\n".join(changes)
            
        await self.send_log(after.guild, "guild_role_update", log_embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User | discord.Member):
        if user.bot:
            return
            
        message = reaction.message
        if not message.guild: # Only log guild reactions
            return
            
        log_embed = discord.Embed(
            title="Reaction Added",
            description=f"**User:** {user.mention} ({user})\n**Channel:** {message.channel.mention}\n**[Jump to Message]({message.jump_url})**",
            color=discord.Color.green()
        )
        
        emoji_display = str(reaction.emoji)
        if isinstance(reaction.emoji, discord.Emoji): # Custom emoji
            emoji_display = f"<:{reaction.emoji.name}:{reaction.emoji.id}> (`{reaction.emoji.name}`)"
        elif isinstance(reaction.emoji, discord.PartialEmoji):
             emoji_display = f"{reaction.emoji} (`{reaction.emoji.name if reaction.emoji.name else 'Partial'}`)"


        log_embed.add_field(name="Emoji", value=emoji_display, inline=True)
        log_embed.add_field(name="Message Author", value=f"{message.author.mention} ({message.author.id})", inline=True)
        
        content_display = message.content[:1000] if message.content else "[No text content]"
        if message.embeds:
            content_display += " (+ embeds)" # Indicate embeds are present
        if message.attachments:
            content_display += f" (+ {len(message.attachments)} attachment(s))"

        log_embed.add_field(name="Message Content Snippet", value=f"```\n{content_display}\n```", inline=False)
        
        await self.send_log(message.guild, "reaction_add", log_embed)
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User | discord.Member):
        if user.bot: # Usually reactions removed by bots are not important for logging this way
            return
            
        message = reaction.message
        if not message.guild:
            return
            
        log_embed = discord.Embed(
            title="Reaction Removed",
            description=f"**User:** {user.mention} ({user})\n**Channel:** {message.channel.mention}\n**[Jump to Message]({message.jump_url})**",
            color=discord.Color.gold() # Using gold for removed, can be orange or yellow too
        )
        
        emoji_display = str(reaction.emoji)
        if isinstance(reaction.emoji, discord.Emoji):
            emoji_display = f"<:{reaction.emoji.name}:{reaction.emoji.id}> (`{reaction.emoji.name}`)"
        elif isinstance(reaction.emoji, discord.PartialEmoji):
             emoji_display = f"{reaction.emoji} (`{reaction.emoji.name if reaction.emoji.name else 'Partial'}`)"

        log_embed.add_field(name="Emoji", value=emoji_display, inline=True)
        log_embed.add_field(name="Message Author", value=f"{message.author.mention} ({message.author.id})", inline=True)
        
        await self.send_log(message.guild, "reaction_remove", log_embed)

    @commands.Cog.listener()
    async def on_guild_ban_add(self, guild: discord.Guild, user: discord.User | discord.Member):
        log_embed = discord.Embed(
            title="Member Banned",
            description=f"**User:** {user.mention} ({user})\n**ID:** `{user.id}`",
            color=discord.Color.dark_red()
        )
        
        if user.display_avatar:
            log_embed.set_thumbnail(url=user.display_avatar.url)
        
        # Try to get audit log entry for more info (moderator and reason)
        # This requires 'View Audit Log' permission for the bot.
        moderator = "Unknown"
        reason = "No reason provided."
        try:
            # Iterate backwards from recent logs to find the ban entry for this user
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban).flatten():
                if entry.target and entry.target.id == user.id:
                    moderator = f"{entry.user.mention} ({entry.user})"
                    if entry.reason:
                        reason = entry.reason
                    break # Found the relevant entry
        except discord.Forbidden:
            moderator = "Unknown (Audit Log permission missing)"
            reason = "Unknown (Audit Log permission missing)"
        except discord.HTTPException:
            moderator = "Unknown (Error fetching Audit Log)" # Network or other HTTP error
        
        log_embed.add_field(name="Banned By", value=moderator, inline=False)
        log_embed.add_field(name="Reason", value=reason, inline=False)
        
        await self.send_log(guild, "guild_ban_add", log_embed)
    
    @commands.Cog.listener()
    async def on_guild_ban_remove(self, guild: discord.Guild, user: discord.User): # User is discord.User here
        log_embed = discord.Embed(
            title="Member Unbanned",
            description=f"**User:** {user.mention} ({user})\n**ID:** `{user.id}`",
            color=discord.Color.green() # Using green for unban
        )
        
        if user.display_avatar:
            log_embed.set_thumbnail(url=user.display_avatar.url)
        
        moderator = "Unknown"
        reason = "No reason provided." # Default if not found in audit log
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban).flatten():
                if entry.target and entry.target.id == user.id:
                    moderator = f"{entry.user.mention} ({entry.user})"
                    if entry.reason:
                        reason = entry.reason
                    break
        except discord.Forbidden:
            moderator = "Unknown (Audit Log permission missing)"
            reason = "Unknown (Audit Log permission missing)"
        except discord.HTTPException:
            moderator = "Unknown (Error fetching Audit Log)"

        log_embed.add_field(name="Unbanned By", value=moderator, inline=False)
        log_embed.add_field(name="Reason (if available)", value=reason, inline=False) # Clarify reason might not be from unban action itself
        
        await self.send_log(guild, "guild_ban_remove", log_embed)

def setup(bot: Bot): # Added type hint for bot
    bot.add_cog(Event(bot))