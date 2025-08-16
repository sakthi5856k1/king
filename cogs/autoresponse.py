import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from utils.helpers import create_embed, create_success_embed, create_error_embed, is_staff
from config.settings import AUTORESPONSE_CONFIG

class AutoResponse(commands.Cog):
    """Auto response system for common questions/triggers"""
    
    def __init__(self, bot):
        self.bot = bot
        self.response_cooldowns = {}  # Track response cooldowns per user
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle auto responses"""
        # Ignore bot messages and DMs
        if message.author.bot or isinstance(message.channel, discord.DMChannel):
            return
        
        # Check if auto responses are enabled
        if not AUTORESPONSE_CONFIG['enabled']:
            return
        
        # Check cooldown
        now = datetime.utcnow().timestamp()
        user_id = message.author.id
        
        if user_id in self.response_cooldowns:
            if now - self.response_cooldowns[user_id] < AUTORESPONSE_CONFIG['cooldown']:
                return
        
        # Get auto response
        response = self.bot.db.get_autoresponse(message.guild.id, message.content)
        
        if response:
            # Update cooldown
            self.response_cooldowns[user_id] = now
            
            # Send response
            try:
                await message.reply(response, mention_author=False)
            except discord.Forbidden:
                try:
                    await message.channel.send(response)
                except discord.Forbidden:
                    pass
    
    @commands.group(name='autoresponse', aliases=['ar'], invoke_without_command=True)
    @is_staff()
    async def autoresponse_group(self, ctx):
        """Auto response management commands"""
        embed = create_embed(
            "🤖 Auto Response Commands",
            f"`{ctx.prefix}ar add <trigger> <response>` - Add auto response\n"
            f"`{ctx.prefix}ar remove <trigger>` - Remove auto response\n"
            f"`{ctx.prefix}ar list` - List all auto responses\n"
            f"`{ctx.prefix}ar toggle` - Toggle auto responses on/off"
        )
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='add')
    @is_staff()
    async def add_autoresponse(self, ctx, trigger, *, response):
        """Add an auto response"""
        if len(trigger) < 2:
            embed = create_error_embed("❌ Invalid Trigger", "Trigger must be at least 2 characters long.")
            await ctx.send(embed=embed)
            return
        
        if len(response) > 2000:
            embed = create_error_embed("❌ Response Too Long", "Response must be 2000 characters or less.")
            await ctx.send(embed=embed)
            return
        
        # Add to database
        self.bot.db.add_autoresponse(ctx.guild.id, trigger, response)
        
        embed = create_success_embed(
            "✅ Auto Response Added",
            f"**Trigger:** {trigger}\n**Response:** {response[:100]}{'...' if len(response) > 100 else ''}"
        )
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='remove', aliases=['delete', 'rm'])
    @is_staff()
    async def remove_autoresponse(self, ctx, *, trigger):
        """Remove an auto response"""
        if self.bot.db.remove_autoresponse(ctx.guild.id, trigger):
            embed = create_success_embed(
                "✅ Auto Response Removed",
                f"Removed auto response for trigger: **{trigger}**"
            )
        else:
            embed = create_error_embed(
                "❌ Not Found",
                f"No auto response found for trigger: **{trigger}**"
            )
        
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='list')
    @is_staff()
    async def list_autoresponses(self, ctx, page: int = 1):
        """List all auto responses"""
        autoresponses = self.bot.db.get_guild_autoresponses(ctx.guild.id)
        
        if not autoresponses:
            embed = create_embed(
                "🤖 Auto Responses",
                "No auto responses configured for this server."
            )
            await ctx.send(embed=embed)
            return
        
        # Pagination
        per_page = 5
        total_pages = max(1, (len(autoresponses) + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        
        start = (page - 1) * per_page
        end = start + per_page
        
        embed = create_embed(
            f"🤖 Auto Responses - Page {page}/{total_pages}",
            ""
        )
        
        items = list(autoresponses.items())[start:end]
        
        for trigger, data in items:
            response = data['response']
            uses = data['uses']
            
            # Truncate long responses
            if len(response) > 200:
                response = response[:200] + "..."
            
            embed.add_field(
                name=f"📝 {trigger} (Used {uses} times)",
                value=response,
                inline=False
            )
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Total: {len(autoresponses)} responses")
        
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='toggle')
    @is_staff()
    async def toggle_autoresponses(self, ctx):
        """Toggle auto responses on/off for the server"""
        guild_config = self.bot.db.get_guild_config(ctx.guild.id)
        current_state = guild_config.get('autoresponse_enabled', True)
        new_state = not current_state
        
        self.bot.db.update_guild_config(ctx.guild.id, {'autoresponse_enabled': new_state})
        
        status = "enabled" if new_state else "disabled"
        embed = create_success_embed(
            f"🤖 Auto Responses {status.title()}",
            f"Auto responses are now **{status}** for this server."
        )
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='edit')
    @is_staff()
    async def edit_autoresponse(self, ctx, trigger, *, new_response):
        """Edit an existing auto response"""
        autoresponses = self.bot.db.get_guild_autoresponses(ctx.guild.id)
        
        if trigger.lower() not in autoresponses:
            embed = create_error_embed(
                "❌ Not Found",
                f"No auto response found for trigger: **{trigger}**"
            )
            await ctx.send(embed=embed)
            return
        
        if len(new_response) > 2000:
            embed = create_error_embed("❌ Response Too Long", "Response must be 2000 characters or less.")
            await ctx.send(embed=embed)
            return
        
        # Update the response
        self.bot.db.add_autoresponse(ctx.guild.id, trigger, new_response)
        
        embed = create_success_embed(
            "✅ Auto Response Updated",
            f"**Trigger:** {trigger}\n**New Response:** {new_response[:100]}{'...' if len(new_response) > 100 else ''}"
        )
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='info')
    @is_staff()
    async def autoresponse_info(self, ctx, *, trigger):
        """Get detailed information about an auto response"""
        autoresponses = self.bot.db.get_guild_autoresponses(ctx.guild.id)
        
        if trigger.lower() not in autoresponses:
            embed = create_error_embed(
                "❌ Not Found",
                f"No auto response found for trigger: **{trigger}**"
            )
            await ctx.send(embed=embed)
            return
        
        data = autoresponses[trigger.lower()]
        created_at = datetime.fromisoformat(data['created_at'])
        
        embed = create_embed(
            f"📝 Auto Response: {trigger}",
            f"**Response:**\n{data['response']}\n\n"
            f"**Uses:** {data['uses']}\n"
            f"**Created:** {created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='stats')
    @is_staff()
    async def autoresponse_stats(self, ctx):
        """View auto response statistics"""
        autoresponses = self.bot.db.get_guild_autoresponses(ctx.guild.id)
        guild_config = self.bot.db.get_guild_config(ctx.guild.id)
        
        total_responses = len(autoresponses)
        total_uses = sum(data['uses'] for data in autoresponses.values())
        enabled = guild_config.get('autoresponse_enabled', True)
        
        # Most used response
        most_used = None
        if autoresponses:
            most_used = max(autoresponses.items(), key=lambda x: x[1]['uses'])
        
        embed = create_embed(
            "📊 Auto Response Statistics",
            f"**Status:** {'Enabled' if enabled else 'Disabled'}\n"
            f"**Total Responses:** {total_responses}\n"
            f"**Total Uses:** {total_uses}\n"
            f"**Most Used:** {most_used[0] if most_used else 'None'} ({most_used[1]['uses']} uses)" if most_used else "**Most Used:** None"
        )
        
        await ctx.send(embed=embed)
    
    @autoresponse_group.command(name='clear')
    @is_staff()
    async def clear_autoresponses(self, ctx):
        """Clear all auto responses (with confirmation)"""
        autoresponses = self.bot.db.get_guild_autoresponses(ctx.guild.id)
        
        if not autoresponses:
            embed = create_error_embed("❌ No Responses", "No auto responses to clear.")
            await ctx.send(embed=embed)
            return
        
        # Confirmation
        embed = create_embed(
            "⚠️ Confirm Clear",
            f"Are you sure you want to delete all **{len(autoresponses)}** auto responses?\n\n"
            f"React with ✅ to confirm or ❌ to cancel."
        )
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == msg.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Clear all responses
                self.bot.db.autoresponse_data[str(ctx.guild.id)] = {}
                
                embed = create_success_embed(
                    "✅ Responses Cleared",
                    "All auto responses have been deleted."
                )
            else:
                embed = create_embed("❌ Cancelled", "Clear operation cancelled.")
            
        except asyncio.TimeoutError:
            embed = create_error_embed("⏰ Timeout", "Confirmation timed out. Operation cancelled.")
        
        try:
            await msg.edit(embed=embed)
            await msg.clear_reactions()
        except discord.Forbidden:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoResponse(bot))
