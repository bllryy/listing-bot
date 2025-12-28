import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from discord.ui import Modal, InputText, View, Button, Select
import base64
import ujson
from bot.bot import Bot
from bot.util.constants import is_authorized_to_use_bot, button_customId_info

class ButtonSelectView(View):
    def __init__(self, bot: Bot, embed_name: str, channel: discord.TextChannel):
        super().__init__(timeout=300)
        self.bot = bot
        self.embed_name = embed_name
        self.channel = channel
        self.selected_buttons = []
        
        # Create select menu with available buttons
        options = []
        for button_id, button_info in button_customId_info.items():
            if button_info.get("type") == discord.ui.Button:
                emoji = button_info.get("emoji", "")
                text = button_info.get("text", button_id)
                description = button_info.get("description", "")[:100]  # Discord limit
                
                options.append(discord.SelectOption(
                    label=text,
                    value=button_id,
                    description=description,
                    emoji=emoji
                ))
        
        # Split into multiple selects if too many options (Discord limit is 25)
        if len(options) > 25:
            options = options[:25]
        
        select = Select(
            placeholder="Choose buttons to add to the embed...",
            min_values=0,
            max_values=min(len(options), 5),  # Max 5 buttons per row
            options=options
        )
        select.callback = self.select_callback
        self.add_item(select)
        
        # Add confirm button
        confirm_btn = Button(label="Send Embed", style=discord.ButtonStyle.green, emoji="✅")
        confirm_btn.callback = self.confirm_callback
        self.add_item(confirm_btn)
        
        # Add cancel button
        cancel_btn = Button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)
    
    async def select_callback(self, interaction: discord.Interaction):
        self.selected_buttons = interaction.data['values']
        
        button_names = []
        for button_id in self.selected_buttons:
            button_info = button_customId_info.get(button_id, {})
            button_names.append(button_info.get("text", button_id))
        
        if self.selected_buttons:
            description = f"Selected buttons: {', '.join(button_names)}"
        else:
            description = "No buttons selected."
        
        embed = discord.Embed(
            title="Button Selection",
            description=description,
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def confirm_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed_data = await self.bot.db.fetchone("SELECT data FROM custom_embeds WHERE name=?", self.embed_name)
        if not embed_data:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No embed found with name '{self.embed_name}'.",
                color=discord.Color.red()
            )
            return await interaction.followup.edit_message(embed=embed, view=None)
        
        try:
            decoded_data = ujson.loads(base64.b64decode(embed_data[0]).decode())
            custom_embed = self._create_embed_from_data(decoded_data)
            
            button_view = None
            if self.selected_buttons:
                button_view = View(timeout=None)
                for button_id in self.selected_buttons:
                    button_info = button_customId_info.get(button_id, {})
                    if button_info.get("type") == discord.ui.Button:
                        btn = Button(
                            label=button_info.get("text", button_id),
                            emoji=button_info.get("emoji"),
                            style=button_info.get("style", discord.ButtonStyle.gray),
                            custom_id=button_id
                        )
                        button_view.add_item(btn)
            
            await self.channel.send(embed=custom_embed, view=button_view)
            
            embed = discord.Embed(
                title="✅ Embed Sent",
                description=f"Custom embed '{self.embed_name}' sent to {self.channel.mention}" + 
                           (f" with {len(self.selected_buttons)} button(s)!" if self.selected_buttons else "!") + 
                           (f' if the buttons don\'t work, consider using {self.bot.get_command_link("bot restart")}'),
                color=discord.Color.green()
            )
            await interaction.followup.edit_message(embed=embed, view=None)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to send embed: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.edit_message(embed=embed, view=None)
    
    async def cancel_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❌ Cancelled",
            description="Embed sending cancelled.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    def _create_embed_from_data(self, data):
        """Create a Discord embed from embed data"""
        try:
            color = int(data['color'], 16) if data['color'] else discord.Color.default()
        except:
            color = discord.Color.default()
            
        embed = discord.Embed(
            title=data.get('title', ''),
            description=data.get('description', ''),
            color=color
        )
        
        if data.get('footer'):
            embed.set_footer(text=data['footer']['text'])
        if data.get('image'):
            embed.set_image(url=data['image']['url'])
        if data.get('thumbnail'):
            embed.set_thumbnail(url=data['thumbnail']['url'])
        if data.get('author'):
            embed.set_author(name=data['author']['name'])
        
        for field in data.get('fields', []):
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field.get('inline', False)
            )
        
        return embed

class EmbedModal(Modal):
    def __init__(self, bot: Bot, name: str, title: str, color: str, description: str = None):
        super().__init__(title="Create Custom Embed")
        self.bot = bot
        self.embed_name = name
        self.embed_title = title
        self.embed_color = color
        
        self.add_item(InputText(
            label="Description",
            placeholder="Enter the embed description",
            style=discord.InputTextStyle.long,
            value=description or "",
            required=False
        ))
        
        self.add_item(InputText(
            label="Footer Text",
            placeholder="Enter footer text (optional)",
            style=discord.InputTextStyle.short,
            required=False
        ))
        
        self.add_item(InputText(
            label="Image URL",
            placeholder="Enter image URL (optional)",
            style=discord.InputTextStyle.short,
            required=False
        ))
        
        self.add_item(InputText(
            label="Thumbnail URL",
            placeholder="Enter thumbnail URL (optional)",
            style=discord.InputTextStyle.short,
            required=False
        ))
        
        self.add_item(InputText(
            label="Author Name",
            placeholder="Enter author name (optional)",
            style=discord.InputTextStyle.short,
            required=False
        ))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Check if embed already exists
        existing = await self.bot.db.fetchone("SELECT * FROM custom_embeds WHERE name=?", self.embed_name)
        if existing:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An embed with name '{self.embed_name}' already exists.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Prepare embed data
        embed_data = {
            "title": self.embed_title,
            "description": self.children[0].value or "",
            "color": self.embed_color.lstrip('#'),
            "footer": {"text": self.children[1].value} if self.children[1].value else None,
            "image": {"url": self.children[2].value} if self.children[2].value else None,
            "thumbnail": {"url": self.children[3].value} if self.children[3].value else None,
            "author": {"name": self.children[4].value} if self.children[4].value else None,
            "fields": []
        }
        
        # Encode and save to database
        encoded_data = base64.b64encode(ujson.dumps(embed_data).encode()).decode()
        await self.bot.db.execute(
            "INSERT INTO custom_embeds (name, created_by, data) VALUES (?, ?, ?)",
            self.embed_name, interaction.user.id, encoded_data
        )
        
        # Create preview embed
        preview_embed = self._create_embed_from_data(embed_data)
        
        embed = discord.Embed(
            title="✅ Embed Created",
            description=f"Custom embed '{self.embed_name}' created successfully!\n\n**Preview:**",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embeds=[embed, preview_embed], ephemeral=True)
    
    def _create_embed_from_data(self, data):
        """Create a Discord embed from embed data"""
        try:
            color = int(data['color'], 16) if data['color'] else discord.Color.default()
        except:
            color = discord.Color.default()
            
        embed = discord.Embed(
            title=data.get('title', ''),
            description=data.get('description', ''),
            color=color
        )
        
        if data.get('footer'):
            embed.set_footer(text=data['footer']['text'])
        if data.get('image'):
            embed.set_image(url=data['image']['url'])
        if data.get('thumbnail'):
            embed.set_thumbnail(url=data['thumbnail']['url'])
        if data.get('author'):
            embed.set_author(name=data['author']['name'])
        
        for field in data.get('fields', []):
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field.get('inline', False)
            )
        
        return embed

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    embed = SlashCommandGroup("embed", description="Custom embed management commands")

    @embed.command(
        name="create",
        description="Create a new custom embed"
    )
    @is_authorized_to_use_bot()
    @option("name", description="Unique name for the embed", type=str)
    @option("title", description="Title of the embed", type=str)
    @option("color", description="Color of the embed (hex code)", type=str, required=False, default="00FF00")
    async def create_embed(self, ctx: discord.ApplicationContext, name: str, title: str, color: str = "00FF00"):
        # Validate color format
        color = color.lstrip('#')
        if not all(c in '0123456789ABCDEFabcdef' for c in color) or len(color) != 6:
            return await ctx.respond("❌ Invalid color format. Use hex format like `FF0000` or `#FF0000`", ephemeral=True)
        
        modal = EmbedModal(self.bot, name, title, color)
        await ctx.send_modal(modal)

    @embed.command(
        name="list",
        description="List all custom embeds"
    )
    @is_authorized_to_use_bot()
    async def list_embeds(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        embeds = await self.bot.db.fetchall("SELECT name, created_by FROM custom_embeds ORDER BY name")
        
        if not embeds:
            embed = discord.Embed(
                title="📝 Custom Embeds",
                description="No custom embeds found. Use `/embed create` to create one!",
                color=discord.Color.blue()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        description = []
        for name, created_by in embeds:
            creator = self.bot.get_user(created_by)
            creator_name = creator.display_name if creator else f"User ID: {created_by}"
            description.append(f"• **{name}** - Created by {creator_name}")
        
        embed = discord.Embed(
            title="📝 Custom Embeds",
            description="\n".join(description),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use /embed view [name] to preview an embed")
        await ctx.respond(embed=embed, ephemeral=True)

    @embed.command(
        name="view",
        description="View/preview a custom embed"
    )
    @is_authorized_to_use_bot()
    @option("name", description="Name of the embed to view", type=str)
    async def view_embed(self, ctx: discord.ApplicationContext, name: str):
        await ctx.defer(ephemeral=True)
        
        embed_data = await self.bot.db.fetchone("SELECT data, created_by FROM custom_embeds WHERE name=?", name)
        if not embed_data:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No embed found with name '{name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        # Decode and create embed
        try:
            decoded_data = ujson.loads(base64.b64decode(embed_data[0]).decode())
            preview_embed = self._create_embed_from_data(decoded_data)
            
            creator = self.bot.get_user(embed_data[1])
            creator_name = creator.display_name if creator else f"User ID: {embed_data[1]}"
            
            info_embed = discord.Embed(
                title="🔍 Embed Preview",
                description=f"**Embed Name:** {name}\n**Created by:** {creator_name}",
                color=discord.Color.blue()
            )
            
            await ctx.respond(embeds=[info_embed, preview_embed], ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to load embed data: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @embed.command(
        name="delete",
        description="Delete a custom embed"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("name", description="Name of the embed to delete", type=str)
    async def delete_embed(self, ctx: discord.ApplicationContext, name: str):
        await ctx.defer(ephemeral=True)
        
        existing = await self.bot.db.fetchone("SELECT created_by FROM custom_embeds WHERE name=?", name)
        if not existing:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No embed found with name '{name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        # Check if user can delete (creator or admin)
        if existing[0] != ctx.author.id:
            # Add additional permission check here if needed
            pass
        
        await self.bot.db.execute("DELETE FROM custom_embeds WHERE name=?", name)
        
        embed = discord.Embed(
            title="✅ Embed Deleted",
            description=f"Custom embed '{name}' deleted successfully!",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @embed.command(
        name="send",
        description="Send a custom embed to a channel"
    )
    @is_authorized_to_use_bot()
    @option("name", description="Name of the embed to send", type=str)
    @option("channel", description="Channel to send the embed to", type=discord.TextChannel, required=False)
    @option("add_buttons", description="Add interactive buttons to the embed", type=bool, required=False, default=False)
    async def send_embed(self, ctx: discord.ApplicationContext, name: str, channel: discord.TextChannel = None, add_buttons: bool = False):
        await ctx.defer(ephemeral=True)
        
        target_channel = channel or ctx.channel
        
        embed_data = await self.bot.db.fetchone("SELECT data FROM custom_embeds WHERE name=?", name)
        if not embed_data:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No embed found with name '{name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        if add_buttons:
            # Show button selection interface
            embed = discord.Embed(
                title="Button Selection",
                description="Choose which buttons to add to your embed:",
                color=discord.Color.blue()
            )
            view = ButtonSelectView(self.bot, name, target_channel)
            await ctx.respond(embed=embed, view=view, ephemeral=True)
        else:
            # Send embed without buttons (original functionality)
            try:
                decoded_data = ujson.loads(base64.b64decode(embed_data[0]).decode())
                custom_embed = self._create_embed_from_data(decoded_data)
                
                await target_channel.send(embed=custom_embed)
                
                embed = discord.Embed(
                    title="✅ Embed Sent",
                    description=f"Custom embed '{name}' sent to {target_channel.mention}!",
                    color=discord.Color.green()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to send embed: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)

    @embed.command(
        name="edit",
        description="Edit an existing custom embed"
    )
    @is_authorized_to_use_bot()
    @option("name", description="Name of the embed to edit", type=str)
    async def edit_embed(self, ctx: discord.ApplicationContext, name: str):
        await ctx.defer(ephemeral=True)
        
        embed_data = await self.bot.db.fetchone("SELECT data, created_by FROM custom_embeds WHERE name=?", name)
        if not embed_data:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No embed found with name '{name}'.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        # Check permissions
        if embed_data[1] != ctx.author.id:
            # Add additional permission check here if needed
            pass
        
        try:
            decoded_data = ujson.loads(base64.b64decode(embed_data[0]).decode())
            
            # Delete the old embed
            await self.bot.db.execute("DELETE FROM custom_embeds WHERE name=?", name)
            
            # Create modal with existing data
            modal = EmbedModal(
                self.bot, 
                name, 
                decoded_data.get('title', ''), 
                decoded_data.get('color', '00FF00'),
                decoded_data.get('description', '')
            )
            
            # Pre-fill modal with existing data
            if decoded_data.get('footer'):
                modal.children[1].value = decoded_data['footer']['text']
            if decoded_data.get('image'):
                modal.children[2].value = decoded_data['image']['url']
            if decoded_data.get('thumbnail'):
                modal.children[3].value = decoded_data['thumbnail']['url']
            if decoded_data.get('author'):
                modal.children[4].value = decoded_data['author']['name']
            
            await ctx.send_modal(modal)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to load embed for editing: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)

    def _create_embed_from_data(self, data):
        """Create a Discord embed from embed data"""
        try:
            color = int(data['color'], 16) if data['color'] else discord.Color.default()
        except:
            color = discord.Color.default()
            
        embed = discord.Embed(
            title=data.get('title', ''),
            description=data.get('description', ''),
            color=color
        )
        
        if data.get('footer'):
            embed.set_footer(text=data['footer']['text'])
        if data.get('image'):
            embed.set_image(url=data['image']['url'])
        if data.get('thumbnail'):
            embed.set_thumbnail(url=data['thumbnail']['url'])
        if data.get('author'):
            embed.set_author(name=data['author']['name'])
        
        for field in data.get('fields', []):
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=field.get('inline', False)
            )
        
        return embed

def setup(bot):
    bot.add_cog(Embed(bot))
