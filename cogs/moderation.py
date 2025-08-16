import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from utils.helpers import (create_embed, create_success_embed, create_error_embed, 
                          create_warning_embed, parse_time, format_time, is_moderator)
from config.settings import MODERATION_CONFIG

class Moderation(commands.Cog):
    """Moderation system with basic commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.muted_users = {}  # Track temporarily muted users
    
    @commands.command(name='kick')
    @is_moderator()
    async def kick_user(self, ctx, user: discord.Member, *, reason="No reason provided"):
        """Kick a user from the server"""
        # Permission checks
        if user.id == ctx.author.id:
            embed = create_error_embed("❌ Invalid Target", "You cannot kick yourself.")
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = create_error_embed("❌ Insufficient Permissions", "You cannot kick this user (role hierarchy).")
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.guild.me.top_role:
            embed = create_error_embed("❌ Bot Insufficient Permissions", "I cannot kick this user (role hierarchy).")
            await ctx.send(embed=embed)
            return
        
        try:
            # Send DM to user before kicking
            try:
                dm_embed = create_embed(
                    f"👢 Kicked from {ctx.guild.name}",
                    f"**Reason:** {reason}\n**Moderator:** {ctx.author}"
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            
            # Kick the user
            await user.kick(reason=f"{ctx.author}: {reason}")
            
            # Log the action
            await self.log_moderation_action(ctx.guild, "kick", user, ctx.author, reason)
            
            embed = create_success_embed(
                "👢 User Kicked",
                f"**User:** {user} ({user.id})\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {ctx.author}"
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = create_error_embed("❌ Permission Error", "I don't have permission to kick this user.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("❌ Error", f"Failed to kick user: {str(e)}")
            await ctx.send(embed=embed)
    
    @commands.command(name='ban')
    @is_moderator()
    async def ban_user(self, ctx, user: discord.Member, delete_days: int = 0, *, reason="No reason provided"):
        """Ban a user from the server"""
        # Permission checks
        if user.id == ctx.author.id:
            embed = create_error_embed("❌ Invalid Target", "You cannot ban yourself.")
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = create_error_embed("❌ Insufficient Permissions", "You cannot ban this user (role hierarchy).")
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.guild.me.top_role:
            embed = create_error_embed("❌ Bot Insufficient Permissions", "I cannot ban this user (role hierarchy).")
            await ctx.send(embed=embed)
            return
        
        if delete_days < 0 or delete_days > 7:
            embed = create_error_embed("❌ Invalid Delete Days", "Delete days must be between 0 and 7.")
            await ctx.send(embed=embed)
            return
        
        try:
            # Send DM to user before banning
            try:
                dm_embed = create_embed(
                    f"🔨 Banned from {ctx.guild.name}",
                    f"**Reason:** {reason}\n**Moderator:** {ctx.author}"
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            
            # Ban the user
            await user.ban(reason=f"{ctx.author}: {reason}", delete_message_days=delete_days)
            
            # Log the action
            await self.log_moderation_action(ctx.guild, "ban", user, ctx.author, reason)
            
            embed = create_success_embed(
                "🔨 User Banned",
                f"**User:** {user} ({user.id})\n"
                f"**Reason:** {reason}\n"
                f"**Delete Days:** {delete_days}\n"
                f"**Moderator:** {ctx.author}"
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = create_error_embed("❌ Permission Error", "I don't have permission to ban this user.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("❌ Error", f"Failed to ban user: {str(e)}")
            await ctx.send(embed=embed)
    
    @commands.command(name='unban')
    @is_moderator()
    async def unban_user(self, ctx, user_id: int, *, reason="No reason provided"):
        """Unban a user from the server"""
        try:
            user = discord.Object(id=user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            
            # Log the action
            await self.log_moderation_action(ctx.guild, "unban", user, ctx.author, reason)
            
            embed = create_success_embed(
                "🔓 User Unbanned",
                f"**User ID:** {user_id}\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {ctx.author}"
            )
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            embed = create_error_embed("❌ Not Found", "User is not banned or doesn't exist.")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = create_error_embed("❌ Permission Error", "I don't have permission to unban users.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("❌ Error", f"Failed to unban user: {str(e)}")
            await ctx.send(embed=embed)
    
    @commands.command(name='mute')
    @is_moderator()
    async def mute_user(self, ctx, user: discord.Member, duration=None, *, reason="No reason provided"):
        """Mute a user (remove send message permissions)"""
        # Permission checks
        if user.id == ctx.author.id:
            embed = create_error_embed("❌ Invalid Target", "You cannot mute yourself.")
            await ctx.send(embed=embed)
            return
        
        if user.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = create_error_embed("❌ Insufficient Permissions", "You cannot mute this user (role hierarchy).")
            await ctx.send(embed=embed)
            return
        
        # Find or create mute role
        mute_role = discord.utils.get(ctx.guild.roles, name=MODERATION_CONFIG['mute_role'])
        if not mute_role:
            try:
                mute_role = await ctx.guild.create_role(
                    name=MODERATION_CONFIG['mute_role'],
                    permissions=discord.Permissions(send_messages=False, speak=False),
                    reason="Auto-created mute role"
                )
                
                # Set permissions for all channels
                for channel in ctx.guild.channels:
                    try:
                        await channel.set_permissions(mute_role, send_messages=False, speak=False)
                    except discord.Forbidden:
                        pass
                        
            except discord.Forbidden:
                embed = create_error_embed("❌ Permission Error", "I cannot create the mute role.")
                await ctx.send(embed=embed)
                return
        
        # Check if user is already muted
        if mute_role in user.roles:
            embed = create_error_embed("❌ Already Muted", "User is already muted.")
            await ctx.send(embed=embed)
            return
        
        try:
            # Add mute role
            await user.add_roles(mute_role, reason=f"{ctx.author}: {reason}")
            
            # Parse duration
            unmute_time = None
            if duration:
                duration_seconds = parse_time(duration)
                if duration_seconds > 0:
                    unmute_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
                    self.muted_users[user.id] = {
                        'guild_id': ctx.guild.id,
                        'unmute_time': unmute_time,
                        'reason': reason
                    }
                    
                    # Schedule unmute
                    asyncio.create_task(self.schedule_unmute(user.id, duration_seconds))
            
            # Log the action
            await self.log_moderation_action(ctx.guild, "mute", user, ctx.author, reason)
            
            duration_str = f" for {format_time(parse_time(duration))}" if duration else " indefinitely"
            
            embed = create_success_embed(
                "🔇 User Muted",
                f"**User:** {user} ({user.id})\n"
                f"**Duration:** {duration_str}\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {ctx.author}"
            )
            await ctx.send(embed=embed)
            
            # Send DM to user
            try:
                dm_embed = create_embed(
                    f"🔇 Muted in {ctx.guild.name}",
                    f"**Duration:** {duration_str}\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            embed = create_error_embed("❌ Permission Error", "I don't have permission to mute this user.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("❌ Error", f"Failed to mute user: {str(e)}")
            await ctx.send(embed=embed)
    
    @commands.command(name='unmute')
    @is_moderator()
    async def unmute_user(self, ctx, user: discord.Member, *, reason="No reason provided"):
        """Unmute a user"""
        mute_role = discord.utils.get(ctx.guild.roles, name=MODERATION_CONFIG['mute_role'])
        
        if not mute_role or mute_role not in user.roles:
            embed = create_error_embed("❌ Not Muted", "User is not muted.")
            await ctx.send(embed=embed)
            return
        
        try:
            # Remove mute role
            await user.remove_roles(mute_role, reason=f"{ctx.author}: {reason}")
            
            # Remove from scheduled unmutes
            if user.id in self.muted_users:
                del self.muted_users[user.id]
            
            # Log the action
            await self.log_moderation_action(ctx.guild, "unmute", user, ctx.author, reason)
            
            embed = create_success_embed(
                "🔊 User Unmuted",
                f"**User:** {user} ({user.id})\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {ctx.author}"
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = create_error_embed("❌ Permission Error", "I don't have permission to unmute this user.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("❌ Error", f"Failed to unmute user: {str(e)}")
            await ctx.send(embed=embed)
    
    @commands.command(name='warn')
    @is_moderator()
    async def warn_user(self, ctx, user: discord.Member, *, reason="No reason provided"):
        """Warn a user"""
        if user.id == ctx.author.id:
            embed = create_error_embed("❌ Invalid Target", "You cannot warn yourself.")
            await ctx.send(embed=embed)
            return
        
        # Add warning to database
        warning_count = self.bot.db.add_warning(user.id, ctx.guild.id, reason, ctx.author.id)
        
        # Log the action
        await self.log_moderation_action(ctx.guild, "warn", user, ctx.author, reason)
        
        embed = create_warning_embed(
            "⚠️ User Warned",
            f"**User:** {user} ({user.id})\n"
            f"**Warning #{warning_count}**\n"
            f"**Reason:** {reason}\n"
            f"**Moderator:** {ctx.author}"
        )
        await ctx.send(embed=embed)
        
        # Send DM to user
        try:
            dm_embed = create_embed(
                f"⚠️ Warning in {ctx.guild.name}",
                f"**Warning #{warning_count}**\n**Reason:** {reason}\n**Moderator:** {ctx.author}"
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        
        # Check for automatic actions based on warning count
        if warning_count >= MODERATION_CONFIG['max_warns']:
            action = MODERATION_CONFIG['warn_actions'].get(warning_count)
            if action == 'timeout':
                try:
                    await user.timeout(timedelta(hours=1), reason="Automatic action: Too many warnings")
                    embed = create_embed("🔇 Automatic Action", f"{user.mention} has been timed out for 1 hour (too many warnings).")
                    await ctx.send(embed=embed)
                except discord.Forbidden:
                    pass
            elif action == 'kick':
                try:
                    await user.kick(reason="Automatic action: Too many warnings")
                    embed = create_embed("👢 Automatic Action", f"{user.mention} has been kicked (too many warnings).")
                    await ctx.send(embed=embed)
                except discord.Forbidden:
                    pass
    
    @commands.command(name='warnings', aliases=['warns'])
    async def view_warnings(self, ctx, user: discord.Member = None):
        """View warnings for a user"""
        target = user if user is not None else ctx.author
        warnings = self.bot.db.get_warnings(target.id, ctx.guild.id)
        
        if not warnings:
            embed = create_embed(
                f"⚠️ Warnings for {target.display_name}",
                "No warnings found."
            )
            await ctx.send(embed=embed)
            return
        
        embed = create_embed(
            f"⚠️ Warnings for {target.display_name}",
            f"Total warnings: **{len(warnings)}**"
        )
        
        for i, warning in enumerate(warnings[-5:], 1):  # Show last 5 warnings
            moderator = self.bot.get_user(int(warning['moderator_id']))
            mod_name = moderator.display_name if moderator else "Unknown"
            timestamp = datetime.fromisoformat(warning['timestamp']).strftime('%Y-%m-%d %H:%M')
            
            embed.add_field(
                name=f"Warning #{len(warnings) - 5 + i}",
                value=f"**Reason:** {warning['reason']}\n**By:** {mod_name}\n**Date:** {timestamp}",
                inline=False
            )
        
        if len(warnings) > 5:
            embed.set_footer(text=f"Showing last 5 of {len(warnings)} warnings")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='purge', aliases=['clear'])
    @is_moderator()
    async def purge_messages(self, ctx, amount: int, user: discord.Member = None):
        """Delete messages in bulk"""
        if amount <= 0 or amount > 100:
            embed = create_error_embed("❌ Invalid Amount", "Amount must be between 1 and 100.")
            await ctx.send(embed=embed)
            return
        
        try:
            if user:
                # Delete messages from specific user
                def is_target(message):
                    return message.author == user
                
                deleted = await ctx.channel.purge(limit=amount, check=is_target)
            else:
                # Delete all messages
                deleted = await ctx.channel.purge(limit=amount)
            
            # Log the action
            reason = f"Purged {len(deleted)} messages" + (f" from {user}" if user else "")
            await self.log_moderation_action(ctx.guild, "purge", None, ctx.author, reason)
            
            embed = create_success_embed(
                "🗑️ Messages Purged",
                f"Deleted **{len(deleted)}** messages" + (f" from {user.mention}" if user else "")
            )
            
            # Send temporary confirmation
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            try:
                await msg.delete()
            except discord.NotFound:
                pass
                
        except discord.Forbidden:
            embed = create_error_embed("❌ Permission Error", "I don't have permission to delete messages.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = create_error_embed("❌ Error", f"Failed to purge messages: {str(e)}")
            await ctx.send(embed=embed)
    
    async def schedule_unmute(self, user_id, duration):
        """Schedule automatic unmute"""
        await asyncio.sleep(duration)
        
        if user_id not in self.muted_users:
            return
        
        mute_data = self.muted_users[user_id]
        guild = self.bot.get_guild(mute_data['guild_id'])
        
        if not guild:
            del self.muted_users[user_id]
            return
        
        user = guild.get_member(user_id)
        if not user:
            del self.muted_users[user_id]
            return
        
        mute_role = discord.utils.get(guild.roles, name=MODERATION_CONFIG['mute_role'])
        if mute_role and mute_role in user.roles:
            try:
                await user.remove_roles(mute_role, reason="Automatic unmute (duration expired)")
                
                # Log the action
                await self.log_moderation_action(guild, "unmute", user, self.bot.user, "Automatic unmute (duration expired)")
                
            except discord.Forbidden:
                pass
        
        del self.muted_users[user_id]
    
    async def log_moderation_action(self, guild, action, target, moderator, reason):
        """Log moderation actions"""
        # This will be handled by the logging cog
        self.bot.dispatch('moderation_action', guild, action, target, moderator, reason)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
