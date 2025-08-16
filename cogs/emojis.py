
import discord
from discord.ext import commands
import json
import os
import asyncio
import aiohttp
from utils.helpers import create_embed, create_success_embed, create_error_embed, create_warning_embed, is_staff
from config.settings import BOT_CONFIG

class EmojiManager(commands.Cog):
    """Animated emoji support and management system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.emoji_data_file = 'data/emojis.json'
        self.emoji_data = self.load_emoji_data()
    
    def load_emoji_data(self):
        """Load emoji data from file"""
        if os.path.exists(self.emoji_data_file):
            with open(self.emoji_data_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_emoji_data(self):
        """Save emoji data to file"""
        os.makedirs('data', exist_ok=True)
        with open(self.emoji_data_file, 'w') as f:
            json.dump(self.emoji_data, f, indent=2)
    
    @commands.group(name='emoji', aliases=['emote'], invoke_without_command=True)
    async def emoji_group(self, ctx):
        """Emoji management commands"""
        embed = create_embed(
            "🎭 Emoji Commands",
            f"`{ctx.prefix}emoji add <name> <url/attachment>` - Add emoji from URL or file\n"
            f"`{ctx.prefix}emoji remove <name>` - Remove an emoji\n"
            f"`{ctx.prefix}emoji list [page]` - List server emojis\n"
            f"`{ctx.prefix}emoji info <emoji>` - Get emoji information\n"
            f"`{ctx.prefix}emoji steal <emoji> [name]` - Steal emoji from message\n"
            f"`{ctx.prefix}emoji rename <old_name> <new_name>` - Rename emoji\n"
            f"`{ctx.prefix}emoji search <query>` - Search emojis by name\n"
            f"`{ctx.prefix}emoji stats` - Server emoji statistics"
        )
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='add')
    @commands.has_permissions(manage_emojis=True)
    async def add_emoji(self, ctx, name: str, url: str = None):
        """Add an emoji to the server"""
        # Check if guild has emoji slots
        if len(ctx.guild.emojis) >= ctx.guild.emoji_limit:
            embed = create_error_embed(
                "❌ Emoji Limit Reached",
                f"This server has reached its emoji limit ({ctx.guild.emoji_limit})"
            )
            await ctx.send(embed=embed)
            return
        
        # Validate emoji name
        if not name.isalnum() or len(name) < 2 or len(name) > 32:
            embed = create_error_embed(
                "❌ Invalid Name",
                "Emoji name must be 2-32 alphanumeric characters"
            )
            await ctx.send(embed=embed)
            return
        
        # Check if emoji name already exists
        if discord.utils.get(ctx.guild.emojis, name=name):
            embed = create_error_embed(
                "❌ Name Taken",
                f"An emoji with the name '{name}' already exists"
            )
            await ctx.send(embed=embed)
            return
        
        # Get image data
        image_data = None
        
        if ctx.message.attachments:
            # From attachment
            attachment = ctx.message.attachments[0]
            if not attachment.content_type.startswith('image/'):
                embed = create_error_embed(
                    "❌ Invalid File",
                    "Please provide a valid image file (PNG, JPG, GIF)"
                )
                await ctx.send(embed=embed)
                return
            
            if attachment.size > 256000:  # 256 KB limit
                embed = create_error_embed(
                    "❌ File Too Large",
                    "Image must be smaller than 256 KB"
                )
                await ctx.send(embed=embed)
                return
            
            image_data = await attachment.read()
        
        elif url:
            # From URL
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            embed = create_error_embed(
                                "❌ Invalid URL",
                                "Could not download image from URL"
                            )
                            await ctx.send(embed=embed)
                            return
                        
                        if int(resp.headers.get('content-length', 0)) > 256000:
                            embed = create_error_embed(
                                "❌ File Too Large",
                                "Image must be smaller than 256 KB"
                            )
                            await ctx.send(embed=embed)
                            return
                        
                        image_data = await resp.read()
            except Exception as e:
                embed = create_error_embed(
                    "❌ Download Failed",
                    "Failed to download image from URL"
                )
                await ctx.send(embed=embed)
                return
        
        else:
            embed = create_error_embed(
                "❌ No Image",
                "Please provide an image URL or attach an image file"
            )
            await ctx.send(embed=embed)
            return
        
        # Create emoji
        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
            
            # Store emoji data
            guild_id = str(ctx.guild.id)
            if guild_id not in self.emoji_data:
                self.emoji_data[guild_id] = {}
            
            self.emoji_data[guild_id][str(emoji.id)] = {
                'name': name,
                'creator': ctx.author.id,
                'created_at': discord.utils.utcnow().isoformat(),
                'animated': emoji.animated,
                'uses': 0
            }
            self.save_emoji_data()
            
            embed = create_success_embed(
                "✅ Emoji Added",
                f"Successfully added {'animated' if emoji.animated else 'static'} emoji: {emoji}\n"
                f"**Name:** {name}\n"
                f"**ID:** {emoji.id}"
            )
            embed.set_thumbnail(url=emoji.url)
            
        except discord.HTTPException as e:
            embed = create_error_embed(
                "❌ Creation Failed",
                f"Failed to create emoji: {str(e)}"
            )
        
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='remove', aliases=['delete'])
    @commands.has_permissions(manage_emojis=True)
    async def remove_emoji(self, ctx, emoji: discord.Emoji):
        """Remove an emoji from the server"""
        if emoji.guild != ctx.guild:
            embed = create_error_embed(
                "❌ Invalid Emoji",
                "This emoji is not from this server"
            )
            await ctx.send(embed=embed)
            return
        
        try:
            emoji_name = emoji.name
            emoji_id = emoji.id
            
            await emoji.delete()
            
            # Remove from data
            guild_id = str(ctx.guild.id)
            if guild_id in self.emoji_data and str(emoji_id) in self.emoji_data[guild_id]:
                del self.emoji_data[guild_id][str(emoji_id)]
                self.save_emoji_data()
            
            embed = create_success_embed(
                "✅ Emoji Removed",
                f"Successfully removed emoji: **{emoji_name}**"
            )
            
        except discord.HTTPException as e:
            embed = create_error_embed(
                "❌ Removal Failed",
                f"Failed to remove emoji: {str(e)}"
            )
        
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='list')
    async def list_emojis(self, ctx, page: int = 1):
        """List server emojis with pagination"""
        emojis = ctx.guild.emojis
        if not emojis:
            embed = create_embed(
                "🎭 Server Emojis",
                "This server has no custom emojis."
            )
            await ctx.send(embed=embed)
            return
        
        # Separate animated and static emojis
        animated_emojis = [e for e in emojis if e.animated]
        static_emojis = [e for e in emojis if not e.animated]
        
        # Pagination
        per_page = 20
        total_pages = max(1, (len(emojis) + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        
        start = (page - 1) * per_page
        end = start + per_page
        page_emojis = emojis[start:end]
        
        embed = create_embed(
            f"🎭 Server Emojis - Page {page}/{total_pages}",
            f"**Total:** {len(emojis)}/{ctx.guild.emoji_limit}\n"
            f"**Animated:** {len(animated_emojis)} | **Static:** {len(static_emojis)}"
        )
        
        # Group emojis for display
        emoji_text = ""
        for i, emoji in enumerate(page_emojis):
            if i % 5 == 0 and i > 0:
                emoji_text += "\n"
            emoji_type = "🎬" if emoji.animated else "🖼️"
            emoji_text += f"{emoji_type} {emoji} "
        
        if emoji_text:
            embed.add_field(
                name="Emojis",
                value=emoji_text,
                inline=False
            )
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Use {ctx.prefix}emoji list <page>")
        
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='info')
    async def emoji_info(self, ctx, emoji: discord.Emoji):
        """Get detailed information about an emoji"""
        if emoji.guild != ctx.guild:
            embed = create_error_embed(
                "❌ Invalid Emoji",
                "This emoji is not from this server"
            )
            await ctx.send(embed=embed)
            return
        
        # Get stored data
        guild_id = str(ctx.guild.id)
        emoji_data = {}
        if guild_id in self.emoji_data and str(emoji.id) in self.emoji_data[guild_id]:
            emoji_data = self.emoji_data[guild_id][str(emoji.id)]
        
        embed = create_embed(
            f"🎭 Emoji Info: {emoji.name}",
            f"**Name:** {emoji.name}\n"
            f"**ID:** {emoji.id}\n"
            f"**Type:** {'Animated' if emoji.animated else 'Static'}\n"
            f"**Created:** {emoji.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            f"**URL:** [Click here]({emoji.url})"
        )
        
        if emoji_data:
            creator = self.bot.get_user(emoji_data.get('creator'))
            creator_name = creator.display_name if creator else "Unknown"
            embed.add_field(
                name="Additional Info",
                value=f"**Added by:** {creator_name}\n"
                      f"**Uses:** {emoji_data.get('uses', 0)}",
                inline=False
            )
        
        embed.set_thumbnail(url=emoji.url)
        
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='steal')
    @commands.has_permissions(manage_emojis=True)
    async def steal_emoji(self, ctx, emoji: discord.PartialEmoji, name: str = None):
        """Steal an emoji from another server"""
        if not name:
            name = emoji.name
        
        # Validate name
        if not name.isalnum() or len(name) < 2 or len(name) > 32:
            embed = create_error_embed(
                "❌ Invalid Name",
                "Emoji name must be 2-32 alphanumeric characters"
            )
            await ctx.send(embed=embed)
            return
        
        # Check emoji limit
        if len(ctx.guild.emojis) >= ctx.guild.emoji_limit:
            embed = create_error_embed(
                "❌ Emoji Limit Reached",
                f"This server has reached its emoji limit ({ctx.guild.emoji_limit})"
            )
            await ctx.send(embed=embed)
            return
        
        # Check if name exists
        if discord.utils.get(ctx.guild.emojis, name=name):
            embed = create_error_embed(
                "❌ Name Taken",
                f"An emoji with the name '{name}' already exists"
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Download emoji
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji.url) as resp:
                    if resp.status != 200:
                        embed = create_error_embed(
                            "❌ Download Failed",
                            "Could not download the emoji"
                        )
                        await ctx.send(embed=embed)
                        return
                    
                    image_data = await resp.read()
            
            # Create emoji
            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
            
            # Store data
            guild_id = str(ctx.guild.id)
            if guild_id not in self.emoji_data:
                self.emoji_data[guild_id] = {}
            
            self.emoji_data[guild_id][str(new_emoji.id)] = {
                'name': name,
                'creator': ctx.author.id,
                'created_at': discord.utils.utcnow().isoformat(),
                'animated': new_emoji.animated,
                'uses': 0,
                'stolen_from': str(emoji.id)
            }
            self.save_emoji_data()
            
            embed = create_success_embed(
                "✅ Emoji Stolen",
                f"Successfully stole {'animated' if new_emoji.animated else 'static'} emoji: {new_emoji}\n"
                f"**Name:** {name}"
            )
            embed.set_thumbnail(url=new_emoji.url)
            
        except discord.HTTPException as e:
            embed = create_error_embed(
                "❌ Steal Failed",
                f"Failed to steal emoji: {str(e)}"
            )
        
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='rename')
    @commands.has_permissions(manage_emojis=True)
    async def rename_emoji(self, ctx, emoji: discord.Emoji, new_name: str):
        """Rename an existing emoji"""
        if emoji.guild != ctx.guild:
            embed = create_error_embed(
                "❌ Invalid Emoji",
                "This emoji is not from this server"
            )
            await ctx.send(embed=embed)
            return
        
        # Validate new name
        if not new_name.isalnum() or len(new_name) < 2 or len(new_name) > 32:
            embed = create_error_embed(
                "❌ Invalid Name",
                "Emoji name must be 2-32 alphanumeric characters"
            )
            await ctx.send(embed=embed)
            return
        
        # Check if new name exists
        if discord.utils.get(ctx.guild.emojis, name=new_name):
            embed = create_error_embed(
                "❌ Name Taken",
                f"An emoji with the name '{new_name}' already exists"
            )
            await ctx.send(embed=embed)
            return
        
        try:
            old_name = emoji.name
            await emoji.edit(name=new_name)
            
            # Update data
            guild_id = str(ctx.guild.id)
            if guild_id in self.emoji_data and str(emoji.id) in self.emoji_data[guild_id]:
                self.emoji_data[guild_id][str(emoji.id)]['name'] = new_name
                self.save_emoji_data()
            
            embed = create_success_embed(
                "✅ Emoji Renamed",
                f"Successfully renamed emoji from **{old_name}** to **{new_name}**\n{emoji}"
            )
            
        except discord.HTTPException as e:
            embed = create_error_embed(
                "❌ Rename Failed",
                f"Failed to rename emoji: {str(e)}"
            )
        
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='search')
    async def search_emojis(self, ctx, *, query: str):
        """Search emojis by name"""
        query = query.lower()
        matching_emojis = [e for e in ctx.guild.emojis if query in e.name.lower()]
        
        if not matching_emojis:
            embed = create_embed(
                "🔍 Search Results",
                f"No emojis found matching '{query}'"
            )
            await ctx.send(embed=embed)
            return
        
        embed = create_embed(
            f"🔍 Search Results for '{query}'",
            f"Found {len(matching_emojis)} emojis:"
        )
        
        # Display results
        emoji_text = ""
        for i, emoji in enumerate(matching_emojis[:25]):  # Limit to 25
            if i % 5 == 0 and i > 0:
                emoji_text += "\n"
            emoji_type = "🎬" if emoji.animated else "🖼️"
            emoji_text += f"{emoji_type} {emoji} "
        
        if emoji_text:
            embed.add_field(
                name="Results",
                value=emoji_text,
                inline=False
            )
        
        if len(matching_emojis) > 25:
            embed.set_footer(text=f"Showing first 25 of {len(matching_emojis)} results")
        
        await ctx.send(embed=embed)
    
    @emoji_group.command(name='stats')
    async def emoji_stats(self, ctx):
        """Show emoji statistics for the server"""
        emojis = ctx.guild.emojis
        animated_emojis = [e for e in emojis if e.animated]
        static_emojis = [e for e in emojis if not e.animated]
        
        # Get usage data
        guild_id = str(ctx.guild.id)
        total_uses = 0
        most_used = None
        
        if guild_id in self.emoji_data:
            uses_data = [(emoji_id, data['uses'], data['name']) 
                        for emoji_id, data in self.emoji_data[guild_id].items()]
            if uses_data:
                total_uses = sum(uses for _, uses, _ in uses_data)
                most_used = max(uses_data, key=lambda x: x[1])
        
        embed = create_embed(
            "📊 Emoji Statistics",
            f"**Total Emojis:** {len(emojis)}/{ctx.guild.emoji_limit}\n"
            f"**Animated:** {len(animated_emojis)}\n"
            f"**Static:** {len(static_emojis)}\n"
            f"**Total Uses:** {total_uses}\n"
        )
        
        if most_used and most_used[1] > 0:
            most_used_emoji = discord.utils.get(emojis, id=int(most_used[0]))
            if most_used_emoji:
                embed.add_field(
                    name="Most Used",
                    value=f"{most_used_emoji} **{most_used[2]}** ({most_used[1]} uses)",
                    inline=False
                )
        
        # Calculate slots remaining
        remaining_total = ctx.guild.emoji_limit - len(emojis)
        embed.add_field(
            name="Available Slots",
            value=f"**{remaining_total}** total slots remaining",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track emoji usage"""
        if message.author.bot or not message.guild:
            return
        
        guild_id = str(message.guild.id)
        if guild_id not in self.emoji_data:
            return
        
        # Find custom emojis in message
        import re
        emoji_pattern = re.compile(r'<a?:(\w+):(\d+)>')
        matches = emoji_pattern.findall(message.content)
        
        for name, emoji_id in matches:
            if emoji_id in self.emoji_data[guild_id]:
                self.emoji_data[guild_id][emoji_id]['uses'] += 1
        
        # Save if any emojis were used
        if matches:
            self.save_emoji_data()

async def setup(bot):
    await bot.add_cog(EmojiManager(bot))
