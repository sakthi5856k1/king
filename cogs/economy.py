import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from utils.helpers import create_embed, create_success_embed, create_error_embed, format_time
from config.settings import ECONOMY_CONFIG

class Economy(commands.Cog):
    """Economy system with user balances and transactions"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='balance', aliases=['bal', 'money'])
    async def balance(self, ctx, user: discord.Member = None):
        """Check your or another user's balance"""
        target = user if user is not None else ctx.author
        user_data = self.bot.db.get_user(target.id)
        
        embed = create_embed(
            f"💰 {target.display_name}'s Balance",
            f"**Current Balance:** ${user_data['balance']:,}\n"
            f"**Total Earned:** ${user_data['total_earned']:,}\n"
            f"**Total Spent:** ${user_data['total_spent']:,}"
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='daily')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def daily(self, ctx):
        """Claim your daily reward"""
        if not self.bot.db.can_daily(ctx.author.id):
            user_data = self.bot.db.get_user(ctx.author.id)
            next_daily = user_data['last_daily'] + ECONOMY_CONFIG['daily_cooldown']
            remaining = next_daily - datetime.utcnow().timestamp()
            
            embed = create_error_embed(
                "⏰ Daily Already Claimed",
                f"You can claim your next daily reward in {format_time(int(remaining))}."
            )
            await ctx.send(embed=embed)
            return
        
        # Check for daily boost perk
        base_amount = ECONOMY_CONFIG['daily_amount']
        bonus_amount = 0
        
        if self.bot.db.is_perk_active(ctx.author.id, 'daily_boost'):
            bonus_amount = base_amount // 2  # 50% bonus
        
        total_amount = base_amount + bonus_amount
        
        # Claim daily
        self.bot.db.claim_daily(ctx.author.id)
        
        # Add bonus if applicable
        if bonus_amount > 0:
            self.bot.db.add_balance(ctx.author.id, bonus_amount)
            
        description = f"You received **${total_amount:,}**!"
        if bonus_amount > 0:
            description += f"\n📈 Daily Boost: +**${bonus_amount:,}** bonus!"
        description += "\nCome back tomorrow for another reward."
        
        embed = create_success_embed("🎁 Daily Reward Claimed!", description)
        await ctx.send(embed=embed)
    
    @commands.command(name='work')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def work(self, ctx):
        """Work to earn money"""
        if not self.bot.db.can_work(ctx.author.id):
            user_data = self.bot.db.get_user(ctx.author.id)
            next_work = user_data['last_work'] + ECONOMY_CONFIG['work_cooldown']
            remaining = next_work - datetime.utcnow().timestamp()
            
            embed = create_error_embed(
                "⏰ Still Working",
                f"You're still tired from your last job. Rest for {format_time(int(remaining))}."
            )
            await ctx.send(embed=embed)
            return
        
        # Random work scenarios
        jobs = [
            "delivered packages",
            "cleaned offices",
            "walked dogs",
            "mowed lawns",
            "tutored students",
            "fixed computers",
            "painted houses",
            "washed cars",
            "served tables",
            "stocked shelves"
        ]
        
        job = random.choice(jobs)
        base_amount = random.randint(ECONOMY_CONFIG['work_min'], ECONOMY_CONFIG['work_max'])
        bonus_amount = 0
        
        # Check for work boost perk
        if self.bot.db.is_perk_active(ctx.author.id, 'work_boost'):
            bonus_amount = base_amount // 3  # 33% bonus
        
        total_amount = base_amount + bonus_amount
        
        # Work
        self.bot.db.work(ctx.author.id, total_amount)
        
        description = f"You {job} and earned **${total_amount:,}**!"
        if bonus_amount > 0:
            description += f"\n⚡ Work Boost: +**${bonus_amount:,}** bonus!"
        
        embed = create_success_embed("💼 Work Complete!", description)
        await ctx.send(embed=embed)
    
    @commands.command(name='pay', aliases=['give'])
    async def pay(self, ctx, user: discord.Member, amount: int):
        """Pay another user"""
        if user.bot:
            embed = create_error_embed("❌ Invalid User", "You can't pay bots.")
            await ctx.send(embed=embed)
            return
        
        if user.id == ctx.author.id:
            embed = create_error_embed("❌ Invalid User", "You can't pay yourself.")
            await ctx.send(embed=embed)
            return
        
        if amount <= 0:
            embed = create_error_embed("❌ Invalid Amount", "Amount must be positive.")
            await ctx.send(embed=embed)
            return
        
        # Check if user has enough money
        if not self.bot.db.remove_balance(ctx.author.id, amount):
            embed = create_error_embed("❌ Insufficient Funds", "You don't have enough money.")
            await ctx.send(embed=embed)
            return
        
        # Add money to recipient
        self.bot.db.add_balance(user.id, amount)
        
        embed = create_success_embed(
            "💸 Payment Sent",
            f"You paid **${amount:,}** to {user.mention}!"
        )
        await ctx.send(embed=embed)
        
        # Notify recipient
        try:
            recipient_embed = create_embed(
                "💰 Payment Received",
                f"You received **${amount:,}** from {ctx.author.mention} in {ctx.guild.name}!"
            )
            await user.send(embed=recipient_embed)
        except discord.Forbidden:
            pass
    
    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx, page: int = 1):
        """View the money leaderboard"""
        users_data = self.bot.db.users_data
        
        # Sort by balance
        sorted_users = sorted(
            users_data.items(),
            key=lambda x: x[1]['balance'],
            reverse=True
        )
        
        # Pagination
        per_page = 10
        total_pages = max(1, (len(sorted_users) + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        
        start = (page - 1) * per_page
        end = start + per_page
        
        embed = create_embed(
            f"💰 Money Leaderboard - Page {page}/{total_pages}",
            ""
        )
        
        leaderboard_text = ""
        for i, (user_id, data) in enumerate(sorted_users[start:end], start + 1):
            user = self.bot.get_user(int(user_id))
            if user:
                name = user.display_name
            else:
                name = f"Unknown User ({user_id})"
            
            balance = data['balance']
            
            # Add medal for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            leaderboard_text += f"{medal} **{name}** - ${balance:,}\n"
        
        embed.description = leaderboard_text or "No users found."
        embed.set_footer(text=f"Page {page}/{total_pages}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='gamble', aliases=['bet'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gamble(self, ctx, amount: int):
        """Gamble your money (50/50 chance)"""
        if amount <= 0:
            embed = create_error_embed("❌ Invalid Amount", "Amount must be positive.")
            await ctx.send(embed=embed)
            return
        
        user_data = self.bot.db.get_user(ctx.author.id)
        if user_data['balance'] < amount:
            embed = create_error_embed("❌ Insufficient Funds", "You don't have enough money.")
            await ctx.send(embed=embed)
            return
        
        # Maximum bet
        max_bet = min(user_data['balance'], 10000)
        if amount > max_bet:
            embed = create_error_embed(
                "❌ Bet Too High",
                f"Maximum bet is **${max_bet:,}**."
            )
            await ctx.send(embed=embed)
            return
        
        # Remove the bet amount
        self.bot.db.remove_balance(ctx.author.id, amount)
        
        # Check for gamble luck perk (increases win chance)
        win_chance = 0.5  # 50% base chance
        if self.bot.db.is_perk_active(ctx.author.id, 'gamble_luck'):
            win_chance = 0.65  # 65% chance with luck perk
        
        won = random.random() < win_chance
        
        luck_active = self.bot.db.is_perk_active(ctx.author.id, 'gamble_luck')
        
        if won:
            # Win double the amount
            winnings = amount * 2
            self.bot.db.add_balance(ctx.author.id, winnings)
            
            description = f"You bet **${amount:,}** and won **${winnings:,}**!\n"
            description += f"Net profit: **${amount:,}**"
            if luck_active:
                description += f"\n🍀 Gamble Luck helped you win!"
            
            embed = create_success_embed("🎉 You Won!", description)
        else:
            description = f"You bet **${amount:,}** and lost it all!\n"
            if luck_active:
                description += "Even with Gamble Luck, fortune wasn't on your side this time."
            else:
                description += "Better luck next time!"
            
            embed = create_error_embed("😢 You Lost!", description)
        
        await ctx.send(embed=embed)
    
    def get_shop_items(self):
        """Get available shop items"""
        return {
            'role_colors': {
                'red_role': {'name': '🔴 Red Color Role', 'price': 5000, 'type': 'role', 'color': 0xFF0000},
                'blue_role': {'name': '🔵 Blue Color Role', 'price': 5000, 'type': 'role', 'color': 0x0000FF},
                'green_role': {'name': '🟢 Green Color Role', 'price': 5000, 'type': 'role', 'color': 0x00FF00},
                'purple_role': {'name': '🟣 Purple Color Role', 'price': 5000, 'type': 'role', 'color': 0x800080},
                'orange_role': {'name': '🟠 Orange Color Role', 'price': 5000, 'type': 'role', 'color': 0xFFA500},
                'yellow_role': {'name': '🟡 Yellow Color Role', 'price': 5000, 'type': 'role', 'color': 0xFFFF00},
            },
            'special_roles': {
                'vip_role': {'name': '⭐ VIP Member', 'price': 15000, 'type': 'role', 'color': 0xFFD700},
                'supporter_role': {'name': '💎 Server Supporter', 'price': 25000, 'type': 'role', 'color': 0x00FFFF},
                'legend_role': {'name': '👑 Legend', 'price': 50000, 'type': 'role', 'color': 0xFF1493},
            },
            'perks': {
                'daily_boost': {'name': '📈 Daily Boost (7 days)', 'price': 10000, 'type': 'perk', 'duration': 7},
                'work_boost': {'name': '⚡ Work Boost (7 days)', 'price': 8000, 'type': 'perk', 'duration': 7},
                'gamble_luck': {'name': '🍀 Gamble Luck (3 days)', 'price': 12000, 'type': 'perk', 'duration': 3},
            },
            'items': {
                'trophy': {'name': '🏆 Trophy', 'price': 2000, 'type': 'item', 'description': 'A shiny trophy for your collection'},
                'medal': {'name': '🥇 Gold Medal', 'price': 3500, 'type': 'item', 'description': 'A prestigious gold medal'},
                'crown': {'name': '👑 Crown', 'price': 7500, 'type': 'item', 'description': 'A royal crown fit for a king'},
                'gem': {'name': '💎 Diamond', 'price': 15000, 'type': 'item', 'description': 'A rare and valuable diamond'},
                'crystal': {'name': '🔮 Magic Crystal', 'price': 20000, 'type': 'item', 'description': 'A mysterious crystal with unknown powers'},
            }
        }

    @commands.command(name='shop')
    async def shop(self, ctx, category=None):
        """View the shop"""
        shop_items = self.get_shop_items()
        
        if category is None:
            # Show shop categories
            embed = create_embed(
                "🛒 Economy Shop",
                "Welcome to the shop! Choose a category to browse items."
            )
            
            embed.add_field(
                name="🎨 Color Roles",
                value=f"`{ctx.prefix}shop colors`\nCustom colored roles for your profile",
                inline=True
            )
            embed.add_field(
                name="⭐ Special Roles", 
                value=f"`{ctx.prefix}shop special`\nExclusive premium roles",
                inline=True
            )
            embed.add_field(
                name="🚀 Perks",
                value=f"`{ctx.prefix}shop perks`\nTemporary boosts and benefits",
                inline=True
            )
            embed.add_field(
                name="🎁 Items",
                value=f"`{ctx.prefix}shop items`\nCollectible items for your inventory",
                inline=True
            )
            embed.add_field(
                name="💡 How to Buy",
                value=f"`{ctx.prefix}buy <item_id>`\nExample: `{ctx.prefix}buy red_role`",
                inline=False
            )
            
            user_data = self.bot.db.get_user(ctx.author.id)
            embed.set_footer(text=f"Your balance: ${user_data['balance']:,}")
            
            await ctx.send(embed=embed)
            return
        
        # Show specific category
        category_map = {
            'colors': ('🎨 Color Roles', shop_items['role_colors']),
            'special': ('⭐ Special Roles', shop_items['special_roles']),
            'perks': ('🚀 Perks', shop_items['perks']),
            'items': ('🎁 Items', shop_items['items'])
        }
        
        if category.lower() not in category_map:
            embed = create_error_embed(
                "❌ Invalid Category",
                f"Available categories: `colors`, `special`, `perks`, `items`"
            )
            await ctx.send(embed=embed)
            return
        
        title, items = category_map[category.lower()]
        embed = create_embed(title, "")
        
        user_data = self.bot.db.get_user(ctx.author.id)
        inventory = user_data.get('inventory', {})
        
        for item_id, item_data in items.items():
            owned = "✅ Owned" if item_id in inventory else ""
            price_text = f"${item_data['price']:,}"
            
            if item_data['type'] == 'perk':
                description = f"Duration: {item_data['duration']} days"
            elif item_data['type'] == 'item':
                description = item_data.get('description', 'Collectible item')
            else:
                description = "Role with custom color"
            
            embed.add_field(
                name=f"{item_data['name']} {owned}",
                value=f"**Price:** {price_text}\n**ID:** `{item_id}`\n{description}",
                inline=True
            )
        
        embed.set_footer(text=f"Your balance: ${user_data['balance']:,} | Use /buy <item_id> to purchase")
        await ctx.send(embed=embed)
    
    @commands.command(name='buy', aliases=['purchase'])
    async def buy_item(self, ctx, item_id=None):
        """Buy an item from the shop"""
        if not item_id:
            embed = create_error_embed(
                "❌ Missing Item ID",
                f"Please specify an item to buy.\nExample: `{ctx.prefix}buy red_role`\n\nUse `{ctx.prefix}shop` to see available items."
            )
            await ctx.send(embed=embed)
            return
        
        shop_items = self.get_shop_items()
        all_items = {}
        for category in shop_items.values():
            all_items.update(category)
        
        if item_id not in all_items:
            embed = create_error_embed(
                "❌ Item Not Found",
                f"Item `{item_id}` doesn't exist.\nUse `{ctx.prefix}shop` to see available items."
            )
            await ctx.send(embed=embed)
            return
        
        item_data = all_items[item_id]
        user_data = self.bot.db.get_user(ctx.author.id)
        
        # Check if user already owns the item
        inventory = user_data.get('inventory', {})
        if item_id in inventory:
            embed = create_error_embed(
                "❌ Already Owned",
                f"You already own **{item_data['name']}**!"
            )
            await ctx.send(embed=embed)
            return
        
        # Check if user has enough money
        if user_data['balance'] < item_data['price']:
            needed = item_data['price'] - user_data['balance']
            embed = create_error_embed(
                "❌ Insufficient Funds",
                f"You need **${needed:,}** more to buy **{item_data['name']}**.\n"
                f"Required: **${item_data['price']:,}**\n"
                f"Your balance: **${user_data['balance']:,}**"
            )
            await ctx.send(embed=embed)
            return
        
        # Process purchase
        if not self.bot.db.remove_balance(ctx.author.id, item_data['price']):
            embed = create_error_embed(
                "❌ Purchase Failed",
                "Failed to process payment. Please try again."
            )
            await ctx.send(embed=embed)
            return
        
        # Add item to inventory
        self.bot.db.add_to_inventory(ctx.author.id, item_id, item_data)
        
        # Handle different item types
        if item_data['type'] == 'role':
            await self.handle_role_purchase(ctx, item_id, item_data)
        elif item_data['type'] == 'perk':
            await self.handle_perk_purchase(ctx, item_id, item_data)
        
        embed = create_success_embed(
            "🛒 Purchase Successful!",
            f"You bought **{item_data['name']}** for **${item_data['price']:,}**!\n"
            f"Remaining balance: **${user_data['balance'] - item_data['price']:,}**"
        )
        
        if item_data['type'] == 'item':
            embed.add_field(
                name="📦 Added to Inventory",
                value=f"Check your inventory with `{ctx.prefix}inventory`",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def handle_role_purchase(self, ctx, item_id, item_data):
        """Handle role purchases"""
        try:
            # Check if role already exists
            existing_role = discord.utils.get(ctx.guild.roles, name=item_data['name'])
            
            if not existing_role:
                # Create the role
                role = await ctx.guild.create_role(
                    name=item_data['name'],
                    color=discord.Color(item_data['color']),
                    reason=f"Shop purchase by {ctx.author}"
                )
            else:
                role = existing_role
            
            # Add role to user
            await ctx.author.add_roles(role, reason=f"Shop purchase: {item_data['name']}")
            
        except discord.Forbidden:
            embed = create_error_embed(
                "⚠️ Role Assignment Failed",
                "I don't have permission to create or assign roles. Please contact an administrator."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed(
                "⚠️ Role Assignment Failed",
                f"Failed to assign role: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    async def handle_perk_purchase(self, ctx, item_id, item_data):
        """Handle perk purchases"""
        # Activate perk with expiration
        expiry = datetime.utcnow() + timedelta(days=item_data['duration'])
        self.bot.db.activate_perk(ctx.author.id, item_id, expiry)
    
    @commands.command(name='inventory', aliases=['inv', 'items'])
    async def inventory(self, ctx, user: discord.Member = None):
        """View your or another user's inventory"""
        target = user if user else ctx.author
        user_data = self.bot.db.get_user(target.id)
        inventory = user_data.get('inventory', {})
        
        if not inventory:
            pronoun = "You don't" if target == ctx.author else f"{target.display_name} doesn't"
            embed = create_embed(
                f"📦 {target.display_name}'s Inventory",
                f"{pronoun} have any items yet.\n"
                f"Visit the shop with `{ctx.prefix}shop` to buy items!"
            )
            await ctx.send(embed=embed)
            return
        
        embed = create_embed(
            f"📦 {target.display_name}'s Inventory",
            f"Total items: {len(inventory)}"
        )
        
        # Group items by type
        roles = []
        perks = []
        items = []
        
        for item_id, item_info in inventory.items():
            item_type = item_info.get('type', 'item')
            name = item_info.get('name', item_id)
            
            if item_type == 'role':
                roles.append(name)
            elif item_type == 'perk':
                expiry = item_info.get('expiry')
                if expiry and datetime.fromisoformat(expiry) > datetime.utcnow():
                    time_left = datetime.fromisoformat(expiry) - datetime.utcnow()
                    days_left = time_left.days
                    perks.append(f"{name} ({days_left}d left)")
                else:
                    perks.append(f"~~{name}~~ (expired)")
            else:
                items.append(name)
        
        if roles:
            embed.add_field(
                name="🎭 Roles",
                value="\n".join(roles[:10]) + ("\n..." if len(roles) > 10 else ""),
                inline=False
            )
        
        if perks:
            embed.add_field(
                name="🚀 Active Perks",
                value="\n".join(perks[:10]) + ("\n..." if len(perks) > 10 else ""),
                inline=False
            )
        
        if items:
            embed.add_field(
                name="🎁 Items",
                value="\n".join(items[:10]) + ("\n..." if len(items) > 10 else ""),
                inline=False
            )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.command(name='sell')
    async def sell_item(self, ctx, *, item_name=None):
        """Sell an item from your inventory"""
        if not item_name:
            embed = create_error_embed(
                "❌ Missing Item",
                f"Please specify an item to sell.\nExample: `{ctx.prefix}sell Trophy`\n\nUse `{ctx.prefix}inventory` to see your items."
            )
            await ctx.send(embed=embed)
            return
        
        user_data = self.bot.db.get_user(ctx.author.id)
        inventory = user_data.get('inventory', {})
        
        # Find item by name
        item_to_sell = None
        item_id = None
        
        for inv_item_id, item_info in inventory.items():
            if item_info.get('name', '').lower() == item_name.lower():
                item_to_sell = item_info
                item_id = inv_item_id
                break
        
        if not item_to_sell:
            embed = create_error_embed(
                "❌ Item Not Found",
                f"You don't own an item called **{item_name}**.\nUse `{ctx.prefix}inventory` to see your items."
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate sell price (50% of original price)
        original_price = item_to_sell.get('price', 0)
        sell_price = original_price // 2
        
        if sell_price == 0:
            embed = create_error_embed(
                "❌ Cannot Sell",
                f"**{item_to_sell['name']}** cannot be sold."
            )
            await ctx.send(embed=embed)
            return
        
        # Remove item from inventory and add money
        self.bot.db.remove_from_inventory(ctx.author.id, item_id)
        self.bot.db.add_balance(ctx.author.id, sell_price)
        
        # Remove role if it's a role item
        if item_to_sell.get('type') == 'role':
            try:
                role = discord.utils.get(ctx.guild.roles, name=item_to_sell['name'])
                if role and role in ctx.author.roles:
                    await ctx.author.remove_roles(role, reason=f"Sold item: {item_to_sell['name']}")
            except discord.Forbidden:
                pass
        
        embed = create_success_embed(
            "💰 Item Sold!",
            f"You sold **{item_to_sell['name']}** for **${sell_price:,}**!\n"
            f"New balance: **${user_data['balance'] + sell_price:,}**"
        )
        await ctx.send(embed=embed)
    
    @commands.group(name='eco', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def economy_admin(self, ctx):
        """Economy administration commands"""
        embed = create_embed(
            "💰 Economy Admin Commands",
            f"`{ctx.prefix}eco give <user> <amount>` - Give money to user\n"
            f"`{ctx.prefix}eco take <user> <amount>` - Take money from user\n"
            f"`{ctx.prefix}eco set <user> <amount>` - Set user's balance\n"
            f"`{ctx.prefix}eco reset <user>` - Reset user's economy data"
        )
        await ctx.send(embed=embed)
    
    @economy_admin.command(name='give')
    @commands.has_permissions(administrator=True)
    async def give_money(self, ctx, user: discord.Member, amount: int):
        """Give money to a user"""
        if amount <= 0:
            embed = create_error_embed("❌ Invalid Amount", "Amount must be positive.")
            await ctx.send(embed=embed)
            return
        
        self.bot.db.add_balance(user.id, amount)
        
        embed = create_success_embed(
            "💰 Money Given",
            f"Gave **${amount:,}** to {user.mention}."
        )
        await ctx.send(embed=embed)
    
    @economy_admin.command(name='take')
    @commands.has_permissions(administrator=True)
    async def take_money(self, ctx, user: discord.Member, amount: int):
        """Take money from a user"""
        if amount <= 0:
            embed = create_error_embed("❌ Invalid Amount", "Amount must be positive.")
            await ctx.send(embed=embed)
            return
        
        if self.bot.db.remove_balance(user.id, amount):
            embed = create_success_embed(
                "💸 Money Taken",
                f"Took **${amount:,}** from {user.mention}."
            )
        else:
            # Take what they have
            user_data = self.bot.db.get_user(user.id)
            taken = user_data['balance']
            self.bot.db.update_user(user.id, {'balance': 0})
            
            embed = create_success_embed(
                "💸 Money Taken",
                f"Took **${taken:,}** from {user.mention} (all they had)."
            )
        
        await ctx.send(embed=embed)
    
    @economy_admin.command(name='set')
    @commands.has_permissions(administrator=True)
    async def set_balance(self, ctx, user: discord.Member, amount: int):
        """Set a user's balance"""
        if amount < 0:
            embed = create_error_embed("❌ Invalid Amount", "Amount cannot be negative.")
            await ctx.send(embed=embed)
            return
        
        self.bot.db.update_user(user.id, {'balance': amount})
        
        embed = create_success_embed(
            "💰 Balance Set",
            f"Set {user.mention}'s balance to **${amount:,}**."
        )
        await ctx.send(embed=embed)
    
    @economy_admin.command(name='reset')
    @commands.has_permissions(administrator=True)
    async def reset_user(self, ctx, user: discord.Member):
        """Reset a user's economy data"""
        # Remove user from database
        if str(user.id) in self.bot.db.users_data:
            del self.bot.db.users_data[str(user.id)]
        
        embed = create_success_embed(
            "🔄 User Reset",
            f"Reset all economy data for {user.mention}."
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
