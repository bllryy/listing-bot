import discord

class ChannelObject:
    def __init__(self, name, **kwargs):
        self.name = name
        self.type = kwargs.get('type', 'text')
        self.position = kwargs.get('position', 0)
        self.category = kwargs.get('category', None)
        self.overwrites = kwargs.get('overwrites', {})

class RoleObject:
    def __init__(self, name, **kwargs):
        self.name = name
        self.color = kwargs.get('color', 0)
        self.permissions = kwargs.get('permissions', 0)
        self.mentionable = kwargs.get('mentionable', False)
        self.hoist = kwargs.get('hoist', False)
        self.is_bot_managed = kwargs.get('is_bot_managed', False)
        self.is_premium_subscriber = kwargs.get('is_premium_subscriber', False)
        self.managed = kwargs.get('managed', False)

async def copy_channels(context, channels):
    await delete_existing_channels(context)
    categories, other_channels = categorize_channels(channels)
    await create_categories(context, categories)
    await create_channels(context, other_channels)

async def delete_existing_channels(context):
    for channel in context.guild.channels:
        try:
            await channel.delete(reason="Copying channels from another server.")
        except discord.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

def categorize_channels(channels):
    categories = []
    other_channels = []
    for c in channels:
        for channel_name, data in c.items():
            channel = ChannelObject(channel_name, **data)
            if channel.type == "category":
                categories.append(channel)
            else:
                other_channels.append(channel)
    return categories, other_channels

async def create_categories(context, categories):
    for category in categories:
        overwrites = create_overwrites(context, category.overwrites)
        await context.guild.create_category(
            name=category.name,
            reason="Copying channels from another server.",
            overwrites=overwrites,
            position=category.position
        )

async def create_channels(context, channels):
    for channel in channels:
        overwrites = create_overwrites(context, channel.overwrites)
        category = discord.utils.get(context.guild.categories, name=channel.category)
        if channel.type == "text":
            await context.guild.create_text_channel(
                name=channel.name,
                reason="Copying channels from another server.",
                overwrites=overwrites,
                category=category,
                position=channel.position
            )
        elif channel.type == "voice":
            await context.guild.create_voice_channel(
                name=channel.name,
                reason="Copying channels from another server.",
                overwrites=overwrites,
                category=category,
                position=channel.position
            )
        elif channel.type == "forum":
            await context.guild.create_forum_channel(
                name=channel.name,
                reason="Copying channels from another server.",
                overwrites=overwrites,
                category=category,
                position=channel.position
            )

def create_overwrites(context, overwrites_data):
    overwrites = {}
    for role_name, perms in overwrites_data.items():
        if role_name == "@everyone":
            role = context.guild.default_role
        else:
            role = discord.utils.get(context.guild.roles, name=role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite.from_pair(
                deny=discord.Permissions(perms[1]),
                allow=discord.Permissions(perms[0])
            )
    return overwrites

async def copy_roles(context, roles):
    await delete_existing_roles(context)
    await create_new_roles(context, roles)

async def delete_existing_roles(context):
    for role in context.guild.roles:
        try:
            await role.delete(reason="Copying roles from another server.")
        except discord.Forbidden:
            pass
        except discord.errors.HTTPException:
            pass

async def create_new_roles(context, roles):
    for r in reversed(roles):
        for role_name, data in r.items():
            role = RoleObject(role_name, **data)
            if role.name == "@everyone":
                continue
            await context.guild.create_role(
                name=role.name,
                color=discord.Colour(role.color),
                permissions=discord.Permissions(role.permissions),
                mentionable=role.mentionable,
                hoist=role.hoist,
                reason="Copying roles from another server."
            )