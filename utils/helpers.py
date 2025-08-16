import discord
from discord.ext import commands
import datetime
import json
import os
from config.settings import BOT_CONFIG

def create_embed(title=None, description=None, color=None, footer=None):
    """Create a standard embed with bot branding"""
    if color is None:
        color = BOT_CONFIG['embed_color']
    
    embed = discord.Embed(color=color)
    
    if title:
        embed.title = title
    
    if description:
        embed.description = description
    
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text="Vantha Pesuvom")
    
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed

def create_success_embed(title=None, description=None):
    """Create a success embed"""
    return create_embed(title=title, description=description, color=BOT_CONFIG['success_color'])

def create_error_embed(title=None, description=None):
    """Create an error embed"""
    return create_embed(title=title, description=description, color=BOT_CONFIG['error_color'])

def create_warning_embed(title=None, description=None):
    """Create a warning embed"""
    return create_embed(title=title, description=description, color=BOT_CONFIG['warning_color'])

def format_time(seconds):
    """Format seconds into a readable time string"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h"
    else:
        days = seconds // 86400
        return f"{days}d"

def parse_time(time_str):
    """Parse a time string into seconds"""
    time_str = time_str.lower()
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    total_seconds = 0
    current_number = ""
    
    for char in time_str:
        if char.isdigit():
            current_number += char
        elif char in multipliers:
            if current_number:
                total_seconds += int(current_number) * multipliers[char]
                current_number = ""
    
    if current_number:
        total_seconds += int(current_number)
    
    return total_seconds

def is_staff():
    """Check if user has staff permissions"""
    def predicate(ctx):
        if ctx.author.id == BOT_CONFIG['owner_id']:
            return True
        
        return any(role.permissions.manage_guild for role in ctx.author.roles)
    
    return commands.check(predicate)

def is_moderator():
    """Check if user has moderator permissions"""
    def predicate(ctx):
        if ctx.author.id == BOT_CONFIG['owner_id']:
            return True
        
        return any(role.permissions.kick_members for role in ctx.author.roles)
    
    return commands.check(predicate)

def ensure_data_directory():
    """Ensure the data directory exists"""
    if not os.path.exists('data'):
        os.makedirs('data')

def load_json(file_path, default=None):
    """Load JSON data from file"""
    if default is None:
        default = {}
    
    ensure_data_directory()
    
    if not os.path.exists(file_path):
        save_json(file_path, default)
        return default
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default

def save_json(file_path, data):
    """Save JSON data to file"""
    ensure_data_directory()
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def get_user_mention(user_id):
    """Get a user mention string from user ID"""
    return f"<@{user_id}>"

def get_channel_mention(channel_id):
    """Get a channel mention string from channel ID"""
    return f"<#{channel_id}>"

def get_role_mention(role_id):
    """Get a role mention string from role ID"""
    return f"<@&{role_id}>"
