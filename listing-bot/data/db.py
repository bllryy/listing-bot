import aiosqlite
import asyncio
import logging
import re

class Database:
    def __init__(self, db_path: str, max_retries: int = 3, retry_delay: float = 1.0):
        self.db_path = db_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn = None

    async def connect(self):
        for attempt in range(self.max_retries):
            try:
                self.conn = await aiosqlite.connect(self.db_path)
                await self._update_schema() 
                await self.initialize_schema()
                await self.ensure_required_tables_data()  # Add this line
                break
            except Exception as e:
                logging.error(f"Failed to connect to database (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to connect to the database after multiple attempts")

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def ensure_connection(self):
        if not self.conn or not self.conn._conn:
            await self.connect()

    async def update_config(self, option: str, value: any) -> bool:
        """
        Updates a configuration option in the database with automatic type detection
        Args:
            option: The config option to update
            value: The new value to set
        Returns:
            bool: True if update succeeded
        """
        await self.ensure_connection()
        try:
            data_type = type(value).__name__
            
            await self.conn.execute("DELETE FROM config WHERE key = ?", (option,))
            
            await self.conn.execute(
                "INSERT INTO config (key, value, data_type) VALUES (?, ?, ?)",
                (option, str(value), data_type)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    async def execute(self, query: str, *args):
        await self.ensure_connection()
        for attempt in range(self.max_retries):
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    await self.conn.commit()
                    return cursor
            except Exception as e:
                logging.error(f"Failed to execute query (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to execute query after multiple attempts")

    async def fetch(self, query: str, *args):
        await self.ensure_connection()
        for attempt in range(self.max_retries):
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchall()
            except Exception as e:
                logging.error(f"Failed to fetch data (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to fetch data after multiple attempts")

    async def fetchone(self, query: str, *args):
        await self.ensure_connection()
        for attempt in range(self.max_retries):
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchone()
            except Exception as e:
                logging.error(f"Failed to fetch one (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to fetch one after multiple attempts")
        
    async def fetchall(self, query: str, *args):
        await self.ensure_connection()
        for attempt in range(self.max_retries):
            try:
                async with self.conn.cursor() as cursor:
                    await cursor.execute(query, args)
                    return await cursor.fetchall()
            except Exception as e:
                logging.error(f"Failed to fetch all (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        else:
            raise Exception("Failed to fetch all after multiple attempts")
        
    async def get_config(self, key: str):
        query = "SELECT value, data_type FROM config WHERE key = ?"
        result = await self.fetchone(query, key)
        if result:
            value, data_type = result
            if data_type == 'int':
                return int(value)
            elif data_type == 'float':
                return float(value)
            elif data_type == 'bool':
                return value.lower() in ('true', '1')
            else:
                return value
        return None
    
    async def set_config(self, key: str, value: any):
        data_type = type(value).__name__
        query = "INSERT OR REPLACE INTO config (key, value, data_type) VALUES (?, ?, ?)"
        await self.execute(query, key, str(value), data_type)
        return True
    
    async def delete_config(self, key: str):
        query = "DELETE FROM config WHERE key = ?"
        await self.execute(query, key)
        return True
    
    async def _update_schema(self):
        """
        Compares the current DB schema with the defined schema and:
        1. Applies necessary ALTER TABLE commands to add missing columns
        2. Drops tables that are no longer in the schema definition
        3. Recreates tables with updated constraints when necessary
        """
        logging.info("Checking for database schema updates...")
        schema = DatabaseSchema()
        
        # Extract table names and columns from schema
        defined_schema = {}
        defined_tables = set()
        table_constraints = {}  # Store PRIMARY KEY and other constraints
        
        for query in schema.create_table_queries:
            table_name_match = re.search(r'CREATE TABLE IF NOT EXISTS "(\w+)"', query)
            if not table_name_match:
                continue
            table_name = table_name_match.group(1)
            defined_tables.add(table_name)
            
            columns_str_match = re.search(r'\((.*)\)', query, re.DOTALL)
            if not columns_str_match:
                continue
            columns_str = columns_str_match.group(1)

            # Parse column definitions and constraints more carefully
            column_defs = re.split(r',\s*(?![^()]*\))', columns_str.strip())
            
            columns = {}
            constraints = []
            
            for col_def in column_defs:
                col_def = col_def.strip()
                if not col_def: 
                    continue
                
                # Check if this is a constraint (PRIMARY KEY, FOREIGN KEY, etc.)
                if col_def.upper().startswith('PRIMARY KEY') or col_def.upper().startswith('FOREIGN KEY') or col_def.upper().startswith('UNIQUE'):
                    constraints.append(col_def)
                    continue
                
                # Parse column definition
                parts = col_def.split()
                if not parts: 
                    continue
                    
                col_name = parts[0].strip('"')
                col_definition = ' '.join(parts[1:])
                columns[col_name] = col_definition

            defined_schema[table_name] = columns
            table_constraints[table_name] = constraints

        cursor = await self.conn.cursor()
        
        # Clean up any leftover temporary tables from failed migrations
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_new'")
        temp_tables = await cursor.fetchall()
        for (temp_table,) in temp_tables:
            logging.warning(f"Found leftover temporary table {temp_table}, cleaning up...")
            try:
                await self.conn.execute(f'DROP TABLE "{temp_table}"')
                logging.info(f"Successfully cleaned up temporary table {temp_table}")
            except Exception as cleanup_err:
                logging.error(f"Error cleaning up temporary table {temp_table}: {cleanup_err}")
        
        await cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in await cursor.fetchall()]

        # Drop tables that no longer exist in the schema
        for table in existing_tables:
            # Skip internal sqlite tables
            if table.startswith('sqlite_'):
                continue
                
            if table not in defined_tables:
                try:
                    drop_query = f'DROP TABLE "{table}"'
                    logging.warning(f"Dropping table that's no longer in schema: {table}")
                    await self.conn.execute(drop_query)
                    logging.info(f"Successfully dropped table: {table}")
                except Exception as e:
                    logging.error(f"Failed to drop table {table}: {e}")

        # Handle table updates
        for table, required_columns in defined_schema.items():
            if table not in existing_tables:
                continue

            await cursor.execute(f'PRAGMA table_info("{table}")')
            existing_cols_info = await cursor.fetchall()
            existing_col_names = {row[1] for row in existing_cols_info}
            
            # Check for columns to add
            columns_to_add = []
            for col_name, col_definition in required_columns.items():
                if col_name not in existing_col_names:
                    columns_to_add.append((col_name, col_definition))
            
            # Check for columns to drop
            cols_to_drop = [col for col in existing_col_names if col not in required_columns]
            
            # Check if table has constraints (need to recreate if so)
            has_constraints = bool(table_constraints.get(table, []))
            
            # If we have constraints or columns to drop, recreate the table
            if has_constraints or cols_to_drop or (columns_to_add and has_constraints):
                try:
                    logging.info(f"Recreating table {table} due to constraints or column changes")
                    
                    # Create a new table with the correct schema
                    temp_table = f"{table}_new"
                    
                    # First, check if temp table already exists and drop it
                    await cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{temp_table}'")
                    if await cursor.fetchone():
                        logging.warning(f"Temporary table {temp_table} already exists, dropping it")
                        await self.conn.execute(f'DROP TABLE "{temp_table}"')
                    
                    create_temp_query = f'CREATE TABLE "{temp_table}" ('
                    
                    # Add column definitions
                    all_definitions = []
                    for col_name, col_definition in required_columns.items():
                        all_definitions.append(f'"{col_name}" {col_definition}')
                    
                    # Add constraints
                    for constraint in table_constraints.get(table, []):
                        all_definitions.append(constraint)
                    
                    create_temp_query += ', '.join(all_definitions) + ')'
                    
                    await self.conn.execute(create_temp_query)
                    
                    # Copy data from old table to new table (only for existing columns)
                    remaining_cols = [col for col in existing_col_names if col in required_columns]
                    if remaining_cols:
                        copy_query = f'INSERT INTO "{temp_table}" ('
                        copy_query += ', '.join([f'"{col}"' for col in remaining_cols])
                        copy_query += f') SELECT '
                        copy_query += ', '.join([f'"{col}"' for col in remaining_cols])
                        copy_query += f' FROM "{table}"'
                        
                        await self.conn.execute(copy_query)
                    
                    # Drop old table and rename new table
                    await self.conn.execute(f'DROP TABLE "{table}"')
                    await self.conn.execute(f'ALTER TABLE "{temp_table}" RENAME TO "{table}"')
                    
                    logging.info(f"Successfully recreated table {table} with updated schema")
                except Exception as e:
                    logging.error(f"Failed to update schema for table {table}: {e}")
                    # Enhanced cleanup - remove temp table if it exists
                    try:
                        await cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{temp_table}'")
                        if await cursor.fetchone():
                            await self.conn.execute(f'DROP TABLE "{temp_table}"')
                            logging.info(f"Cleaned up temporary table {temp_table}")
                    except Exception as cleanup_err:
                        logging.error(f"Error during temp table cleanup: {cleanup_err}")
            
            # If no constraints and only adding columns, use ALTER TABLE
            elif columns_to_add and not cols_to_drop:
                for col_name, col_definition in columns_to_add:
                    try:
                        # Skip adding columns with PRIMARY KEY constraint via ALTER TABLE
                        if 'PRIMARY KEY' in col_definition.upper():
                            logging.warning(f"Cannot add PRIMARY KEY column {col_name} to existing table {table}, skipping")
                            continue
                            
                        alter_query = f'ALTER TABLE "{table}" ADD COLUMN "{col_name}" {col_definition}'
                        logging.info(f"Applying migration: {alter_query}")
                        await self.conn.execute(alter_query)
                    except Exception as e:
                        logging.error(f"Failed to apply migration for {table}.{col_name}: {e}")
        
        await self.conn.commit()
        await cursor.close()
        logging.info("Database schema check complete.")

    async def initialize_schema(self):
        schema = DatabaseSchema()
        for query in schema.create_table_queries:
            await self.execute(query)

    async def ensure_required_tables_data(self):
        """
        Ensures that critical tables like ai_config and hosting have at least one row with default values.
        This is important for the proper functioning of features that rely on these tables.
        """
        logging.info("Ensuring required tables have data...")
        
        # Check and initialize ai_config
        ai_config = await self.fetchone("SELECT COUNT(*) FROM ai_config")
        if not ai_config or ai_config[0] == 0:
            logging.info("Initializing ai_config table with default values...")
            await self.execute(
                """
                INSERT INTO ai_config 
                (monthly_limit, remaining_credits_free, remaining_credits_paid, last_reset) 
                VALUES (150, 150, 0, CURRENT_TIMESTAMP)
                """
            )
        
        # Check and initialize hosting
        hosting_data = await self.fetchone("SELECT COUNT(*) FROM hosting")
        if not hosting_data or hosting_data[0] == 0:
            # Set initial hosting expiration to 30 days from now
            from datetime import datetime, timezone, timedelta
            expiration_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            
            logging.info("Initializing hosting table with default values...")
            await self.execute(
                """
                INSERT INTO hosting 
                (paid_until, paid_by, last_payment, last_payment_amount, last_payment_method) 
                VALUES (?, NULL, CURRENT_TIMESTAMP, 0, 'Initial Setup')
                """,
                expiration_date
            )

class DatabaseSchema:
    def __init__(self):
        self.create_table_queries = [
            """
            CREATE TABLE IF NOT EXISTS "accounts" (
                "uuid" TEXT,
                "username" TEXT,
                "profile" TEXT,
                "payment_methods" TEXT,
                "additional_information" TEXT,
                "price" INTEGER,
                "number" INTEGER,
                "channel_id" INTEGER,
                "message_id" INTEGER,
                "listed_by" INTEGER,
                "show_username" TEXT DEFAULT 'true'
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "config" (
                "key" TEXT,
                "value" TEXT,
                "data_type" TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "profiles" (
                "uuid" TEXT,
                "username" TEXT,
                "profile" TEXT,
                "payment_methods" TEXT,
                "additional_information" TEXT,
                "price" INTEGER,
                "number" INTEGER,
                "channel_id" INTEGER,
                "message_id" INTEGER,
                "listed_by" INTEGER,
                "show_username" TEXT DEFAULT 'true'
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "roles" (
                "role_id" INTEGER,
                "used" TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "tickets" (
                "opened_by" INTEGER,
                "channel_id" INTEGER,
                "initial_message_id" INTEGER,
                "role_id" INTEGER,
                "is_open" INTEGER DEFAULT 1,
                "claimed" INTEGER,
                "ticket_type" TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "vouches" (
                "user_id" INTEGER,
                "message" TEXT,
                "avatar" TEXT,
                "username" TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "alts" (
                "uuid"	TEXT,
                "username"	TEXT,
                "profile"	TEXT,
                "payment_methods"	TEXT,
                "additional_information"	TEXT,
                "price"	INTEGER,
                "number"	INTEGER,
                "channel_id"	INTEGER,
                "message_id"	INTEGER,
                "listed_by"	INTEGER,
                "show_username"	TEXT DEFAULT 'true',
                "farming" TEXT DEFAULT 'true',
                "mining" TEXT DEFAULT 'false'
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "sellers" (
                "user_id"	INTEGER,
                "payment_methods"	TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "auth" (
                "user_id"	INTEGER,
                "refresh_token"	TEXT,
                "ip_address"	TEXT,
                "bot_id"	INTEGER,
                "browser_fingerprint"	TEXT,
                "fingerprint_hash" TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "auth_bots" (
                "client_id"	INTEGER,
                "client_secret"	TEXT,
                "bot_token"	TEXT,
                "redirect_uri"	TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "transactions" (
                "user_id" INTEGER,
                "amount" INTEGER,
                "rate" TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "tags" (
                "name" TEXT,
                "content" TEXT,
                "created_by" INTEGER
            );            
            """,
            """
            CREATE TABLE IF NOT EXISTS "panels" (
                "name" TEXT,
                "embed_text" TEXT,
                "data" TEXT
            )
            """,
            # data is b64 encoded json
            """
            CREATE TABLE IF NOT EXISTS "custom_mappings" (
                "message_id" INTEGER,
                "category_id" INTEGER,
                "role_id" INTEGER,
                "name" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "payment_details" (
                "user_id" INTEGER PRIMARY KEY,
                "paypal_email" TEXT,
                "business_name" TEXT,
                "currency" TEXT DEFAULT 'USD',
                "bitcoin_address" TEXT,
                "ethereum_address" TEXT,
                "litecoin_address" TEXT,
                "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "tos_agreed" (
                "user_id" INTEGER PRIMARY KEY,
                "agreed_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "browser_fingerprints" (
                "user_id" INTEGER,
                "user_agent" TEXT,
                "language" TEXT,
                "platform" TEXT,
                "cookie_enabled" INTEGER,
                "hardware_concurrency" INTEGER,
                "device_memory" INTEGER,
                "max_touch_points" INTEGER,
                "screen_width" INTEGER,
                "screen_height" INTEGER,
                "screen_color_depth" INTEGER,
                "timezone_name" TEXT,
                "timezone_offset" INTEGER,
                "webgl_vendor" TEXT,
                "webgl_renderer" TEXT,
                "webgl_unmasked_vendor" TEXT,
                "webgl_unmasked_renderer" TEXT,
                "audio_fingerprint" TEXT,
                "network_downlink" REAL,
                "network_effective_type" TEXT,
                "timestamp" INTEGER,
                "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "fingerprint_languages" (
                "user_id" INTEGER,
                "language" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "fingerprint_fonts" (
                "user_id" INTEGER,
                "font_name" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "fingerprint_plugins" (
                "user_id" INTEGER,
                "plugin_name" TEXT,
                "plugin_filename" TEXT,
                "plugin_description" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "fingerprint_webgl_extensions" (
                "user_id" INTEGER,
                "extension_name" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "fingerprint_storage" (
                "user_id" INTEGER,
                "storage_type" TEXT,
                "supported" INTEGER
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "fingerprint_protocols" (
                "user_id" INTEGER,
                "protocol" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "ai_config" (
                "monthly_limit" INTEGER DEFAULT 2000,
                "remaining_credits_free" INTEGER DEFAULT 2000,
                "remaining_credits_paid" INTEGER DEFAULT 0,
                "last_reset" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "ai_calls" (
                "call_type" TEXT,
                "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "response_time_ms" INTEGER,
                "input_tokens" INTEGER,
                "output_tokens" INTEGER,
                "response_text" TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "hosting" (
                "paid_until" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    
                "paid_by" INTEGER,
                "last_payment" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "last_payment_amount" REAL,
                "last_payment_method" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "ticket_roles" (
                "role_id"	INTEGER,
                "ticket_type"	TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS "account_stats" (
                "uuid" TEXT,
                "skill_average" REAL DEFAULT 0.0,
                "catacombs_level" INTEGER DEFAULT 0,
                "zombie_slayer_level" INTEGER DEFAULT 0,
                "spider_slayer_level" INTEGER DEFAULT 0,
                "wolf_slayer_level" INTEGER DEFAULT 0,
                "enderman_slayer_level" INTEGER DEFAULT 0,
                "blaze_slayer_level" INTEGER DEFAULT 0,
                "vampire_slayer_level" INTEGER DEFAULT 0,
                "skyblock_level" INTEGER DEFAULT 0,
                "total_networth" REAL DEFAULT 0.0,
                "soulbound_networth" REAL DEFAULT 0.0,
                "liquid_networth" REAL DEFAULT 0.0,
                "heart_of_the_mountain_level" INTEGER DEFAULT 0,
                "mithril_powder" INTEGER DEFAULT 0,
                "gemstone_powder" INTEGER DEFAULT 0,
                "glaciate_powder" INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "profile_stats" (
                "uuid" TEXT,
                "profile" TEXT,
                "total_networth" REAL DEFAULT 0.0,
                "soulbound_networth" REAL DEFAULT 0.0,
                "liquid_networth" REAL DEFAULT 0.0,
                "minion_slots" INTEGER DEFAULT 0,
                "minion_bonus_slots" INTEGER DEFAULT 0,
                "maxed_collections" INTEGER DEFAULT 0,
                "unlocked_collections" INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "sellauth_config" (
                "user_id" INTEGER PRIMARY KEY,
                "product_id" INTEGER,
                "variant_id" INTEGER,
                "shop_id" INTEGER,
                "shop_name" TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "custom_embeds" (
                "name" TEXT PRIMARY KEY,
                "created_by" INTEGER,
                "data" TEXT,
                "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "auth_actions" (
                "action_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER,
                "action_type" TEXT,
                "timestamp" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "details" TEXT,
                "resolved" INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "cog_actions" (
                "guild_id" INTEGER,
                "action_type" TEXT,
                "enabled" INTEGER DEFAULT 0,
                PRIMARY KEY ("guild_id", "action_type")
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "cog_action_settings" (
                "guild_id" INTEGER,
                "action_type" TEXT,
                "setting_key" TEXT,
                "setting_value" TEXT,
                PRIMARY KEY ("guild_id", "action_type", "setting_key")
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "cog_action_channels" (
                "guild_id" INTEGER,
                "action_type" TEXT,
                "channel_type" TEXT,
                "channel_id" INTEGER,
                PRIMARY KEY ("guild_id", "action_type", "channel_type")
            )
            """
        ]