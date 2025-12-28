import discord
from discord.ext import commands
from discord import SlashCommandGroup
from discord.ui import View, Select

from bot.util.constants import is_authorized_to_use_bot

from bot.bot import Bot

allowed_payment_methods = ['paypal', 'bitcoin', 'litecoin', 'ethereum', 'venmo', 'cashapp', 'zelle', 'paysafecard', 'google_pay', 'apple_pay', 'binance_pay', 'swap', 'bank_transfer', 'usdc', 'usdt', 'solana']

class Methods(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    methods = SlashCommandGroup("methods", description="Commands related to payment methods")

    @methods.command(
        name="set",
        description="Set your payment methods"
    )
    @is_authorized_to_use_bot()
    async def methods_set(self, ctx: discord.ApplicationContext):

        view = View(disable_on_timeout=True)
        select = Select(
            placeholder="Select your payment methods",
            options=[
                discord.SelectOption(label=method, value=method, emoji=self.bot.get_emoji(method.upper())) for method in allowed_payment_methods
            ],
            min_values=1,
            max_values=12
        )

        async def select_callback(interaction: discord.Interaction):
            payment_methods = '/'.join(select.values)
            data = await self.bot.db.fetchone("SELECT * FROM sellers WHERE user_id=?", ctx.author.id)
            if not data:
                await self.bot.db.execute("INSERT INTO sellers (user_id, payment_methods) VALUES (?, ?)", ctx.author.id, payment_methods)
            else:
                await self.bot.db.execute("UPDATE sellers SET payment_methods=? WHERE user_id=?", payment_methods, ctx.author.id)

            view.disable_all_items()
            await interaction.response.edit_message(view=view)

            embed = discord.Embed(
                title="Payment Methods Set",
                description="Payment methods set successfully",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        select.callback = select_callback
        view.add_item(select)

        await ctx.respond("Select your payment methods", view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(Methods(bot))