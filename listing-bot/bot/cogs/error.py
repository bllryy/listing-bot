import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from discord.ui import View, Button, Modal, InputText
from bot.bot import Bot
import json

class ErrorModal(Modal):
    def __init__(self):
        super().__init__(title="Error Testing Modal")
        
        self.add_item(InputText(
            label="Enter anything to trigger an error",
            placeholder="This will cause an intentional error...",
            required=True
        ))
    
    async def callback(self, interaction: discord.Interaction):
        # Intentionally cause different types of errors
        error_type = self.children[0].value.lower()
        
        if "valueerror" in error_type:
            raise ValueError("This is an intentional ValueError from the modal!")
        elif "typeerror" in error_type:
            raise TypeError("This is an intentional TypeError from the modal!")
        elif "keyerror" in error_type:
            raise KeyError("This is an intentional KeyError from the modal!")
        elif "indexerror" in error_type:
            test_list = [1, 2, 3]
            return test_list[10]  # This will raise IndexError
        elif "attributeerror" in error_type:
            none_obj = None
            return none_obj.some_attribute  # This will raise AttributeError
        else:
            # Default error
            raise RuntimeError(f"Modal error triggered with input: {self.children[0].value}")

class ErrorButton(View):
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(
        label="Launch Error Modal", 
        style=discord.ButtonStyle.danger,
        emoji="💥"
    )
    async def error_modal_button(self, button: Button, interaction: discord.Interaction):
        modal = ErrorModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="Direct Button Error", 
        style=discord.ButtonStyle.red,
        emoji="⚠️"
    )
    async def direct_error_button(self, button: Button, interaction: discord.Interaction):
        # This button causes an immediate error
        raise Exception("This is a direct button error for testing!")

class Error(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(
        name="error",
        description="Intentionally throws an error for testing purposes"
    )
    @option(
        name="error_type",
        description="Type of error to test",
        type=str,
        choices=["command", "button_modal", "both"],
        default="command"
    )
    async def error_command(self, ctx: discord.ApplicationContext, error_type: str):
        if error_type == "command":
            raise ValueError("This is a test error from the slash command.")
        
        elif error_type == "button_modal":
            embed = discord.Embed(
                title="🧪 Error Testing Interface",
                description="Use the buttons below to test different error scenarios:\n\n"
                           "🔹 **Error Modal**: Opens a modal where you can trigger specific errors\n"
                           "🔹 **Direct Error**: Immediately triggers a button error\n\n"
                           "**Modal Error Types:**\n"
                           "• Type `valueerror` for ValueError\n"
                           "• Type `typeerror` for TypeError\n"
                           "• Type `keyerror` for KeyError\n"
                           "• Type `indexerror` for IndexError\n"
                           "• Type `attributeerror` for AttributeError\n"
                           "• Type anything else for RuntimeError",
                color=discord.Color.red()
            )
            
            view = ErrorButton()
            await ctx.respond(embed=embed, view=view)
        
        elif error_type == "both":
            embed = discord.Embed(
                title="🧪 Error Testing Interface",
                description="This command will error AND provide buttons for more errors!",
                color=discord.Color.red()
            )
            
            view = ErrorButton()
            await ctx.respond(embed=embed, view=view)
            
            # Now cause the command error
            raise RuntimeError("This is a command error that happens after sending the view!")

def setup(bot: Bot):
    bot.add_cog(Error(bot))