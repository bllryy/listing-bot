from chat_exporter.construct.attachment_handler import AttachmentHandler
import discord
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

class CustomHandler(AttachmentHandler):
    """Custom handler for processing attachments."""
    
    def __init__(self, api_url: str = "", api_key: str = "API_KEY"):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key or os.getenv("API_KEY")
        
        if not self.api_key:
            raise ValueError("API key must be provided either as parameter or in .env file as API_KEY")

    async def process_asset(self, attachment: discord.Attachment) -> discord.Attachment:
        """Process the asset and return the modified attachment object."""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch attachment: {response.status}")
                data = await response.read()
                
            
            form_data = aiohttp.FormData()
            form_data.add_field('file', data, filename=attachment.filename, content_type=attachment.content_type or 'application/octet-stream')
            form_data.add_field('filename', attachment.filename)
            form_data.add_field('attachment_id', str(attachment.id))
            
            upload_url = f"{self.api_url}/api/upload/attachment"
            headers = {"X-API-Key": self.api_key}
            
            async with session.post(upload_url, data=form_data, headers=headers) as upload_response:
                if upload_response.status != 200:
                    response_text = await upload_response.text()
                    raise Exception(f"Failed to upload attachment: {upload_response.status} - {response_text}")
                
                safe_filename = f"{attachment.id}_{attachment.filename}"
                server_url = f"{self.api_url}/static/uploads/{safe_filename}"
                
                attachment.url = server_url
                attachment.proxy_url = server_url
                
                return attachment