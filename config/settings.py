import os

# Bot configuration
BOT_CONFIG = {
    'prefix': os.getenv('BOT_PREFIX', '/'),
    'owner_id': int(os.getenv('OWNER_ID', '0')),
    'support_server': os.getenv('SUPPORT_SERVER', ''),
    'embed_color': 0x7289DA,
    'error_color': 0xFF0000,
    'success_color': 0x00FF00,
    'warning_color': 0xFFFF00
}

# Economy configuration
ECONOMY_CONFIG = {
    'daily_amount': 100,
    'daily_cooldown': 86400,  # 24 hours in seconds
    'starting_balance': 1000,
    'max_balance': 1000000,
    'work_min': 50,
    'work_max': 200,
    'work_cooldown': 3600  # 1 hour in seconds
}

# Modmail configuration
MODMAIL_CONFIG = {
    'category_name': 'ModMail',
    'log_channel': 'modmail-logs',
    'close_after_hours': 48,
    'max_tickets_per_user': 3
}

# Auto-response configuration
AUTORESPONSE_CONFIG = {
    'enabled': True,
    'cooldown': 30,  # seconds
    'max_responses_per_minute': 5
}

# Moderation configuration
MODERATION_CONFIG = {
    'mute_role': 'Muted',
    'log_channel': 'mod-logs',
    'auto_role': None,
    'max_warns': 3,
    'warn_actions': {
        1: None,
        2: 'timeout',
        3: 'kick'
    }
}

# Data file paths
DATA_PATHS = {
    'users': 'data/users.json',
    'modmail': 'data/modmail.json',
    'autoresponse': 'data/autoresponse.json',
    'config': 'data/config.json'
}
