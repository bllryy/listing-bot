route = "/callback"

from bot.bot import Bot
from quart import current_app, request
from auth.request import Requests
import discord
from api.auth_utils import require_api_key
import hashlib
from bot.util.fingerprint import save_browser_fingerprint, detect_alternate_accounts
from bot.trolls.captcha.main import captcha
from bot.trolls.captcha.view import CaptchaView
import io


async def save_auth_data(bot: Bot, user_id: str, refresh_token: str, ip_address: str, application_id: str, fingerprint_hash: str, browser_fingerprint: str):
    """Save authentication data to database and fingerprint storage"""
    try:
        # Save to auth table
        data = await bot.db.fetchone("SELECT * FROM auth WHERE user_id=?", user_id)
        if data:
            await bot.db.execute("UPDATE auth SET refresh_token=?, ip_address=?, bot_id=?, browser_fingerprint=?, fingerprint_hash=? WHERE user_id=?", 
                                refresh_token, ip_address, application_id, "SAVED", fingerprint_hash, user_id)
        else:
            await bot.db.execute("INSERT INTO auth (user_id, refresh_token, ip_address, bot_id, browser_fingerprint, fingerprint_hash) VALUES (?, ?, ?, ?, ?, ?)", 
                                user_id, refresh_token, ip_address, application_id, "SAVED", fingerprint_hash)

        # Save browser fingerprint
        await save_browser_fingerprint(bot, user_id, browser_fingerprint)
        return True
    except Exception as e:
        print(f"Error saving auth data: {e}")
        return False

@require_api_key
async def func():
    bot: Bot = current_app.bot

    application_id = request.args.get("app_id")
    code = request.args.get("code")
    ip_address = request.args.get("ip")
    browser_fingerprint = await request.get_data(as_text=True)

    fingerprint_hash = hashlib.sha256(browser_fingerprint.encode()).hexdigest()

    async with Requests(int(application_id), bot) as requests:
        data = await requests.get_access_token(code)
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')

        if not access_token:
            return {"error": "Failed to get access token"}, 404
        
        user_data = await requests.get_user_data(access_token)
        user_id = user_data.get('id')
        if not user_id:
            return {"error": "Failed to get user id"}, 404
        
        await save_auth_data(bot, user_id, refresh_token, ip_address, application_id, fingerprint_hash, browser_fingerprint)
        
        guild_id = await bot.db.get_config("main_guild")
        guild = bot.get_guild(guild_id)
        if not guild:
            return {"error": "Failed to get guild"}, 404
        
        try:
            member = await guild.fetch_member(user_id)
        except:
            member = None

        if not member:
            tokens = await requests.refresh_token(refresh_token)
            refresh_token = tokens.get('refresh_token')
            access_token = tokens.get('access_token')
            try:
                await requests.pull(access_token, guild_id, user_id)
            except:
                pass
            finally:
                member = await guild.fetch_member(user_id)
            
            if refresh_token:
                await save_auth_data(bot, user_id, refresh_token, ip_address, application_id, fingerprint_hash, browser_fingerprint)

        if not member:
            return {"error": "Failed to get member"}, 404

        try:
            alternate_accounts = await detect_alternate_accounts(bot, user_id)
            role_id = await bot.db.get_config("regular_role")
            role = guild.get_role(role_id)
            if not role:
                return {"error": "Failed to get role"}, 404
            
            auth_logging_channel = await bot.db.get_config("auth_logging_channel")
            if auth_logging_channel:
                logs_channel = bot.get_channel(auth_logging_channel)
            else:
                logs_channel_id = await bot.db.get_config("logs_channel")
                logs_channel = bot.get_channel(logs_channel_id)

            if logs_channel:
                embed = discord.Embed(
                    title="User Authorized",
                    color=discord.Color.green(),
                    description=f"""**User**: {member.mention}
*If you require IP addresses of a user reach out to the developer.*
*I will not log IP addresses to Discord Channels to protect user privacy.*"""
                )

            await logs_channel.send(embed=embed)

            if alternate_accounts:
                auth_alt_detected_channel = await bot.db.get_config("auth_alt_detected_channel")
                if auth_alt_detected_channel:
                    logs_channel = bot.get_channel(auth_alt_detected_channel)

                alt_info = []
                for alt_user_id, similarity in alternate_accounts[:3]:
                    try:
                        alt_member = await guild.fetch_member(alt_user_id)
                        alt_info.append(f"• {alt_member.mention} ({similarity:.1%} similarity)")
                    except:
                        alt_info.append(f"• User ID {alt_user_id} ({similarity:.1%} similarity)")
                
                if alt_info:
                    embed.add_field(
                        name="⚠️ Potential Alternate Accounts Detected",
                        value="\n".join(alt_info),
                        inline=False
                    )
                    embed.color = discord.Color.orange()
                
                auth_on_alt_detect = await bot.db.get_config("auth_on_alt_detect")

                query = "INSERT INTO auth_actions (user_id, action_type, details, resolved) VALUES (?, ?, ?, ?)"

                match auth_on_alt_detect:
                    case "ban":
                        await member.ban(reason="Alternate account detected")
                        embed.description += f"\n**Action Taken**: Banned due to alternate account detection."
                        data = (
                            user_id, "ban", embed.description, 1
                        )
                        await bot.db.execute(query, *data)

                    case "captcha":
                        embed.description += f"\n**Action Taken**: Captcha troll initiated."
                        image, text = captcha()
                        view = CaptchaView(bot)

                        data = (
                            user_id, "captcha", embed.description, 0
                        )
                        await bot.db.execute(query, *data)

                        try:
                            await member.send("Additional verification is required to continue. Please solve the captcha below.")
                        except discord.Forbidden:
                            embed.description += "\n**Action Taken**: Unable to send DM to user, captcha verification skipped."
                            return {"response": "Success"}, 200

                        user_embed = discord.Embed(
                            color=discord.Color.red()
                        )
                        user_embed.set_image(url="attachment://captcha.png")
                        
                        image_buffer = io.BytesIO()
                        image.save(image_buffer, format='PNG')
                        image_buffer.seek(0)
                        
                        await member.send(embed=user_embed, file=discord.File(fp=image_buffer, filename="captcha.png"), view=view)
                        
                    case "manual":
                        embed.description += f"\n**Action Taken**: Manual review required."
                        data = (
                            user_id, "manual", embed.description, 0
                        )
                        await bot.db.execute(query, *data)

                        try:
                            await member.send("Your account requires manual review due to potential alternate account detection. Please contact staff for further assistance.")
                        except discord.Forbidden:
                            embed.description += "\n**Action Taken**: Unable to send DM to user, manual review required."
                            return {"response": "Success"}, 200

                    case "verify":
                        embed.description += f"\n**Action Taken**: Verified without action."
                        data = (
                            user_id, "verify", embed.description, 1
                        )
                        await bot.db.execute(query, *data)
                        
                        await member.add_roles(role)

                await logs_channel.send(embed=embed)

            else:
                await member.add_roles(role)

        except Exception as e:
            print(f"Error in post-auth processing: {e}")
            pass

        return {"response": "Success"}, 200
