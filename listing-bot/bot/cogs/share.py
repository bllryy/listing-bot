import discord
from discord.ext import commands
from discord import SlashCommandGroup, option

from bot.util.constants import is_authorized_to_use_bot

from bot.bot import Bot


class Share(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    share = SlashCommandGroup("share", description="Commands related to profit sharing")
    view = share.create_subgroup("view", "Commands related to viewing profit sharing information")
    transaction = SlashCommandGroup("transaction", description="Commands related to transactions")

    @transaction.command(
        name="log",
        description="Log a transaction"
    )
    @is_authorized_to_use_bot()
    @option(
        name="amount",
        description="The amount of the transaction",
        type=int,
    )
    async def transaction_log(self, ctx:discord.ApplicationContext, amount:int):
        await ctx.defer(ephemeral=True)

        share_percentage = await self.bot.db.get_config("share_percentage")
        if not share_percentage:
            embed = discord.Embed(
                title="Error",
                description="Share percentage not set.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        share_percentage = share_percentage / 100
        share_amount = amount * share_percentage

        await self.bot.db.execute("INSERT INTO transactions (user_id, amount, rate) VALUES (?, ?, ?)", ctx.author.id, amount, str(share_percentage))

        embed = discord.Embed(
            title="Transaction Logged",
            description=f"Transaction of {amount} logged. You owe an extra {share_amount}.",
            color=discord.Color.green()
        )

        await ctx.respond(embed=embed)

    @transaction.command(
        name="force-log",
        description="Force log a transaction"
    )
    @is_authorized_to_use_bot(strict=True)
    @option(
        name="amount",
        description="The amount of the transaction",
        type=int,
    )
    @option(
        name="user",
        description="The user to log the transaction for",
        type=discord.Member,
    )
    async def transaction_force_log(self, ctx:discord.ApplicationContext, amount:int, user:discord.Member):
        await ctx.defer(ephemeral=True)

        share_percentage = await self.bot.db.get_config("share_percentage")
        if not share_percentage:
            embed = discord.Embed(
                title="Error",
                description="Share percentage not set.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed)
        
        share_percentage = share_percentage / 100
        share_amount = amount * share_percentage

        await self.bot.db.execute("INSERT INTO transactions (user_id, amount, rate) VALUES (?, ?, ?)", user.id, amount, str(share_percentage))

        embed = discord.Embed(
            title="Transaction Logged",
            description=f"Transaction of {amount} logged for {user.mention}. They owe an extra {share_amount}.",
            color=discord.Color.green()
        )

        await ctx.respond(embed=embed)

    @view.command(
        name="transactions",
        description="View transactions"
    )
    @is_authorized_to_use_bot()
    async def view_transactions(self, ctx:discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        transactions = await self.bot.db.fetchall("SELECT * FROM transactions")
        users = {}
        for transaction in transactions:
            user_id, amount, rate = transaction
            if user_id not in users:
                users[user_id] = 0

            rate = float(rate)
            share_amount = amount * rate
            users[user_id] += share_amount

        embed = discord.Embed(
            title="Transactions",
            description="Transactions logged",
            color=discord.Color.green()
        )
        for user_id, share_amount in users.items():
            user = await self.bot.get_or_fetch_user(user_id)
            if not user:
                embed.add_field(name="Unknown User", value=f"Owes {share_amount}$")
                continue

            embed.add_field(name=user.display_name, value=f"Owes {share_amount}$")

        await ctx.respond(embed=embed)

    @transaction.command(
        name="clear",
        description="Clear transactions for a user"
    )
    @is_authorized_to_use_bot(strict=True)
    @option(
        name="user",
        description="The user to clear transactions for",
        type=discord.Member,
    )
    async def transaction_clear(self, ctx:discord.ApplicationContext, user:discord.Member):
        await ctx.defer(ephemeral=True)

        await self.bot.db.execute("DELETE FROM transactions WHERE user_id=?", user.id)

        embed = discord.Embed(
            title="Transactions Cleared",
            description=f"Transactions cleared for {user.mention}.",
            color=discord.Color.green()
        )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Share(bot))