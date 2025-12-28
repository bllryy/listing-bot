from bot.bot import Bot

async def validate_sellauth_data(bot: Bot, api_key: str, store_id: str):
    """
    Fetch products from SellAuth API
    """
    url = f"https://api.sellauth.com/v1/shops/{store_id}/products"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    json_data = {
        "page": 1,
        "perPage": 1,
    }
    
    async with bot.session.get(url, json=json_data, headers=headers) as response:
        if response.status != 200:
            return False
        return True
    