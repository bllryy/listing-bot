import discord
from discord.ext import commands, tasks
from discord import option, SlashCommandGroup
import re
from collections import defaultdict
import asyncio

from bot.bot import Bot
from bot.util.constants import is_authorized_to_use_bot
from bot.util.paginator import Paginator

class Customer(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        self.milestone_checker.start()

    def cog_unload(self):
        self.milestone_checker.cancel()

    customer = SlashCommandGroup("customer", description="Commands related to customers")
    milestone = customer.create_subgroup(name="milestone", description="Manage milestone roles")

    @customer.command(
        name="add",
        description="Give a customer the customer role"
    )
    @is_authorized_to_use_bot()
    @option(
        "user",
        "The user to give the customer role",
        type=discord.Member,
        required=True
    )
    @option(
        "amount",
        "The amount that the user bought for.",
        type=int,
        required=False
    )
    @option(
        "good",
        "The good that was sold",
        type=str,
        required=False,
        default="account"
    )
    async def customer_add(self, ctx: discord.ApplicationContext, user: discord.Member, amount: int = None, good: str = "account"):
        await ctx.defer()

        content = None
        vouch_channel_id = await self.bot.db.get_config("vouch_channel")
        if amount:
            content = f"## Thanks for your purchase at {ctx.guild.name}.\nWe ask you to please leave a review in <#{vouch_channel_id}>.\nThe review can be something like this: `+rep {ctx.author.mention} {amount}$ {good}`\n\nAlternatively, you can leave a vouch here, for it to appear as anonymous."

        role_id = await self.bot.db.get_config("customer_role")
        role = ctx.guild.get_role(role_id)
        if not role:
            embed = discord.Embed(
                title="Error",
                description="Customer role not found.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        await user.add_roles(role)
        embed = discord.Embed(
            title="Success",
            description=f"Added {user.mention} to the customer role!",
            color=discord.Color.green()
        )
        await ctx.respond(f'{user.mention}, check your dms or use the {self.bot.get_command_link("rep add")} command to vouch for the seller.', embed=embed)

        if content:
            await user.send(content)

    @customer.command(
        name="remove",
        description="Remove the customer role from a user"
    )
    @option(
        "user",
        "The user to remove the customer role from",
        type=discord.Member,
        required=True
    )
    @is_authorized_to_use_bot()
    async def customer_remove(self, ctx: discord.ApplicationContext, user: discord.Member):
        await ctx.defer()

        role_id = await self.bot.db.get_config("customer_role")
        role = ctx.guild.get_role(role_id)
        if not role:
            embed = discord.Embed(
                title="Error",
                description="Customer role not found.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        await user.remove_roles(role)
        embed = discord.Embed(
            title="Success",
            description=f"Removed the customer role from {user.mention}!",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @customer.command(
        name="leaderboard",
        description="View the top spending customers based on vouches"
    )
    async def customer_leaderboard(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        vouches = await self.bot.db.fetchall("SELECT user_id, message, username FROM vouches")
        
        if not vouches:
            embed = discord.Embed(
                title="Customer Leaderboard",
                description="No vouches found in the database.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        customer_stats = defaultdict(lambda: {'total_spent': 0, 'purchase_count': 0, 'name': None, 'username': None})
        pattern = re.compile(r'(\d+)\$|\$(\d+)|(\d+)\s?bucks')
        
        for user_id, message, username in vouches:
            matches = pattern.findall(message)
            amounts = [int(match) for group in matches for match in group if match and match.isdigit()]
            amount = max(amounts) if amounts else 0
            
            if amount > 0:
                customer_id = str(user_id)
                customer_stats[customer_id]['total_spent'] += amount
                customer_stats[customer_id]['purchase_count'] += 1
                customer_stats[customer_id]['username'] = username
        
        if not customer_stats:
            embed = discord.Embed(
                title="Customer Leaderboard",
                description="No valid customer spending data found in vouches.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        sorted_customers = sorted(
            customer_stats.items(),
            key=lambda x: (x[1]['total_spent'], x[1]['purchase_count']),
            reverse=True
        )
        
        top_customers = sorted_customers[:50]
        user_cache = {}
        
        if ctx.guild:
            for member in ctx.guild.members:
                user_cache[str(member.id)] = member.display_name
        
        for customer_id, stats in top_customers:
            if customer_id not in user_cache:
                try:
                    user = self.bot.get_user(int(customer_id))
                    if user:
                        user_cache[customer_id] = user.display_name
                    else:
                        user_cache[customer_id] = stats['username'] or f"User {customer_id}"
                except:
                    user_cache[customer_id] = stats['username'] or f"User {customer_id}"
        
        for customer_id, stats in customer_stats.items():
            stats['name'] = user_cache.get(customer_id, stats['username'] or f"User {customer_id}")

        if not customer_stats:
            embed = discord.Embed(
                title="Customer Leaderboard",
                description="No valid customer spending data found in vouches.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        sorted_customers = sorted(
            customer_stats.items(),
            key=lambda x: (x[1]['total_spent'], x[1]['purchase_count']),
            reverse=True
        )

        embeds = []
        customers_per_page = 10
        
        for page_start in range(0, len(sorted_customers), customers_per_page):
            page_customers = sorted_customers[page_start:page_start + customers_per_page]
            
            embed = discord.Embed(
                title="💸 Customer Spending Leaderboard",
                color=discord.Color.blue()
            )

            for rank, (user_id, stats) in enumerate(page_customers, start=page_start + 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**#{rank}**"
                embed.add_field(
                    name=f"{medal} {stats['name']}",
                    value=f"💰 ${stats['total_spent']:,} spent • 🛒 {stats['purchase_count']} purchases",
                    inline=True
                )

            embed.set_footer(text=f"Page {len(embeds) + 1} • Showing {page_start + 1}-{min(page_start + customers_per_page, len(sorted_customers))} of {len(sorted_customers)} customers")
            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.respond(embed=embeds[0])
        else:
            paginator = Paginator(embeds, timeout=300)
            message = await ctx.respond(embed=embeds[0], view=paginator)
            paginator.message = message

    @milestone.command(
        name="create",
        description="Create a milestone role for a specific spending amount"
    )
    @is_authorized_to_use_bot(strict=True)
    @option(
        "amount",
        "The spending amount required for this milestone",
        type=int,
        required=True
    )
    @option(
        "role",
        "The role to give when the milestone is reached",
        type=discord.Role,
        required=True
    )
    async def milestone_create(self, ctx: discord.ApplicationContext, amount: int, role: discord.Role):
        await ctx.defer()

        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="Amount must be greater than 0.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        config_key = f"milestone_role_{amount}"
        existing = await self.bot.db.get_config(config_key)
        
        if existing:
            embed = discord.Embed(
                title="Error",
                description=f"A milestone role already exists for ${amount:,}.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        await self.bot.db.set_config(config_key, str(role.id))
        
        embed = discord.Embed(
            title="Milestone Created",
            description=f"Created milestone: **${amount:,}** → {role.mention}",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @milestone.command(
        name="remove",
        description="Remove a milestone role"
    )
    @is_authorized_to_use_bot(strict=True)
    @option(
        "amount",
        "The spending amount of the milestone to remove",
        type=int,
        required=True
    )
    async def milestone_remove(self, ctx: discord.ApplicationContext, amount: int):
        await ctx.defer()

        config_key = f"milestone_role_{amount}"
        existing = await self.bot.db.get_config(config_key)
        
        if not existing:
            embed = discord.Embed(
                title="Error",
                description=f"No milestone role exists for ${amount:,}.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)

        await self.bot.db.delete_config(config_key)
        
        embed = discord.Embed(
            title="Milestone Removed",
            description=f"Removed milestone for **${amount:,}**.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @milestone.command(
        name="list",
        description="View all milestone roles"
    )
    async def milestone_list(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        all_configs = await self.bot.db.fetchall("SELECT key, value FROM config WHERE key LIKE 'milestone_role_%'")
        
        if not all_configs:
            embed = discord.Embed(
                title="Milestone Roles",
                description="No milestone roles have been configured.",
                color=discord.Color.blue()
            )
            return await ctx.respond(embed=embed)

        milestones = []
        for key, role_id in all_configs:
            try:
                amount = int(key.replace("milestone_role_", ""))
                role = ctx.guild.get_role(int(role_id))
                if role:
                    milestones.append((amount, role))
                else:
                    await self.bot.db.delete_config(key)
            except (ValueError, TypeError):
                continue

        if not milestones:
            embed = discord.Embed(
                title="Milestone Roles",
                description="No valid milestone roles found.",
                color=discord.Color.blue()
            )
            return await ctx.respond(embed=embed)

        milestones.sort(key=lambda x: x[0])

        embed = discord.Embed(
            title="💎 Milestone Roles",
            color=discord.Color.purple()
        )

        description = ""
        for amount, role in milestones:
            description += f"**${amount:,}** → {role.mention}\n"

        embed.description = description
        embed.set_footer(text=f"{len(milestones)} milestone(s) configured")
        await ctx.respond(embed=embed)

    @tasks.loop(minutes=1)
    async def milestone_checker(self):
        """Check and assign milestone roles every minute"""
        try:
            all_configs = await self.bot.db.fetchall("SELECT key, value FROM config WHERE key LIKE 'milestone_role_%'")
            if not all_configs:
                return

            milestones = []
            for key, role_id in all_configs:
                try:
                    amount = int(key.replace("milestone_role_", ""))
                    milestones.append((amount, int(role_id)))
                except (ValueError, TypeError):
                    continue

            if not milestones:
                return

            milestones.sort(key=lambda x: x[0], reverse=True)

            vouches = await self.bot.db.fetchall("SELECT user_id, message FROM vouches")
            customer_spending = defaultdict(int)
            pattern = re.compile(r'(\d+)\$|\$(\d+)|(\d+)\s?bucks')

            for user_id, message in vouches:
                matches = pattern.findall(message)
                amounts = [int(match) for group in matches for match in group if match and match.isdigit()]
                amount = max(amounts) if amounts else 0
                if amount > 0:
                    customer_spending[user_id] += amount

            for guild in self.bot.guilds:
                try:
                    for user_id, total_spent in customer_spending.items():
                        member = guild.get_member(user_id)
                        if not member:
                            continue

                        qualified_milestone = None
                        for amount, role_id in milestones:
                            if total_spent >= amount:
                                qualified_milestone = (amount, role_id)
                                break

                        if not qualified_milestone:
                            continue

                        milestone_amount, milestone_role_id = qualified_milestone
                        role = guild.get_role(milestone_role_id)
                        if not role:
                            continue

                        # Check if user already has this role
                        if role in member.roles:
                            continue

                        # Remove lower milestone roles and add the new one
                        roles_to_remove = []
                        for amount, role_id in milestones:
                            if amount < milestone_amount:
                                lower_role = guild.get_role(role_id)
                                if lower_role and lower_role in member.roles:
                                    roles_to_remove.append(lower_role)

                        try:
                            if roles_to_remove:
                                await member.remove_roles(*roles_to_remove, reason="Milestone upgrade")
                            await member.add_roles(role, reason=f"Reached ${milestone_amount:,} spending milestone")
                            
                            # Log the milestone achievement
                            print(f"Assigned milestone role {role.name} to {member.display_name} for spending ${milestone_amount:,}")
                        except discord.Forbidden:
                            continue
                        except discord.HTTPException:
                            continue

                except Exception as e:
                    print(f"Error processing milestones for guild {guild.name}: {e}")
                    continue

        except Exception as e:
            print(f"Error in milestone checker: {e}")

    @milestone_checker.before_loop
    async def before_milestone_checker(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Customer(bot))