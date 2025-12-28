import discord
from discord.ext import commands
import ai
from bot.bot import Bot
from discord import SlashCommandGroup
from bot.util.constants import is_authorized_to_use_bot

class AICog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    ai = SlashCommandGroup("ai", description="Commands related to AI features")

    @ai.command(
        name="edit",
        description="Edit the server description used for the AI agent."
    )
    @is_authorized_to_use_bot(strict=True)
    async def ai_desc_edit(self, ctx: discord.ApplicationContext):

        async def modal_callback(interaction: discord.Interaction):
            await self.bot.db.update_config("ai_info", modal.children[0].value)
            await interaction.response.send_message("Server info updated.", ephemeral=True)

        modal = discord.ui.Modal(
            discord.ui.InputText(
                label="Server Description",
                style=discord.InputTextStyle.long,
                placeholder="Enter a new description of the server here...",
            ),
            title="Edit Server Description",
        )

        modal.callback = modal_callback

        await ctx.send_modal(modal)


def setup(bot: Bot):
    bot.add_cog(AICog(bot))
