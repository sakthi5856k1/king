import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from utils.helpers import create_embed, create_success_embed, create_error_embed, is_staff
from config.settings import MODMAIL_CONFIG

class ModMail(commands.Cog):
    """ModMail system for private user-to-moderator communication"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_dms = {}  # Track users currently in DM modmail
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle DM messages for modmail"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only handle DM messages
        if not isinstance(message.channel, discord.DMChannel):
            return
        
        # Check if user has any mutual guilds with the bot
        mutual_guilds = [guild for guild in self.bot.guilds if guild.get_member(message.author.id)]
        
        if not mutual_guilds:
            return
        
        # If user is not in an active modmail session, start one
        if message.author.id not in self.active_dms:
            await self.start_modmail_session(message.author, message.content, mutual_guilds)
        else:
            # Forward message to existing ticket
            await self.forward_to_modmail(message.author, message.content)
    
    async def start_modmail_session(self, user, initial_message, guilds):
        """Start a new modmail session"""
        # For simplicity, use the first mutual guild
        guild = guilds[0]
        
        # Check if user already has too many open tickets
        existing_tickets = self.bot.db.get_user_tickets(user.id, guild.id)
        if len(existing_tickets) >= MODMAIL_CONFIG['max_tickets_per_user']:
            embed = create_error_embed(
                "Too Many Tickets",
                f"You already have {len(existing_tickets)} open tickets. Please wait for them to be resolved."
            )
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                pass
            return
        
        # Find or create modmail category
        category = discord.utils.get(guild.categories, name=MODMAIL_CONFIG['category_name'])
        if not category:
            try:
                category = await guild.create_category(MODMAIL_CONFIG['category_name'])
            except discord.Forbidden:
                return
        
        # Create ticket channel
        channel_name = f"ticket-{user.name}-{user.discriminator}"
        try:
            channel = await guild.create_text_channel(
                channel_name,
                category=category,
                topic=f"ModMail ticket for {user} ({user.id})"
            )
        except discord.Forbidden:
            return
        
        # Create ticket in database
        ticket_id = self.bot.db.create_modmail_ticket(user.id, guild.id, channel.id)
        
        # Add user to active DMs
        self.active_dms[user.id] = {
            'ticket_id': ticket_id,
            'channel_id': channel.id,
            'guild_id': guild.id
        }
        
        # Send initial messages
        embed = create_embed(
            "📨 ModMail Ticket Created",
            f"**User:** {user.mention} ({user})\n"
            f"**User ID:** {user.id}\n"
            f"**Created:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"**Initial Message:**\n{initial_message}"
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await channel.send(embed=embed)
        
        # Send confirmation to user
        user_embed = create_success_embed(
            "📨 ModMail Ticket Created",
            f"Your message has been sent to the moderators of **{guild.name}**.\n"
            f"You can continue to send messages here and they will be forwarded to the staff.\n\n"
            f"To close this ticket, react with 🔒 or type `close`."
        )
        
        try:
            msg = await user.send(embed=user_embed)
            await msg.add_reaction("🔒")
        except discord.Forbidden:
            pass
        
        # Add initial message to ticket
        self.bot.db.add_modmail_message(ticket_id, user.id, initial_message)
    
    async def forward_to_modmail(self, user, content):
        """Forward user message to modmail channel"""
        if user.id not in self.active_dms:
            return
        
        session = self.active_dms[user.id]
        channel = self.bot.get_channel(session['channel_id'])
        
        if not channel:
            # Channel was deleted, clean up
            del self.active_dms[user.id]
            return
        
        # Check if user wants to close the ticket
        if content.lower() in ['close', 'closed', 'resolve', 'resolved']:
            await self.close_ticket(session['ticket_id'], user.id, user=user)
            return
        
        # Create embed for the message
        embed = create_embed(
            f"💬 {user.display_name}",
            content
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_footer(text=f"User ID: {user.id}")
        
        await channel.send(embed=embed)
        
        # Add message to database
        self.bot.db.add_modmail_message(session['ticket_id'], user.id, content)
    
    @commands.command(name='reply', aliases=['r'])
    @is_staff()
    async def reply_to_ticket(self, ctx, *, message):
        """Reply to a modmail ticket"""
        # Check if this is a modmail channel
        if not ctx.channel.topic or 'ModMail ticket for' not in ctx.channel.topic:
            embed = create_error_embed("❌ Invalid Channel", "This is not a modmail ticket channel.")
            await ctx.send(embed=embed)
            return
        
        # Extract user ID from channel topic
        try:
            user_id = int(ctx.channel.topic.split('(')[1].split(')')[0])
            user = self.bot.get_user(user_id)
        except:
            embed = create_error_embed("❌ Error", "Could not find user for this ticket.")
            await ctx.send(embed=embed)
            return
        
        if not user:
            embed = create_error_embed("❌ User Not Found", "The user for this ticket could not be found.")
            await ctx.send(embed=embed)
            return
        
        # Send message to user
        embed = create_embed(
            f"💬 {ctx.author.display_name} (Staff)",
            message
        )
        embed.set_author(name=f"{ctx.author} (Staff)", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"From: {ctx.guild.name}")
        
        try:
            await user.send(embed=embed)
            
            # Confirm in channel
            confirm_embed = create_success_embed("✅ Message Sent", f"Reply sent to {user}")
            await ctx.send(embed=confirm_embed)
            
            # Find ticket ID and add to database
            for ticket_id, session in self.active_dms.items():
                if session['channel_id'] == ctx.channel.id:
                    self.bot.db.add_modmail_message(ticket_id, ctx.author.id, f"[STAFF] {message}")
                    break
            
        except discord.Forbidden:
            embed = create_error_embed("❌ Cannot Send", "Could not send message to user (DMs disabled).")
            await ctx.send(embed=embed)
    
    @commands.command(name='close')
    @is_staff()
    async def close_ticket_command(self, ctx, *, reason="No reason provided"):
        """Close a modmail ticket"""
        # Check if this is a modmail channel
        if not ctx.channel.topic or 'ModMail ticket for' not in ctx.channel.topic:
            embed = create_error_embed("❌ Invalid Channel", "This is not a modmail ticket channel.")
            await ctx.send(embed=embed)
            return
        
        # Find the ticket ID
        ticket_id = None
        for tid, session in self.active_dms.items():
            if session['channel_id'] == ctx.channel.id:
                ticket_id = session['ticket_id']
                break
        
        if ticket_id:
            await self.close_ticket(ticket_id, ctx.author.id, reason=reason, channel=ctx.channel)
        else:
            # Try to close anyway (in case of database desync)
            await ctx.channel.delete(reason=f"ModMail ticket closed by {ctx.author}")
    
    async def close_ticket(self, ticket_id, closer_id, reason="No reason provided", user=None, channel=None):
        """Close a modmail ticket"""
        ticket = self.bot.db.get_modmail_ticket(ticket_id)
        if not ticket:
            return
        
        # Close in database
        self.bot.db.close_modmail_ticket(ticket_id, closer_id)
        
        # Remove from active DMs
        user_id = int(ticket['user_id'])
        if user_id in self.active_dms:
            del self.active_dms[user_id]
        
        # Get user and channel if not provided
        if not user:
            user = self.bot.get_user(user_id)
        
        if not channel:
            channel = self.bot.get_channel(int(ticket['channel_id']))
        
        # Send closure message to user
        if user:
            embed = create_embed(
                "🔒 Ticket Closed",
                f"Your modmail ticket has been closed.\n\n**Reason:** {reason}\n\n"
                f"If you need further assistance, feel free to send another message."
            )
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                pass
        
        # Delete channel after a delay
        if channel:
            embed = create_embed(
                "🔒 Ticket Closed",
                f"This ticket has been closed by <@{closer_id}>.\n**Reason:** {reason}\n\n"
                f"Channel will be deleted in 10 seconds."
            )
            await channel.send(embed=embed)
            
            await asyncio.sleep(10)
            try:
                await channel.delete(reason=f"ModMail ticket closed by {closer_id}")
            except discord.NotFound:
                pass
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle ticket closure via reaction"""
        if user.bot:
            return
        
        if isinstance(reaction.message.channel, discord.DMChannel) and str(reaction.emoji) == "🔒":
            if user.id in self.active_dms:
                session = self.active_dms[user.id]
                await self.close_ticket(session['ticket_id'], user.id, user=user)
    
    @commands.group(name='modmail', invoke_without_command=True)
    @is_staff()
    async def modmail_group(self, ctx):
        """ModMail management commands"""
        embed = create_embed(
            "📨 ModMail Commands",
            f"`{ctx.prefix}modmail setup` - Set up modmail category\n"
            f"`{ctx.prefix}reply <message>` - Reply to a ticket\n"
            f"`{ctx.prefix}close [reason]` - Close a ticket\n"
            f"`{ctx.prefix}modmail stats` - View modmail statistics"
        )
        await ctx.send(embed=embed)
    
    @modmail_group.command(name='setup')
    @is_staff()
    async def setup_modmail(self, ctx):
        """Set up modmail for the server"""
        # Create category if it doesn't exist
        category = discord.utils.get(ctx.guild.categories, name=MODMAIL_CONFIG['category_name'])
        if not category:
            try:
                category = await ctx.guild.create_category(MODMAIL_CONFIG['category_name'])
                embed = create_success_embed(
                    "✅ ModMail Setup Complete",
                    f"Created category: {category.name}\n\n"
                    f"Users can now DM the bot to create tickets!"
                )
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = create_error_embed(
                    "❌ Setup Failed",
                    "I don't have permission to create categories."
                )
                await ctx.send(embed=embed)
        else:
            embed = create_error_embed(
                "❌ Already Set Up",
                f"ModMail category already exists: {category.name}"
            )
            await ctx.send(embed=embed)
    
    @modmail_group.command(name='stats')
    @is_staff()
    async def modmail_stats(self, ctx):
        """View modmail statistics"""
        total_tickets = len(self.bot.db.modmail_data)
        active_tickets = len([t for t in self.bot.db.modmail_data.values() if t['status'] == 'open'])
        active_dms = len(self.active_dms)
        
        embed = create_embed(
            "📊 ModMail Statistics",
            f"**Total Tickets:** {total_tickets}\n"
            f"**Active Tickets:** {active_tickets}\n"
            f"**Active DM Sessions:** {active_dms}"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModMail(bot))
