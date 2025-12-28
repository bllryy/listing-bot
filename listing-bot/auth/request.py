import aiohttp
from aiohttp import BasicAuth
from .auth import Auth

import json
from bot.bot import Bot

class Requests:
    def __init__(self, client_id: int, bot: Bot):
        self.bot = bot
        self.session = None
        self.client_id = client_id

    async def init(self):
        client_id, client_secret, bot_token, redirect_uri = await self.bot.db.fetchone("SELECT * FROM auth_bots WHERE client_id=?", self.client_id)
        self.auth = Auth(client_id, self.bot)
        await self.auth.init()
        
        self.redirect_uri = redirect_uri
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()
    
    async def get_access_token(self, code: str) -> dict:
        headers = self.auth.generate_headers('get_access_token')
        payload = self.auth.generate_payload('get_access_token', code=code)

        auth = BasicAuth(self.auth.client_id, self.auth.client_secret)
        
        async with self.session.post('https://discord.com/api/v10/oauth2/token', headers=headers, data=payload, auth=auth) as response:
            return await response.json()

    async def get_user_data(self, access_token: str) -> dict:
        headers = self.auth.generate_headers('get_user_data', access_token=access_token)
        
        async with self.session.get('https://discord.com/api/v10/users/@me', headers=headers) as response:
            return await response.json()
        
    async def get_guilds_data(self, access_token: str):
        headers = self.auth.generate_headers('get_user_data', access_token=access_token)
        
        async with self.session.get('https://discord.com/api/v10/users/@me/guilds', headers=headers) as response:
            return await response.json()
        
    async def refresh_token(self, refresh_token: str) -> dict:
        headers = self.auth.generate_headers('refresh_token')
        payload = self.auth.generate_payload('refresh_token', refresh_token=refresh_token)

        auth = BasicAuth(self.auth.client_id, self.auth.client_secret)

        async with self.session.post('https://discord.com/api/v10/oauth2/token', headers=headers, data=payload, auth=auth) as response:
            return await response.json()
        
    async def pull(self, access_token: str, guild_id: str, user_id: str, roles: list = None) -> dict:
        headers = self.auth.generate_headers('pull')
        payload = self.auth.generate_payload('pull', access_token=access_token)

        if roles:
            payload['roles'] = roles

        payload_json = json.dumps(payload)

        try:
            async with self.session.put(f'https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}', headers=headers, data=payload_json) as response:
                return await response.json()
        except:
            return {}
        
    async def get_api_data(self, ip_address: str) -> dict:
        async with self.session.get(f'http://ipapi.co/{ip_address}/json') as response:
            return await response.json()
