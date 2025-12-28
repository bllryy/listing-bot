from bot.bot import Bot
import discord

def get_role_config_name(ticket_type: str):
    role_configs_for_specific_ticket_types = {}
    
    for action in ["buy", "sell"]:
        for item_type in ["account", "profile", "alt", "mfa"]:
            role_key = f"{item_type}_seller_role"
            ticket_key = f"{action}-{item_type}"
            role_configs_for_specific_ticket_types[ticket_key] = role_key
        
        role_configs_for_specific_ticket_types[f"{action}-coins"] = "coin_seller_role"
    
    role_configs_for_specific_ticket_types["middleman"] = "middleman_role"

    if ticket_type in role_configs_for_specific_ticket_types:
        return role_configs_for_specific_ticket_types[ticket_type]

    return "seller_role"

async def get_default_overwrites(bot: Bot, guild_id: int, user_id: int = None, ticket_type: str = None, role_id_overwrite: int = None) -> tuple:

    # Initialize seller_role to None
    seller_role = None
    role_config_name = get_role_config_name(ticket_type)
    if role_config_name:
        config_exists = await bot.db.get_config(role_config_name)
        if config_exists:
            seller_role = config_exists
        else:
            seller_role = await bot.db.get_config("seller_role")

    # Fallback if no role config found
    if seller_role is None:
        seller_role = await bot.db.get_config("seller_role")

    regular_role = await bot.db.get_config("regular_role")

    guild = bot.get_guild(guild_id)
    if not guild:
        return {}, None, None
    
    # Convert role IDs to role objects (with None checks)
    seller_role = guild.get_role(seller_role) if seller_role else None
    regular_role = guild.get_role(regular_role) if regular_role else None

    # Find or create a role for this ticket (normalize boolean comparisons)
    if not role_id_overwrite:
        # Try multiple boolean representations for backward compatibility
        available_role = await bot.db.fetchone("SELECT * FROM roles WHERE used = ? OR used = ? OR used = ?", 0, "0", "False")
    else:
        available_role = await bot.db.fetchone("SELECT * FROM roles WHERE role_id=?", role_id_overwrite)

    if available_role:
        # Mark role as used (use consistent boolean representation)
        await bot.db.execute("UPDATE roles SET used = ? WHERE role_id = ?", 1, available_role[0])
        role = guild.get_role(available_role[0])
        if not role:
            role_name = "𝔟𝔬𝔱𝔰.𝔫𝔬𝔢𝔪𝔱.𝔡𝔢𝔳 | 𝔪𝔞𝔡𝔢 𝔟𝔶 𝔫𝔬𝔪"
            role = await guild.create_role(name=role_name, reason="Ticket System")
            await bot.db.execute("UPDATE roles SET role_id = ? WHERE role_id = ?", role.id, available_role[0])

    else:
        role_name = "𝔟𝔬𝔱𝔰.𝔫𝔬𝔢𝔪𝔱.𝔡𝔢𝔳 | 𝔪𝔞𝔡𝔢 𝔟𝔶 𝔫𝔬𝔪"
        role = await guild.create_role(name=role_name, reason="Ticket System")
        await bot.db.execute("INSERT INTO roles (role_id, used) VALUES (?, ?)", role.id, 1)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    # Add staff roles for ticket type
    roles = []
    if ticket_type:
        roles = await bot.db.fetchall("SELECT role_id FROM ticket_roles WHERE ticket_type = ?", ticket_type)
        for _role in roles:
            role_object = guild.get_role(_role[0])
            if role_object:
                overwrites[role_object] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    # If no specific roles configured for ticket type, use seller role
    if seller_role and not roles:
        overwrites[seller_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    if regular_role:
        overwrites[regular_role] = discord.PermissionOverwrite(read_messages=False, view_channel=False)
    
    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    if not user_id:
        return overwrites, role, None
    
    else:
        tos_agreed = await bot.db.fetchone("SELECT * FROM tos_agreed WHERE user_id = ?", user_id)
        if not tos_agreed:
            return overwrites, role, False
        
        else:
            return overwrites, role, True
