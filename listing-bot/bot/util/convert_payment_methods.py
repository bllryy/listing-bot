from bot.bot import Bot

def convert_payment_methods(bot: Bot, methods: str) -> str:
    if not methods:
        return ""
    
    single_methods = methods.split('/')
    emojis = []
    
    for method in single_methods:
        method_clean = method.strip().upper()
        emoji = bot.get_emoji(method_clean)
        if emoji is not None:
            emojis.append(emoji)
        else:
            # Fallback to the method name if emoji not found
            emojis.append(method.strip().title())
    
    return '/'.join(emojis)