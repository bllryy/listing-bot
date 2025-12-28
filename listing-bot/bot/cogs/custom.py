import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from bot.util.views import CustomView
import base64
import ujson
from discord.ui import Button, View, Modal

from bot.bot import Bot

class Custom(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    custom = SlashCommandGroup("custom", description="Custom panel management commands")
    panel = custom.create_subgroup("panel", "Custom panel commands")
    button = custom.create_subgroup("button", "Custom button commands")
    input = custom.create_subgroup("input", "Custom input commands")

    @panel.command(
        name="create",
        description="Create a new custom panel"
    )
    @option("name", description="Name of the panel", type=str)
    @option("embed_title", description="Title of the embed", type=str)
    @option("embed_color", description="Color of the embed (hex code)", type=str, required=False, default="FF0000")
    async def create_panel(self, ctx: discord.ApplicationContext, 
                        name: str, embed_title: str, 
                        embed_color: str = "FF0000"):
        
        chars = ("0123456789abcdef")
        if len(embed_color) != 6 or any(c not in chars for c in embed_color.lower()):
            embed = discord.Embed(
                title="Error",
                description="Embed color must be a valid 6-digit hex code (e.g., FF0000 for red).",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        modal = Modal(
            discord.ui.InputText(
                label="Embed Description",
                placeholder="Enter the embed description",
                style=discord.InputTextStyle.long
            ),
            title="Create Custom Panel"
        )
        async def modal_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            embed_description = modal.children[0].value

            existing = await self.bot.db.fetchone("SELECT * FROM panels WHERE name=?", name)
            if existing:
                embed = discord.Embed(
                    title="Error",
                    description=f"A panel with name '{name}' already exists.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            panel_data = {
                "buttons": [],
                "modals": [],
                "embed": {
                    "title": embed_title,
                    "description": embed_description,
                    "color": embed_color.lstrip('#')
                }
            }
            
            encoded_data = base64.b64encode(ujson.dumps(panel_data).encode()).decode()
            await self.bot.db.execute(
                "INSERT INTO panels (name, embed_text, data) VALUES (?, ?, ?)",
                name, f"{embed_title}\n{embed_description}", encoded_data
            )
            
            embed = discord.Embed(
                title="Panel Created",
                description=f"Panel '{name}' created successfully! Use `/custom button add {name}` to add buttons.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed, ephemeral=True)

        modal.callback = modal_callback
        await ctx.send_modal(modal)
        
    @panel.command(
        name="delete",
        description="Delete a custom panel"
    )
    @option("name", description="Name of the panel to delete", type=str)
    async def delete_panel(self, ctx: discord.ApplicationContext, name: str):
        await ctx.defer(ephemeral=True)
        
        existing = await self.bot.db.fetchone("SELECT * FROM panels WHERE name=?", name)
        if not existing:
            embed = discord.Embed(
                title="Error",
                description=f"No panel found with name '{name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        await self.bot.db.execute("DELETE FROM panels WHERE name=?", name)
        embed = discord.Embed(
            title="Panel Deleted",
            description=f"Panel '{name}' deleted successfully!",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @panel.command(
        name="list",
        description="List all custom panels"
    )
    async def list_panels(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        panels = await self.bot.db.fetchall("SELECT name, embed_text FROM panels")
        
        if not panels:
            embed = discord.Embed(
                title="No Panels Found",
                description="There are no custom panels available.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        embed = discord.Embed(title="Custom Panels", color=discord.Color.blue())
        
        for i, (name, embed_text) in enumerate(panels, 1):
            preview = embed_text[:100] + "..." if len(embed_text) > 100 else embed_text
            embed.add_field(name=f"{i}. {name}", value=preview, inline=False)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @panel.command(
        name="post",
        description="Post a panel to a channel"
    )
    @option("panel_name", description="Name of the panel", type=str)
    @option("channel", description="Channel to post to", type=discord.TextChannel)
    @option("category", description="Category for created tickets", type=discord.CategoryChannel)
    @option("role", description="Role to mention in tickets", type=discord.Role)
    @option("ticket_type", description="Type of the ticket (e.g., support, sales, etc.)", type=str)
    async def post_panel(self, ctx: discord.ApplicationContext, 
                        panel_name: str, channel: discord.TextChannel, 
                        category: discord.CategoryChannel, role: discord.Role,
                        ticket_type: str):
        await ctx.defer(ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            embed = discord.Embed(
                title="Error",
                description=f"No panel found with name '{panel_name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        encoded_data = panel[0]
        panel_data = ujson.loads(base64.b64decode(encoded_data).decode())
        
        if not panel_data["buttons"]:
            embed = discord.Embed(
                title="Error",
                description=f"Panel '{panel_name}' has no buttons. Add at least one button before posting.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        embed_data = panel_data.get("embed", {})
        embed = discord.Embed(
            title=embed_data.get("title", "Custom Panel"),
            description=embed_data.get("description", "Click a button below"),
            color=int(embed_data.get("color", "FF0000"), 16)
        )
        
        view = CustomView(self.bot, encoded_data)
        message = await channel.send(embed=embed, view=view)
        
        ticket_name = f"ticket-{ticket_type}"
        await self.bot.db.execute(
            "INSERT INTO custom_mappings (message_id, category_id, role_id, name) VALUES (?, ?, ?, ?)",
            message.id, category.id, role.id, ticket_name
        )
        
        embed = discord.Embed(
            title="Panel Posted",
            description=f"Panel '{panel_name}' posted to {channel.mention} with ticket type '{ticket_type}'.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)
    
    @button.command(
        name="add",
        description="Add a button to a panel"
    )
    @option("panel_name", description="Name of the panel", type=str)
    @option("label", description="Button label", type=str)
    @option("style", description="Button style", 
            choices=["blurple", "grey", "green", "red"], 
            type=str)
    @option("modal_title", description="Title for the modal", type=str)
    async def add_button(self, ctx: discord.ApplicationContext, 
                        panel_name: str, label: str, 
                        style: str, modal_title: str):
        await ctx.defer(ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            embed = discord.Embed(
                title="Error",
                description=f"No panel found with name '{panel_name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel_data = ujson.loads(base64.b64decode(panel[0]).decode())
        
        if len(panel_data["buttons"]) >= 5:
            embed = discord.Embed(
                title="Error",
                description="This panel already has the maximum of 5 buttons.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        style_map = {
            "blurple": "primary",
            "grey": "secondary",
            "green": "success",
            "red": "danger"
        }
        
        panel_data["buttons"].append({
            "label": label,
            "style": style_map[style]
        })
        
        panel_data["modals"].append({
            "title": modal_title,
            "components": []
        })
        
        encoded_data = base64.b64encode(ujson.dumps(panel_data).encode()).decode()
        await self.bot.db.execute("UPDATE panels SET data=? WHERE name=?", encoded_data, panel_name)
        
        embed = discord.Embed(
            title="Button Added",
            description=f"Button '{label}' added to panel '{panel_name}'.\n"
                        f"Use `/custom input add` to add inputs to this button's modal.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @button.command(
        name="remove",
        description="Remove a button from a panel"
    )
    @option("panel_name", description="Name of the panel", type=str)
    @option("button_index", description="Index of the button (1-5)", type=int)
    async def remove_button(self, ctx: discord.ApplicationContext, panel_name: str, button_index: int):
        await ctx.defer(ephemeral=True)
        
        if button_index < 1 or button_index > 5:
            embed = discord.Embed(
                title="Error",
                description="Button index must be between 1 and 5.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            embed = discord.Embed(
                title="Error",
                description=f"No panel found with name '{panel_name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel_data = ujson.loads(base64.b64decode(panel[0]).decode())
        
        if len(panel_data["buttons"]) < button_index:
            embed = discord.Embed(
                title="Error",
                description=f"This panel only has {len(panel_data['buttons'])} buttons.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        removed_button = panel_data["buttons"].pop(button_index - 1)
        panel_data["modals"].pop(button_index - 1)
        
        encoded_data = base64.b64encode(ujson.dumps(panel_data).encode()).decode()
        await self.bot.db.execute("UPDATE panels SET data=? WHERE name=?", encoded_data, panel_name)
        
        embed = discord.Embed(
            title="Button Removed",
            description=f"Button '{removed_button['label']}' removed from panel '{panel_name}'.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @input.command(
        name="add",
        description="Add an input field to a button's modal"
    )
    @option("panel_name", description="Name of the panel", type=str)
    @option("button_index", description="Index of the button (1-5)", type=int)
    @option("label", description="Input field label", type=str)
    @option("placeholder", description="Input field placeholder", type=str)
    @option("length", description="Input field length", choices=["short", "long"], type=str)
    @option("required", description="Is this input required?", type=bool, default=True)
    async def add_input(self, ctx: discord.ApplicationContext, 
                        panel_name: str, button_index: int, 
                        label: str, placeholder: str, 
                        length: str, required: bool = True):
        await ctx.defer(ephemeral=True)
        
        if button_index < 1 or button_index > 5:
            embed = discord.Embed(
                title="Error",
                description="Button index must be between 1 and 5.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            embed = discord.Embed(
                title="Error",
                description=f"No panel found with name '{panel_name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel_data = ujson.loads(base64.b64decode(panel[0]).decode())
        
        if len(panel_data["buttons"]) < button_index:
            embed = discord.Embed(
                title="Error",
                description=f"This panel only has {len(panel_data['buttons'])} buttons.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        if len(panel_data["modals"][button_index - 1]["components"]) >= 5:
            embed = discord.Embed(
                title="Error",
                description="This modal already has the maximum of 5 input fields.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel_data["modals"][button_index - 1]["components"].append({
            "label": label,
            "placeholder": placeholder,
            "length": length,
            "required": required
        })
        
        encoded_data = base64.b64encode(ujson.dumps(panel_data).encode()).decode()
        await self.bot.db.execute("UPDATE panels SET data=? WHERE name=?", encoded_data, panel_name)
        
        embed = discord.Embed(
            title="Input Field Added",
            description=f"Input field '{label}' added to button {button_index} in panel '{panel_name}'.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @input.command(
        name="remove",
        description="Remove an input field from a button's modal"
    )
    @option("panel_name", description="Name of the panel", type=str)
    @option("button_index", description="Index of the button (1-5)", type=int)
    @option("input_index", description="Index of the input field (1-5)", type=int)
    async def remove_input(self, ctx: discord.ApplicationContext, 
                        panel_name: str, button_index: int, input_index: int):
        await ctx.defer(ephemeral=True)
        
        if button_index < 1 or button_index > 5:
            embed = discord.Embed(
                title="Error",
                description="Button index must be between 1 and 5.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        if input_index < 1 or input_index > 5:
            embed = discord.Embed(
                title="Error",
                description="Input index must be between 1 and 5.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            embed = discord.Embed(
                title="Error",
                description=f"No panel found with name '{panel_name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel_data = ujson.loads(base64.b64decode(panel[0]).decode())
        
        if len(panel_data["buttons"]) < button_index:
            embed = discord.Embed(
                title="Error",
                description=f"This panel only has {len(panel_data['buttons'])} buttons.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        components = panel_data["modals"][button_index - 1]["components"]
        if len(components) < input_index:
            embed = discord.Embed(
                title="Error",
                description=f"This modal only has {len(components)} input fields.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        removed_input = components.pop(input_index - 1)
        
        encoded_data = base64.b64encode(ujson.dumps(panel_data).encode()).decode()
        await self.bot.db.execute("UPDATE panels SET data=? WHERE name=?", encoded_data, panel_name)
        
        embed = discord.Embed(
            title="Input Field Removed",
            description=f"Input field '{removed_input['label']}' removed from button {button_index} in panel '{panel_name}'.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @panel.command(
        name="info",
        description="View detailed info about a panel"
    )
    @option("panel_name", description="Name of the panel", type=str)
    async def panel_info(self, ctx: discord.ApplicationContext, panel_name: str):
        await ctx.defer(ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            embed = discord.Embed(
                title="Panel Not Found",
                description=f"No panel found with name '{panel_name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        panel_data = ujson.loads(base64.b64decode(panel[0]).decode())
        
        embed = discord.Embed(
            title=f"Panel: {panel_name}",
            color=discord.Color.blue()
        )
        
        embed_data = panel_data.get("embed", {})
        embed.add_field(
            name="Embed",
            value=f"**Title:** {embed_data.get('title', 'None')}\n"
                  f"**Description:** {embed_data.get('description', 'None')[:100]}...\n"
                  f"**Color:** #{embed_data.get('color', 'FF0000')}",
            inline=False
        )
        
        for i, button in enumerate(panel_data["buttons"], 1):
            modal = panel_data["modals"][i-1]
            input_count = len(modal["components"])
            embed.add_field(
                name=f"Button {i}: {button['label']}",
                value=f"**Style:** {button['style']}\n"
                      f"**Modal Title:** {modal['title']}\n"
                      f"**Input Fields:** {input_count}",
                inline=True
            )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @panel.command(
        name="preview",
        description="Preview a panel with interactive buttons (no functionality)"
    )
    @option("panel_name", description="Name of the panel to preview", type=str)
    async def preview_panel(self, ctx: discord.ApplicationContext, panel_name: str):
        await ctx.defer(ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            return await ctx.respond(f"No panel found with name '{panel_name}'.", ephemeral=True)
        
        encoded_data = panel[0]
        panel_data = ujson.loads(base64.b64decode(encoded_data).decode())
        
        embed_data = panel_data.get("embed", {})
        embed = discord.Embed(
            title=embed_data.get("title", "Custom Panel"),
            description=embed_data.get("description", "Click a button below"),
            color=int(embed_data.get("color", "FF0000"), 16)
        )
        
        style_map = {
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
            "success": discord.ButtonStyle.success,
            "danger": discord.ButtonStyle.danger
        }
        
        class PreviewView(View):
            def __init__(self):
                super().__init__(timeout=120)
                
                for button_data in panel_data["buttons"]:
                    style = style_map.get(button_data["style"], discord.ButtonStyle.secondary)
                    button = Button(
                        label=button_data["label"],
                        style=style,
                        disabled=False
                    )
                    async def preview_callback(interaction, button_label=button_data["label"]):
                        await interaction.response.send_message(
                            f"This is a preview of button '{button_label}'. In a real panel, this would open a modal.",
                            ephemeral=True
                        )
                    button.callback = preview_callback
                    self.add_item(button)
        
        await ctx.respond("📋 **Panel Preview**", embed=embed, view=PreviewView(), ephemeral=False)
        await ctx.respond("✅ Preview sent! This shows exactly how your panel will appear to users.", ephemeral=True)

    @panel.command(
        name="send",
        description="Send a panel to any channel (without ticket functionality)"
    )
    @option("panel_name", description="Name of the panel", type=str)
    @option("channel", description="Channel to send to", type=discord.TextChannel)
    async def send_panel(self, ctx: discord.ApplicationContext, panel_name: str, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)
        
        panel = await self.bot.db.fetchone("SELECT data FROM panels WHERE name=?", panel_name)
        if not panel:
            return await ctx.respond(f"No panel found with name '{panel_name}'.", ephemeral=True)
        
        encoded_data = panel[0]
        panel_data = ujson.loads(base64.b64decode(encoded_data).decode())
        
        if not panel_data["buttons"]:
            embed = discord.Embed(
                title="No Buttons",
                description=f"Panel '{panel_name}' has no buttons. Add at least one button before sending.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        embed_data = panel_data.get("embed", {})
        embed = discord.Embed(
            title=embed_data.get("title", "Custom Panel"),
            description=embed_data.get("description", "Click a button below"),
            color=int(embed_data.get("color", "FF0000"), 16)
        )
        
        try:
            view = CustomView(self.bot, encoded_data)
            message = await channel.send(embed=embed, view=view)
            confirm_embed = discord.Embed(
                title="Panel Sent Successfully",
                description=f"Panel '{panel_name}' has been sent to {channel.mention}\n[Jump to Message]({message.jump_url})",
                color=discord.Color.green()
            )
            confirm_embed.add_field(
                name="⚠️ Important Note", 
                value="This panel was sent without ticket functionality. User interactions will still open modals, but no tickets will be created.",
                inline=False
            )
            await ctx.respond(embed=confirm_embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Permission Error",
                description=f"I don't have permission to send messages in {channel.mention}.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="Error Sending Panel",
                description=f"An error occurred while sending the panel: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Custom(bot))