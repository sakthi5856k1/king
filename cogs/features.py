import discord
from discord.ext import commands
import asyncio
import json
import random
from datetime import datetime, timedelta
from utils.helpers import create_embed, create_success_embed, create_error_embed, create_warning_embed, is_staff
from config.settings import BOT_CONFIG

class LatestFeatures(commands.Cog):
    """Latest features and utilities for the Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.polls = {}  # Store active polls
        self.reminders = {}  # Store reminders
        self.giveaways = {}  # Store active giveaways
    
    @commands.group(name='poll', invoke_without_command=True)
    async def poll_group(self, ctx):
        """Poll system commands"""
        embed = create_embed(
            "📊 Poll Commands",
            f"`{ctx.prefix}poll create <question> | <option1> | <option2> | ...` - Create a poll\n"
            f"`{ctx.prefix}poll end <poll_id>` - End a poll early\n"
            f"`{ctx.prefix}poll list` - List active polls\n"
            f"`{ctx.prefix}poll results <poll_id>` - View poll results"
        )
        await ctx.send(embed=embed)
    
    @poll_group.command(name='create')
    async def create_poll(self, ctx, *, poll_data):
        """Create a poll with multiple options"""
        if '|' not in poll_data:
            embed = create_error_embed(
                "❌ Invalid Format",
                f"Use: `{ctx.prefix}poll create <question> | <option1> | <option2> | ...`"
            )
            await ctx.send(embed=embed)
            return
        
        parts = [part.strip() for part in poll_data.split('|')]
        if len(parts) < 3:
            embed = create_error_embed(
                "❌ Not Enough Options",
                "Polls need at least 2 options"
            )
            await ctx.send(embed=embed)
            return
        
        if len(parts) > 11:  # Question + 10 options max
            embed = create_error_embed(
                "❌ Too Many Options",
                "Maximum 10 poll options allowed"
            )
            await ctx.send(embed=embed)
            return
        
        question = parts[0]
        options = parts[1:]
        
        # Create poll embed
        embed = create_embed(
            f"📊 {question}",
            ""
        )
        
        # Add reaction emojis
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        description = ""
        for i, option in enumerate(options):
            description += f"{reactions[i]} {option}\n"
        
        embed.description = description
        embed.set_footer(text=f"Poll by {ctx.author} • React to vote!")
        
        message = await ctx.send(embed=embed)
        
        # Add reactions
        for i in range(len(options)):
            await message.add_reaction(reactions[i])
        
        # Store poll data
        poll_id = str(message.id)
        self.polls[poll_id] = {
            'question': question,
            'options': options,
            'creator': ctx.author.id,
            'channel': ctx.channel.id,
            'guild': ctx.guild.id,
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        }
        
        embed = create_success_embed(
            "✅ Poll Created",
            f"Poll created successfully! ID: `{poll_id}`"
        )
        await ctx.send(embed=embed)
    
    @poll_group.command(name='end')
    @is_staff()
    async def end_poll(self, ctx, poll_id: str):
        """End a poll and show results"""
        if poll_id not in self.polls:
            embed = create_error_embed("❌ Poll Not Found", "Invalid poll ID")
            await ctx.send(embed=embed)
            return
        
        poll = self.polls[poll_id]
        if not poll['active']:
            embed = create_error_embed("❌ Poll Already Ended", "This poll has already ended")
            await ctx.send(embed=embed)
            return
        
        # Get the original message
        try:
            channel = self.bot.get_channel(poll['channel'])
            message = await channel.fetch_message(int(poll_id))
        except:
            embed = create_error_embed("❌ Message Not Found", "Could not find the poll message")
            await ctx.send(embed=embed)
            return
        
        # Count votes
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        results = []
        total_votes = 0
        
        for i, option in enumerate(poll['options']):
            reaction = discord.utils.get(message.reactions, emoji=reactions[i])
            count = reaction.count - 1 if reaction else 0  # -1 for bot's reaction
            results.append((option, count))
            total_votes += count
        
        # Create results embed
        embed = create_embed(
            f"📊 Poll Results: {poll['question']}",
            f"**Total Votes:** {total_votes}"
        )
        
        if total_votes > 0:
            # Sort by votes
            results.sort(key=lambda x: x[1], reverse=True)
            
            for i, (option, votes) in enumerate(results):
                percentage = (votes / total_votes * 100) if total_votes > 0 else 0
                bar_length = int(percentage / 10)
                bar = '█' * bar_length + '░' * (10 - bar_length)
                
                embed.add_field(
                    name=f"{'🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else '📊'} {option}",
                    value=f"{bar} {votes} votes ({percentage:.1f}%)",
                    inline=False
                )
        else:
            current_desc = embed.description or ""
            embed.description = current_desc + "\n\nNo votes were cast."
        
        poll['active'] = False
        await ctx.send(embed=embed)
    
    @commands.command(name='remind', aliases=['reminder'])
    async def set_reminder(self, ctx, time, *, message):
        """Set a reminder (e.g., !remind 1h Take a break)"""
        from utils.helpers import parse_time
        
        duration = parse_time(time)
        if duration <= 0:
            embed = create_error_embed(
                "❌ Invalid Time",
                "Please provide a valid time (e.g., 1h, 30m, 2d)"
            )
            await ctx.send(embed=embed)
            return
        
        if duration > 7 * 24 * 3600:  # 1 week max
            embed = create_error_embed(
                "❌ Time Too Long",
                "Maximum reminder time is 1 week"
            )
            await ctx.send(embed=embed)
            return
        
        reminder_time = datetime.utcnow() + timedelta(seconds=duration)
        reminder_id = f"{ctx.author.id}_{ctx.message.id}"
        
        self.reminders[reminder_id] = {
            'user_id': ctx.author.id,
            'channel_id': ctx.channel.id,
            'message': message,
            'reminder_time': reminder_time,
            'created_at': datetime.utcnow()
        }
        
        # Schedule the reminder
        asyncio.create_task(self.send_reminder(reminder_id, duration))
        
        from utils.helpers import format_time
        embed = create_success_embed(
            "⏰ Reminder Set",
            f"I'll remind you in {format_time(duration)}:\n**{message}**"
        )
        await ctx.send(embed=embed)
    
    async def send_reminder(self, reminder_id, delay):
        """Send a reminder after the specified delay"""
        await asyncio.sleep(delay)
        
        if reminder_id not in self.reminders:
            return
        
        reminder = self.reminders[reminder_id]
        channel = self.bot.get_channel(reminder['channel_id'])
        user = self.bot.get_user(reminder['user_id'])
        
        if channel and user:
            embed = create_embed(
                "⏰ Reminder",
                f"**{user.mention}** You asked me to remind you:\n{reminder['message']}"
            )
            embed.set_footer(text=f"Set {reminder['created_at'].strftime('%Y-%m-%d %H:%M')} UTC")
            
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                # Try to DM the user instead
                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass
        
        # Clean up
        del self.reminders[reminder_id]
    
    @commands.group(name='giveaway', aliases=['gw'], invoke_without_command=True)
    @is_staff()
    async def giveaway_group(self, ctx):
        """Giveaway system commands"""
        embed = create_embed(
            "🎉 Giveaway Commands",
            f"`{ctx.prefix}gw create <duration> <prize>` - Create a giveaway\n"
            f"`{ctx.prefix}gw end <giveaway_id>` - End a giveaway early\n"
            f"`{ctx.prefix}gw reroll <giveaway_id>` - Reroll winner\n"
            f"`{ctx.prefix}gw list` - List active giveaways"
        )
        await ctx.send(embed=embed)
    
    @giveaway_group.command(name='create')
    @is_staff()
    async def create_giveaway(self, ctx, duration, *, prize):
        """Create a giveaway"""
        from utils.helpers import parse_time, format_time
        
        duration_seconds = parse_time(duration)
        if duration_seconds <= 0:
            embed = create_error_embed(
                "❌ Invalid Duration",
                "Please provide a valid duration (e.g., 1h, 30m, 1d)"
            )
            await ctx.send(embed=embed)
            return
        
        if duration_seconds > 30 * 24 * 3600:  # 30 days max
            embed = create_error_embed(
                "❌ Duration Too Long",
                "Maximum giveaway duration is 30 days"
            )
            await ctx.send(embed=embed)
            return
        
        end_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        embed = create_embed(
            "🎉 GIVEAWAY 🎉",
            f"**Prize:** {prize}\n"
            f"**Duration:** {format_time(duration_seconds)}\n"
            f"**Ends:** <t:{int(end_time.timestamp())}:R>\n"
            f"**Hosted by:** {ctx.author.mention}\n\n"
            f"React with 🎉 to enter!"
        )
        embed.color = 0xf39c12
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("🎉")
        
        giveaway_id = str(message.id)
        self.giveaways[giveaway_id] = {
            'prize': prize,
            'host': ctx.author.id,
            'channel': ctx.channel.id,
            'guild': ctx.guild.id,
            'end_time': end_time,
            'active': True,
            'created_at': datetime.utcnow()
        }
        
        # Schedule giveaway end
        asyncio.create_task(self.end_giveaway_auto(giveaway_id, duration_seconds))
        
        embed = create_success_embed(
            "✅ Giveaway Created",
            f"Giveaway created successfully! ID: `{giveaway_id}`"
        )
        await ctx.send(embed=embed)
    
    async def end_giveaway_auto(self, giveaway_id, delay):
        """Automatically end giveaway after delay"""
        await asyncio.sleep(delay)
        await self.end_giveaway_logic(giveaway_id)
    
    @giveaway_group.command(name='end')
    @is_staff()
    async def end_giveaway_command(self, ctx, giveaway_id: str):
        """End a giveaway early"""
        if giveaway_id not in self.giveaways:
            embed = create_error_embed("❌ Giveaway Not Found", "Invalid giveaway ID")
            await ctx.send(embed=embed)
            return
        
        await self.end_giveaway_logic(giveaway_id)
        embed = create_success_embed("✅ Giveaway Ended", "Giveaway ended manually")
        await ctx.send(embed=embed)
    
    async def end_giveaway_logic(self, giveaway_id):
        """Logic to end giveaway and pick winner"""
        if giveaway_id not in self.giveaways:
            return
        
        giveaway = self.giveaways[giveaway_id]
        if not giveaway['active']:
            return
        
        try:
            channel = self.bot.get_channel(giveaway['channel'])
            message = await channel.fetch_message(int(giveaway_id))
            
            # Get participants
            reaction = discord.utils.get(message.reactions, emoji="🎉")
            if not reaction:
                embed = create_embed("🎉 Giveaway Ended", "No participants found!")
                await channel.send(embed=embed)
                return
            
            participants = []
            async for user in reaction.users():
                if not user.bot:
                    participants.append(user)
            
            if not participants:
                embed = create_embed(
                    "🎉 Giveaway Ended",
                    f"**Prize:** {giveaway['prize']}\n**Winner:** No valid participants!"
                )
                await channel.send(embed=embed)
            else:
                winner = random.choice(participants)
                embed = create_embed(
                    "🎉 Giveaway Ended",
                    f"**Prize:** {giveaway['prize']}\n**Winner:** {winner.mention}\n**Participants:** {len(participants)}"
                )
                embed.set_thumbnail(url=winner.display_avatar.url)
                await channel.send(embed=embed)
                
                # Try to DM the winner
                try:
                    dm_embed = create_success_embed(
                        "🎉 Congratulations!",
                        f"You won the giveaway for **{giveaway['prize']}** in {channel.guild.name}!"
                    )
                    await winner.send(embed=dm_embed)
                except discord.Forbidden:
                    pass
            
            giveaway['active'] = False
            
        except Exception as e:
            print(f"Error ending giveaway: {e}")
    
    @commands.command(name='weather')
    async def weather_command(self, ctx, *, location="New York"):
        """Get weather information (placeholder)"""
        # This would normally use a weather API
        embed = create_embed(
            f"🌤️ Weather for {location}",
            "Weather API integration coming soon!\n\n"
            "This command will show:\n"
            "• Current temperature\n"
            "• Weather conditions\n"
            "• Humidity and wind\n"
            "• 5-day forecast"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='quote')
    async def random_quote(self, ctx):
        """Get a random inspirational quote"""
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
            ("Life is what happens to you while you're busy making other plans.", "John Lennon"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
            ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
            ("Don't let yesterday take up too much of today.", "Will Rogers"),
            ("You learn more from failure than from success.", "Unknown"),
            ("If you are working on something exciting that you really care about, you don't have to be pushed.", "Steve Jobs"),
            ("Experience is the name everyone gives to their mistakes.", "Oscar Wilde")
        ]
        
        quote, author = random.choice(quotes)
        
        embed = create_embed(
            "💭 Quote of the Moment",
            f"*\"{quote}\"*\n\n**— {author}**"
        )
        embed.color = 0x9b59b6
        
        await ctx.send(embed=embed)
    
    @commands.command(name='flip', aliases=['coin'])
    async def coin_flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🥈"
        
        embed = create_embed(
            f"{emoji} Coin Flip",
            f"**Result:** {result}!"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='roll', aliases=['dice'])
    async def roll_dice(self, ctx, sides: int = 6):
        """Roll a dice (default 6 sides)"""
        if sides < 2 or sides > 100:
            embed = create_error_embed(
                "❌ Invalid Dice",
                "Dice must have between 2 and 100 sides"
            )
            await ctx.send(embed=embed)
            return
        
        result = random.randint(1, sides)
        
        embed = create_embed(
            f"🎲 Dice Roll (d{sides})",
            f"**Result:** {result}"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='choose')
    async def choose_option(self, ctx, *, options):
        """Choose between multiple options (separate with commas)"""
        if ',' not in options:
            embed = create_error_embed(
                "❌ Invalid Format",
                "Please separate options with commas\nExample: `!choose pizza, burger, sushi`"
            )
            await ctx.send(embed=embed)
            return
        
        choices = [option.strip() for option in options.split(',')]
        if len(choices) < 2:
            embed = create_error_embed(
                "❌ Not Enough Options",
                "Please provide at least 2 options"
            )
            await ctx.send(embed=embed)
            return
        
        chosen = random.choice(choices)
        
        embed = create_embed(
            "🤔 Choice Made",
            f"I choose: **{chosen}**"
        )
        embed.set_footer(text=f"Selected from {len(choices)} options")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, question):
        """Ask the magic 8-ball a question"""
        responses = [
            "It is certain", "It is decidedly so", "Without a doubt",
            "Yes definitely", "You may rely on it", "As I see it, yes",
            "Most likely", "Outlook good", "Yes", "Signs point to yes",
            "Reply hazy, try again", "Ask again later", "Better not tell you now",
            "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful"
        ]
        
        response = random.choice(responses)
        
        embed = create_embed(
            "🎱 Magic 8-Ball",
            f"**Question:** {question}\n**Answer:** {response}"
        )
        embed.color = 0x2c3e50
        
        await ctx.send(embed=embed)
    
    @commands.command(name='features')
    async def features_info(self, ctx):
        """Show information about the latest features"""
        embed = create_embed(
            "🚀 Latest Features",
            "Here are the newest additions to the bot:"
        )
        
        features = [
            ("📊 Poll System", "Create interactive polls with multiple options"),
            ("⏰ Reminders", "Set personal reminders for important tasks"),
            ("🎉 Giveaways", "Host exciting giveaways with automatic winner selection"),
            ("🎲 Fun Commands", "Coin flip, dice roll, 8-ball, and choice maker"),
            ("💭 Random Quotes", "Get inspirational quotes when you need motivation"),
            ("🌤️ Weather Info", "Weather integration (coming soon)"),
        ]
        
        for name, description in features:
            embed.add_field(
                name=name,
                value=description,
                inline=True
            )
        
        embed.set_footer(text="More features are being added regularly!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LatestFeatures(bot))