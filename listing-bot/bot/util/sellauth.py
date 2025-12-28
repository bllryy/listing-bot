import asyncio
import json
import httpx
import os
from dotenv import load_dotenv
import hashlib
import base64

from bot.bot import Bot

load_dotenv()

async def get_store_details(bot: Bot, user_id: int):
    query = await bot.db.fetchone("""
        SELECT product_id, variant_id, shop_id, shop_name
        FROM sellauth_config WHERE user_id = ?
    """, user_id)
    if query:
        product_id, variant_id, shop_id, shop_name = query
        return product_id, variant_id, shop_id, shop_name
    return None

async def solve_altcha(client: httpx.AsyncClient):
    try:
        response = await client.get("https://api-internal-2.sellauth.com/v1/altcha")
        response.raise_for_status()
        challenge_data = response.json()
        
        challenge = challenge_data['challenge']
        salt = challenge_data['salt']
        algorithm = challenge_data['algorithm']
        max_number = challenge_data['maxnumber']
        signature = challenge_data['signature']
        
        
        for number in range(max_number + 1):
            input_str = f"{salt}{number}"
            hash_hex = hashlib.sha256(input_str.encode()).hexdigest()
            
            if hash_hex == challenge:
                payload = {
                    'algorithm': algorithm,
                    'challenge': challenge,
                    'number': number,
                    'salt': salt,
                    'signature': signature
                }
                
                payload_str = json.dumps(payload, separators=(',', ':'))
                return base64.b64encode(payload_str.encode()).decode()
        
        return None
    except Exception as e:
        return None

async def create_checkout(price: float, seller_id: int, bot: Bot):
    """Create a checkout with specified quantity"""

    store_details = await get_store_details(bot, seller_id)
    if not store_details:
        return None
    
    productId, variantId, shopId, shopName = store_details
    
    cart = [{
        'productId': productId,
        'variantId': variantId,
        'quantity': price*100
    }]
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://{shopName}.mysellauth.com/',
        'Origin': f'https://{shopName}.mysellauth.com',
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        altcha_token = await solve_altcha(client)
        if not altcha_token:
            return None
                
        body = {
            'cart': cart,
            'shopId': shopId,
            'currency': 'USD',
            'altcha': altcha_token,
        }
        
        try:
            response = await client.post(
                'https://api-internal-2.sellauth.com/v1/checkout/',
                headers=headers,
                json=body,
                timeout=10.0
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('error'):
                return None
            
            checkout_url = data.get('url')
            if checkout_url:
                return checkout_url
            else:
                return None
                
        except Exception as e:
            return None
