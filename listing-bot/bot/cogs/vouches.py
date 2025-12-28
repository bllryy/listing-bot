import discord
from discord.ext import commands
from discord import option, SlashCommandGroup
import re
from collections import defaultdict
from discord.ui import View, button

from bot.util.constants import is_customer
from bot.util.paginator import Paginator

from bot.bot import Bot

class VouchDeletionPaginator(View):
    def __init__(self, vouches_data, bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=300)
        self.vouches_data = vouches_data  # List of (rowid, user_id, message, avatar, username)
        self.bot = bot
        self.page = 0
        self.vouches_per_page = 5
        
        if len(vouches_data) <= self.vouches_per_page:
            self.disable_navigation()
    
    def disable_navigation(self):
        self.children[0].disabled = True  # Previous
        self.children[1].disabled = True  # Next
    
    def get_current_vouches(self):
        start = self.page * self.vouches_per_page
        end = start + self.vouches_per_page
        return self.vouches_data[start:end]
    
    def create_embed(self):
        current_vouches = self.get_current_vouches()
        
        embed = discord.Embed(
            title="📝 Vouches History",
            color=discord.Color.blue()
        )
        
        if not current_vouches:
            embed.description = "No vouches found."
            return embed
        
        description = ""
        for i, (rowid, user_id, message, avatar, username) in enumerate(current_vouches):
            vouch_num = (self.page * self.vouches_per_page) + i + 1
            
            # Extract amount from message
            pattern = r'(\d+)\$|\$(\d+)|(\d+)\s?bucks'
            matches = re.findall(pattern, message)
            amounts = [int(match) for group in matches for match in group if match and match.isdigit()]
            amount = max(amounts) if amounts else 0
            
            # Clean message (remove mentions and amounts at the end)
            clean_message = re.sub(r'\s*\(<@!?\d+>;\s*\$?\d+\$?\)\s*$', '', message)
            clean_message = clean_message[:100] + "..." if len(clean_message) > 100 else clean_message
            
            description += f"**#{vouch_num}** (ID: {rowid})\n"
            description += f"👤 **{username}** • 💰 **${amount}**\n"
            description += f"💬 *{clean_message}*\n\n"
        
        embed.description = description
        
        total_pages = (len(self.vouches_data) + self.vouches_per_page - 1) // self.vouches_per_page
        embed.set_footer(text=f"Page {self.page + 1}/{total_pages} • {len(self.vouches_data)} total vouches")
        
        return embed
    
    def update_button_states(self):
        total_pages = (len(self.vouches_data) + self.vouches_per_page - 1) // self.vouches_per_page
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page >= total_pages - 1
    
    @button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if self.page > 0:
            self.page -= 1
            self.update_button_states()
            embed = self.create_embed()
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
    
    @button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        
        total_pages = (len(self.vouches_data) + self.vouches_per_page - 1) // self.vouches_per_page
        if self.page < total_pages - 1:
            self.page += 1
            self.update_button_states()
            embed = self.create_embed()
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
    
    @button(label="🗑️ Delete Vouch", style=discord.ButtonStyle.danger, row=1)
    async def delete_vouch(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Show modal for vouch ID input
        modal = VouchDeletionModal(self)
        await interaction.response.send_modal(modal)
    
    async def delete_vouch_by_id(self, rowid: int, interaction: discord.Interaction):
        try:
            # Delete the vouch from database
            result = await self.bot.db.execute("DELETE FROM vouches WHERE rowid = ?", rowid)
            
            # Remove from local data
            self.vouches_data = [v for v in self.vouches_data if v[0] != rowid]
            
            # Adjust page if necessary
            total_pages = (len(self.vouches_data) + self.vouches_per_page - 1) // self.vouches_per_page
            if self.page >= total_pages and total_pages > 0:
                self.page = total_pages - 1
            elif len(self.vouches_data) == 0:
                self.page = 0
            
            self.update_button_states()
            
            embed = discord.Embed(
                title="✅ Vouch Deleted",
                description=f"Vouch with ID {rowid} has been deleted successfully.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Update the main message
            if len(self.vouches_data) == 0:
                embed = discord.Embed(
                    title="📝 Vouches History",
                    description="No vouches found.",
                    color=discord.Color.blue()
                )
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            else:
                embed = self.create_embed()
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to delete vouch: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class VouchDeletionModal(discord.ui.Modal):
    def __init__(self, paginator: VouchDeletionPaginator):
        super().__init__(title="Delete Vouch")
        self.paginator = paginator
        
        self.vouch_id = discord.ui.InputText(
            label="Vouch ID",
            placeholder="Enter the ID of the vouch to delete",
            required=True,
            max_length=10
        )
        self.add_item(self.vouch_id)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            rowid = int(self.vouch_id.value)
            
            # Check if the ID exists in current data
            vouch_exists = any(v[0] == rowid for v in self.paginator.vouches_data)
            
            if not vouch_exists:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Vouch with ID {rowid} not found.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            await self.paginator.delete_vouch_by_id(rowid, interaction)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Error",
                description="Please enter a valid number for the vouch ID.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class Vouches(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    def _extract_amount_from_message(self, message):
        """Extract dollar amount from vouch message"""
        if not message:
            return 0.0
        
        # Patterns to match: $50, 50$, 50 bucks, etc.
        patterns = [
            r'(\d+(?:\.\d{2})?)\$',  # 50$ or 50.99$
            r'\$(\d+(?:\.\d{2})?)',  # $50 or $50.99
            r'(\d+(?:\.\d{2})?)\s?(?:bucks?|dollars?)',  # 50 bucks, 50 dollars
            r'(\d+(?:\.\d{2})?)\s?(?:usd|USD)',  # 50 USD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return 0.0

    def _extract_mentioned_user_from_message(self, message):
        """Extract mentioned user ID from vouch message using regex"""
        if not message:
            return None
        
        # Look for Discord mention pattern: <@userid> or <@!userid>
        pattern = r'<@!?(\d+)>'
        match = re.search(pattern, message)
        
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        return None

    vouches = SlashCommandGroup("vouches", description="Commands related to vouches")
    rep = SlashCommandGroup("rep", description="Commands related to reputation")
    remove = vouches.create_subgroup(name="remove", description="Remove vouches from the database")

    @vouches.command(
        name="restore",
        description="Restore vouches from the database."
    )
    @commands.is_owner()
    @option(
        name="channel",
        description="The channel to restore vouches to.",
        type=discord.TextChannel,
        required=True
    )
    async def vouches_restore(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)

        webhooks = await channel.webhooks()
        if not webhooks:
            webhook = await channel.create_webhook(name="Vouches")
        else:
            webhook = webhooks[0]

        vouches = await self.bot.db.fetchall("SELECT * FROM vouches")

        embed = discord.Embed(
            title="Vouch Restoration in Progress",
            description=f"This may take a while. (0/{len(vouches)})",
            color=discord.Color.red()
        )

        response: discord.WebhookMessage = await ctx.respond(embed=embed, ephemeral=True)

        for i, vouch in enumerate(vouches):
            user_id, vouch_content, avatar, username = vouch

            try:
                await webhook.send(
                    content=vouch_content,
                    username=username,
                    avatar_url=avatar
                )
            except:
                pass


            if i % 4 == 0:
                embed.description = f"This may take a while. ({vouches.index(vouch)}/{len(vouches)})"
                await response.edit(embed=embed)

            elif i == len(vouches) - 1:
                embed.description = f"This may take a while. ({vouches.index(vouch)}/{len(vouches)})"
                await response.edit(embed=embed)

        embed.title = "Vouch Restoration Complete"
        embed.description = "Vouches have been restored successfully."
        embed.color = discord.Color.green()

        await ctx.respond(embed=embed, ephemeral=True)

    @vouches.command(
        name="global-leaderboard",
        description="Show global vouch leaderboard across all shops"
    )
    async def global_leaderboard(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        
        try:
            # Fetch vouches from all bots
            all_shop_data = await self._fetch_all_shop_vouches()
            
            if not all_shop_data:
                embed = discord.Embed(
                    title="🏆 Global Vouch Leaderboard",
                    description="No vouches found across any shops.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed)
            
            # Aggregate vouches by vouched-for users (mentioned in messages)
            seller_stats = defaultdict(lambda: {
                'total_vouches': 0,
                'total_amount': 0.0,
                'username': '',
                'avatar': '',
                'shops': set()
            })
            
            for shop_data in all_shop_data:
                shop_name = shop_data.get('shop_info', {}).get('shop_name', 'Unknown Shop')
                # Ensure shop_name is not None
                if shop_name is None:
                    shop_name = 'Unknown Shop'
                    
                for vouch in shop_data.get('vouches', []):
                    message = vouch.get('message', '')
                    amount = vouch.get('amount', 0.0)
                    
                    # Use the mentioned_user_id from API if available, otherwise extract from message
                    mentioned_user_id = vouch.get('mentioned_user_id')
                    if not mentioned_user_id:
                        mentioned_user_id = self._extract_mentioned_user_from_message(message)
                    
                    if mentioned_user_id:  # Only count vouches that mention someone
                        seller_stats[mentioned_user_id]['total_vouches'] += 1
                        seller_stats[mentioned_user_id]['total_amount'] += amount
                        # Try to get username from the bot if possible, otherwise use Unknown
                        try:
                            user = self.bot.get_user(mentioned_user_id)
                            if user:
                                seller_stats[mentioned_user_id]['username'] = user.display_name
                                seller_stats[mentioned_user_id]['avatar'] = str(user.avatar.url) if user.avatar else ''
                            else:
                                seller_stats[mentioned_user_id]['username'] = f'User {mentioned_user_id}'
                                seller_stats[mentioned_user_id]['avatar'] = ''
                        except:
                            seller_stats[mentioned_user_id]['username'] = f'User {mentioned_user_id}'
                            seller_stats[mentioned_user_id]['avatar'] = ''
                        seller_stats[mentioned_user_id]['shops'].add(shop_name)
            
            # Sort by total amount (then by total vouches as tiebreaker)
            sorted_sellers = sorted(
                seller_stats.items(),
                key=lambda x: (x[1]['total_amount'], x[1]['total_vouches']),
                reverse=True
            )
            
            # Create leaderboard embed
            embed = discord.Embed(
                title="🏆 Global Vouch Leaderboard",
                description="Top vouched sellers across all shops (sorted by total amount)",
                color=discord.Color.gold()
            )
            
            leaderboard_text = ""
            for i, (user_id, stats) in enumerate(sorted_sellers[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                username = stats['username']
                vouches = stats['total_vouches']
                amount = stats['total_amount']
                shops = [shop for shop in list(stats['shops']) if shop is not None]  # Filter out None values
                
                shop_list = ", ".join(shops[:2]) if shops else "Unknown Shop"  # Show first 2 shops
                if len(shops) > 2:
                    shop_list += f" +{len(shops)-2} more"
                
                leaderboard_text += f"{medal} **{username}**\n"
                leaderboard_text += f"   📊 {vouches} vouches • 💰 ${amount:.2f}\n"
                leaderboard_text += f"   🏪 {shop_list}\n\n"
            
            embed.description = leaderboard_text or "No sellers found."
            
            # Add footer with shop count
            shop_names = set()
            for shop in all_shop_data:
                shop_name = shop.get('shop_info', {}).get('shop_name')
                if shop_name is not None:
                    shop_names.add(shop_name)
            
            total_shops = len(shop_names)
            embed.set_footer(text=f"Data from {total_shops} shops • Updated now")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to fetch global leaderboard: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed)
    
    async def _fetch_all_shop_vouches(self):
        """Fetch vouches from all bots using the communication system"""
        try:
            # Get all available bots from ports
            ports = self.bot.communication.fetch_ports()
            all_shop_data = []
            
            for bot_name, port in ports.items():
                try:
                    # Request vouches from each bot
                    response = await self.bot.communication.request(
                        endpoint="vouches/all",
                        request_type="GET",
                        bots=[bot_name]
                    )
                    
                    if response and response.get('success'):
                        all_shop_data.append(response)
                        
                except Exception as e:
                    print(f"Failed to fetch vouches from {bot_name}: {e}")
                    continue
            
            return all_shop_data
            
        except Exception as e:
            print(f"Error fetching shop vouches: {e}")
            return []

    @vouches.command(
        name="leaderboard",
        description="Show local vouch leaderboard for this shop"
    )
    async def local_leaderboard(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        
        try:
            # Get all vouches from local database
            vouches = await self.bot.db.fetchall("SELECT user_id, message, username, avatar FROM vouches")
            
            if not vouches:
                embed = discord.Embed(
                    title="🏆 Local Vouch Leaderboard",
                    description="No vouches found in this shop.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed)
            
            # Aggregate vouches by vouched-for users (mentioned in messages)
            seller_stats = defaultdict(lambda: {
                'total_vouches': 0,
                'total_amount': 0.0,
                'username': '',
                'avatar': ''
            })
            
            for user_id, message, username, avatar in vouches:
                amount = self._extract_amount_from_message(message)
                
                # Extract the mentioned user ID (the person being vouched for)
                mentioned_user_id = self._extract_mentioned_user_from_message(message)
                
                if mentioned_user_id:  # Only count vouches that mention someone
                    seller_stats[mentioned_user_id]['total_vouches'] += 1
                    seller_stats[mentioned_user_id]['total_amount'] += amount
                    
                    # Try to get username from the bot if possible
                    try:
                        user = self.bot.get_user(mentioned_user_id)
                        if user:
                            seller_stats[mentioned_user_id]['username'] = user.display_name
                            seller_stats[mentioned_user_id]['avatar'] = str(user.avatar.url) if user.avatar else ''
                        else:
                            seller_stats[mentioned_user_id]['username'] = f'User {mentioned_user_id}'
                            seller_stats[mentioned_user_id]['avatar'] = ''
                    except:
                        seller_stats[mentioned_user_id]['username'] = f'User {mentioned_user_id}'
                        seller_stats[mentioned_user_id]['avatar'] = ''
            
            # Sort by total amount (then by total vouches as tiebreaker)
            sorted_sellers = sorted(
                seller_stats.items(),
                key=lambda x: (x[1]['total_amount'], x[1]['total_vouches']),
                reverse=True
            )
            
            # Create leaderboard embed
            shop_name = "This Shop"
            shop_info = await self.bot.db.fetchone("SELECT shop_name FROM sellauth_config LIMIT 1")
            if shop_info and shop_info[0]:
                shop_name = shop_info[0]
            
            embed = discord.Embed(
                title=f"🏆 {shop_name} Vouch Leaderboard",
                description="Top vouched sellers in this shop (sorted by total amount)",
                color=discord.Color.blue()
            )
            
            leaderboard_text = ""
            for i, (user_id, stats) in enumerate(sorted_sellers[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                username = stats['username']
                vouches = stats['total_vouches']
                amount = stats['total_amount']
                
                leaderboard_text += f"{medal} **{username}**\n"
                leaderboard_text += f"   📊 {vouches} vouches • 💰 ${amount:.2f}\n\n"
            
            embed.description = leaderboard_text or "No sellers found."
            embed.set_footer(text=f"Local shop data • Updated now")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to generate local leaderboard: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed)

    @vouches.command(
        name="import",
        description="Import vouches from a channel."
    )
    @commands.is_owner()
    @option(
        name="channel",
        description="The channel to import vouches from.",
        type=discord.TextChannel,
        required=True
    )
    async def vouches_import(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)

        vouches = await self.bot.db.fetchall("SELECT message FROM vouches")
        vouch_set = {v[0] for v in vouches}
        embed = discord.Embed(
            title="Vouch Import in Progress",
            description="This may take a while. (0 messages processed)",
            color=discord.Color.red()
        )
        response: discord.WebhookMessage = await ctx.respond(embed=embed, ephemeral=True)
        count = 0
        async for message in channel.history(limit=None):
            if message.content in vouch_set:
                continue
            
            await self.bot.db.execute(
                "INSERT INTO vouches (user_id, message, avatar, username) VALUES (?, ?, ?, ?)",
                message.author.id,
                message.content,
                str(message.author.display_avatar.url),
                message.author.name
            )
            count += 1

            if count % 10 == 0:
                embed.description = f"This may take a while. ({count} messages processed)"
                await response.edit(embed=embed)

    @remove.command(
        name="match",
        description="Remove vouches that include a text."
    )
    @commands.is_owner()
    @option(
        name="string",
        description="The string to match.",
        type=str,
        required=True
    )
    async def remove_match(self, ctx: discord.ApplicationContext, string: str):
        await ctx.defer(ephemeral=True)
        await self.bot.db.execute("DELETE FROM vouches WHERE message LIKE ?", f"%{string}%")

        embed = discord.Embed(
            title="Vouches Removed",
            description=f"Vouches that include `{string}` have been removed.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @rep.command(
        name="view",
        description="View vouches of a specific person"
    )
    @option(
        name="user",
        description="The user to view vouches of.",
        type=discord.User,
        required=True
    )
    async def view_vouches(self, ctx: discord.ApplicationContext, user: discord.User):
        await ctx.defer(ephemeral=True)

        embed = discord.Embed(
            title="Vouches Profile",
            description=f"{user.mention} ({user.name}) `{user.id}`",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

        vouches = await self.bot.db.fetchall("SELECT * FROM vouches WHERE message LIKE ?", f"%{user.id}%")

        if not vouches:
            embed.description += "\nNo vouches found for this user."
            return await ctx.respond(embed=embed, ephemeral=True)
        
        amount = 0
        for user_id, message, avatar, username in vouches:
            pattern = r'(\d+)\$|\$(\d+)|(\d+)\s?bucks'
            matches = re.findall(pattern, message)
            matches = [int(match) for group in matches for match in group if match and match.isdigit()]
            if matches:
                amount += max(matches)

        embed.description += f"\nhas **{len(vouches)}** vouches\nand dealt with **{amount}$**."
        embed.set_footer(text="Vouches are not moderated by the bot. Count and amount are based on available data.")

        await ctx.respond(embed=embed, ephemeral=True)

    @rep.command(
        name="history",
        description="View vouches from a specific user with management options"
    )
    @commands.has_permissions(manage_messages=True)
    @option(
        name="user",
        description="The user whose vouches to view",
        type=discord.User,
        required=True
    )
    async def vouch_history(self, ctx: discord.ApplicationContext, user: discord.User):
        await ctx.defer()

        # Fetch vouches with rowid for deletion functionality
        vouches = await self.bot.db.fetchall("SELECT rowid, user_id, message, avatar, username FROM vouches WHERE user_id = ?", user.id)

        if not vouches:
            embed = discord.Embed(
                title="📝 Vouches History",
                description=f"No vouches found from {user.mention}.",
                color=discord.Color.blue()
            )
            await ctx.respond(embed=embed)
            return

        # Create paginator with delete functionality
        paginator = VouchDeletionPaginator(vouches, self.bot)
        embed = paginator.create_embed()
        embed.title += f" - {user.display_name}"
        
        message = await ctx.respond(embed=embed, view=paginator)
        paginator.message = message

    @rep.command(
        name="leaderboard",
        description="View the top vouched sellers in the server"
    )
    async def vouch_leaderboard(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        vouches = await self.bot.db.fetchall("SELECT user_id, message FROM vouches")
        
        if not vouches:
            embed = discord.Embed(
                title="Vouch Leaderboard",
                description="No vouches found in the database.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        seller_stats = defaultdict(lambda: {'count': 0, 'total_amount': 0, 'name': None})
        mention_pattern = re.compile(r'<@!?(\d+)>')
        amount_pattern = re.compile(r'(\d+)\$|\$(\d+)|(\d+)\s?bucks')
        
        for user_id, message in vouches:
            mentioned_users = mention_pattern.findall(message)
            
            matches = amount_pattern.findall(message)
            amounts = [int(match) for group in matches for match in group if match and match.isdigit()]
            amount = max(amounts) if amounts else 0
            
            for mentioned_user_id in mentioned_users:
                seller_stats[mentioned_user_id]['count'] += 1
                seller_stats[mentioned_user_id]['total_amount'] += amount

        if not seller_stats:
            embed = discord.Embed(
                title="Vouch Leaderboard",
                description="No valid vouches with mentioned users found.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        sorted_sellers = sorted(
            seller_stats.items(),
            key=lambda x: (x[1]['total_amount'], x[1]['count']),
            reverse=True
        )
        
        seller_role_id = await self.bot.db.get_config("seller_role")
        seller_role = ctx.guild.get_role(seller_role_id) if seller_role_id else None
        
        filtered_sellers = []
        user_cache = {}
        
        if ctx.guild:
            for member in ctx.guild.members:
                if seller_role and seller_role in member.roles:
                    user_cache[str(member.id)] = member.display_name
            
            for seller_id, stats in sorted_sellers:
                if seller_id in user_cache:
                    filtered_sellers.append((seller_id, stats))
                else:
                    try:
                        user = self.bot.get_user(int(seller_id))
                        if user:
                            member = ctx.guild.get_member(user.id)
                            if member and seller_role and seller_role in member.roles:
                                user_cache[seller_id] = user.display_name
                                filtered_sellers.append((seller_id, stats))
                    except:
                        continue
        else:
            filtered_sellers = sorted_sellers[:50]
            for seller_id, stats in filtered_sellers:
                try:
                    user = self.bot.get_user(int(seller_id))
                    if user:
                        user_cache[seller_id] = user.display_name
                    else:
                        user_cache[seller_id] = f"User {seller_id}"
                except:
                    user_cache[seller_id] = f"User {seller_id}"
        
        for seller_id, stats in filtered_sellers:
            stats['name'] = user_cache.get(seller_id, f"User {seller_id}")
        
        if not filtered_sellers:
            embed = discord.Embed(
                title="Vouch Leaderboard",
                description="No sellers with vouches found." + (f" (Only showing users with {seller_role.mention} role)" if seller_role else ""),
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        embeds = []
        sellers_per_page = 10
        
        for page_start in range(0, len(filtered_sellers), sellers_per_page):
            page_sellers = filtered_sellers[page_start:page_start + sellers_per_page]
            
            embed = discord.Embed(
                title="🏆 Vouch Leaderboard",
                color=discord.Color.gold()
            )
            
            for rank, (user_id, stats) in enumerate(page_sellers, start=page_start + 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**#{rank}**"
                embed.add_field(
                    name=f"{medal} {stats['name']}",
                    value=f"💰 ${stats['total_amount']:,} • 📝 {stats['count']} vouches",
                    inline=True
                )

            footer_text = f"Page {len(embeds) + 1} • Showing {page_start + 1}-{min(page_start + sellers_per_page, len(filtered_sellers))} of {len(filtered_sellers)} sellers"
            if seller_role:
                footer_text += f" (Only {seller_role.name}s shown)"
            embed.set_footer(text=footer_text)
            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            paginator = Paginator(embeds, timeout=300)
            message = await ctx.respond(embed=embeds[0], view=paginator)
            paginator.message = message

    @rep.command(
        name="add",
        description="Add a vouch for a user."
    )
    @option(
        name="user",
        description="The user to vouch for.",
        type=discord.User,
        required=True
    )
    @option(
        name="message",
        description="The vouch message.",
        type=str,
        required=True
    )
    @option(
        name="amount",
        description="The amount of money involved in the vouch. (in usd)",
        type=int,
        required=True,
    )
    @is_customer()
    async def add_vouch(self, ctx: discord.ApplicationContext, user: discord.User, message: str, amount: int):
        await ctx.defer(ephemeral=True)
        if amount < 0:
            return await ctx.respond("Amount must be a positive number.", ephemeral=True)
        
        query = f"INSERT INTO vouches (user_id, message, avatar, username) VALUES (?, ?, ?, ?)"
        await self.bot.db.execute(
            query,
            ctx.author.id,
            f"{message} ({user.mention}; {amount}$)",
            str(ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url),
            ctx.author.name
        )
        embed = discord.Embed(
            title="Vouch Added",
            description=f"Vouch for {user.mention} has been added successfully.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="Message", value=message, inline=False)
        embed.add_field(name="Amount", value=f"{amount}$", inline=False)
        embed.set_footer(text=f"Vouched by {ctx.author.name} ({ctx.author.id})", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        vouch_channel = await self.bot.db.get_config("vouch_channel")
        if vouch_channel:
            channel = self.bot.get_channel(vouch_channel)
            if channel:
                await channel.send(embed=embed)

        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Vouches(bot))