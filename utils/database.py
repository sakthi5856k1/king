import json
import os
import asyncio
from datetime import datetime, timedelta
from config.settings import DATA_PATHS, ECONOMY_CONFIG
from utils.helpers import load_json, save_json

class Database:
    """Simple JSON-based database for bot data"""
    
    def __init__(self):
        self.users_data = load_json(DATA_PATHS['users'], {})
        self.modmail_data = load_json(DATA_PATHS['modmail'], {})
        self.autoresponse_data = load_json(DATA_PATHS['autoresponse'], {})
        self.config_data = load_json(DATA_PATHS['config'], {})
        
        # Auto-save every 5 minutes
        asyncio.create_task(self._auto_save())
    
    async def _auto_save(self):
        """Auto-save data every 5 minutes"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            self.save_all()
    
    def save_all(self):
        """Save all data to files"""
        save_json(DATA_PATHS['users'], self.users_data)
        save_json(DATA_PATHS['modmail'], self.modmail_data)
        save_json(DATA_PATHS['autoresponse'], self.autoresponse_data)
        save_json(DATA_PATHS['config'], self.config_data)
    
    # User data methods
    def get_user(self, user_id):
        """Get user data"""
        user_id = str(user_id)
        if user_id not in self.users_data:
            self.users_data[user_id] = {
                'balance': ECONOMY_CONFIG['starting_balance'],
                'last_daily': 0,
                'last_work': 0,
                'warnings': [],
                'total_earned': 0,
                'total_spent': 0,
                'inventory': {},
                'active_perks': {},
                'created_at': datetime.utcnow().isoformat()
            }
        return self.users_data[user_id]
    
    def update_user(self, user_id, data):
        """Update user data"""
        user_id = str(user_id)
        user = self.get_user(user_id)
        user.update(data)
        self.users_data[user_id] = user
    
    def add_balance(self, user_id, amount):
        """Add balance to user"""
        user = self.get_user(user_id)
        user['balance'] += amount
        user['total_earned'] += amount
        self.update_user(user_id, user)
    
    def remove_balance(self, user_id, amount):
        """Remove balance from user"""
        user = self.get_user(user_id)
        if user['balance'] >= amount:
            user['balance'] -= amount
            user['total_spent'] += amount
            self.update_user(user_id, user)
            return True
        return False
    
    def can_daily(self, user_id):
        """Check if user can claim daily reward"""
        user = self.get_user(user_id)
        now = datetime.utcnow().timestamp()
        return now - user['last_daily'] >= ECONOMY_CONFIG['daily_cooldown']
    
    def can_work(self, user_id):
        """Check if user can work"""
        user = self.get_user(user_id)
        now = datetime.utcnow().timestamp()
        return now - user['last_work'] >= ECONOMY_CONFIG['work_cooldown']
    
    def claim_daily(self, user_id):
        """Claim daily reward"""
        if not self.can_daily(user_id):
            return False
        
        user = self.get_user(user_id)
        user['last_daily'] = datetime.utcnow().timestamp()
        self.add_balance(user_id, ECONOMY_CONFIG['daily_amount'])
        return True
    
    def work(self, user_id, amount):
        """Work for money"""
        if not self.can_work(user_id):
            return False
        
        user = self.get_user(user_id)
        user['last_work'] = datetime.utcnow().timestamp()
        self.add_balance(user_id, amount)
        return True
    
    def add_warning(self, user_id, guild_id, reason, moderator_id):
        """Add warning to user"""
        user = self.get_user(user_id)
        warning = {
            'reason': reason,
            'moderator_id': str(moderator_id),
            'guild_id': str(guild_id),
            'timestamp': datetime.utcnow().isoformat()
        }
        user['warnings'].append(warning)
        self.update_user(user_id, user)
        return len(user['warnings'])
    
    def get_warnings(self, user_id, guild_id=None):
        """Get user warnings"""
        user = self.get_user(user_id)
        warnings = user['warnings']
        
        if guild_id:
            warnings = [w for w in warnings if w['guild_id'] == str(guild_id)]
        
        return warnings
    
    # Inventory methods
    def add_to_inventory(self, user_id, item_id, item_data):
        """Add item to user's inventory"""
        user = self.get_user(user_id)
        if 'inventory' not in user:
            user['inventory'] = {}
        
        user['inventory'][item_id] = {
            'name': item_data['name'],
            'type': item_data['type'],
            'price': item_data['price'],
            'purchased_at': datetime.utcnow().isoformat()
        }
        
        # Add extra data for specific types
        if item_data['type'] == 'perk':
            user['inventory'][item_id]['duration'] = item_data['duration']
        elif item_data['type'] == 'item':
            user['inventory'][item_id]['description'] = item_data.get('description', '')
        elif item_data['type'] == 'role':
            user['inventory'][item_id]['color'] = item_data.get('color', 0)
        
        self.update_user(user_id, user)
    
    def remove_from_inventory(self, user_id, item_id):
        """Remove item from user's inventory"""
        user = self.get_user(user_id)
        if 'inventory' in user and item_id in user['inventory']:
            del user['inventory'][item_id]
            self.update_user(user_id, user)
            return True
        return False
    
    def activate_perk(self, user_id, perk_id, expiry):
        """Activate a perk for a user"""
        user = self.get_user(user_id)
        if 'active_perks' not in user:
            user['active_perks'] = {}
        
        user['active_perks'][perk_id] = {
            'activated_at': datetime.utcnow().isoformat(),
            'expires_at': expiry.isoformat()
        }
        
        # Add expiry to inventory item
        if 'inventory' in user and perk_id in user['inventory']:
            user['inventory'][perk_id]['expiry'] = expiry.isoformat()
        
        self.update_user(user_id, user)
    
    def is_perk_active(self, user_id, perk_id):
        """Check if a perk is active for a user"""
        user = self.get_user(user_id)
        active_perks = user.get('active_perks', {})
        
        if perk_id not in active_perks:
            return False
        
        expiry = datetime.fromisoformat(active_perks[perk_id]['expires_at'])
        return datetime.utcnow() < expiry
    
    def get_active_perks(self, user_id):
        """Get all active perks for a user"""
        user = self.get_user(user_id)
        active_perks = user.get('active_perks', {})
        current_time = datetime.utcnow()
        
        valid_perks = {}
        for perk_id, perk_data in active_perks.items():
            expiry = datetime.fromisoformat(perk_data['expires_at'])
            if current_time < expiry:
                valid_perks[perk_id] = perk_data
        
        return valid_perks
    
    # Modmail methods
    def create_modmail_ticket(self, user_id, guild_id, channel_id):
        """Create a modmail ticket"""
        ticket_id = f"{guild_id}_{user_id}_{datetime.utcnow().timestamp()}"
        self.modmail_data[ticket_id] = {
            'user_id': str(user_id),
            'guild_id': str(guild_id),
            'channel_id': str(channel_id),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'open',
            'messages': []
        }
        return ticket_id
    
    def get_modmail_ticket(self, ticket_id):
        """Get modmail ticket"""
        return self.modmail_data.get(ticket_id)
    
    def close_modmail_ticket(self, ticket_id, closer_id):
        """Close modmail ticket"""
        if ticket_id in self.modmail_data:
            self.modmail_data[ticket_id]['status'] = 'closed'
            self.modmail_data[ticket_id]['closed_by'] = str(closer_id)
            self.modmail_data[ticket_id]['closed_at'] = datetime.utcnow().isoformat()
    
    def add_modmail_message(self, ticket_id, user_id, content):
        """Add message to modmail ticket"""
        if ticket_id in self.modmail_data:
            message = {
                'user_id': str(user_id),
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.modmail_data[ticket_id]['messages'].append(message)
    
    def get_user_tickets(self, user_id, guild_id):
        """Get user's active tickets"""
        user_id = str(user_id)
        guild_id = str(guild_id)
        
        tickets = []
        for ticket_id, ticket in self.modmail_data.items():
            if (ticket['user_id'] == user_id and 
                ticket['guild_id'] == guild_id and 
                ticket['status'] == 'open'):
                tickets.append(ticket_id)
        
        return tickets
    
    # Auto-response methods
    def add_autoresponse(self, guild_id, trigger, response):
        """Add auto-response"""
        guild_id = str(guild_id)
        if guild_id not in self.autoresponse_data:
            self.autoresponse_data[guild_id] = {}
        
        self.autoresponse_data[guild_id][trigger.lower()] = {
            'response': response,
            'created_at': datetime.utcnow().isoformat(),
            'uses': 0
        }
    
    def remove_autoresponse(self, guild_id, trigger):
        """Remove auto-response"""
        guild_id = str(guild_id)
        if guild_id in self.autoresponse_data:
            trigger = trigger.lower()
            if trigger in self.autoresponse_data[guild_id]:
                del self.autoresponse_data[guild_id][trigger]
                return True
        return False
    
    def get_autoresponse(self, guild_id, message_content):
        """Get auto-response for message"""
        guild_id = str(guild_id)
        if guild_id not in self.autoresponse_data:
            return None
        
        message_content = message_content.lower()
        for trigger, data in self.autoresponse_data[guild_id].items():
            if trigger in message_content:
                self.autoresponse_data[guild_id][trigger]['uses'] += 1
                return data['response']
        
        return None
    
    def get_guild_autoresponses(self, guild_id):
        """Get all auto-responses for guild"""
        guild_id = str(guild_id)
        return self.autoresponse_data.get(guild_id, {})
    
    # Config methods
    def get_guild_config(self, guild_id):
        """Get guild configuration"""
        guild_id = str(guild_id)
        if guild_id not in self.config_data:
            self.config_data[guild_id] = {
                'modmail_category': None,
                'modmail_log_channel': None,
                'mod_log_channel': None,
                'mute_role': None,
                'auto_role': None,
                'prefix': None
            }
        return self.config_data[guild_id]
    
    def update_guild_config(self, guild_id, config):
        """Update guild configuration"""
        guild_id = str(guild_id)
        current = self.get_guild_config(guild_id)
        current.update(config)
        self.config_data[guild_id] = current
