import discord
from discord.ext import commands
from discord import SlashCommandGroup, option
import aiohttp

import urllib.parse
import io
from datetime import datetime
import qrcode
from bot.util.constants import is_authorized_to_use_bot

from bot.bot import Bot

class Payments(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    async def fetch_crypto_price(self, crypto_id):
        """Fetch current cryptocurrency price in USD from CoinGecko API"""
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data[crypto_id]["usd"]
                    else:
                        return None
        except Exception as e:
            print(f"Error fetching crypto price: {e}")
            return None

    async def convert_usd_to_crypto(self, usd_amount, crypto_type):
        """Convert USD amount to cryptocurrency amount"""
        crypto_id_map = {
            "bitcoin": "bitcoin",
            "ethereum": "ethereum",
            "litecoin": "litecoin"
        }
        
        crypto_id = crypto_id_map.get(crypto_type)
        crypto_price = await self.fetch_crypto_price(crypto_id)
        
        if not crypto_price or crypto_price <= 0:
            return None
            
        crypto_amount = round(usd_amount / crypto_price, 8)
        return crypto_amount

    payments = SlashCommandGroup("payments", description="Payment and invoice management commands")

    @payments.command(
        name="setup",
        description="Set up your payment details for invoicing"
    )
    @option("payment_type", description="Type of payment to set up", 
            choices=["paypal", "bitcoin", "ethereum", "litecoin"], type=str)
    @option("address", description="Email (PayPal) or wallet address (crypto)", type=str)
    @option("business_name", description="Optional business name for invoices", type=str, required=False)
    @option("currency", description="Default currency for PayPal (default: USD)", type=str, required=False, default="USD")
    @is_authorized_to_use_bot()
    async def setup_payments(self, ctx: discord.ApplicationContext, 
                           payment_type: str, address: str, 
                           business_name: str = None, currency: str = "USD"):
        await ctx.defer(ephemeral=True)
        
        if payment_type == "paypal":
            if "@" not in address or "." not in address:
                embed = discord.Embed(
                    title="Error",
                    description="Please enter a valid email address for PayPal.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
        elif payment_type in ["bitcoin", "ethereum", "litecoin"]:
            if len(address) < 26:
                embed = discord.Embed(
                    title="Error",
                    description=f"The {payment_type} address appears to be too short. Please verify it.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
        existing = await self.bot.db.fetchone("SELECT * FROM payment_details WHERE user_id=?", ctx.author.id)
        
        if existing:
            if payment_type == "paypal":
                await self.bot.db.execute(
                    "UPDATE payment_details SET paypal_email=?, business_name=?, currency=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?",
                    address, business_name, currency.upper(), ctx.author.id
                )
            else:
                column_name = f"{payment_type}_address"
                query = f"UPDATE payment_details SET {column_name}=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?"
                await self.bot.db.execute(query, address, ctx.author.id)
                
                if business_name:
                    await self.bot.db.execute(
                        "UPDATE payment_details SET business_name=? WHERE user_id=? AND business_name IS NULL",
                        business_name, ctx.author.id
                    )
            
            action = "updated"
        else:
            if payment_type == "paypal":
                await self.bot.db.execute(
                    "INSERT INTO payment_details (user_id, paypal_email, business_name, currency) VALUES (?, ?, ?, ?)",
                    ctx.author.id, address, business_name, currency.upper()
                )
            else:
                column_name = f"{payment_type}_address"
                columns = ["user_id", column_name]
                values = [ctx.author.id, address]
                
                if business_name:
                    columns.append("business_name")
                    values.append(business_name)
                
                columns_str = ", ".join(columns)
                placeholders = ", ".join(["?" for _ in columns])
                query = f"INSERT INTO payment_details ({columns_str}) VALUES ({placeholders})"
                
                await self.bot.db.execute(query, *values)
            
            action = "set up"
        
        payment_name = payment_type.capitalize()
        embed = discord.Embed(
            title="Payment Details Saved",
            description=f"Your {payment_name} payment method has been {action} successfully.",
            color=discord.Color.green()
        )
        
        if payment_type == "paypal":
            embed.add_field(name="PayPal Email", value=address)
            embed.add_field(name="Default Currency", value=currency.upper())
        else:
            embed.add_field(name=f"{payment_name} Address", value=f"`{address}`")
        
        if business_name:
            embed.add_field(name="Business Name", value=business_name, inline=False)
        
        await ctx.respond(embed=embed, ephemeral=True)

    @payments.command(
        name="methods",
        description="View or update your saved payment methods"
    )
    @is_authorized_to_use_bot()
    async def view_payment_methods(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        payment_details = await self.bot.db.fetchone(
            "SELECT paypal_email, bitcoin_address, ethereum_address, litecoin_address, business_name, currency FROM payment_details WHERE user_id=?", 
            ctx.author.id
        )
        
        if not payment_details:
            embed = discord.Embed(
                title="No Payment Methods Found",
                description="You haven't set up any payment methods yet. Use `/payments setup` to get started.",
                color=discord.Color.orange()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        paypal_email, btc_address, eth_address, ltc_address, business_name, currency = payment_details
        
        embed = discord.Embed(
            title="Your Payment Methods",
            description=f"Business name: {business_name or 'Not set'}",
            color=discord.Color.blue()
        )
        
        if paypal_email:
            embed.add_field(name="PayPal", value=f"Email: {paypal_email}\nCurrency: {currency}", inline=False)
        
        if btc_address:
            embed.add_field(name="Bitcoin", value=f"`{btc_address}`", inline=False)
        
        if eth_address:
            embed.add_field(name="Ethereum", value=f"`{eth_address}`", inline=False)
        
        if ltc_address:
            embed.add_field(name="Litecoin", value=f"`{ltc_address}`", inline=False)
        
        embed.set_footer(text="Use /payments setup to add or update payment methods")
        
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(
        name="invoice", 
        description="Create an invoice for the customer to pay (amount in USD)"
    )
    @option("amount", description="Amount to invoice in USD (e.g. 20.99)", type=float)
    @option("payment_method", description="Payment method to use", 
            choices=["paypal", "bitcoin", "ethereum", "litecoin"], type=str)
    @option("description", description="Description of what's being sold", type=str, required=False)
    @option("currency", description="Currency code (for PayPal, default: USD)", type=str, required=False)
    @is_authorized_to_use_bot()
    async def create_invoice(self, ctx: discord.ApplicationContext, 
                           amount: float, payment_method: str,
                           description: str = None, currency: str = None):
        await ctx.defer(ephemeral=True)
        
        columns = "paypal_email, bitcoin_address, ethereum_address, litecoin_address, business_name, currency"
        payment_details = await self.bot.db.fetchone(
            f"SELECT {columns} FROM payment_details WHERE user_id=?", ctx.author.id
        )
        
        if not payment_details:
            embed = discord.Embed(
                title="Payment Setup Required",
                description="You need to set up your payment details first with `/payments setup`.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        paypal_email, btc_address, eth_address, ltc_address, business_name, default_currency = payment_details
        business_name = business_name or ctx.author.display_name
        
        if payment_method == "paypal" and not paypal_email:
            embed = discord.Embed(
                title="PayPal Not Set Up",
                description="You need to set up your PayPal email first with `/payments setup paypal`.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        if payment_method == "bitcoin" and not btc_address:
            embed = discord.Embed(
                title="Bitcoin Address Not Set Up",
                description="You need to set up your Bitcoin address first with `/payments setup bitcoin`.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
            
        if payment_method == "ethereum" and not eth_address:
            embed = discord.Embed(
                title="Ethereum Address Not Set Up",
                description="You need to set up your Ethereum address first with `/payments setup ethereum`.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
            
        if payment_method == "litecoin" and not ltc_address:
            embed = discord.Embed(
                title="Litecoin Address Not Set Up",
                description="You need to set up your Litecoin address first with `/payments setup litecoin`.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        invoice_description = description or f"Payment to {business_name}"
        
        if payment_method == "paypal":
            invoice_currency = (currency or default_currency).upper()
            formatted_amount = "{:.2f}".format(amount)
            
            params = {
                "cmd": "_xclick",
                "business": paypal_email,
                "amount": formatted_amount,
                "currency_code": invoice_currency,
                "item_name": invoice_description,
                "no_shipping": "1",
                "no_note": "0",
                "cn": f"{ctx.channel.id}",
                "payment_type": "gift"
            }
            
            paypal_base_url = "https://www.paypal.com/cgi-bin/webscr"
            payment_link = f"{paypal_base_url}?{urllib.parse.urlencode(params)}"
            
            customer_embed = discord.Embed(
                title=f"Invoice for {formatted_amount} {invoice_currency}",
                description=f"**Item:** {invoice_description}\n**Seller:** {business_name}",
                color=discord.Color.blue()
            )
            customer_embed.add_field(name="Amount", value=f"{formatted_amount} {invoice_currency}")
            customer_embed.add_field(name="Payment Method", value="PayPal (Friends & Family)")
            customer_embed.add_field(name="Instructions", value="Click the button below to pay via Friends & Family", inline=False)
            customer_embed.set_footer(text=f"Created by {ctx.author.name} • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            class PaymentView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(
                        label=f"Pay {formatted_amount} {invoice_currency}",
                        url=payment_link,
                        style=discord.ButtonStyle.url
                    ))
            
            view = PaymentView()
            await ctx.respond("Invoice created successfully!", ephemeral=True)
            await ctx.channel.send(embed=customer_embed, view=view)
            
        else:
            crypto_name = payment_method.capitalize()
            crypto_address = None
            
            if payment_method == "bitcoin":
                crypto_address = btc_address
            elif payment_method == "ethereum":
                crypto_address = eth_address
            elif payment_method == "litecoin":
                crypto_address = ltc_address
            
            crypto_amount = await self.convert_usd_to_crypto(amount, payment_method)
            
            if crypto_amount is None:
                embed = discord.Embed(
                    title="Conversion Error",
                    description=f"Could not fetch current {crypto_name} price. Please try again later.",
                    color=discord.Color.red()
                )
                return await ctx.respond(embed=embed, ephemeral=True)
            
            qr_data = f"{payment_method}:{crypto_address}?amount={crypto_amount}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            qr_file = discord.File(buffer, filename="payment_qr.png")
            
            customer_embed = discord.Embed(
                title=f"Invoice for ${amount:.2f} USD",
                description=f"**Item:** {invoice_description}\n**Seller:** {business_name}",
                color=discord.Color.red()
            )
            customer_embed.add_field(name="Amount (USD)", value=f"${amount:.2f}")
            customer_embed.add_field(name=f"Amount ({crypto_name})", value=f"{crypto_amount:.8f}")
            customer_embed.add_field(name="Payment Method", value=crypto_name)
            customer_embed.add_field(name=f"{crypto_name} Address", value=f"`{crypto_address}`", inline=False)
            customer_embed.add_field(
                name="Instructions", 
                value=f"Scan the QR code below or send exactly **{crypto_amount:.8f} {crypto_name}** to the address above", 
                inline=False
            )
            customer_embed.set_footer(text=f"Created by {ctx.author.name} • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            customer_embed.set_image(url="attachment://payment_qr.png")

            invoice_view = discord.ui.View()
            view_address = discord.ui.Button(
                label=f"Copy {crypto_name} Address",
                style=discord.ButtonStyle.primary
            )

            async def copy_address_callback(interaction: discord.Interaction):
                await interaction.response.send_message(
                    crypto_address, 
                    ephemeral=True
                )

            view_address.callback = copy_address_callback

            view_amount = discord.ui.Button(
                label=f"Copy Amount ({crypto_name})",
                style=discord.ButtonStyle.primary
            )
            async def copy_amount_callback(interaction: discord.Interaction):
                await interaction.response.send_message(
                    f"{crypto_amount:.8f}", 
                    ephemeral=True
                )
            view_amount.callback = copy_amount_callback

            invoice_view.add_item(view_address)
            invoice_view.add_item(view_amount)

            await ctx.respond("Invoice created successfully!", ephemeral=True)
            await ctx.channel.send(embed=customer_embed, file=qr_file, view=invoice_view)

    @commands.slash_command(
        name="setup-email",
        description="Set up your email for hosting payments."
    )
    @option("email", description="Your email address.", type=str)
    @is_authorized_to_use_bot(strict=True)
    async def setup_email(self, ctx: discord.ApplicationContext, email: str):
        await ctx.defer(ephemeral=True)
        
        if "@" not in email or "." not in email:
            embed = discord.Embed(
                title="Invalid Email",
                description="Please enter a valid email address.",
                color=discord.Color.red()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO config (key, value, data_type) VALUES (?, ?, ?)",
            "email_address", email, "str"
        )
        
        embed = discord.Embed(
            title="Email Set Up",
            description=f"Your email `{email}` has been set up successfully for payments.",
            color=discord.Color.green()
        )
        
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Payments(bot))