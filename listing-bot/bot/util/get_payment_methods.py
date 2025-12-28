from bot.bot import Bot

async def get_payment_methods(bot: Bot, user_id: int):
    data = await bot.db.fetchone("SELECT * FROM sellers WHERE user_id=?", user_id)
    if data:
        return data[1]
    return None