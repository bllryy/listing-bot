from bot.bot import Bot

async def get_available_number(bot: Bot, table):
    """
    Returns the first available number in the given table.
    """

    number = 1
    while await bot.db.fetchone(f"SELECT * FROM {table} WHERE number=?", number):
        number += 1

    return number
