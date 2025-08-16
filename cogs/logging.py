import discord
from discord.ext import commands
import logging
from datetime import datetime
from utils.helpers import create_embed, create_success_embed, create_error_embed, is_staff

class Logging(commands.Cog):
    """Logging system for server events and moderation actions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log when a member joins"""
        embed = create_embed(
            "📥 Member Joined",
            f"**User:** {member.mention} ({member})\n"
            f"**ID:** {member.id}\n"
            f"**Account Created:** {member.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"**Member Count:** {member.guild.member_count}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.color = 0x00ff00
        
        await self.send_to_log_channel(member.guild, embed, "member_events")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log when a member leaves"""
        embed = create_embed(
            "📤 Member Left",
            f"**User:** {member} ({member.id})\n"
            f"**Joined:** {member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else 'Unknown'} UTC\n"
            f"**Roles:** {', '.join([role.name for role in member.roles[1:]]) if len(member.roles) > 1 else 'None'}\n"
            f"**Member Count:** {member.guild.member_count}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.color = 0xff0000
        
        await self.send_to_log_channel(member.guild, embed, "member_events")
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Log when a member is banned"""
        embed = create_embed(
            "🔨 Member Banned",
            f"**User:** {user} ({user.id})\n"
            f"**Account Created:** {user.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.color = 0x8b0000
        
        await self.send_to_log_channel(guild, embed, "moderation")
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Log when a member is unbanned"""
        embed = create_embed(
            "🔓 Member Unbanned",
            f"**User:** {user} ({user.id})\n"
            f"**Account Created:** {user.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.color = 0x00ff00
        
        await self.send_to_log_channel(guild, embed, "moderation")
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log when a message is deleted"""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        # Don't log if message was deleted by purge command (too spammy)
        if hasattr(message, '_purged'):
            return
        
        embed = create_embed(
            "🗑️ Message Deleted",
            f"**Author:** {message.author.mention} ({message.author})\n"
            f"**Channel:** {message.channel.mention}\n"
            f"**Content:** {message.content[:1000] if message.content else '*No content*'}"
        )
        embed.set_footer(text=f"Message ID: {message.id} • Author ID: {message.author.id}")
        embed.color = 0xff6b6b
        
        # Add attachments info
        if message.attachments:
            attachments = [f"{att.filename} ({att.size} bytes)" for att in message.attachments]
            embed.add_field(name="Attachments", value="\n".join(attachments)[:1024], inline=False)
        
        await self.send_to_log_channel(message.guild, embed, "message_events")
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log when a message is edited"""
        # Ignore bot messages, DMs, and embeds
        if before.author.bot or not before.guild or before.content == after.content:
            return
        
        embed = create_embed(
            "✏️ Message Edited",
            f"**Author:** {before.author.mention} ({before.author})\n"
            f"**Channel:** {before.channel.mention}\n"
            f"**Message:** [Jump to message]({after.jump_url})"
        )
        
        # Add before/after content
        if before.content:
            embed.add_field(
                name="Before",
                value=before.content[:1024],
                inline=False
            )
        
        if after.content:
            embed.add_field(
                name="After",
                value=after.content[:1024],
                inline=False
            )
        
        embed.set_footer(text=f"Message ID: {before.id} • Author ID: {before.author.id}")
        embed.color = 0xffd93d
        
        await self.send_to_log_channel(before.guild, embed, "message_events")
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log when a member is updated (roles, nickname)"""
        guild = before.guild
        
        # Check nickname change
        if before.nick != after.nick:
            embed = create_embed(
                "👤 Nickname Changed",
                f"**User:** {after.mention} ({after})\n"
                f"**Before:** {before.nick or 'None'}\n"
                f"**After:** {after.nick or 'None'}"
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.color = 0x74c0fc
            
            await self.send_to_log_channel(guild, embed, "member_events")
        
        # Check role changes
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        
        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles
        
        if added_roles or removed_roles:
            embed = create_embed(
                "🏷️ Roles Updated",
                f"**User:** {after.mention} ({after})"
            )
            
            if added_roles:
                embed.add_field(
                    name="Added Roles",
                    value=", ".join([role.mention for role in added_roles]),
                    inline=False
                )
            
            if removed_roles:
                embed.add_field(
                    name="Removed Roles",
                    value=", ".join([role.mention for role in removed_roles]),
                    inline=False
                )
            
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.color = 0x845ec2
            
            await self.send_to_log_channel(guild, embed, "member_events")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Log voice channel events"""
        if before.channel == after.channel:
            return
        
        embed = None
        
        if before.channel is None and after.channel is not None:
            # User joined a voice channel
            embed = create_embed(
                "🔊 Voice Channel Joined",
                f"**User:** {member.mention} ({member})\n"
                f"**Channel:** {after.channel.mention}"
            )
            embed.color = 0x51cf66
            
        elif before.channel is not None and after.channel is None:
            # User left a voice channel
            embed = create_embed(
                "🔇 Voice Channel Left",
                f"**User:** {member.mention} ({member})\n"
                f"**Channel:** {before.channel.mention}"
            )
            embed.color = 0xff6b6b
            
        elif before.channel != after.channel:
            # User moved between voice channels
            embed = create_embed(
                "🔄 Voice Channel Moved",
                f"**User:** {member.mention} ({member})\n"
                f"**From:** {before.channel.mention}\n"
                f"**To:** {after.channel.mention}"
            )
            embed.color = 0x74c0fc
        
        if embed:
            embed.set_thumbnail(url=member.display_avatar.url)
            await self.send_to_log_channel(member.guild, embed, "voice_events")
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log when a channel is created"""
        embed = create_embed(
            "📝 Channel Created",
            f"**Channel:** {channel.mention}\n"
            f"**Type:** {channel.type.name.title()}\n"
            f"**Category:** {channel.category.name if channel.category else 'None'}"
        )
        embed.color = 0x51cf66
        
        await self.send_to_log_channel(channel.guild, embed, "server_events")
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log when a channel is deleted"""
        embed = create_embed(
            "🗑️ Channel Deleted",
            f"**Channel:** #{channel.name}\n"
            f"**Type:** {channel.type.name.title()}\n"
            f"**Category:** {channel.category.name if channel.category else 'None'}"
        )
        embed.color = 0xff6b6b
        
        await self.send_to_log_channel(channel.guild, embed, "server_events")
    
    @commands.Cog.listener()
    async def on_moderation_action(self, guild, action, target, moderator, reason):
        """Log moderation actions"""
        actions_emoji = {
            'kick': '👢',
            'ban': '🔨',
            'unban': '🔓',
            'mute': '🔇',
            'unmute': '🔊',
            'warn': '⚠️',
            'purge': '🗑️'
        }
        
        emoji = actions_emoji.get(action, '🔧')
        action_name = action.title()
        
        embed = create_embed(
            f"{emoji} {action_name}",
            f"**Target:** {target if target else 'N/A'}\n"
            f"**Moderator:** {moderator}\n"
            f"**Reason:** {reason}"
        )
        
        if target and hasattr(target, 'display_avatar'):
            embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.color = 0xff8c42
        
        await self.send_to_log_channel(guild, embed, "moderation")
    
    async def send_to_log_channel(self, guild, embed, log_type):
        """Send embed to appropriate log channel"""
        guild_config = self.bot.db.get_guild_config(guild.id)
        
        # Map log types to config keys
        channel_mapping = {
            "moderation": "mod_log_channel",
            "member_events": "member_log_channel",
            "message_events": "message_log_channel",
            "voice_events": "voice_log_channel",
            "server_events": "server_log_channel"
        }
        
        # Try specific log channel first, then general log channel
        config_key = channel_mapping.get(log_type, "log_channel")
        channel_id = guild_config.get(config_key) or guild_config.get("log_channel")
        
        if not channel_id:
            return
        
        channel = guild.get_channel(int(channel_id))
        if not channel:
            return
        
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            self.logger.error(f"Failed to send log message: {e}")
    
    @commands.group(name='logging', aliases=['log'], invoke_without_command=True)
    @is_staff()
    async def logging_group(self, ctx):
        """Logging system configuration"""
        embed = create_embed(
            "📊 Logging Commands",
            f"`{ctx.prefix}log channel <channel>` - Set general log channel\n"
            f"`{ctx.prefix}log moderation <channel>` - Set moderation log channel\n"
            f"`{ctx.prefix}log members <channel>` - Set member log channel\n"
            f"`{ctx.prefix}log messages <channel>` - Set message log channel\n"
            f"`{ctx.prefix}log voice <channel>` - Set voice log channel\n"
            f"`{ctx.prefix}log server <channel>` - Set server log channel\n"
            f"`{ctx.prefix}log disable <type>` - Disable logging type\n"
            f"`{ctx.prefix}log status` - View current logging configuration"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='channel')
    @is_staff()
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the general log channel"""
        self.bot.db.update_guild_config(ctx.guild.id, {"log_channel": str(channel.id)})
        
        embed = create_success_embed(
            "✅ Log Channel Set",
            f"General log channel set to {channel.mention}"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='moderation', aliases=['mod'])
    @is_staff()
    async def set_mod_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the moderation log channel"""
        self.bot.db.update_guild_config(ctx.guild.id, {"mod_log_channel": str(channel.id)})
        
        embed = create_success_embed(
            "✅ Moderation Log Channel Set",
            f"Moderation log channel set to {channel.mention}"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='members')
    @is_staff()
    async def set_member_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the member log channel"""
        self.bot.db.update_guild_config(ctx.guild.id, {"member_log_channel": str(channel.id)})
        
        embed = create_success_embed(
            "✅ Member Log Channel Set",
            f"Member log channel set to {channel.mention}"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='messages')
    @is_staff()
    async def set_message_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the message log channel"""
        self.bot.db.update_guild_config(ctx.guild.id, {"message_log_channel": str(channel.id)})
        
        embed = create_success_embed(
            "✅ Message Log Channel Set",
            f"Message log channel set to {channel.mention}"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='voice')
    @is_staff()
    async def set_voice_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the voice log channel"""
        self.bot.db.update_guild_config(ctx.guild.id, {"voice_log_channel": str(channel.id)})
        
        embed = create_success_embed(
            "✅ Voice Log Channel Set",
            f"Voice log channel set to {channel.mention}"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='server')
    @is_staff()
    async def set_server_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the server log channel"""
        self.bot.db.update_guild_config(ctx.guild.id, {"server_log_channel": str(channel.id)})
        
        embed = create_success_embed(
            "✅ Server Log Channel Set",
            f"Server log channel set to {channel.mention}"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='disable')
    @is_staff()
    async def disable_logging(self, ctx, log_type):
        """Disable a specific logging type"""
        valid_types = ["moderation", "members", "messages", "voice", "server", "all"]
        
        if log_type.lower() not in valid_types:
            embed = create_error_embed(
                "❌ Invalid Type",
                f"Valid types: {', '.join(valid_types)}"
            )
            await ctx.send(embed=embed)
            return
        
        if log_type.lower() == "all":
            config_update = {
                "log_channel": None,
                "mod_log_channel": None,
                "member_log_channel": None,
                "message_log_channel": None,
                "voice_log_channel": None,
                "server_log_channel": None
            }
        else:
            config_key = f"{log_type.lower()}_log_channel" if log_type != "moderation" else "mod_log_channel"
            config_update = {config_key: None}
        
        self.bot.db.update_guild_config(ctx.guild.id, config_update)
        
        embed = create_success_embed(
            "✅ Logging Disabled",
            f"Disabled logging for: **{log_type}**"
        )
        await ctx.send(embed=embed)
    
    @logging_group.command(name='status')
    @is_staff()
    async def logging_status(self, ctx):
        """View current logging configuration"""
        guild_config = self.bot.db.get_guild_config(ctx.guild.id)
        
        embed = create_embed(
            "📊 Logging Configuration",
            ""
        )
        
        log_types = [
            ("General", "log_channel"),
            ("Moderation", "mod_log_channel"),
            ("Members", "member_log_channel"),
            ("Messages", "message_log_channel"),
            ("Voice", "voice_log_channel"),
            ("Server", "server_log_channel")
        ]
        
        for log_name, config_key in log_types:
            channel_id = guild_config.get(config_key)
            if channel_id:
                channel = ctx.guild.get_channel(int(channel_id))
                status = channel.mention if channel else "❌ Channel not found"
            else:
                status = "❌ Not configured"
            
            embed.add_field(
                name=f"{log_name} Logs",
                value=status,
                inline=True
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
