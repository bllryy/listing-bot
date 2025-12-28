import discord
from discord.ext import commands

from bot.bot import Bot
from discord import SlashCommandGroup, option

from bot.util.constants import is_authorized_to_use_bot
from bot.util.sellauth import create_checkout

class SellAuth(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    sellauth = SlashCommandGroup("sellauth", description="Commands related to SellAuth")

    @sellauth.command(
        name="checkout",
        description="Create a checkout for a product."
    )
    @option("price", description="Price of the product in USD", type=float)
    @option("seller", description="The seller", type=discord.Member)
    async def create_checkout(self, ctx: discord.ApplicationContext, price: float, seller: discord.Member):
        await ctx.defer()

        checkout_url = await create_checkout(price, seller.id, self.bot)
        if checkout_url:
            embed = discord.Embed(
                title="✅ Checkout Created Successfully",
                description=f"A secure checkout has been created for this transaction.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="💰 Price",
                value=f"${price:.2f} USD",
                inline=True
            )
            embed.add_field(
                name="👤 Seller",
                value=f"{seller.mention}\n({seller.display_name})",
                inline=True
            )
            embed.add_field(
                name="🔗 URL",
                value=f"[Click here to proceed]({checkout_url})",
                inline=False
            )
            embed.set_footer(text="This checkout link is secure and processed through SellAuth")
            
            view = discord.ui.View()
            checkout_button = discord.ui.Button(
                label="Open Checkout",
                style=discord.ButtonStyle.url,
                url=checkout_url,
                emoji="🛒"
            )
            view.add_item(checkout_button)
            
            await ctx.respond(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title="Checkout Failed",
                description="Failed to create checkout. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed)

    @sellauth.command(
        name="configure",
        description="Configure your SellAuth store details."
    )
    @option("product_id", description="Product ID for your store", type=int)
    @option("variant_id", description="Variant ID for your product", type=int)
    @option("shop_id", description="Shop ID for your store", type=int)
    @option("shop_name", description="Shop name for your store", type=str)
    @is_authorized_to_use_bot()
    async def configure_store(self, ctx: discord.ApplicationContext, product_id: int, variant_id: int, shop_id: int, shop_name: str):
        await ctx.defer(ephemeral=True)

        await self.bot.db.execute("""
            INSERT OR REPLACE INTO sellauth_config (user_id, product_id, variant_id, shop_id, shop_name)
            VALUES (?, ?, ?, ?, ?)
        """, ctx.author.id, product_id, variant_id, shop_id, shop_name)
        embed = discord.Embed(
            title="Store Configuration Updated",
            description="Your SellAuth store details have been successfully updated.",
            color=discord.Color.green()
        )
        embed.add_field(name="Product ID", value=str(product_id), inline=True)
        embed.add_field(name="Variant ID", value=str(variant_id), inline=True)
        embed.add_field(name="Shop ID", value=str(shop_id), inline=True)
        embed.add_field(name="Shop Name", value=shop_name, inline=True)
        await ctx.respond(embed=embed, ephemeral=True)

    @sellauth.command(
        name="setup",
        description="View setup instructions for SellAuth integration."
    )
    @is_authorized_to_use_bot()
    async def setup_instructions(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)

        embed = discord.Embed(
            title="📋 SellAuth Setup Instructions",
            description="Follow these steps to configure SellAuth integration:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Step 1: Create SellAuth Account",
            value="• Go to [SellAuth](https://sellauth.com)\n• Create your account\n• Set up your store (The name you enter there will be your Shop Name)",
            inline=False
        )
        
        embed.add_field(
            name="Step 2: Get Store Details",
            value="• Navigate to your product page\n• Find your Product ID (**Price of one cent!**)\n• Locate your Variant ID\n• Note your Shop ID",
            inline=False
        )
        
        embed.add_field(
            name="Step 3: Configure Bot",
            value=f"• Use {self.bot.get_command_link('sellauth configure')} command\n• Enter all required IDs\n• Verify configuration is working",
            inline=False
        )
        
        embed.add_field(
            name="Step 4: Test Integration",
            value="• Create a test checkout\n• Verify payment processing.",
            inline=False
        )
        
        embed.set_footer(text="Contact support if you need help with any of these steps")
        
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot: Bot):
    bot.add_cog(SellAuth(bot))