import socket
from api.api import create_api
from bot.bot import create_bot
from dotenv import load_dotenv
import json
import os
import traceback


from contextlib import closing

def get_available_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

load_dotenv()
app = create_api()
bot = create_bot()

bot_name = os.path.basename(os.getcwd())

try:
    with open("../parent_api/ports.json", "r") as f:
        ports: dict = json.load(f)

    port = ports.get(bot_name, get_available_port())
    ports[bot_name] = port

    with open("../parent_api/ports.json", "w") as f:
        json.dump(ports, f, indent=4)

except FileNotFoundError:
    print("Warning: parent_api/ports.json not found, using default port 3080")
    port = 3080
except json.JSONDecodeError as e:
    print(f"Warning: Failed to parse ports.json: {e}, using default port 3080")
    port = 3080
except Exception as e:
    print(f"Warning: Unexpected error reading ports.json: {e}, using default port 3080")
    port = 3080

try:
    bot.run(app, port)
except Exception as e:
    error_info = f"Fatal error starting bot: {str(e)}\n{traceback.format_exc()}"
    raise