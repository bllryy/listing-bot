import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
from bot.bot import Bot
import json

class Domains(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    domains = SlashCommandGroup("domains", description="Commands related to domain management")

    @domains.command(
        name="use",
        description="List all domains managed by the bot"
    )
    @option(
        "domain",
        description="The domain to use",
        type=str,
        required=True
    )
    @commands.is_owner()
    async def use_domain(self, ctx: discord.ApplicationContext, domain: str):
        await ctx.defer(ephemeral=True)
        if domain.startswith("https://") or domain.startswith("http://"):
            return await ctx.respond("Please provide a domain without the protocol (http:// or https://).", ephemeral=True)
        
        domain = domain.strip().lower()
        if domain.endswith("/"):
            domain = domain[:-1]

        domain_file_path = "../parent_api/custom_domains.json"
        try:
            with open(domain_file_path, "r") as f:
                domains = json.load(f)
            domains.append(domain)
        except FileNotFoundError:
            domains = [domain]
        except json.JSONDecodeError:
            return await ctx.respond("Error reading the domain file. Please check the file format.", ephemeral=True)
        except Exception as e:
            return await ctx.respond(f"An unexpected error occurred: {str(e)}", ephemeral=True)
        try:
            with open(domain_file_path, "w") as f:
                json.dump(domains, f, indent=4)
        except Exception as e:
            return await ctx.respond(f"An error occurred while saving the domain: {str(e)}", ephemeral=True)

        await self.bot.db.execute("UPDATE auth_bots SET redirect_uri=?", f'https://{domain}/authorize')
        await self.bot.db.update_config("domain", domain)

        embed = discord.Embed(
            title="Domain Updated",
            description=f"The domain has been set to `{domain}`.",
            color=discord.Color.green()
        )
        setup = discord.Embed(
            title="Setup Instructions",
            description=f"""To use the bot with the new domain, please follow these steps:
1. Manage your DNS settings on your domain registrar.
2. Set up a CNAME record pointing from root ({domain}, or simpler `@` if you're using Cloudflare) to `domains.noemt.dev`.
## If you use my integrated auth system:
Add the following to your **all** bot's redirect URIs:
`https://{domain}/authorize`
"""
        )
        await ctx.respond(embeds=[embed, setup], ephemeral=True)

    @domains.command(
        name="reset",
        description="Reset the domain to the default"
    )
    @commands.is_owner()
    async def reset_domain(self, ctx: discord.ApplicationContext):
        await self.bot.db.execute("UPDATE auth_bots SET redirect_uri=?", "https://v2.noemt.dev/authorize")
        await self.bot.db.update_config("domain", "v2.noemt.dev")

        embed = discord.Embed(
            title="Domain Reset",
            description="The domain has been reset to the default.",
            color=discord.Color.green()
        )
        await ctx.respond(embeds=[embed], ephemeral=True)

def setup(bot: Bot):
    bot.add_cog(Domains(bot))
