import base64
from bot.bot import Bot
import base64
from bot.util.constants import bot_name

class Auth:
    def __init__(self, client_id: int, bot: Bot):
        self.bot = bot
        self.client_id = client_id

    async def init(self):
        client_id, client_secret, bot_token, redirect_uri = await self.bot.db.fetchone("SELECT * FROM auth_bots WHERE client_id=?", self.client_id)

        self.bot_token = bot_token
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        encoded_client_id = bot_token.split('.')[0]
        padded_encoded_client_id = encoded_client_id + '=' * (-len(encoded_client_id) % 4)
        self.client_id = base64.b64decode(padded_encoded_client_id).decode('utf-8')

        self.scope = "%20".join(["identify", "guilds.join", "guilds"])

    def get_url(self) -> str:
        state = f'{self.client_id},{bot_name}'
        return f'https://discord.com/api/oauth2/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope={self.scope}&state={base64.b64encode(state.encode()).decode()}'

    def generate_headers(self, header_type: str, access_token: str = None):
        
        if header_type in ['refresh_token', 'get_access_token']:
            return { 'Content-Type': 'application/x-www-form-urlencoded' }
        
        elif header_type == 'pull':
            return { 'Authorization': f'Bot {self.bot_token}', 'Content-Type': 'application/json' }
        
        elif header_type == 'get_user_data':
            return { 'Authorization': f'Bearer {access_token}' }
        
    def generate_payload(self, body_type: str, refresh_token: str = None, access_token: str = None, code: str = None):

        if body_type == 'refresh_token':
            return {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
        
        elif body_type == 'get_access_token':
            return {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            }
        
        elif body_type == 'pull':
            return { 'access_token': access_token }
