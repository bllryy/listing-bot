import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from bot.util.views import AuthorizeView
from bot.util.constants import is_authorized_to_use_bot, auth_config_options
from discord.ui import View, Button
from auth.request import Requests
from bot.bot import Bot
import json

from bot.util.helper.account import AccountObject
from bot.util.helper.profile import ProfileObject
from bot.util.helper.macro_alt import AltObject
from bot.util.list import list_account, list_profile, list_alt

from bot.util.restore import *

def get_guild_data(guild_id: int) -> dict:
    with open("./data/server_data.json", "r") as f:
        data = json.load(f)

    return data.get(str(guild_id), {})


class Auth(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    auth = SlashCommandGroup("auth", description="Commands related to authorization")
    auth_config = auth.create_subgroup("config", description="Authentication configuration commands")

    @auth.command(
        name="panel",
        description="Sends an authorization panel"
    )
    @is_authorized_to_use_bot()
    async def auth_panel(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        embed = discord.Embed(
            title="Verification Required",
            description="Click the Button below to allow us to restore you to __**this**__ server in the future in case of termination.\nYou might be pulled back even after you leave the server.",
            color=discord.Color.embed_background()
        )
        await ctx.send(embed=embed, view=AuthorizeView(self.bot))
        await ctx.respond("Authorization Panel has been sent.")

    @auth.command(
        name="pull",
        description="Pull users back to the server"
    )
    @option(
        name="user_id",
        description="The user id to pull back",
        type=str,
        required=False
    )
    @is_authorized_to_use_bot()
    async def auth_pull(self, ctx: discord.ApplicationContext, user_id: str = None):
        await ctx.defer(ephemeral=True)

        if user_id and not user_id.isdigit():
            embed = discord.Embed(
                title="Error",
                description="User ID must be a number.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        if user_id:
            await self.pull_user(ctx, int(user_id))
        else:
            await self.pull_all_users(ctx)

    async def pull_user(self, ctx: discord.ApplicationContext, user_id: int):
        user_data = await self.bot.db.fetchone("SELECT * FROM auth WHERE user_id=?", user_id)
        if not user_data:
            embed = discord.Embed(
                title="Error",
                description="User not found in the database.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        try:
            await ctx.guild.fetch_member(user_id)
            embed = discord.Embed(
                title="Error",
                description="User is already in the server.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        except discord.errors.NotFound:
            pass
        
        user_id, refresh_token, ip_address, client_id, fingerprint, fingerprint_hash = user_data

        try:
            await ctx.guild.fetch_member(client_id)
        except discord.errors.NotFound:
            embed = discord.Embed(
                title="Error",
                description="The required application was not found in the server.",
                color=discord.Color.embed_background()
            )
            view = View()
            view.add_item(Button(style=discord.ButtonStyle.link, label="Invite Bot", url=f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot"))
            return await ctx.respond(embed=embed, ephemeral=True, view=view)

        async with Requests(client_id, self.bot) as requests:
            data = await requests.refresh_token(refresh_token)
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')

            if not access_token:
                await self.bot.db.execute("DELETE FROM auth WHERE user_id=?", user_id)
                embed = discord.Embed(
                    title="Error",
                    description="Failed to refresh token. User has been removed from the database.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            await self.bot.db.execute("UPDATE auth SET refresh_token=? WHERE user_id=?", refresh_token, user_id)
            await requests.pull(access_token, ctx.guild.id, user_id, [])

            embed = discord.Embed(
                title="Success",
                description=f"User has been pulled back to the server.",
                color=discord.Color.green()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

    async def pull_all_users(self, ctx: discord.ApplicationContext):
        users = await self.bot.db.fetchall("SELECT * FROM auth")
        if not users:
            embed = discord.Embed(
                title="Error",
                description="No users found in the database.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        bot_ids = {user_data[3] for user_data in users}

        needed_apps = []
        for bot_id in bot_ids:
            try:
                await ctx.guild.fetch_member(bot_id)
            except discord.errors.NotFound:
                needed_apps.append(bot_id)

        if needed_apps:
            embed = discord.Embed(
                title="Error",
                description="The following applications are required in the server for this command to work:\n" + "\n".join([f"`{app}`" for app in needed_apps]),
                color=discord.Color.red()
            )
            view = View()
            for i, app in enumerate(needed_apps):
                view.add_item(Button(style=discord.ButtonStyle.link, label=f"Invite Bot {i+1}", url=f"https://discord.com/oauth2/authorize?client_id={app}&permissions=8&scope=bot"))
            return await ctx.respond(embed=embed, ephemeral=True, view=view)

        for user_data in users:
            user_id, refresh_token, ip_address, client_id, fingerprint, fingerprint_hash = user_data

            async with Requests(client_id, self.bot) as requests:
                data = await requests.refresh_token(refresh_token)
                access_token = data.get('access_token')
                refresh_token = data.get('refresh_token')

                if not access_token:
                    await self.bot.db.execute("DELETE FROM auth WHERE user_id=?", user_id)
                    continue

                await self.bot.db.execute("UPDATE auth SET refresh_token=? WHERE user_id=?", refresh_token, user_id)
                await requests.pull(access_token, ctx.guild.id, user_id, [])

        embed = discord.Embed(
            title="Success",
            description=f"All users have been pulled back to the server.",
            color=discord.Color.green()
        )
        return await ctx.respond(embed=embed, ephemeral=True)
    
    async def pull_member(self, ctx: discord.ApplicationContext, member, roles, guild_id, offset):
        user_id = member["id"]

        member_data = await self.bot.db.fetchone("SELECT * FROM auth WHERE user_id=?", user_id)
        if not member_data:
            return await self.bot.db.execute("DELETE FROM auth WHERE user_id=?", user_id)
        
        user_id, refresh_token, ip_address, client_id, fingerprint, fingerprint_hash = member_data

        async with Requests(client_id, self.bot) as requests:
            tokens = await requests.refresh_token(refresh_token)
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            if not refresh_token:
                return await self.bot.db.execute("DELETE FROM auth WHERE user_id=?", user_id)

            roles_list = []
            member_roles = [role for role in member["roles"] if role != guild_id]
            for role_id in member_roles:
                for role in roles:
                    for role_name, data in role.items():
                        if data["id"] == role_id:
                            roles_list.append({role_name: data})

            snowflake_ids = []
            for role in roles_list:
                for role_name, data in role.items():
                    _role = None
                    for role in ctx.guild.roles:
                        if (
                            role.name == role_name and
                            role.position == data["position"]-offset
                        ):
                            _role = role
                            break

                    if _role:
                        snowflake_ids.append(_role.id)

            member_object_guild = ctx.guild.get_member(member["id"])
            if member_object_guild:
                for snowflake_id in snowflake_ids:
                    role = ctx.guild.get_role(snowflake_id)
                    if role:
                        try:
                            await member_object_guild.add_roles(role)
                        except discord.Forbidden:
                            pass
                        except discord.HTTPException:
                            pass
            else:
                await requests.pull(access_token, ctx.guild.id, user_id, snowflake_ids)
    
    @auth.command(
        name="restore",
        description="Restore your old server"
    )
    @commands.is_owner()
    async def auth_restore(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        roles = ctx.guild.roles
        top_role = ctx.guild.me.top_role

        if not top_role or top_role != roles[-1]:
            embed = discord.Embed(
                title="Error",
                description="Bot does not have the highest role in the server.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        main_guild = await self.bot.db.get_config("main_guild")
        guild = self.bot.get_guild(main_guild)

        if main_guild:
            data = get_guild_data(main_guild)
            if not data:
                embed = discord.Embed(
                    title="Error",
                    description="Main Guild data not found.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(
                title="Error",
                description="Main Guild is not set.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        users = await self.bot.db.fetchall("SELECT * FROM auth")
        if not users:
            users = []

        bot_ids = {user_data[3] for user_data in users}

        needed_apps = []
        for bot_id in bot_ids:
            try:
                await ctx.guild.fetch_member(bot_id)
            except discord.errors.NotFound:
                needed_apps.append(bot_id)

        if needed_apps:
            embed = discord.Embed(
                title="Error",
                description="The following applications are required in the server for this command to work:\n" + "\n".join([f"`{app}`" for app in needed_apps]),
                color=discord.Color.red()
            )
            view = View()
            for i, app in enumerate(needed_apps):
                view.add_item(Button(style=discord.ButtonStyle.link, label=f"Invite Bot {i+1}", url=f"https://discord.com/oauth2/authorize?client_id={app}&permissions=8&scope=bot"))
            return await ctx.respond(embed=embed, ephemeral=True, view=view)

        roles = data.get("roles", [])
        channels = data.get("channels", [])
        members = data.get("members", [])

        await copy_roles(ctx, roles)
        await copy_channels(ctx, channels)

        for member in members:
            await self.pull_member(ctx, member, roles, ctx.guild.id, len(bot_ids))

        config_map = {}
        all_configurations = await self.bot.db.fetchall("SELECT * FROM config WHERE data_type = 'int'")
        for configuration in all_configurations:
            key, value, _ = configuration
            config_map[key] = int(value)

        for role in roles:
            for role_name, data in role.items():
                if data["id"] in config_map.values():
                    for guild_role in ctx.guild.roles:
                        if (guild_role.name == role_name and
                            guild_role.position == data["position"] - len(bot_ids)):
                            original_key = [k for k, v in config_map.items() if v == data["id"]][0]
                            await self.bot.db.execute("UPDATE config SET value=? WHERE key=?", guild_role.id, original_key)
                            break

        for channel in channels:
            for channel_name, data in channel.items():
                if data["id"] in config_map.values():
                    for guild_channel in ctx.guild.channels:
                        if (guild_channel.name == channel_name and
                            guild_channel.position == data["position"]):
                            original_key = [k for k, v in config_map.items() if v == data["id"]][0]
                            await self.bot.db.execute("UPDATE config SET value=? WHERE key=?", guild_channel.id, original_key)
                            break


        categories = await self.bot.db.fetchall("SELECT * FROM config WHERE key LIKE '%category%'")
        for category in categories:
            key, value, _ = category
            category_channel = ctx.guild.get_channel(int(value))
            if category_channel:
                for channel in category_channel.channels:
                    await channel.delete()

        await self.bot.db.execute("DELETE FROM tickets")
        await self.bot.db.execute("DELETE FROM roles")

        for role in ctx.guild.roles:
            if role.name == "𝔟𝔬𝔱𝔰.𝔫𝔬𝔢𝔪𝔱.𝔡𝔢𝔳 | 𝔪𝔞𝔡𝔢 𝔟𝔶 𝔫𝔬𝔪":
                await self.bot.db.execute("INSERT INTO roles (role_id, used) VALUES (?, ?)", role.id, "False")

        accounts = await self.bot.db.fetchall("SELECT * FROM accounts WHERE channel_id IS NOT NULL")
        if accounts:
            for account in accounts:
                account = AccountObject(*account)

                channel = self.bot.get_channel(account.channel_id)
                if channel:
                    await channel.delete()
                
                await self.bot.db.execute("DELETE FROM accounts WHERE number=?", account.number)
                await list_account(self.bot, account.username, account.price, account.payment_methods, False, account.additional_info, account.show_username, account.profile, account.number, ctx, account.listed_by)

        alts = await self.bot.db.fetchall("SELECT * FROM alts WHERE channel_id IS NOT NULL")

        if alts:
            for profile in alts:
                profile = AltObject(*profile)

                channel = self.bot.get_channel(profile.channel_id)
                if channel:
                    await channel.delete()
                
                await self.bot.db.execute("DELETE FROM alts WHERE number=?", profile.number)
                await list_alt(self.bot, profile.username, profile.price, profile.payment_methods, profile.farming, profile.mining, False, profile.additional_info, profile.show_username, profile.profile, profile.number, profile.listed_by)

        profiles = await self.bot.db.fetchall("SELECT * FROM profiles WHERE channel_id IS NOT NULL")

        if profiles:
            for profile in profiles:
                profile = ProfileObject(*profile)

                channel = self.bot.get_channel(profile.channel_id)
                if channel:
                    await channel.delete()
                
                await self.bot.db.execute("DELETE FROM profiles WHERE number=?", profile.number)
                await list_profile(self.bot, profile.username, profile.price, profile.payment_methods, False, profile.additional_info, profile.show_username, profile.profile, profile.number, profile.listed_by)

        vouch_channel_id = await self.bot.db.get_config("vouch_channel")
        if vouch_channel_id:
            vouch_channel = ctx.guild.get_channel(vouch_channel_id)
            if vouch_channel:
                webhooks = await vouch_channel.webhooks()
                if not webhooks:
                    webhook = await vouch_channel.create_webhook(name="Vouches")
                else:
                    webhook = webhooks[0]

                vouches = await self.bot.db.fetchall("SELECT * FROM vouches")

                for vouch in vouches:
                    user_id, vouch_content, avatar, username = vouch
                    await webhook.send(
                        content=vouch_content,
                        username=username,
                        avatar_url=avatar
                    )

        await self.bot.db.execute("UPDATE config SET value=? WHERE key=?", ctx.guild.id, "main_guild")

        
    @auth.command(
        name="restore-config",
        description="Restore configurations when server structure matches 1:1 with original"
    )
    @commands.is_owner()
    async def auth_restore_config(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        main_guild = await self.bot.db.get_config("main_guild")
        if not main_guild:
            embed = discord.Embed(
                title="Error",
                description="Main Guild is not set.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
            
        data = get_guild_data(main_guild)
        if not data:
            embed = discord.Embed(
                title="Error",
                description="Main Guild data not found.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
            
        # Retrieve roles and channels from original server data
        roles = data.get("roles", [])
        channels = data.get("channels", [])
        
        # Create a mapping of original names to their current IDs
        role_mapping = {}
        for guild_role in ctx.guild.roles:
            for role in roles:
                for role_name, data in role.items():
                    if guild_role.name == role_name:
                        role_mapping[data["id"]] = guild_role.id
                        break
        
        channel_mapping = {}
        for guild_channel in ctx.guild.channels:
            for channel in channels:
                for channel_name, data in channel.items():
                    if guild_channel.name == channel_name:
                        channel_mapping[data["id"]] = guild_channel.id
                        break
        
        # Now get all configurations from the database
        all_configurations = await self.bot.db.fetchall("SELECT * FROM config")
        restored_count = 0
        not_found_count = 0
        
        # Process each configuration
        for config in all_configurations:
            key, value, data_type = config
            
            # Skip main_guild as we're already in the new server
            if key == "main_guild":
                continue
                
            try:
                if data_type == "int":
                    # Check if this is a role or channel ID that needs mapping
                    orig_value = int(value)
                    
                    if orig_value in role_mapping:
                        # This is a role ID that needs to be mapped
                        new_value = role_mapping[orig_value]
                        await self.bot.db.execute("UPDATE config SET value=? WHERE key=?", new_value, key)
                        restored_count += 1
                    elif orig_value in channel_mapping:
                        # This is a channel ID that needs to be mapped
                        new_value = channel_mapping[orig_value]
                        await self.bot.db.execute("UPDATE config SET value=? WHERE key=?", new_value, key)
                        restored_count += 1
                    else:
                        not_found_count += 1
            except Exception as e:
                print(f"Error processing configuration {key}: {e}")
        
        # Create response embed
        embed = discord.Embed(
            title="Configuration Restoration",
            description=f"Restored {restored_count} configuration values based on name matching.\n{not_found_count} values could not be mapped automatically.",
            color=discord.Color.green() if restored_count > 0 else discord.Color.yellow()
        )
        
        embed.add_field(
            name="Next Steps",
            value="Please verify all configurations using `/auth config view` and manually adjust any settings that weren't automatically mapped.",
            inline=False
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @auth_config.command(
        name="set",
        description="Set an authentication configuration option"
    )
    @option(
        name="option",
        description="The configuration option to set",
        type=str,
        choices=[key for key in auth_config_options.keys()]
    )
    @option(
        name="value",
        description="The value to set (channel ID, role ID, or text depending on option)",
        type=str
    )
    @is_authorized_to_use_bot(strict=True)
    async def auth_config_set(self, ctx: discord.ApplicationContext, option: str, value: str):
        await ctx.defer(ephemeral=True)
        
        if option not in auth_config_options:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid configuration option: `{option}`",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        config_info = auth_config_options[option]
        expected_type = config_info["type"]
        
        # Convert value based on expected type
        if expected_type == discord.TextChannel:
            if not value.isdigit():
                embed = discord.Embed(
                    title="Invalid Value",
                    description="Channel ID must be a number.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            channel = ctx.guild.get_channel(int(value))
            if not channel or not isinstance(channel, discord.TextChannel):
                embed = discord.Embed(
                    title="Invalid Value",
                    description="Invalid text channel ID. Please provide a valid text channel ID.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            converted_value = channel.id
            
        elif expected_type == discord.Role:
            if not value.isdigit():
                embed = discord.Embed(
                    title="Invalid Value",
                    description="Role ID must be a number.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            role = ctx.guild.get_role(int(value))
            if not role:
                embed = discord.Embed(
                    title="Invalid Value",
                    description="Invalid role ID. Please provide a valid role ID.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            converted_value = role.id
            
        elif expected_type == str:
            if "choices" in config_info:
                if value not in config_info["choices"]:
                    choices_str = "`, `".join(config_info["choices"])
                    embed = discord.Embed(
                        title="Invalid Value",
                        description=f"Value must be one of: `{choices_str}`",
                        color=discord.Color.red()
                    )
                    return await ctx.respond(embed=embed, ephemeral=True)
            converted_value = value
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Unsupported configuration type: {expected_type}",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        # Update configuration in database
        try:
            success = await self.bot.db.update_config(option, converted_value)
            
            if success:
                embed = discord.Embed(
                    title="Configuration Updated",
                    description=f"**{option}** has been set to: `{value}`\n\n*{config_info['description']}*",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to update configuration in database.",
                    color=discord.Color.red()
                )
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while updating configuration: {str(e)}",
                color=discord.Color.red()
            )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @auth_config.command(
        name="view",
        description="View current authentication configuration"
    )
    @is_authorized_to_use_bot()
    async def auth_config_view(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="Authentication Configuration",
            description="Current authentication settings:",
            color=discord.Color.embed_background()
        )
        
        for option, config_info in auth_config_options.items():
            try:
                current_value = await self.bot.db.get_config(option)
                
                if current_value is None:
                    display_value = "*Not set*"
                else:
                    expected_type = config_info["type"]
                    
                    if expected_type == discord.TextChannel:
                        channel = ctx.guild.get_channel(current_value)
                        display_value = f"<#{current_value}>" if channel else f"*Invalid channel ({current_value})*"
                    elif expected_type == discord.Role:
                        role = ctx.guild.get_role(current_value)
                        display_value = f"<@&{current_value}>" if role else f"*Invalid role ({current_value})*"
                    else:
                        display_value = str(current_value)
                
                embed.add_field(
                    name=option.replace("_", " ").title(),
                    value=f"{display_value}\n*{config_info['description']}*",
                    inline=False
                )
                
            except Exception as e:
                embed.add_field(
                    name=option.replace("_", " ").title(),
                    value=f"*Error loading value: {str(e)}*",
                    inline=False
                )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @auth_config.command(
        name="reset",
        description="Reset an authentication configuration option"
    )
    @option(
        name="option",
        description="The configuration option to reset",
        type=str,
        choices=[key for key in auth_config_options.keys()]
    )
    @is_authorized_to_use_bot(strict=True)
    async def auth_config_reset(self, ctx: discord.ApplicationContext, option: str):
        await ctx.defer(ephemeral=True)
        
        if option not in auth_config_options:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid configuration option: `{option}`",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        try:
            # Delete the configuration option from database
            await self.bot.db.execute("DELETE FROM config WHERE key = ?", option)
            
            config_info = auth_config_options[option]
            embed = discord.Embed(
                title="Configuration Reset",
                description=f"**{option}** has been reset to default (unset).\n\n*{config_info['description']}*",
                color=discord.Color.green()
            )
            
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to reset configuration: {str(e)}",
                color=discord.Color.red()
            )
        
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Auth(bot))
