import discord
from discord.ext import commands
from discord import SlashCommandGroup, option

from bot.util.constants import is_authorized_to_use_bot
from bot.util.views import TermsView

from bot.bot import Bot


class Terms(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    terms = SlashCommandGroup("terms", description="Commands related to terms of service")

    @terms.command(
        name="edit",
        description="Edit the terms of service"
    )
    @is_authorized_to_use_bot(strict=True)
    async def terms_edit(self, ctx: discord.ApplicationContext):

        async def modal_callback(interaction: discord.Interaction):
            await self.bot.db.update_config("terms_of_service", modal.children[0].value)
            await self.bot.db.execute("DELETE FROM tos_agreed")

            await interaction.response.send_message("Terms of service updated. Previous acceptence records have been deleted due to new terms of service.", ephemeral=True)

        modal = discord.ui.Modal(
            discord.ui.InputText(
                label="Terms of Service",
                style=discord.InputTextStyle.long,
                placeholder="Enter the new terms of service here...",
            ),
            title="Edit Terms of Service",
        )

        modal.callback = modal_callback

        await ctx.send_modal(modal)

    @terms.command(
        name="view",
        description="View the current terms of service"
    )
    async def terms_view(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        terms = await self.bot.db.get_config("terms_of_service")
        if not terms:
            embed = discord.Embed(
                title="Terms of Service",
                description="No terms of service set.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="Terms of Service",
                description=terms,
                color=discord.Color.green()
            )
            embed.set_footer(text="Click the button below to accept the terms of service.")

        await ctx.respond(embed=embed, view=TermsView(self.bot), ephemeral=True)

def setup(bot):
    bot.add_cog(Terms(bot))