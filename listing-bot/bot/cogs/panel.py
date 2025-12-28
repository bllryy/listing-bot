import discord
from discord import SlashCommandGroup
from discord.ext import commands
from bot.bot import Bot

from bot.util.constants import is_authorized_to_use_bot

from bot.util.panels.account import AccountSale
from bot.util.panels.profile import ProfileSale
from bot.util.panels.alt import AltSale
from bot.util.panels.coin import CoinSale
from bot.util.panels.mfa import MFASale
from bot.util.panels.middleman import Middleman
from bot.util.transform import abbreviate

class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    panel = SlashCommandGroup("panel", description="Commands related to ticket panels")

    @panel.command(
        name="account",
        description="Send the account panel"
    )
    @is_authorized_to_use_bot()
    async def account_panel(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="Sell an Account", description="Click the button below to sell an account", color=discord.Color.red())
        view = AccountSale(bot=self.bot)
        await ctx.send(embed=embed, view=view)

        await ctx.respond("Panel created!", ephemeral=True)

    @panel.command(
        name="profile",
        description="Send the profile panel"
    )
    @is_authorized_to_use_bot()
    async def profile_panel(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="Sell a Profile", description="Click the button below to sell a profile", color=discord.Color.red())
        view = ProfileSale(bot=self.bot)
        await ctx.send(embed=embed, view=view)

        await ctx.respond("Panel created!", ephemeral=True)

    @panel.command(
        name="alt",
        description="Send the alt panel"
    )
    @is_authorized_to_use_bot()
    async def alt_panel(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="Sell an Alt", description="Click the button below to sell an alt", color=discord.Color.red())
        view = AltSale(bot=self.bot)
        await ctx.send(embed=embed, view=view)

        await ctx.respond("Panel created!", ephemeral=True)

    @panel.command(
        name="middleman",
        description="Send the middleman panel"
    )
    @is_authorized_to_use_bot()
    async def middleman_panel(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="Middleman Panel", description="Click the button below to request a middleman", color=discord.Color.red())
        view = Middleman(bot=self.bot)
        await ctx.send(embed=embed, view=view)

        await ctx.respond("Panel created!", ephemeral=True)

    @panel.command(
        name="mfa",
        description="Send the alt panel"
    )
    @is_authorized_to_use_bot()
    async def mfa_panel(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="MFA Panel", description="Interact with the buttons to buy or sell MFA's", color=discord.Color.red())
        view = MFASale(bot=self.bot)

        rank_emojies = {
            "non": f"{self.bot.get_emoji('NON_LEFT')}{self.bot.get_emoji('NON_RIGHT')}",
            "vip": f"{self.bot.get_emoji('VIP_LEFT')}{self.bot.get_emoji('VIP_RIGHT')}",
            "vip+": f"{self.bot.get_emoji('VIP_LEFT')}{self.bot.get_emoji('VIPPLUS_RIGHT')}",
            "mvp": f"{self.bot.get_emoji('MVP_LEFT')}{self.bot.get_emoji('MVP_RIGHT')}",
            "mvp+": f"{self.bot.get_emoji('MVP_LEFT')}{self.bot.get_emoji('MVP_PLUS_RIGHT')}",
        }

        ranks = ["non", "vip", "vip+", "mvp", "mvp+"]
        for rank in ranks:
            rank_price = await self.bot.db.get_config(f"{rank}_price")
            if rank_price:
                embed.add_field(name=rank_emojies.get(rank), value=f"**${rank_price}**", inline=True)

        await ctx.send(embed=embed, view=view)

        await ctx.respond("Panel created!", ephemeral=True)

    @panel.command(
        name="coins",
        description="Send the coin panel"
    )
    @is_authorized_to_use_bot()
    async def coin_panel(self, ctx: discord.ApplicationContext):

        buy_base = await self.bot.db.get_config("coin_price_buy")
        sell_base = await self.bot.db.get_config("coin_price_sell")

        async def get_tiers(tier_type):
            tiers = []
            tier_num = 1
            while True:
                key = f"{tier_type}_coins_tier_{tier_num}"
                value = await self.bot.db.get_config(key)
                if not value:
                    break
                try:
                    threshold, price = value.split(';')
                    tiers.append({
                        "threshold": int(threshold),
                        "price": float(price)
                    })
                    tier_num += 1
                except:
                    break
            return sorted(tiers, key=lambda x: x["threshold"])

        buy_tiers = await get_tiers("buy")
        sell_tiers = await get_tiers("sell")

        def build_price_string(base_price, tiers):
            string = f"Base Price: **${base_price}/mil**\n" if base_price else ""
            for tier in tiers:
                string += f"`${tier['price']}/mil` above {abbreviate(tier['threshold'])}\n"
            return string or "Not configured"

        buy_str = build_price_string(buy_base, buy_tiers)
        sell_str = build_price_string(sell_base, sell_tiers)

        embed = discord.Embed(title="Coin Panel", description="Click the button below to buy/sell coins", color=discord.Color.red())
        embed.add_field(name="Buy Prices", value=buy_str, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Sell Prices", value=sell_str, inline=True)

        view = CoinSale(bot=self.bot)
        await ctx.send(embed=embed, view=view)
        await ctx.respond("Panel created!", ephemeral=True)

    @panel.command(
        name="multiple",
        description="Create a combined panel with multiple ticket types"
    )
    @is_authorized_to_use_bot()
    async def multipanel(self, ctx: discord.ApplicationContext):
        """Create a combined panel with components from selected panels"""
        view = PanelSelectView(self)
        await ctx.respond("Select panels to combine:", view=view, ephemeral=True)
        await view.wait()
        
        if not view.selected:
            return await ctx.edit(content="Panel creation cancelled.", view=None)

        components = []
        
        for panel_name in view.selected:
            if panel_name == "account":
                view = AccountSale(bot=self.bot)
                children = []
                for child in view.children:
                    child.row = None
                    children.append(child)

                components.extend(children)
            
            elif panel_name == "profile":
                view = ProfileSale(bot=self.bot)
                children = []
                for child in view.children:
                    child.row = None
                    children.append(child)
                    
                components.extend(children)

            elif panel_name == "alt":
                view = AltSale(bot=self.bot)
                children = []
                for child in view.children:
                    child.row = None
                    children.append(child)
                    
                components.extend(children)

            elif panel_name == "mfa":
                view = MFASale(bot=self.bot)
                children = []
                for child in view.children:
                    child.row = None
                    children.append(child)
                    
                components.extend(children)

            elif panel_name == "coins":
                view = CoinSale(bot=self.bot)
                children = []
                for child in view.children:
                    child.row = None
                    children.append(child)
                    
                components.extend(children)

            elif panel_name == "middleman":
                view = Middleman(bot=self.bot)
                children = []
                for child in view.children:
                    child.row = None
                    children.append(child)
                    
                components.extend(children)

        combined_view = discord.ui.View(timeout=None)
        for component in components:
            combined_view.add_item(component)

        embed = discord.Embed(
            title="Open a Ticket",
            description="Click the buttons below to open a ticket.",
            color=discord.Color.red()
        )

        await ctx.send(embed=embed, view=combined_view)
        await ctx.edit(content="Multipanel created!", view=None)

    async def _create_coin_embed(self):
        """Helper to create coin panel embed (reused from coins command)"""
        buy_base = await self.bot.db.get_config("coin_price_buy")
        sell_base = await self.bot.db.get_config("coin_price_sell")

        async def get_tiers(tier_type):
            tiers = []
            tier_num = 1
            while True:
                key = f"{tier_type}_coins_tier_{tier_num}"
                value = await self.bot.db.get_config(key)
                if not value: break
                try:
                    t, p = value.split(';')
                    tiers.append({"threshold": int(t), "price": float(p)})
                    tier_num += 1
                except: break
            return sorted(tiers, key=lambda x: x["threshold"])

        buy_tiers = await get_tiers("buy")
        sell_tiers = await get_tiers("sell")

        def build_price_string(base, tiers):
            string = f"Base: **${base}/mil**\n" if base else ""
            for tier in tiers:
                string += f"`${tier['price']}/mil` above {abbreviate(tier['threshold'])}\n"
            return string or "Not configured"

        embed = discord.Embed(title="Coin Trading", color=discord.Color.red())
        embed.add_field(name="Buy Prices", value=build_price_string(buy_base, buy_tiers), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Sell Prices", value=build_price_string(sell_base, sell_tiers), inline=True)
        
        return embed
    
class PanelSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60, disable_on_timeout=True)
        self.cog = cog
        self.selected = []
        
        self.select = discord.ui.Select(
            placeholder="Choose panels to combine...",
            min_values=1,
            max_values=5,
            options=[
                discord.SelectOption(label="Account", value="account"),
                discord.SelectOption(label="Profile", value="profile"),
                discord.SelectOption(label="Alt", value="alt"),
                discord.SelectOption(label="MFA", value="mfa"),
                discord.SelectOption(label="Coins", value="coins"),
                discord.SelectOption(label="Middleman", value="middleman"),
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        self.selected = self.select.values
        await interaction.response.defer()
        self.stop()

    
def setup(bot):
    bot.add_cog(Panel(bot))


