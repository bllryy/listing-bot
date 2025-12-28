import discord
from discord.ext import commands
from discord import option, SlashCommandGroup

from bot.bot import Bot

allowed_types = ["sell", "buy"]
ticket_types = ["coins", "mfa", "profile", "alt", "account"]
special_types = ["middleman"]

ticket_types = [f"{t}-{tt}" for t in allowed_types for tt in ticket_types] + special_types

class Roles(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    roles = SlashCommandGroup("roles", description="Commands related to custom ticket roles")

    @roles.command(name="add", description="Add roles to a ticket type (up to 5 roles)")
    @option("ticket_type", description="The ticket type to add roles to", choices=ticket_types)
    @option("role1", description="First role to add", type=discord.Role)
    @option("role2", description="Second role to add", type=discord.Role, required=False)
    @option("role3", description="Third role to add", type=discord.Role, required=False)
    @option("role4", description="Fourth role to add", type=discord.Role, required=False)
    @option("role5", description="Fifth role to add", type=discord.Role, required=False)
    @commands.is_owner()
    async def add_roles(self, ctx, ticket_type: str, role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None, role4: discord.Role = None, role5: discord.Role = None):
        await ctx.defer(ephemeral=True)

        roles = [role1, role2, role3, role4, role5]
        roles = [r for r in roles if r is not None]

        if not roles:
            embed = discord.Embed(
                title="Error",
                description="You must provide at least one role.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        # Remove duplicates while preserving order
        seen = set()
        unique_roles = []
        for role in roles:
            if role.id not in seen:
                seen.add(role.id)
                unique_roles.append(role)

        # Delete existing roles for this ticket type
        await self.bot.db.execute("DELETE FROM ticket_roles WHERE ticket_type = ?", ticket_type)

        # Insert new roles
        for role in unique_roles:
            await self.bot.db.execute("INSERT INTO ticket_roles (role_id, ticket_type) VALUES (?, ?)", role.id, ticket_type)
        
        embed = discord.Embed(
            title="Roles Added Successfully",
            description=f"Added {len(unique_roles)} role(s) to ticket type `{ticket_type}`",
            color=discord.Color.green()
        )
        
        role_list = "\n".join([f"• {role.mention} ({role.name})" for role in unique_roles])
        embed.add_field(name="Roles", value=role_list, inline=False)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @roles.command(name="remove", description="Remove specific roles from a ticket type")
    @option("ticket_type", description="The ticket type to remove roles from", choices=ticket_types)
    @option("role1", description="First role to remove", type=discord.Role)
    @option("role2", description="Second role to remove", type=discord.Role, required=False)
    @option("role3", description="Third role to remove", type=discord.Role, required=False)
    @option("role4", description="Fourth role to remove", type=discord.Role, required=False)
    @option("role5", description="Fifth role to remove", type=discord.Role, required=False)
    @commands.is_owner()
    async def remove_roles(self, ctx, ticket_type: str, role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None, role4: discord.Role = None, role5: discord.Role = None):
        await ctx.defer(ephemeral=True)

        roles = [role1, role2, role3, role4, role5]
        roles = [r for r in roles if r is not None]

        # Get existing roles for this ticket type
        existing_roles = await self.bot.db.fetchall("SELECT role_id FROM ticket_roles WHERE ticket_type = ?", ticket_type)
        existing_role_ids = [row[0] for row in existing_roles]
        
        roles_to_remove = [role for role in roles if role.id in existing_role_ids]
        roles_not_found = [role for role in roles if role.id not in existing_role_ids]

        if not roles_to_remove:
            embed = discord.Embed(
                title="Error",
                description=f"None of the specified roles are assigned to ticket type `{ticket_type}`",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        # Remove the roles
        for role in roles_to_remove:
            await self.bot.db.execute("DELETE FROM ticket_roles WHERE ticket_type = ? AND role_id = ?", ticket_type, role.id)
        
        embed = discord.Embed(
            title="Roles Removed Successfully",
            description=f"Removed {len(roles_to_remove)} role(s) from ticket type `{ticket_type}`",
            color=discord.Color.green()
        )
        
        removed_roles = [f"• {role.mention} ({role.name})" for role in roles_to_remove]
        embed.add_field(name="Removed Roles", value="\n".join(removed_roles), inline=False)
        
        if roles_not_found:
            not_found_roles = [f"• {role.mention} ({role.name})" for role in roles_not_found]
            embed.add_field(name="Roles Not Found in Ticket Type", value="\n".join(not_found_roles), inline=False)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @roles.command(name="clear", description="Remove all roles from a ticket type")
    @option("ticket_type", description="The ticket type to clear roles from", choices=ticket_types)
    @commands.is_owner()
    async def clear_roles(self, ctx, ticket_type: str):
        await ctx.defer(ephemeral=True)

        existing_roles = await self.bot.db.fetchall("SELECT role_id FROM ticket_roles WHERE ticket_type = ?", ticket_type)
        
        if not existing_roles:
            embed = discord.Embed(
                title="No Roles Found",
                description=f"No roles are currently assigned to ticket type `{ticket_type}`",
                color=discord.Color.yellow()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        await self.bot.db.execute("DELETE FROM ticket_roles WHERE ticket_type = ?", ticket_type)

        embed = discord.Embed(
            title="Roles Cleared Successfully",
            description=f"Removed all {len(existing_roles)} role(s) from ticket type `{ticket_type}`",
            color=discord.Color.green()
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @roles.command(name="view", description="View all roles assigned to ticket types")
    @option("ticket_type", description="View roles for a specific ticket type (optional)", choices=ticket_types, required=False)
    @commands.is_owner()
    async def view_roles(self, ctx, ticket_type: str = None):
        await ctx.defer(ephemeral=True)

        if ticket_type:
            roles = await self.bot.db.fetchall("SELECT role_id FROM ticket_roles WHERE ticket_type = ?", ticket_type)
            
            if not roles:
                embed = discord.Embed(
                    title="No Roles Found",
                    description=f"No roles are assigned to ticket type `{ticket_type}`",
                    color=discord.Color.yellow()
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            embed = discord.Embed(
                title=f"Roles for {ticket_type}",
                color=discord.Color.blue()
            )
            
            role_list = []
            for role_row in roles:
                role = ctx.guild.get_role(role_row[0])
                if role:
                    role_list.append(f"• {role.mention} ({role.name})")
                else:
                    role_list.append(f"• Deleted Role ({role_row[0]})")
            
            embed.add_field(name=f"Roles ({len(roles)})", value="\n".join(role_list), inline=False)
            
        else:
            all_roles = await self.bot.db.fetchall("SELECT ticket_type, role_id FROM ticket_roles ORDER BY ticket_type")
            
            if not all_roles:
                embed = discord.Embed(
                    title="No Roles Found",
                    description="No roles are assigned to any ticket types",
                    color=discord.Color.yellow()
                )
                return await ctx.respond(embed=embed, ephemeral=True)

            embed = discord.Embed(
                title="All Ticket Type Roles",
                color=discord.Color.blue()
            )
            
            ticket_role_map = {}
            for ticket_type_db, role_id in all_roles:
                if ticket_type_db not in ticket_role_map:
                    ticket_role_map[ticket_type_db] = []
                
                role = ctx.guild.get_role(role_id)
                if role:
                    ticket_role_map[ticket_type_db].append(f"• {role.mention}")
                else:
                    ticket_role_map[ticket_type_db].append(f"• Deleted Role ({role_id})")
            
            for ticket_type_name, role_mentions in ticket_role_map.items():
                embed.add_field(
                    name=f"{ticket_type_name} ({len(role_mentions)})",
                    value="\n".join(role_mentions),
                    inline=True
                )
        
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(Roles(bot))