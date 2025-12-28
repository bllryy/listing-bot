route = "/bot/tickets"

from bot.bot import Bot
from quart import current_app
from api.auth_utils import require_api_key

@require_api_key
async def func():
    bot: Bot = current_app.bot
    
    tickets_data = await bot.db.fetchall("SELECT opened_by, channel_id, initial_message_id, role_id FROM tickets")
    
    tickets = []
    total_tickets = len(tickets_data)
    
    for ticket in tickets_data:
        opened_by, channel_id, initial_message_id, role_id = ticket
        
        # Get user and channel objects if possible
        user = bot.get_user(opened_by)
        username = user.name if user else "Unknown"
        
        channel = bot.get_channel(channel_id)
        channel_name = channel.name if channel else "Unknown"
        
        tickets.append({
            "opened_by": opened_by,
            "username": username,
            "channel_id": channel_id,
            "channel_name": channel_name,
            "initial_message_id": initial_message_id,
            "role_id": role_id
        })
    
    return {
        "total": total_tickets,
        "tickets": tickets
    }, 200