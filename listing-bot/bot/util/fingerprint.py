import ujson as json
import logging
from typing import Dict, List, Tuple, Optional

async def save_browser_fingerprint(bot, user_id: int, fingerprint_data: str) -> bool:
    """
    Save browser fingerprint data to the database using normalized tables.
    
    Args:
        bot: Bot instance with database connection
        user_id: Discord user ID
        fingerprint_data: JSON string containing fingerprint data
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Handle the case where fingerprint_data might already be a dict or need parsing
        if isinstance(fingerprint_data, str):
            try:
                data = json.loads(fingerprint_data)
                logging.debug(f"Parsed JSON data type: {type(data)}")
                
                # Handle double-encoded JSON (JSON string containing another JSON string)
                if isinstance(data, str):
                    logging.debug("Data is still a string after first parse, attempting second parse")
                    data = json.loads(data)
                    logging.debug(f"Second parse data type: {type(data)}")
                    
            except (ValueError, TypeError) as e:
                logging.error(f"Invalid JSON fingerprint data for user {user_id}: {e}")
                logging.error(f"Raw fingerprint data: {fingerprint_data[:500]}...")
                return False
        elif isinstance(fingerprint_data, dict):
            data = fingerprint_data
        else:
            logging.error(f"Invalid fingerprint data type for user {user_id}: {type(fingerprint_data)}")
            return False
        
        # Validate that we have a dictionary
        if not isinstance(data, dict):
            logging.error(f"Fingerprint data is not a dictionary for user {user_id}: {type(data)}")
            logging.error(f"Data content sample: {str(data)[:200]}...")
            return False
        
        await _delete_existing_fingerprint(bot, user_id)
        
        await _save_main_fingerprint(bot, user_id, data)
        
        await _save_fingerprint_languages(bot, user_id, data.get("languages", []))
        await _save_fingerprint_fonts(bot, user_id, data.get("fonts", []))
        await _save_fingerprint_plugins(bot, user_id, data.get("plugins", []))
        await _save_fingerprint_webgl_extensions(bot, user_id, data.get("webgl", {}).get("extensions", []))
        await _save_fingerprint_storage(bot, user_id, data.get("storage", {}))
        await _save_fingerprint_protocols(bot, user_id, data.get("protocols", []))
        
        await _save_fingerprint_storage(bot, user_id, data.get("storage", {}))
        await _save_fingerprint_protocols(bot, user_id, data.get("protocols", []))
        
        logging.info(f"Browser fingerprint saved for user {user_id}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving browser fingerprint for user {user_id}: {e}")
        logging.error(f"Fingerprint data type: {type(fingerprint_data)}")
        logging.error(f"Fingerprint data sample: {str(fingerprint_data)[:200]}...")
        return False

async def _delete_existing_fingerprint(bot, user_id: int):
    """Delete all existing fingerprint data for a user."""
    tables = [
        "browser_fingerprints",
        "fingerprint_languages", 
        "fingerprint_fonts",
        "fingerprint_plugins",
        "fingerprint_webgl_extensions",
        "fingerprint_storage",
        "fingerprint_protocols"
    ]
    
    for table in tables:
        await bot.db.execute(f"DELETE FROM {table} WHERE user_id = ?", user_id)

async def _save_main_fingerprint(bot, user_id: int, data: dict):
    """Save main fingerprint data to browser_fingerprints table."""
    user_agent = data.get("userAgent", "")
    language = data.get("language", "")
    platform = data.get("platform", "")
    cookie_enabled = 1 if data.get("cookieEnabled", False) else 0
    hardware_concurrency = data.get("hardwareConcurrency", 0)
    device_memory = data.get("deviceMemory", 0)
    max_touch_points = data.get("maxTouchPoints", 0)
    
    # Screen data
    screen = data.get("screen", {})
    screen_width = screen.get("width", 0)
    screen_height = screen.get("height", 0)
    screen_color_depth = screen.get("colorDepth", 0)
    
    # Timezone data
    timezone = data.get("timezone", {})
    if isinstance(timezone, dict):
        timezone_name = timezone.get("name", "")
        timezone_offset = timezone.get("offset", 0)
    elif isinstance(timezone, str):
        timezone_name = timezone
        timezone_offset = 0
    else:
        timezone_name = ""
        timezone_offset = 0
    
    # Canvas data - Skip storing base64 data to save storage space
    canvas_text = ""
    canvas_geometry = ""
    
    # WebGL data
    webgl = data.get("webgl", {})
    webgl_vendor = webgl.get("vendor", "")
    webgl_renderer = webgl.get("renderer", "")
    webgl_unmasked_vendor = webgl.get("unmaskedVendor", "")
    webgl_unmasked_renderer = webgl.get("unmaskedRenderer", "")
    
    # Audio data
    audio = data.get("audio", {})
    if isinstance(audio, dict):
        audio_fingerprint = audio.get("fingerprint", "")
    else:
        audio_fingerprint = ""
    
    # Network data
    network = data.get("network", {})
    network_downlink = network.get("downlink", 0.0)
    network_effective_type = network.get("effectiveType", "")
    
    timestamp = data.get("timestamp", 0)
    
    await bot.db.execute("""
        INSERT INTO browser_fingerprints (
            user_id, user_agent, language, platform, cookie_enabled,
            hardware_concurrency, device_memory, max_touch_points, screen_width,
            screen_height, screen_color_depth, timezone_name, timezone_offset,
            webgl_vendor, webgl_renderer, webgl_unmasked_vendor, webgl_unmasked_renderer, 
            audio_fingerprint, network_downlink, network_effective_type, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, 
        user_id, user_agent, language, platform, cookie_enabled,
        hardware_concurrency, device_memory, max_touch_points, screen_width,
        screen_height, screen_color_depth, timezone_name, timezone_offset,
        webgl_vendor, webgl_renderer, webgl_unmasked_vendor, webgl_unmasked_renderer,
        audio_fingerprint, network_downlink, network_effective_type, timestamp
    )

async def _save_fingerprint_languages(bot, user_id: int, languages: list):
    """Save languages to normalized table."""
    for lang in languages:
        if lang:  # Skip empty strings
            await bot.db.execute(
                "INSERT INTO fingerprint_languages (user_id, language) VALUES (?, ?)",
                user_id, lang
            )

async def _save_fingerprint_fonts(bot, user_id: int, fonts: list):
    """Save fonts to normalized table."""
    for font in fonts:
        if font:  # Skip empty strings
            await bot.db.execute(
                "INSERT INTO fingerprint_fonts (user_id, font_name) VALUES (?, ?)",
                user_id, font
            )

async def _save_fingerprint_plugins(bot, user_id: int, plugins: list):
    """Save plugins to normalized table."""
    for plugin in plugins:
        if isinstance(plugin, dict):
            name = plugin.get("name", "")
            filename = plugin.get("filename", "")
            description = plugin.get("description", "")
            
            await bot.db.execute("""
                INSERT INTO fingerprint_plugins (user_id, plugin_name, plugin_filename, plugin_description) 
                VALUES (?, ?, ?, ?)
            """, user_id, name, filename, description)

async def _save_fingerprint_webgl_extensions(bot, user_id: int, extensions: list):
    """Save WebGL extensions to normalized table."""
    for ext in extensions:
        if ext:  # Skip empty strings
            await bot.db.execute(
                "INSERT INTO fingerprint_webgl_extensions (user_id, extension_name) VALUES (?, ?)",
                user_id, ext
            )

async def _save_fingerprint_storage(bot, user_id: int, storage: dict):
    """Save storage support to normalized table."""
    for storage_type, supported in storage.items():
        supported_int = 1 if supported else 0
        await bot.db.execute("""
            INSERT INTO fingerprint_storage (user_id, storage_type, supported) 
            VALUES (?, ?, ?)
        """, user_id, storage_type, supported_int)

async def _save_fingerprint_protocols(bot, user_id: int, protocols: list):
    """Save protocols to normalized table."""
    for protocol in protocols:
        if protocol:  # Skip empty strings
            await bot.db.execute(
                "INSERT INTO fingerprint_protocols (user_id, protocol) VALUES (?, ?)",
                user_id, protocol
            )

async def detect_alternate_accounts(bot, user_id: int) -> List[Tuple[int, float]]:
    """
    Detect potential alternate accounts by comparing browser fingerprints using efficient queries.
    
    Args:
        bot: Bot instance with database connection
        user_id: Discord user ID to check against
        
    Returns:
        List of tuples containing (suspected_user_id, similarity_probability)
    """
    try:
        # Get the current user's fingerprint
        current_fingerprint = await bot.db.fetchone(
            "SELECT * FROM browser_fingerprints WHERE user_id = ?", user_id
        )
        
        if not current_fingerprint:
            return []
        
        # Get all other users for comparison
        other_users = await bot.db.fetchall(
            "SELECT user_id FROM browser_fingerprints WHERE user_id != ?", user_id
        )
        
        if not other_users:
            return []
        
        suspects = []
        
        for (other_user_id,) in other_users:
            similarity = await _calculate_fingerprint_similarity_optimized(bot, user_id, other_user_id)
            
            # Only consider high similarity matches (above 85%)
            if similarity > 0.85:
                suspects.append((other_user_id, similarity))
        
        # Sort by similarity descending
        suspects.sort(key=lambda x: x[1], reverse=True)
        
        return suspects
        
    except Exception as e:
        logging.error(f"Error detecting alternate accounts for user {user_id}: {e}")
        return []

async def _calculate_fingerprint_similarity_optimized(bot, user1_id: int, user2_id: int) -> float:
    """
    Calculate similarity between two browser fingerprints using optimized queries.
    
    Args:
        bot: Bot instance with database connection
        user1_id: First user ID
        user2_id: Second user ID
        
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    try:
        # Get main fingerprint data for both users
        fp1 = await bot.db.fetchone("SELECT * FROM browser_fingerprints WHERE user_id = ?", user1_id)
        fp2 = await bot.db.fetchone("SELECT * FROM browser_fingerprints WHERE user_id = ?", user2_id)
        
        if not fp1 or not fp2:
            return 0.0
        
        # Weight different components by importance (canvas removed to save storage)
        weights = {
            'hardware': 0.30,  # hardware_concurrency, device_memory, screen resolution (increased from 0.25)
            'canvas': 0.00,    # canvas fingerprints (disabled to save storage)
            'webgl': 0.25,     # webgl vendor/renderer info (increased from 0.15)
            'system': 0.15,    # platform, user_agent patterns (increased from 0.10)
            'audio': 0.12,     # audio fingerprint (increased from 0.10)
            'languages': 0.08, # language preferences
            'fonts': 0.05,     # available fonts
            'plugins': 0.04,   # browser plugins
            'network': 0.01    # network characteristics (decreased from 0.03)
        }
        
        scores = {}
        
        # Hardware similarity (columns: 5=hardware_concurrency, 6=device_memory, 8=screen_width, 9=screen_height)
        hardware_score = 0.0
        if fp1[5] == fp2[5]:  # hardware_concurrency
            hardware_score += 0.4
        if fp1[6] == fp2[6]:  # device_memory
            hardware_score += 0.3
        if fp1[8] == fp2[8] and fp1[9] == fp2[9]:  # screen width/height
            hardware_score += 0.3
        scores['hardware'] = hardware_score
        
        # Canvas similarity (columns: 13=canvas_text, 14=canvas_geometry) - Always 0 since we don't store canvas data
        canvas_score = 0.0
        # Canvas data is not stored to save space, so similarity is always 0
        scores['canvas'] = canvas_score
        
        # WebGL similarity (columns: 13=webgl_vendor, 14=webgl_renderer, 15=webgl_unmasked_vendor, 16=webgl_unmasked_renderer)
        webgl_score = 0.0
        if fp1[15] == fp2[15] and fp1[15]:  # webgl_unmasked_vendor
            webgl_score += 0.5
        if fp1[16] == fp2[16] and fp1[16]:  # webgl_unmasked_renderer
            webgl_score += 0.5
        scores['webgl'] = webgl_score
        
        # System similarity (columns: 3=platform, 1=user_agent, 10=screen_color_depth)
        system_score = 0.0
        if fp1[3] == fp2[3]:  # platform
            system_score += 0.4
        if fp1[10] == fp2[10]:  # screen_color_depth
            system_score += 0.3
        # Check user agent similarity
        if fp1[1] and fp2[1]:
            if _extract_browser_pattern(fp1[1]) == _extract_browser_pattern(fp2[1]):
                system_score += 0.3
        scores['system'] = system_score
        
        # Audio similarity (column: 17=audio_fingerprint)
        audio_score = 0.0
        if fp1[17] == fp2[17] and fp1[17]:  # audio_fingerprint
            audio_score = 1.0
        scores['audio'] = audio_score
        
        # Languages similarity (using optimized query)
        languages_score = await _calculate_languages_similarity(bot, user1_id, user2_id)
        scores['languages'] = languages_score
        
        # Fonts similarity (using optimized query)
        fonts_score = await _calculate_fonts_similarity(bot, user1_id, user2_id)
        scores['fonts'] = fonts_score
        
        # Plugins similarity (using optimized query)
        plugins_score = await _calculate_plugins_similarity(bot, user1_id, user2_id)
        scores['plugins'] = plugins_score
        
        # Network similarity (columns: 18=network_downlink, 19=network_effective_type)
        network_score = 0.0
        if fp1[19] == fp2[19] and fp1[19]:  # network_effective_type
            network_score += 0.5
        if fp1[18] and fp2[18]:  # network_downlink
            downlink_diff = abs(fp1[18] - fp2[18])
            if downlink_diff < 1.0:
                network_score += 0.5
        scores['network'] = network_score
        
        # Calculate weighted similarity
        total_similarity = sum(scores[component] * weights[component] for component in weights)
        
        return min(total_similarity, 1.0)  # Cap at 1.0
        
    except Exception as e:
        logging.error(f"Error calculating fingerprint similarity: {e}")
        return 0.0

async def _calculate_languages_similarity(bot, user1_id: int, user2_id: int) -> float:
    """Calculate similarity between language preferences."""
    try:
        # Get languages for both users
        user1_langs = await bot.db.fetchall(
            "SELECT language FROM fingerprint_languages WHERE user_id = ?", user1_id
        )
        user2_langs = await bot.db.fetchall(
            "SELECT language FROM fingerprint_languages WHERE user_id = ?", user2_id
        )
        
        if not user1_langs or not user2_langs:
            return 0.0
        
        set1 = {lang[0] for lang in user1_langs}
        set2 = {lang[0] for lang in user2_langs}
        
        if not set1 or not set2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
        
    except Exception as e:
        logging.error(f"Error calculating languages similarity: {e}")
        return 0.0

async def _calculate_fonts_similarity(bot, user1_id: int, user2_id: int) -> float:
    """Calculate similarity between available fonts."""
    try:
        # Count matching fonts using a single query
        result = await bot.db.fetchone("""
            SELECT COUNT(*) FROM fingerprint_fonts f1 
            INNER JOIN fingerprint_fonts f2 ON f1.font_name = f2.font_name 
            WHERE f1.user_id = ? AND f2.user_id = ?
        """, user1_id, user2_id)
        
        matching_fonts = result[0] if result else 0
        
        # Get total unique fonts for both users
        total_result = await bot.db.fetchone("""
            SELECT COUNT(DISTINCT font_name) FROM fingerprint_fonts 
            WHERE user_id IN (?, ?)
        """, user1_id, user2_id)
        
        total_fonts = total_result[0] if total_result else 0
        
        if total_fonts == 0:
            return 0.0
        
        return matching_fonts / total_fonts
        
    except Exception as e:
        logging.error(f"Error calculating fonts similarity: {e}")
        return 0.0

async def _calculate_plugins_similarity(bot, user1_id: int, user2_id: int) -> float:
    """Calculate similarity between browser plugins."""
    try:
        # Count matching plugins using a single query
        result = await bot.db.fetchone("""
            SELECT COUNT(*) FROM fingerprint_plugins p1 
            INNER JOIN fingerprint_plugins p2 ON p1.plugin_name = p2.plugin_name 
            WHERE p1.user_id = ? AND p2.user_id = ?
        """, user1_id, user2_id)
        
        matching_plugins = result[0] if result else 0
        
        # Get total unique plugins for both users
        total_result = await bot.db.fetchone("""
            SELECT COUNT(DISTINCT plugin_name) FROM fingerprint_plugins 
            WHERE user_id IN (?, ?)
        """, user1_id, user2_id)
        
        total_plugins = total_result[0] if total_result else 0
        
        if total_plugins == 0:
            return 0.0
        
        return matching_plugins / total_plugins
        
    except Exception as e:
        logging.error(f"Error calculating plugins similarity: {e}")
        return 0.0

def _extract_browser_pattern(user_agent: str) -> str:
    """
    Extract browser pattern from user agent for comparison.
    
    Args:
        user_agent: User agent string
        
    Returns:
        str: Simplified browser pattern
    """
    try:
        # Extract major browser and version info, ignore minor versions
        ua = user_agent.lower()
        
        if 'chrome' in ua:
            # Extract Chrome major version
            import re
            match = re.search(r'chrome/(\d+)', ua)
            if match:
                return f"chrome_{match.group(1)}"
        elif 'firefox' in ua:
            match = re.search(r'firefox/(\d+)', ua)
            if match:
                return f"firefox_{match.group(1)}"
        elif 'safari' in ua and 'chrome' not in ua:
            match = re.search(r'version/(\d+)', ua)
            if match:
                return f"safari_{match.group(1)}"
        elif 'edge' in ua:
            match = re.search(r'edge/(\d+)', ua)
            if match:
                return f"edge_{match.group(1)}"
        
        return "unknown"
        
    except:
        return "unknown"

async def get_user_fingerprint_summary(bot, user_id: int) -> Optional[Dict]:
    """
    Get a summary of a user's fingerprint for display purposes.
    
    Args:
        bot: Bot instance with database connection
        user_id: Discord user ID
        
    Returns:
        Dict containing fingerprint summary or None if not found
    """
    try:
        # Get main fingerprint data
        fp = await bot.db.fetchone("SELECT * FROM browser_fingerprints WHERE user_id = ?", user_id)
        if not fp:
            return None
        
        # Get array data counts
        languages_count = await bot.db.fetchone(
            "SELECT COUNT(*) FROM fingerprint_languages WHERE user_id = ?", user_id
        )
        fonts_count = await bot.db.fetchone(
            "SELECT COUNT(*) FROM fingerprint_fonts WHERE user_id = ?", user_id
        )
        plugins_count = await bot.db.fetchone(
            "SELECT COUNT(*) FROM fingerprint_plugins WHERE user_id = ?", user_id
        )
        
        return {
            "user_id": fp[0],
            "platform": fp[3],
            "browser": _extract_browser_pattern(fp[1] or ""),
            "screen_resolution": f"{fp[8]}x{fp[9]}" if fp[8] and fp[9] else "Unknown",
            "hardware_cores": fp[5],
            "device_memory": fp[6],
            "timezone": fp[11],
            "languages_count": languages_count[0] if languages_count else 0,
            "fonts_count": fonts_count[0] if fonts_count else 0,
            "plugins_count": plugins_count[0] if plugins_count else 0,
            "created_at": fp[21]  # created_at column (moved from 23 to 21)
        }
        
    except Exception as e:
        logging.error(f"Error getting fingerprint summary for user {user_id}: {e}")
        return None
