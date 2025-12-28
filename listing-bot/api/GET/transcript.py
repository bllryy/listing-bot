route = "/transcript/<transcript_name>"

import os
from bot.util.constants import bot_name
from api.auth_utils import require_api_key

@require_api_key
async def func(transcript_name: str):

    if not os.path.exists("./templates"):
        os.mkdir("./templates")
        return {"response": False}, 404
    
    if not os.path.exists(f"./templates/{transcript_name}"):
        if not os.path.exists(f"./templates/{bot_name}-{transcript_name}"):
            return {"response": False}, 404
        
        transcript_name = f"{bot_name}-{transcript_name}"
    else:
        transcript_name = f"{transcript_name}"
        
    with open(f"./templates/{transcript_name}", "r") as f:
        transcript = f.read()
        return {"response": transcript}, 200
