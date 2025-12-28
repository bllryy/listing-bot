from discord.ui import View, button
import discord

class Paginator(View):
    def __init__(self, embeds, *args, **kwargs):
        super().__init__(*args, **kwargs, disable_on_timeout=True)

        self.embeds = embeds
        self.page = 0

        if len(embeds) == 1:
            self.disable_buttons()

    def disable_buttons(self):
        self.children[0].disabled = True
        self.children[1].disabled = True

    async def create_embed(self):
        return self.embeds[self.page]

    async def handle_interaction(self, interaction, increment):
        await interaction.response.defer()

        self.page += increment
        self.update_button_states()

        embed = await self.create_embed()
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)

    def update_button_states(self):
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page == len(self.embeds) - 1

    @button(label="<", style=discord.ButtonStyle.blurple, row=1, disabled=True)
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.handle_interaction(interaction, -1)

    @button(label=">", style=discord.ButtonStyle.blurple, row=1)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.handle_interaction(interaction, 1)

    async def on_timeout(self):
        self.disable_buttons()
        await self.message.edit(view=self)
        await super().on_timeout()
