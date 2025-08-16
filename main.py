import discord
from discord.ext import commands
import asyncio
import logging
import os
import json
from config.settings import BOT_CONFIG
from utils.database import Database

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix=BOT_CONFIG['prefix'],
            intents=intents,
            help_command=None
        )

        self.db = Database()
        self.status_rotation_task = None
        self.current_status_index = 0

    async def setup_hook(self):
        """Load all cogs when the bot starts"""
        cogs_to_load = [
            'cogs.modmail',
            'cogs.economy',
            'cogs.autoresponse',
            'cogs.moderation',
            'cogs.logging',
            'cogs.help',
            'cogs.features',
            'cogs.welcome',
            'cogs.emojis'
        ]

        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

        # Calculate total member count across all guilds
        total_members = sum(guild.member_count for guild in self.guilds)

        # Set bot status
        await self.change_presence(
            activity=discord.Game(name="Vantha Pesuvom"),
            status=discord.Status.online
        )

        # Start the status rotation task
        if self.status_rotation_task is None or self.status_rotation_task.done():
            self.status_rotation_task = self.loop.create_task(self.rotate_statuses())

    async def rotate_statuses(self):
        """Rotates bot statuses every 5 seconds"""
        statuses = [
            discord.Game(name="Vantha Pesuvom"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{sum(guild.member_count for guild in self.guilds):,} members"),
            discord.Activity(type=discord.ActivityType.watching, name="credit : King Of My Queen"),
        ]
        while True:
            await self.change_presence(activity=statuses[self.current_status_index])
            self.current_status_index = (self.current_status_index + 1) % len(statuses)
            await asyncio.sleep(5)


    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")

        # Calculate total member count across all guilds
        total_members = sum(guild.member_count for guild in self.guilds)

        # Update status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{total_members:,} members"
            )
        )

    async def on_guild_remove(self, guild):
        """Called when the bot leaves a guild"""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")

        # Calculate total member count across all guilds
        total_members = sum(guild.member_count for guild in self.guilds)

        # Update status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{total_members:,} members"
            )
        )

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param}`")
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Command on cooldown. Try again in {error.retry_after:.2f} seconds.")
            return

        logger.error(f"Unhandled command error in {ctx.command}: {error}")
        await ctx.send("❌ An unexpected error occurred. Please try again later.")

async def main():
    """Main function to run the bot"""
    bot = DiscordBot()

    # Get Discord token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set!")
        return

    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token provided!")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())