route = "/value"

from bot.bot import Bot
from quart import current_app, request, jsonify
from api.auth_utils import require_api_key

from bot.util.calcs import gather_lowball_value, gather_value

@require_api_key
async def func(data: dict):
    bot: Bot = current_app.bot

    """
    request JSON structure:
    {
        catacombs: { 
            dungeons: { 
                catacombs: { 
                    skill: { 
                        totalXp: int
                    }
                }
            }
        },
        slayer: { 
            zombie: { xp: int },
            spider: { xp: int },
            wolf: { xp: int },
            enderman: { xp: int },
            blaze: { xp: int }
        },
        networth: {
            purse: int,
            bank: int,
            personalBank: int,
            types: {
                ... {
                    items: [
                        {
                            price: float,
                            soulbound: bool,
                            cosmetic: bool,
                            calculation: [
                                ...[
                                    
                                ]
                            ]
                        }
                    ]
                }
            }
        }, // recommended: use skyhelper-networth package to get this data, this function is written for that structure.
        skills: {
            ... {
                xp: int
            }
        },
        mining: { 
            mithril_powder: {
                total: int
            },
            gemstone_powder: {
                total: int
            },
            glacite_powder: {
                total: int
            }
        },
        farming: { 
            jacob: {
                unique_golds: int,
                perks: {
                    ... : int // only perks that matter are double_drops and farming_level_cap
                }
            }

        },
        crimson: {
            factions: {
                ... : int // the ... may be mage or barbarian, those factions, the number is the reputation
            },
            kuudra: {
                ... : {} // the data inside doesn't really matter, just the keys, like "none", "hot", etc.
            }
        }
    }
    """

    lowball_value = gather_lowball_value(data)
    total_value = gather_value(data)
    return jsonify({
        "success": True,
        "data": {
            "lowball_value": lowball_value,
            "total_value": total_value
        }
    })
