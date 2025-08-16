import discord
from discord.ext import commands
import json
import os
import asyncio
from utils.helpers import create_embed, create_success_embed, create_error_embed, create_warning_embed, is_staff
from config.settings import BOT_CONFIG

class Welcome(commands.Cog):
    """Welcome and auto role system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.welcome_data = self.load_welcome_data()
    
    def load_welcome_data(self):
        """Load welcome system data"""
        try:
            if os.path.exists('data/welcome.json'):
                with open('data/welcome.json', 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def save_welcome_data(self):
        """Save welcome system data"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/welcome.json', 'w') as f:
                json.dump(self.welcome_data, f, indent=2)
        except Exception as e:
            print(f"Error saving welcome data: {e}")
    
    def get_guild_config(self, guild_id):
        """Get welcome configuration for a guild"""
        guild_id = str(guild_id)
        if guild_id not in self.welcome_data:
            self.welcome_data[guild_id] = {
                'welcome_enabled': False,
                'welcome_channel': None,
                'welcome_message': 'Welcome to {server}, {user}! 🎉',
                'welcome_embed': True,
                'welcome_gif': None,
                'auto_role_enabled': False,
                'auto_roles': [],
                'leave_enabled': False,
                'leave_channel': None,
                'leave_message': '{user} has left {server}. Goodbye! 👋',
                'leave_embed': True,
                'dm_welcome': False,
                'dm_message': 'Welcome to {server}! We hope you enjoy your stay.'
            }
            self.save_welcome_data()
        return self.welcome_data[guild_id]
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle member join events"""
        config = self.get_guild_config(member.guild.id)
        
        # Auto role assignment
        if config['auto_role_enabled'] and config['auto_roles']:
            await self.assign_auto_roles(member, config)
        
        # Welcome message
        if config['welcome_enabled']:
            await self.send_welcome_message(member, config)
        
        # DM welcome
        if config['dm_welcome']:
            await self.send_dm_welcome(member, config)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle member leave events"""
        config = self.get_guild_config(member.guild.id)
        
        if config['leave_enabled'] and config['leave_channel']:
            await self.send_leave_message(member, config)
    
    async def assign_auto_roles(self, member, config):
        """Assign auto roles to new members"""
        try:
            roles_to_add = []
            for role_id in config['auto_roles']:
                role = member.guild.get_role(int(role_id))
                if role and role < member.guild.me.top_role:
                    roles_to_add.append(role)
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Auto role assignment")
        except Exception as e:
            print(f"Error assigning auto roles: {e}")
    
    async def send_welcome_message(self, member, config):
        """Send welcome message to channel"""
        try:
            channel = self.bot.get_channel(int(config['welcome_channel']))
            if not channel:
                return
            
            message = self.format_message(config['welcome_message'], member)
            
            if config['welcome_embed']:
                embed = create_embed(
                    "Welcome! 🎉",
                    message
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                
                # Add GIF image if configured
                if config.get('welcome_gif'):
                    embed.set_image(url=config['welcome_gif'])
                
                embed.add_field(
                    name="Member Count",
                    value=f"{member.guild.member_count}",
                    inline=True
                )
                embed.add_field(
                    name="Account Created",
                    value=f"<t:{int(member.created_at.timestamp())}:R>",
                    inline=True
                )
                await channel.send(embed=embed)
            else:
                await channel.send(message)
        except Exception as e:
            print(f"Error sending welcome message: {e}")
    
    async def send_leave_message(self, member, config):
        """Send leave message to channel"""
        try:
            channel = self.bot.get_channel(int(config['leave_channel']))
            if not channel:
                return
            
            message = self.format_message(config['leave_message'], member)
            
            if config['leave_embed']:
                embed = create_embed(
                    "Goodbye 👋",
                    message
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(
                    name="Member Count",
                    value=f"{member.guild.member_count}",
                    inline=True
                )
                await channel.send(embed=embed)
            else:
                await channel.send(message)
        except Exception as e:
            print(f"Error sending leave message: {e}")
    
    async def send_dm_welcome(self, member, config):
        """Send welcome DM to new member"""
        try:
            message = self.format_message(config['dm_message'], member)
            embed = create_embed(
                f"Welcome to {member.guild.name}!",
                message
            )
            embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
            await member.send(embed=embed)
        except Exception as e:
            print(f"Error sending DM welcome: {e}")
    
    def format_message(self, message, member):
        """Format welcome/leave message with placeholders"""
        formatted = message.replace('{user}', member.mention)\
                          .replace('{username}', member.name)\
                          .replace('{server}', member.guild.name)\
                          .replace('{member_count}', str(member.guild.member_count))
        
        # Convert emoji placeholders to actual emojis
        formatted = self.format_emoji_placeholders(formatted, member.guild)
        return formatted
    
    def format_emoji_placeholders(self, message, guild):
        """Convert emoji placeholders like {emoji:name} to actual Discord emojis"""
        import re
        
        # Pattern to match {emoji:name} or {emote:name}
        pattern = r'\{(emoji|emote):(\w+)\}'
        
        def replace_emoji(match):
            emoji_name = match.group(2)
            
            # Find emoji by name in the guild
            for emoji in guild.emojis:
                if emoji.name.lower() == emoji_name.lower():
                    return str(emoji)
            
            # If not found, return the original placeholder
            return match.group(0)
        
        return re.sub(pattern, replace_emoji, message)
    
    @commands.group(name='welcome', invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def welcome_group(self, ctx):
        """Welcome system commands"""
        embed = create_embed(
            "🎉 Welcome System Commands",
            f"`{ctx.prefix}welcome setup` - Interactive setup\n"
            f"`{ctx.prefix}welcome channel <channel>` - Set welcome channel\n"
            f"`{ctx.prefix}welcome message <message>` - Set welcome message\n"
            f"`{ctx.prefix}welcome gif <url>` - Set welcome GIF\n"
            f"`{ctx.prefix}welcome toggle` - Toggle welcome messages\n"
            f"`{ctx.prefix}welcome embed` - Toggle embed mode\n"
            f"`{ctx.prefix}welcome dm` - Toggle DM welcome\n"
            f"`{ctx.prefix}welcome test` - Test welcome message\n"
            f"`{ctx.prefix}welcome config` - View configuration"
        )
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='setup')
    async def welcome_setup(self, ctx):
        """Interactive welcome system setup"""
        config = self.get_guild_config(ctx.guild.id)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        # Welcome channel setup
        embed = create_embed(
            "🎉 Welcome Setup - Step 1/4",
            "Please mention the channel where welcome messages should be sent.\n"
            "Type `skip` to skip this step."
        )
        await ctx.send(embed=embed)
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            if response.content.lower() != 'skip':
                if response.channel_mentions:
                    config['welcome_channel'] = response.channel_mentions[0].id
                    config['welcome_enabled'] = True
                    embed = create_success_embed(
                        "✅ Channel Set",
                        f"Welcome channel set to {response.channel_mentions[0].mention}"
                    )
                    await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send("Setup cancelled due to timeout.")
            return
        
        # Welcome message setup
        embed = create_embed(
            "🎉 Welcome Setup - Step 2/4",
            "Please enter your welcome message.\n"
            "Available placeholders:\n"
            "• `{user}` - Mention the user\n"
            "• `{username}` - User's name\n"
            "• `{server}` - Server name\n"
            "• `{member_count}` - Total members\n"
            "• `{emoji:name}` - Custom server emoji by name\n"
            "Type `skip` to use default message."
        )
        await ctx.send(embed=embed)
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            if response.content.lower() != 'skip':
                config['welcome_message'] = response.content
                embed = create_success_embed(
                    "✅ Message Set",
                    f"Welcome message updated"
                )
                await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send("Setup cancelled due to timeout.")
            return
        
        # Auto role setup
        embed = create_embed(
            "🎉 Welcome Setup - Step 3/4",
            "Please mention roles to automatically assign to new members.\n"
            "You can mention multiple roles separated by spaces.\n"
            "Type `skip` to skip auto roles."
        )
        await ctx.send(embed=embed)
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            if response.content.lower() != 'skip':
                if response.role_mentions:
                    config['auto_roles'] = [role.id for role in response.role_mentions]
                    config['auto_role_enabled'] = True
                    role_names = [role.name for role in response.role_mentions]
                    embed = create_success_embed(
                        "✅ Auto Roles Set",
                        f"Auto roles: {', '.join(role_names)}"
                    )
                    await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send("Setup cancelled due to timeout.")
            return
        
        # GIF setup
        embed = create_embed(
            "🎉 Welcome Setup - Step 4/5",
            "Would you like to add a GIF image to welcome messages?\n"
            "Please provide a direct link to a GIF/image, or type `skip`.\n"
            "Example: https://example.com/welcome.gif"
        )
        await ctx.send(embed=embed)
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            if response.content.lower() != 'skip':
                gif_url = response.content.strip()
                if gif_url.startswith(('http://', 'https://')):
                    config['welcome_gif'] = gif_url
                    embed = create_success_embed(
                        "✅ Welcome GIF Set",
                        "GIF will be displayed in welcome messages"
                    )
                    embed.set_image(url=gif_url)
                    await ctx.send(embed=embed)
                else:
                    embed = create_warning_embed(
                        "⚠️ Invalid URL",
                        "GIF URL was not valid, skipping this step"
                    )
                    await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send("Setup cancelled due to timeout.")
            return
        
        # DM welcome setup
        embed = create_embed(
            "🎉 Welcome Setup - Step 5/5",
            "Should the bot send a welcome DM to new members?\n"
            "Type `yes` to enable or `no` to disable."
        )
        await ctx.send(embed=embed)
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            if response.content.lower() in ['yes', 'y', 'enable']:
                config['dm_welcome'] = True
                embed = create_success_embed(
                    "✅ DM Welcome Enabled",
                    "New members will receive a welcome DM"
                )
                await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            await ctx.send("Setup cancelled due to timeout.")
            return
        
        self.save_welcome_data()
        
        final_embed = create_success_embed(
            "🎉 Welcome Setup Complete!",
            "Your welcome system has been configured successfully.\n"
            f"Use `{ctx.prefix}welcome test` to test the configuration."
        )
        await ctx.send(embed=final_embed)
    
    @welcome_group.command(name='channel')
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel):
        """Set the welcome channel"""
        
        config = self.get_guild_config(ctx.guild.id)
        config['welcome_channel'] = channel.id
        config['welcome_enabled'] = True
        self.save_welcome_data()
        
        embed = create_success_embed(
            "✅ Welcome Channel Set",
            f"Welcome messages will be sent to {channel.mention}"
        )
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='message')
    async def set_welcome_message(self, ctx, *, message):
        """Set the welcome message
        
        Available placeholders:
        {user} - Mention the user
        {username} - User's name  
        {server} - Server name
        {member_count} - Total members
        {emoji:name} - Custom server emoji by name
        """
        config = self.get_guild_config(ctx.guild.id)
        config['welcome_message'] = message
        self.save_welcome_data()
        
        # Show preview with formatted message
        preview = self.format_message(message, ctx.author)
        
        embed = create_success_embed(
            "✅ Welcome Message Set",
            f"Welcome message updated!\n\n**Preview:**\n{preview}"
        )
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='gif')
    async def set_welcome_gif(self, ctx, *, gif_url=None):
        """Set the welcome GIF image"""
        config = self.get_guild_config(ctx.guild.id)
        
        if gif_url is None:
            # Remove GIF
            config['welcome_gif'] = None
            self.save_welcome_data()
            embed = create_success_embed(
                "✅ GIF Removed",
                "Welcome GIF has been removed from welcome messages"
            )
            await ctx.send(embed=embed)
            return
        
        # Validate URL format
        if not gif_url.startswith(('http://', 'https://')):
            embed = create_error_embed(
                "❌ Invalid URL",
                "Please provide a valid URL starting with http:// or https://"
            )
            await ctx.send(embed=embed)
            return
        
        # Check if URL ends with common image formats
        valid_formats = ('.gif', '.png', '.jpg', '.jpeg', '.webp')
        if not any(gif_url.lower().endswith(fmt) for fmt in valid_formats):
            embed = create_warning_embed(
                "⚠️ URL Warning",
                "The URL doesn't end with a common image format. It may not display correctly."
            )
            await ctx.send(embed=embed)
        
        config['welcome_gif'] = gif_url
        self.save_welcome_data()
        
        # Show preview
        embed = create_success_embed(
            "✅ Welcome GIF Set",
            f"Welcome GIF has been set successfully!"
        )
        embed.set_image(url=gif_url)
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='toggle')
    async def toggle_welcome(self, ctx):
        """Toggle welcome messages on/off"""
        config = self.get_guild_config(ctx.guild.id)
        config['welcome_enabled'] = not config['welcome_enabled']
        self.save_welcome_data()
        
        status = "enabled" if config['welcome_enabled'] else "disabled"
        embed = create_success_embed(
            f"✅ Welcome {status.title()}",
            f"Welcome messages are now {status}"
        )
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='test')
    async def test_welcome(self, ctx):
        """Test the welcome message"""
        config = self.get_guild_config(ctx.guild.id)
        
        if not config['welcome_enabled'] or not config['welcome_channel']:
            embed = create_error_embed(
                "❌ Welcome Not Configured",
                f"Please set up welcome messages first using `{ctx.prefix}welcome setup`"
            )
            await ctx.send(embed=embed)
            return
        
        # Simulate member join
        await self.send_welcome_message(ctx.author, config)
        
        embed = create_success_embed(
            "✅ Test Sent",
            "Welcome message has been sent to the configured channel"
        )
        await ctx.send(embed=embed)
    
    @commands.group(name='autorole', invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def autorole_group(self, ctx):
        """Auto role system commands"""
        embed = create_embed(
            "🎭 Auto Role Commands",
            f"`{ctx.prefix}autorole add <role>` - Add an auto role\n"
            f"`{ctx.prefix}autorole remove <role>` - Remove an auto role\n"
            f"`{ctx.prefix}autorole list` - List current auto roles\n"
            f"`{ctx.prefix}autorole toggle` - Toggle auto role system\n"
            f"`{ctx.prefix}autorole clear` - Clear all auto roles"
        )
        await ctx.send(embed=embed)
    
    @autorole_group.command(name='add')
    async def add_autorole(self, ctx, role: discord.Role):
        """Add a role to auto assign to new members"""
        if role >= ctx.guild.me.top_role:
            embed = create_error_embed(
                "❌ Role Too High",
                "I cannot assign roles higher than my highest role"
            )
            await ctx.send(embed=embed)
            return
        
        config = self.get_guild_config(ctx.guild.id)
        if role.id not in config['auto_roles']:
            config['auto_roles'].append(role.id)
            config['auto_role_enabled'] = True
            self.save_welcome_data()
            
            embed = create_success_embed(
                "✅ Auto Role Added",
                f"{role.mention} will now be assigned to new members"
            )
            await ctx.send(embed=embed)
        else:
            embed = create_warning_embed(
                "⚠️ Role Already Added",
                f"{role.mention} is already in the auto role list"
            )
            await ctx.send(embed=embed)
    
    @autorole_group.command(name='remove')
    async def remove_autorole(self, ctx, role: discord.Role):
        """Remove a role from auto assignment"""
        config = self.get_guild_config(ctx.guild.id)
        if role.id in config['auto_roles']:
            config['auto_roles'].remove(role.id)
            self.save_welcome_data()
            
            embed = create_success_embed(
                "✅ Auto Role Removed",
                f"{role.mention} will no longer be assigned to new members"
            )
            await ctx.send(embed=embed)
        else:
            embed = create_error_embed(
                "❌ Role Not Found",
                f"{role.mention} is not in the auto role list"
            )
            await ctx.send(embed=embed)
    
    @autorole_group.command(name='list')
    async def list_autoroles(self, ctx):
        """List all auto roles"""
        config = self.get_guild_config(ctx.guild.id)
        
        if not config['auto_roles']:
            embed = create_warning_embed(
                "⚠️ No Auto Roles",
                "No auto roles have been configured"
            )
            await ctx.send(embed=embed)
            return
        
        roles = []
        for role_id in config['auto_roles']:
            role = ctx.guild.get_role(role_id)
            if role:
                roles.append(role.mention)
        
        embed = create_embed(
            "🎭 Auto Roles",
            "\n".join(roles) if roles else "No valid roles found"
        )
        embed.add_field(
            name="Status",
            value="Enabled" if config['auto_role_enabled'] else "Disabled",
            inline=True
        )
        await ctx.send(embed=embed)
    
    @autorole_group.command(name='toggle')
    async def toggle_autorole(self, ctx):
        """Toggle auto role system on/off"""
        config = self.get_guild_config(ctx.guild.id)
        config['auto_role_enabled'] = not config['auto_role_enabled']
        self.save_welcome_data()
        
        status = "enabled" if config['auto_role_enabled'] else "disabled"
        embed = create_success_embed(
            f"✅ Auto Role {status.title()}",
            f"Auto role system is now {status}"
        )
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='config')
    async def welcome_config(self, ctx):
        """View current welcome configuration"""
        config = self.get_guild_config(ctx.guild.id)
        
        welcome_channel = "Not set"
        if config['welcome_channel']:
            channel = self.bot.get_channel(config['welcome_channel'])
            welcome_channel = channel.mention if channel else "Invalid channel"
        
        auto_roles = "None"
        if config['auto_roles']:
            roles = []
            for role_id in config['auto_roles']:
                role = ctx.guild.get_role(role_id)
                if role:
                    roles.append(role.name)
            auto_roles = ", ".join(roles) if roles else "None"
        
        welcome_gif = "None"
        if config.get('welcome_gif'):
            welcome_gif = "Set"
        
        embed = create_embed(
            "🎉 Welcome Configuration",
            f"**Welcome Messages:** {'Enabled' if config['welcome_enabled'] else 'Disabled'}\n"
            f"**Welcome Channel:** {welcome_channel}\n"
            f"**Welcome Message:** {config['welcome_message']}\n"
            f"**Welcome GIF:** {welcome_gif}\n"
            f"**Embed Mode:** {'Yes' if config['welcome_embed'] else 'No'}\n"
            f"**DM Welcome:** {'Yes' if config['dm_welcome'] else 'No'}\n\n"
            f"**Auto Roles:** {'Enabled' if config['auto_role_enabled'] else 'Disabled'}\n"
            f"**Roles:** {auto_roles}"
        )
        
        # Show GIF preview if set
        if config.get('welcome_gif'):
            embed.set_image(url=config['welcome_gif'])
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='embed')
    async def toggle_embed(self, ctx):
        """Toggle embed mode for welcome messages"""
        config = self.get_guild_config(ctx.guild.id)
        config['welcome_embed'] = not config['welcome_embed']
        self.save_welcome_data()
        
        mode = "embed" if config['welcome_embed'] else "plain text"
        embed = create_success_embed(
            f"✅ Embed Mode {'Enabled' if config['welcome_embed'] else 'Disabled'}",
            f"Welcome messages will now be sent as {mode}"
        )
        await ctx.send(embed=embed)
    
    @welcome_group.command(name='dm')
    async def toggle_dm(self, ctx):
        """Toggle DM welcome messages"""
        config = self.get_guild_config(ctx.guild.id)
        config['dm_welcome'] = not config['dm_welcome']
        self.save_welcome_data()
        
        status = "enabled" if config['dm_welcome'] else "disabled"
        embed = create_success_embed(
            f"✅ DM Welcome {status.title()}",
            f"DM welcome messages are now {status}"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))