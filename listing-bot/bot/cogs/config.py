import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from bot.util.constants import config_options, is_authorized_to_use_bot
from bot.bot import Bot
import inspect

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    config = SlashCommandGroup("config", "Server configuration commands")

    roles = config.create_subgroup("roles", "Manage role-based configurations")
    channels = config.create_subgroup("channels", "Manage channel configurations")
    numbers = config.create_subgroup("numbers", "Manage numeric configurations")
    floats = config.create_subgroup("floats", "Manage floating-point configurations")
    booleans = config.create_subgroup("booleans", "Manage boolean configurations")
    categories = config.create_subgroup("categories", "Manage category configurations")
    auth = config.create_subgroup("auth", "Manage user authentication settings")
    coins = config.create_subgroup("coins", "Manage coin pricing tiers configurations")

    @config.command(
        name="list",
        description="Lists all the config options"
    )
    @is_authorized_to_use_bot()
    async def list_config(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="Config Options", color=discord.Color.red())
        config_string = ""
        for option in config_options:
            config_string += f"`{option}`: {config_options[option]['description']}\n"
        embed.description = config_string
        await ctx.respond(embed=embed, ephemeral=True)

    @roles.command(
        name="update",
        description="Update a role-based configuration"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("option", description="Config option to update",
            choices=[opt for opt in config_options if config_options[opt]["type"] == discord.Role])
    @option("value", description="Role to use for configuration")
    async def update_role_config(self, ctx: discord.ApplicationContext,
                               option: str, value: discord.Role):
        await self._update_config(ctx, option, value.id)

    @channels.command(
        name="update",
        description="Update a channel-based configuration"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("option", description="Config option to update",
            choices=[opt for opt in config_options if config_options[opt]["type"] in
                    [discord.TextChannel, discord.VoiceChannel]])
    @option("value", description="Channel to use for configuration")
    async def update_channel_config(self, ctx: discord.ApplicationContext,
                                  option: str, value: discord.abc.GuildChannel):
        await self._update_config(ctx, option, value.id)

    @categories.command(
        name="update",
        description="Update a category-based configuration"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("option", description="Config option to update",
            choices=[opt for opt in config_options if config_options[opt]["type"] == discord.CategoryChannel])
    @option("value", description="Category to use for configuration")
    async def update_category_config(self, ctx: discord.ApplicationContext,
                                   option: str, value: discord.CategoryChannel):
        await self._update_config(ctx, option, value.id)

    @numbers.command(
        name="update",
        description="Update an integer configuration"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("option", description="Config option to update",
            choices=[opt for opt in config_options if config_options[opt]["type"] == int])  # Only integers
    @option("value", description="Numeric value to set")
    async def update_number_config(self, ctx: discord.ApplicationContext,
                                 option: str, value: str):
        try:
            converted = int(value)  # Convert directly to int
        except ValueError:
            return await ctx.respond("Invalid integer provided", ephemeral=True)
        await self._update_config(ctx, option, converted)

    @floats.command(  # New command for floats
        name="update",
        description="Update a floating-point configuration"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("option", description="Config option to update",
            choices=[opt for opt in config_options if config_options[opt]["type"] == float])  # Only floats
    @option("value", description="Floating-point value to set")
    async def update_float_config(self, ctx: discord.ApplicationContext,
                                  option: str, value: str):
        try:
            converted = float(value)
        except ValueError:
            return await ctx.respond("Invalid floating-point number provided", ephemeral=True)
        await self._update_config(ctx, option, converted)

    @booleans.command(
        name="update",
        description="Update a boolean configuration"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("option", description="Config option to update",
            choices=[opt for opt in config_options if config_options[opt]["type"] == bool])
    @option("value", description="Boolean value to set", choices=["true", "false"])
    async def update_boolean_config(self, ctx: discord.ApplicationContext,
                                   option: str, value: str):
        converted = value.lower() == "true"
        await self._update_config(ctx, option, converted)


    async def _update_config(self, ctx: discord.ApplicationContext, option: str, value):
        """Helper method to handle config updates"""
        try:
            await self.bot.db.update_config(option, value)
            await ctx.respond(f"Updated `{option}` to `{value}`", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error updating config: {str(e)}", ephemeral=True)

    @roles.command(
        name="view",
        description="View role configuration(s)"
    )
    @is_authorized_to_use_bot()
    @option("option", description="Config option to view (leave blank for all)",
            choices=[opt for opt in config_options if config_options[opt]["type"] == discord.Role],
            required=False, default=None)  # Back to optional
    async def view_role_config(self, ctx: discord.ApplicationContext, option: str = None):
        await self._handle_group_view(ctx, option, discord.Role) # use helper function

    @channels.command(
        name="view",
        description="View channel configuration(s)"
    )
    @is_authorized_to_use_bot()
    @option("option", description="Config option to view (leave blank for all)",
            choices=[opt for opt in config_options if config_options[opt]["type"] in
                    [discord.TextChannel, discord.VoiceChannel]],
            required=False, default=None)  # Back to optional
    async def view_channel_config(self, ctx: discord.ApplicationContext, option: str = None):
        await self._handle_group_view(ctx, option, (discord.TextChannel, discord.VoiceChannel))


    @categories.command(
        name="view",
        description="View category configuration(s)"
    )
    @is_authorized_to_use_bot()
    @option("option", description="Config option to view (leave blank for all)",
            choices=[opt for opt in config_options if config_options[opt]["type"] == discord.CategoryChannel],
            required=False, default=None)  # Back to optional
    async def view_category_config(self, ctx: discord.ApplicationContext, option: str = None):
       await self._handle_group_view(ctx, option, discord.CategoryChannel)

    @numbers.command(
        name="view",
        description="View integer configuration(s)"
    )
    @is_authorized_to_use_bot()
    @option("option", description="Config option to view (leave blank for all)",
            choices=[opt for opt in config_options if config_options[opt]["type"] == int],
            required=False, default=None)  # Back to optional
    async def view_number_config(self, ctx: discord.ApplicationContext, option: str = None):
        await self._handle_group_view(ctx, option, int)

    @floats.command(
        name="view",
        description="View floating-point configuration(s)"
    )
    @is_authorized_to_use_bot()
    @option("option", description="Config option to view (leave blank for all)",
            choices=[opt for opt in config_options if config_options[opt]["type"] == float],
            required=False, default=None)  # Back to optional
    async def view_float_config(self, ctx: discord.ApplicationContext, option: str = None):
        await self._handle_group_view(ctx, option, float)

    @booleans.command(
        name="view",
        description="View boolean configuration(s)"
    )
    @is_authorized_to_use_bot()
    @option("option", description="Config option to view (leave blank for all)",
            choices=[opt for opt in config_options if config_options[opt]["type"] == bool],
            required=False, default=None)
    async def view_boolean_config(self, ctx: discord.ApplicationContext, option: str = None):
        await self._handle_group_view(ctx, option, bool)


    async def _handle_group_view(self, ctx: discord.ApplicationContext, option: str, config_type):
        """Handle group view commands with optional parameter"""
        if option:
            await self._display_config_value(ctx, option)
        else:
            await self._display_type_configs(ctx, config_type)

    async def _display_type_configs(self, ctx: discord.ApplicationContext, config_type):
        """Display all configurations of a specific type"""
        type_options = []
        if inspect.isclass(config_type):
            type_options = [opt for opt in config_options if config_options[opt]["type"] == config_type]
        else:  # Handle tuples of types
            type_options = [opt for opt in config_options if config_options[opt]["type"] in config_type]


        if not type_options:
            await ctx.respond("No configurations available for this type", ephemeral=True)
            return

        values = []
        for opt in type_options:
            value = await self.bot.db.get_config(opt)
            formatted = await self._format_config_value(opt, value, ctx.guild)
            values.append(f"• **{opt}**: {formatted}")

        # Get a user-friendly name for the type.
        if inspect.isclass(config_type):
            type_name = config_type.__name__
        elif isinstance(config_type, tuple):
             type_name = ", ".join(t.__name__ for t in config_type)  #e.g., "TextChannel, VoiceChannel"
        else:
            type_name = str(config_type)

        embed = discord.Embed(
            title=f"{type_name} Configurations",
            description="\n".join(values),
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    async def _display_config_value(self, ctx: discord.ApplicationContext, option: str):
        """Display a single configuration value"""
        value = await self.bot.db.get_config(option)
        formatted = await self._format_config_value(option, value, ctx.guild)
        embed = discord.Embed(
            title=f"Configuration: {option}",
            description=formatted,
            color=discord.Color.blue()
        )
        await ctx.respond(embed=embed, ephemeral=True)


    async def _format_config_value(self, option: str, value, guild: discord.Guild) -> str:
        """Format the stored value into a user-friendly representation"""
        config_type = config_options[option]["type"]

        if value is None:
            return "🚫 Not set"

        if config_type == discord.Role:
            role = guild.get_role(value)
            return role.mention if role else "❌ Deleted role"

        if config_type in [discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]:
            channel = guild.get_channel(value)
            return channel.mention if channel else "❌ Deleted channel"

        if config_type == int:
            return f"🔢 `{int(value)}`"
        if config_type == float:
            return f"🔢 `{float(value)}`"
        if config_type == bool:
            return f"✅ `True`" if value else f"❌ `False`"

        return str(value)
    
    @auth.command(
        name="add",
        description="Adds an auth bot to the list."
    )
    @is_authorized_to_use_bot(strict=True)
    @option("client_id", description="The new bot's id", required=True)
    @option("client_secret", description="The new bot's secret", required=True)
    @option("bot_token", description="The new bot's token", required=True)
    async def config_auth_add(self, ctx: discord.ApplicationContext, client_id: str, client_secret: str, bot_token: str):
        if not client_id.isdigit():
            return await ctx.respond("Client ID is not a number.")

        await self.bot.db.execute("INSERT INTO auth_bots VALUES (?, ?, ?, ?)", int(client_id), client_secret, bot_token, f"https://{await self.bot.get_domain()}/authorize")
        await ctx.respond(f"Your bot has been successfully added.  To ensure proper functionality, add the following as a redirect uri inside of the developer dashboard.\n`https://{await self.bot.get_domain()}/authorize`", ephemeral=True)

    @auth.command(
        name="view",
        description="View all auth bots."
    )
    @is_authorized_to_use_bot()
    async def config_auth_view(self, ctx: discord.ApplicationContext):
        bots = await self.bot.db.fetchall("SELECT client_id, redirect_uri FROM auth_bots")
        
        if not bots:
            return await ctx.respond("No authorized bots found.", ephemeral=True)
        
        description = []
        for i, (client_id, redirect_uri) in enumerate(bots, 1):
            try:
                bot_user = self.bot.get_user(client_id)
                if not bot_user:
                    bot_user = await self.bot.fetch_user(client_id)
                bot_name = f"{bot_user.name} ({bot_user.display_name})" if bot_user else "Unknown Bot"
            except:
                bot_name = "Unknown Bot"
            
            description.append(
                f"**{i}.** {bot_name}\n"
                f"ID: `{client_id}`\n"
                f"Redirect URI: `{redirect_uri}`\n"
            )
        
        embed = discord.Embed(
            title="🤖 Authorized Bots",
            description="\n".join(description),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use /config auth remove [client_id] to remove a bot")
        await ctx.respond(embed=embed, ephemeral=True)

    @auth.command(
        name="remove",
        description="Remove an auth bot."
    )
    @is_authorized_to_use_bot(strict=True)
    @option("client_id", description="The bot's client ID to remove", required=True)
    async def config_auth_remove(self, ctx: discord.ApplicationContext, client_id: str):
        if not client_id.isdigit():
            return await ctx.respond("Client ID must be a number.", ephemeral=True)
        
        client_id_int = int(client_id)
        
        existing_bot = await self.bot.db.fetchone("SELECT client_id FROM auth_bots WHERE client_id = ?", client_id_int)
        if not existing_bot:
            return await ctx.respond("Bot not found in authorized list.", ephemeral=True)
        
        try:
            bot_user = self.bot.get_user(client_id_int)
            if not bot_user:
                bot_user = await self.bot.fetch_user(client_id_int)
            bot_name = f"{bot_user.name} ({bot_user.display_name})" if bot_user else f"Bot ID: {client_id}"
        except:
            bot_name = f"Bot ID: {client_id}"
        
        await self.bot.db.execute("DELETE FROM auth_bots WHERE client_id = ?", client_id_int)
        
        embed = discord.Embed(
            title="✅ Bot Removed",
            description=f"Successfully removed **{bot_name}** from the authorized bots list.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @coins.command(
        name="add",
        description="Add/Update a coin pricing tier"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("type", description="Buy or Sell", choices=["buy", "sell"])
    @option("threshold", description="Minimum coins required for this tier (e.g., 1000000)", min_value=0)
    @option("price", description="Price per million coins at this tier", min_value=0.0)
    async def add_coin_tier(self, ctx: discord.ApplicationContext, 
                          type: str, threshold: int, price: float):
        """Add or update a pricing tier, automatically maintaining sorted order"""
        existing_tiers = []
        tier_num = 1
        while True:
            key = f"{type}_coins_tier_{tier_num}"
            value = await self.bot.db.get_config(key)
            if not value:
                break
            try:
                t, p = value.split(';')
                existing_tiers.append({
                    "threshold": int(t),
                    "price": float(p)
                })
                tier_num += 1
            except:
                break

        updated = False
        for tier in existing_tiers:
            if tier["threshold"] == threshold:
                tier["price"] = price
                updated = True
                break

        if not updated:
            existing_tiers.append({"threshold": threshold, "price": price})

        existing_tiers.sort(key=lambda x: x["threshold"])

        await self.bot.db.execute("DELETE FROM config WHERE key LIKE ?", f"{type}_coins_tier_%")

        for index, tier in enumerate(existing_tiers, start=1):
            new_key = f"{type}_coins_tier_{index}"
            new_value = f"{tier['threshold']};{tier['price']}"
            await self.bot.db.update_config(new_key, new_value)

        action = "updated" if updated else "added"
        await ctx.respond(
            f"Successfully {action} {type} tier at {threshold:,} coins with price ${price}/M\n"
            f"Current tiers have been renumbered automatically.",
            ephemeral=True
        )

    @coins.command(
        name="remove",
        description="Remove a coin pricing tier by position"
    )
    @is_authorized_to_use_bot(strict=True)
    @option("type", description="Buy or Sell", choices=["buy", "sell"])
    @option("tier_number", description="Position number from /config coins_tiers view", min_value=1)
    async def remove_coin_tier(self, ctx: discord.ApplicationContext, type: str, tier_number: int):
        """Remove a tier by its displayed position number"""
        tiers = []
        tier_num = 1
        while True:
            key = f"{type}_coins_tier_{tier_num}"
            value = await self.bot.db.get_config(key)
            if not value:
                break
            try:
                t, p = value.split(';')
                tiers.append({
                    "threshold": int(t),
                    "price": float(p)
                })
                tier_num += 1
            except:
                break

        if tier_number < 1 or tier_number > len(tiers):
            return await ctx.respond(f"Invalid tier number! There {'is' if len(tiers)==1 else 'are'} {len(tiers)} tier(s).", ephemeral=True)

        removed = tiers.pop(tier_number - 1)
        await self.bot.db.execute("DELETE FROM config WHERE key LIKE ?", f"{type}_coins_tier_%")

        for index, tier in enumerate(tiers, start=1):
            new_key = f"{type}_coins_tier_{index}"
            new_value = f"{tier['threshold']};{tier['price']}"
            await self.bot.db.update_config(new_key, new_value)

        await ctx.respond(
            f"Removed {type} tier {tier_number} ({removed['threshold']:,} coins)\n"
            f"Remaining tiers have been renumbered automatically.",
            ephemeral=True
        )

    @coins.command(
        name="view",
        description="View all pricing tiers for a type"
    )
    @is_authorized_to_use_bot()
    @option("type", description="Buy or Sell", choices=["buy", "sell"])
    async def view_coin_tiers(self, ctx: discord.ApplicationContext, type: str):
        """Display sorted pricing tiers"""
        tiers = []
        tier_num = 1
        while True:
            key = f"{type}_coins_tier_{tier_num}"
            value = await self.bot.db.get_config(key)
            if not value:
                break
            try:
                t, p = value.split(';')
                tiers.append({
                    "position": tier_num,
                    "threshold": int(t),
                    "price": float(p)
                })
                tier_num += 1
            except:
                break

        if not tiers:
            return await ctx.respond(f"No tiers found for {type} orders", ephemeral=True)

        description = []
        for idx, tier in enumerate(tiers, 1):
            description.append(
                f"**Tier {idx}**\n"
                f"Threshold: {tier['threshold']:,} coins\n"
                f"Price: ${tier['price']}/M\n"
            )

        embed = discord.Embed(
            title=f"{type.capitalize()} Pricing Tiers",
            description="\n".join(description),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use /config coins_tiers remove [number] to delete a tier")
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Config(bot))