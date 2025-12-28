from bot.bot import Bot
import discord
import re

async def insert_vouch(bot: Bot, user_id: int, content: str, author: discord.User, anonymous: bool = False) -> bool:
    pattern = r'(\d+)\$|\$(\d+)|(\d+)\s?bucks'
    matches = re.findall(pattern, content)
    matches = [int(match) for group in matches for match in group if match and match.isdigit()]

    if "@everyone" in content or "@here" in content:
        try:
            await author.send("You can't mention everyone or here in your vouch message.")
            return False
        
        except:
            return False

    if anonymous:
        profile_picture = "https://images.rawpixel.com/image_800/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDI0LTEyL3YxMTk4LWJiLWVsZW1lbnQtMTUwLXgtbTUyM3o2cjYuanBn.jpg"
        username = "Anonymous Voucher"
    else:
        profile_picture = author.avatar.url if author.avatar else author.default_avatar.url
        username = author.display_name

    await bot.db.execute("INSERT INTO vouches (user_id, message, avatar, username) VALUES (?, ?, ?, ?)", user_id, content, profile_picture, username)
    return True