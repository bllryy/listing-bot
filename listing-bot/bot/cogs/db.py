import discord
from discord.ext import commands
from discord import SlashCommandGroup
from bot.bot import Bot

from bot.util.constants import is_authorized_to_use_bot

class DB(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    _db = SlashCommandGroup("db", description="Database related commands")

    @_db.command(
        name="fix",
        description="Fixes the database by removing invalid entries (channels that don't exist)."
    )
    @is_authorized_to_use_bot()
    async def fix_db(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        fixed_count = 0
        total_checked = 0
        
        try:
            tables_to_check = [
                ("accounts", "channel_id", "message_id"),
                ("profiles", "channel_id", "message_id"), 
                ("alts", "channel_id", "message_id"),
                ("tickets", "channel_id", "initial_message_id")
            ]
            
            for table_name, channel_col, message_col in tables_to_check:
                entries = await self.bot.db.fetchall(f"SELECT rowid, {channel_col}, {message_col} FROM {table_name} WHERE {channel_col} IS NOT NULL")
                
                entries_to_delete = []
                
                for entry in entries:
                    total_checked += 1
                    rowid, channel_id, message_id = entry
                    
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        entries_to_delete.append(rowid)
                        fixed_count += 1
                        continue
                        
                    if message_id:
                        try:
                            message = await channel.fetch_message(message_id)
                            if not message:
                                entries_to_delete.append(rowid)
                                fixed_count += 1
                        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                            entries_to_delete.append(rowid)
                            fixed_count += 1
                
                if entries_to_delete:
                    placeholders = ",".join("?" * len(entries_to_delete))
                    await self.bot.db.execute(f"DELETE FROM {table_name} WHERE rowid IN ({placeholders})", *entries_to_delete)
            
            custom_mappings = await self.bot.db.fetchall("SELECT rowid, message_id, category_id FROM custom_mappings")
            mappings_to_delete = []
            
            for mapping in custom_mappings:
                total_checked += 1
                rowid, message_id, category_id = mapping
                
                message_found = False
                if message_id:
                    for guild in self.bot.guilds:
                        try:
                            for channel in guild.text_channels:
                                try:
                                    message = await channel.fetch_message(message_id)
                                    if message:
                                        message_found = True
                                        break
                                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                                    continue
                            if message_found:
                                break
                        except Exception:
                            continue
                
                category_exists = False
                if category_id:
                    category = self.bot.get_channel(category_id)
                    if category and isinstance(category, discord.CategoryChannel):
                        category_exists = True
                
                if not message_found and not category_exists:
                    mappings_to_delete.append(rowid)
                    fixed_count += 1
            
            if mappings_to_delete:
                placeholders = ",".join("?" * len(mappings_to_delete))
                await self.bot.db.execute(f"DELETE FROM custom_mappings WHERE rowid IN ({placeholders})", *mappings_to_delete)
            
            roles_entries = await self.bot.db.fetchall("SELECT rowid, role_id FROM roles WHERE role_id IS NOT NULL")
            roles_to_delete = []
            
            for role_entry in roles_entries:
                total_checked += 1
                rowid, role_id = role_entry
                
                role_exists = False
                for guild in self.bot.guilds:
                    role = guild.get_role(role_id)
                    if role:
                        role_exists = True
                        break
                
                if not role_exists:
                    roles_to_delete.append(rowid)
                    fixed_count += 1
            
            if roles_to_delete:
                placeholders = ",".join("?" * len(roles_to_delete))
                await self.bot.db.execute(f"DELETE FROM roles WHERE rowid IN ({placeholders})", *roles_to_delete)
            
            ticket_roles = await self.bot.db.fetchall("SELECT rowid, role_id FROM ticket_roles WHERE role_id IS NOT NULL")
            ticket_roles_to_delete = []
            
            for ticket_role in ticket_roles:
                total_checked += 1
                rowid, role_id = ticket_role
                
                role_exists = False
                for guild in self.bot.guilds:
                    role = guild.get_role(role_id)
                    if role:
                        role_exists = True
                        break
                
                if not role_exists:
                    ticket_roles_to_delete.append(rowid)
                    fixed_count += 1
            
            if ticket_roles_to_delete:
                placeholders = ",".join("?" * len(ticket_roles_to_delete))
                await self.bot.db.execute(f"DELETE FROM ticket_roles WHERE rowid IN ({placeholders})", *ticket_roles_to_delete)
            
            embed = discord.Embed(
                title="Database Fix Complete",
                description=f"✅ **Fixed {fixed_count} invalid entries** out of {total_checked} checked.\n\n"
                            f"**Tables cleaned:**\n"
                            f"• Accounts, Profiles, Alts (invalid channels/messages)\n"
                            f"• Tickets (invalid channels/messages)\n" 
                            f"• Custom Mappings (invalid messages/categories)\n"
                            f"• Roles & Ticket Roles (invalid role IDs)",
                color=discord.Color.green()
            )
            
            if fixed_count > 0:
                embed.add_field(
                    name="Actions Taken",
                    value="Removed entries where:\n"
                            "• Channels no longer exist\n"
                            "• Messages no longer exist\n"
                            "• Roles no longer exist\n"
                            "• Categories no longer exist",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Result",
                    value="No invalid entries found! Database is clean.",
                    inline=False
                )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="Database Fix Error",
                description=f"❌ An error occurred while fixing the database:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await ctx.respond(embed=error_embed)

def setup(bot: Bot):
    bot.add_cog(DB(bot))