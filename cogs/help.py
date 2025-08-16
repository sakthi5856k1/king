import discord
from discord.ext import commands
from utils.helpers import create_embed
from config.settings import BOT_CONFIG

class Help(commands.Cog):
    """Help system for the bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', aliases=['h'])
    async def help_command(self, ctx, *, category=None):
        """Show help information"""
        if category is None:
            await self.send_main_help(ctx)
        else:
            await self.send_category_help(ctx, category.lower())

    async def send_main_help(self, ctx):
        """Send the main help menu"""
        embed = create_embed(
            "🤖 Bot Help",
            f"Use `{ctx.prefix}help <category>` for detailed command information.\n\n"
            "**Available Categories:**"
        )

        categories = [
            ("💰 Economy", "economy", "Balance, daily rewards, work, gambling"),
            ("📨 ModMail", "modmail", "Private communication with moderators"),
            ("🔨 Moderation", "moderation", "Kick, ban, mute, warn, purge"),
            ("🤖 Auto Response", "autoresponse", "Automatic message responses"),
            ("📊 Logging", "logging", "Server event and action logging"),
            ("🎉 Features", "features", "Polls, reminders, giveaways, fun commands"),
            ("👋 Welcome", "welcome", "Welcome messages and auto roles"),
            ("🎭 Emojis", "emoji", "Custom emoji management with animation support"),
            ("❓ General", "general", "Basic bot information and utility")
        ]

        for emoji_name, category, description in categories:
            embed.add_field(
                name=emoji_name,
                value=f"`{ctx.prefix}help {category}`\n{description}",
                inline=True
            )

        embed.add_field(
            name="📝 Bot Info",
            value=f"**Prefix:** `{ctx.prefix}`\n"
                  f"**Servers:** {len(self.bot.guilds)}\n"
                  f"**Users:** {len(self.bot.users)}",
            inline=True
        )

        embed.set_footer(text=f"Use {ctx.prefix}help <category> for more details")

        await ctx.send(embed=embed)

    async def send_category_help(self, ctx, category):
        """Show help for a specific category"""
        category = category.lower()

        if category in ['moderation', 'mod', 'admin']:
            await self.moderation_help(ctx)
        elif category in ['economy', 'eco', 'money']:
            await self.economy_help(ctx)
        elif category in ['modmail', 'mail', 'mm']:
            await self.modmail_help(ctx)
        elif category in ['autoresponse', 'ar', 'auto']:
            await self.autoresponse_help(ctx)
        elif category in ['logging', 'log', 'logs']:
            await self.logging_help(ctx)
        elif category in ['features', 'fun', 'polls', 'latest']:
            await self.features_help(ctx)
        elif category in ['welcome', 'autorole', 'greet']:
            await self.welcome_help(ctx)
        elif category in ['emoji', 'emojis', 'emote']:
            await self.emoji_help(ctx)
        elif category in ['general', 'info', 'basic']:
            await self.general_help(ctx)
        elif category in ['help']:
            await self.help_help(ctx)
        else:
            embed = create_embed(
                "❌ Invalid Category",
                f"Category `{category}` not found. Use `{ctx.prefix}help` to see all categories."
            )
            await ctx.send(embed=embed)

    async def economy_help(self, ctx):
        """Economy system help"""
        embed = create_embed(
            "💰 Economy Commands",
            "Manage your virtual money and participate in the server economy."
        )

        user_commands = [
            (f"{ctx.prefix}balance [user]", "Check your or another user's balance"),
            (f"{ctx.prefix}daily", "Claim your daily reward (24h cooldown)"),
            (f"{ctx.prefix}work", "Work to earn money (1h cooldown)"),
            (f"{ctx.prefix}pay <user> <amount>", "Pay money to another user"),
            (f"{ctx.prefix}gamble <amount>", "Gamble your money (50/50 chance)"),
            (f"{ctx.prefix}leaderboard [page]", "View the money leaderboard"),
            (f"{ctx.prefix}shop", "View the shop (coming soon)")
        ]

        admin_commands = [
            (f"{ctx.prefix}eco give <user> <amount>", "Give money to a user"),
            (f"{ctx.prefix}eco take <user> <amount>", "Take money from a user"),
            (f"{ctx.prefix}eco set <user> <amount>", "Set a user's balance"),
            (f"{ctx.prefix}eco reset <user>", "Reset a user's economy data")
        ]

        embed.add_field(
            name="👤 User Commands",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in user_commands]),
            inline=False
        )

        embed.add_field(
            name="👑 Admin Commands",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in admin_commands]),
            inline=False
        )

        await ctx.send(embed=embed)

    async def modmail_help(self, ctx):
        """ModMail system help"""
        embed = create_embed(
            "📨 ModMail Commands",
            "Private communication system between users and moderators."
        )

        user_info = [
            "Send a DM to the bot to create a ticket",
            "Continue sending messages to communicate with staff",
            "React with 🔒 or type `close` to close the ticket"
        ]

        staff_commands = [
            (f"{ctx.prefix}reply <message>", "Reply to a modmail ticket"),
            (f"{ctx.prefix}close [reason]", "Close a modmail ticket"),
            (f"{ctx.prefix}modmail setup", "Set up modmail category"),
            (f"{ctx.prefix}modmail stats", "View modmail statistics")
        ]

        embed.add_field(
            name="👤 For Users",
            value="\n".join([f"• {info}" for info in user_info]),
            inline=False
        )

        embed.add_field(
            name="👮 For Staff",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in staff_commands]),
            inline=False
        )

        await ctx.send(embed=embed)

    async def moderation_help(self, ctx):
        """Moderation system help"""
        embed = create_embed(
            "🔨 Moderation Commands",
            "Tools for maintaining order and managing your server."
        )

        basic_commands = [
            (f"{ctx.prefix}kick <user> [reason]", "Kick a user from the server"),
            (f"{ctx.prefix}ban <user> [days] [reason]", "Ban a user from the server"),
            (f"{ctx.prefix}unban <user_id> [reason]", "Unban a user"),
            (f"{ctx.prefix}mute <user> [duration] [reason]", "Mute a user"),
            (f"{ctx.prefix}unmute <user> [reason]", "Unmute a user"),
            (f"{ctx.prefix}warn <user> <reason>", "Warn a user"),
            (f"{ctx.prefix}warnings [user]", "View warnings for a user"),
            (f"{ctx.prefix}purge <amount> [user]", "Delete messages in bulk")
        ]

        embed.add_field(
            name="🛠️ Commands",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in basic_commands]),
            inline=False
        )

        embed.add_field(
            name="📝 Notes",
            value="• Mute duration examples: `1h`, `30m`, `1d`\n"
                  "• Purge limit: 1-100 messages\n"
                  "• All actions are logged automatically",
            inline=False
        )

        await ctx.send(embed=embed)

    async def autoresponse_help(self, ctx):
        """Auto response system help"""
        embed = create_embed(
            "🤖 Auto Response Commands",
            "Set up automatic responses to common questions and triggers."
        )

        commands = [
            (f"{ctx.prefix}ar add <trigger> <response>", "Add an auto response"),
            (f"{ctx.prefix}ar remove <trigger>", "Remove an auto response"),
            (f"{ctx.prefix}ar list [page]", "List all auto responses"),
            (f"{ctx.prefix}ar edit <trigger> <new_response>", "Edit an auto response"),
            (f"{ctx.prefix}ar info <trigger>", "Get detailed info about a response"),
            (f"{ctx.prefix}ar stats", "View auto response statistics"),
            (f"{ctx.prefix}ar toggle", "Toggle auto responses on/off"),
            (f"{ctx.prefix}ar clear", "Clear all auto responses")
        ]

        embed.add_field(
            name="🛠️ Commands",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in commands]),
            inline=False
        )

        embed.add_field(
            name="📝 Notes",
            value="• Triggers are case-insensitive\n"
                  "• Responses have a 30-second cooldown per user\n"
                  "• Supports partial word matching",
            inline=False
        )

        await ctx.send(embed=embed)

    async def logging_help(self, ctx):
        """Logging system help"""
        embed = create_embed(
            "📊 Logging Commands",
            "Configure logging for various server events and moderation actions."
        )

        commands = [
            (f"{ctx.prefix}log channel <channel>", "Set general log channel"),
            (f"{ctx.prefix}log moderation <channel>", "Set moderation log channel"),
            (f"{ctx.prefix}log members <channel>", "Set member log channel"),
            (f"{ctx.prefix}log messages <channel>", "Set message log channel"),
            (f"{ctx.prefix}log voice <channel>", "Set voice log channel"),
            (f"{ctx.prefix}log server <channel>", "Set server log channel"),
            (f"{ctx.prefix}log disable <type>", "Disable a logging type"),
            (f"{ctx.prefix}log status", "View current configuration")
        ]

        events = [
            "Member joins/leaves",
            "Message edits/deletions",
            "Voice channel activity",
            "Role changes",
            "Channel creation/deletion",
            "Moderation actions"
        ]

        embed.add_field(
            name="🛠️ Commands",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in commands]),
            inline=False
        )

        embed.add_field(
            name="📝 Logged Events",
            value="\n".join([f"• {event}" for event in events]),
            inline=False
        )

        await ctx.send(embed=embed)

    async def features_help(self, ctx):
        """Latest features system help"""
        embed = create_embed(
            "🎉 Latest Features Commands",
            "Advanced utilities including polls, reminders, giveaways, and fun commands."
        )

        poll_commands = [
            (f"{ctx.prefix}poll create <question> | <option1> | <option2>", "Create a poll with options"),
            (f"{ctx.prefix}poll end <poll_id>", "End a poll early"),
            (f"{ctx.prefix}poll list", "List active polls"),
            (f"{ctx.prefix}poll results <poll_id>", "View poll results")
        ]

        reminder_commands = [
            (f"{ctx.prefix}remind <time> <message>", "Set a personal reminder"),
            (f"{ctx.prefix}reminders", "View your active reminders"),
            (f"{ctx.prefix}reminder cancel <id>", "Cancel a reminder")
        ]

        giveaway_commands = [
            (f"{ctx.prefix}giveaway start <duration> <prize>", "Start a giveaway"),
            (f"{ctx.prefix}giveaway end <giveaway_id>", "End a giveaway early"),
            (f"{ctx.prefix}giveaway list", "List active giveaways")
        ]

        fun_commands = [
            (f"{ctx.prefix}flip", "Flip a coin"),
            (f"{ctx.prefix}roll [sides]", "Roll a dice (default 6 sides)"),
            (f"{ctx.prefix}8ball <question>", "Ask the magic 8-ball"),
            (f"{ctx.prefix}choose <option1> | <option2> | ...", "Choose randomly from options"),
            (f"{ctx.prefix}quote", "Get an inspirational quote")
        ]

        embed.add_field(
            name="📊 Polls",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in poll_commands]),
            inline=False
        )

        embed.add_field(
            name="⏰ Reminders",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in reminder_commands]),
            inline=False
        )

        embed.add_field(
            name="🎁 Giveaways",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in giveaway_commands]),
            inline=False
        )

        embed.add_field(
            name="🎲 Fun Commands",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in fun_commands]),
            inline=False
        )

        embed.add_field(
            name="📝 Notes",
            value="• Time examples: `5m`, `1h`, `30s`, `2d`\n"
                  "• Polls support up to 10 options\n"
                  "• Giveaways notify winners via DM",
            inline=False
        )

        await ctx.send(embed=embed)

    async def welcome_help(self, ctx):
        """Welcome and auto role system help"""
        embed = create_embed(
            "👋 Welcome System Commands",
            "Configure welcome messages, auto roles, and member management."
        )

        welcome_commands = [
            (f"{ctx.prefix}welcome setup", "Interactive welcome system setup"),
            (f"{ctx.prefix}welcome channel <channel>", "Set welcome channel"),
            (f"{ctx.prefix}welcome message <message>", "Set welcome message"),
            (f"{ctx.prefix}welcome gif <url>", "Set welcome GIF image"),
            (f"{ctx.prefix}welcome toggle", "Toggle welcome messages"),
            (f"{ctx.prefix}welcome test", "Test welcome message"),
            (f"{ctx.prefix}welcome config", "View configuration")
        ]

        autorole_commands = [
            (f"{ctx.prefix}autorole add <role>", "Add an auto role"),
            (f"{ctx.prefix}autorole remove <role>", "Remove an auto role"),
            (f"{ctx.prefix}autorole list", "List current auto roles"),
            (f"{ctx.prefix}autorole toggle", "Toggle auto role system"),
            (f"{ctx.prefix}autorole clear", "Clear all auto roles")
        ]

        embed.add_field(
            name="🎉 Welcome Messages",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in welcome_commands]),
            inline=False
        )

        embed.add_field(
            name="🎭 Auto Roles",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in autorole_commands]),
            inline=False
        )

        embed.add_field(
            name="📝 Message Placeholders",
            value="`{user}` - Mention the user\n"
                  "`{username}` - User's name\n"
                  "`{server}` - Server name\n"
                  "`{member_count}` - Total members",
            inline=False
        )

        embed.add_field(
            name="✨ Features",
            value="• Custom welcome messages with embeds\n"
                  "• Auto role assignment for new members\n"
                  "• DM welcome messages\n"
                  "• Leave messages\n"
                  "• Interactive setup wizard",
            inline=False
        )

        await ctx.send(embed=embed)

    async def emoji_help(self, ctx):
        """Emoji management system help"""
        embed = create_embed(
            "🎭 Emoji Management Commands",
            "Manage custom emojis, including animated ones, within your server."
        )

        emoji_commands = [
            (f"{ctx.prefix}emoji add <name> <url>", "Add a new emoji (animated or static)"),
            (f"{ctx.prefix}emoji remove <name>", "Remove an emoji"),
            (f"{ctx.prefix}emoji list", "List all custom emojis on the server"),
            (f"{ctx.prefix}emoji download <name>", "Download an emoji file"),
            (f"{ctx.prefix}emoji info <name>", "Get information about an emoji"),
            (f"{ctx.prefix}emoji search <query>", "Search for emojis (coming soon)"),
            (f"{ctx.prefix}emoji animate <name>", "Animate a static emoji (requires configuration)"),
            (f"{ctx.prefix}emoji static <name>", "Convert an animated emoji to static (requires configuration)")
        ]

        embed.add_field(
            name="🛠️ Commands",
            value="\n".join([f"`{cmd}` - {desc}" for cmd, desc in emoji_commands]),
            inline=False
        )

        embed.add_field(
            name="📝 Notes",
            value="• Emoji names must be alphanumeric.\n"
                  "• Animated emojis require the `ANIMATED_EMOJI` permission.\n"
                  "• URLs for adding emojis must be valid image or GIF links.",
            inline=False
        )

        await ctx.send(embed=embed)

    async def general_help(self, ctx):
        """General bot information"""
        embed = create_embed(
            "❓ General Information",
            "Basic bot information and utility commands."
        )

        bot_info = [
            f"**Bot Name:** {self.bot.user.name}",
            f"**Prefix:** `{ctx.prefix}`",
            f"**Servers:** {len(self.bot.guilds)}",
            f"**Users:** {len(self.bot.users)}",
            f"**Commands:** {len(list(self.bot.walk_commands()))}",
            f"**Python Version:** {discord.__version__}",
        ]

        useful_links = [
            "[Support Server](https://discord.gg/example)" if BOT_CONFIG['support_server'] else "Support Server: Not configured",
            "[Bot Invite](https://discord.com/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=8&scope=bot)",
            "[Source Code](https://github.com/example/bot)"
        ]

        embed.add_field(
            name="📊 Bot Statistics",
            value="\n".join(bot_info),
            inline=False
        )

        embed.add_field(
            name="🔗 Useful Links",
            value="\n".join(useful_links),
            inline=False
        )

        embed.add_field(
            name="🚀 Features",
            value="• Complete modmail system\n"
                  "• Economy with daily rewards\n"
                  "• Advanced moderation tools\n"
                  "• Auto response system\n"
                  "• Comprehensive logging\n"
                  "• Modular plugin system",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name='invite')
    async def invite_command(self, ctx):
        """Get the bot invite link"""
        permissions = discord.Permissions(
            kick_members=True,
            ban_members=True,
            manage_messages=True,
            manage_roles=True,
            manage_channels=True,
            view_audit_log=True,
            send_messages=True,
            embed_links=True,
            read_message_history=True,
            add_reactions=True,
            use_external_emojis=True
        )

        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=('bot', 'applications.commands')
        )

        embed = create_embed(
            "🔗 Invite the Bot",
            f"[Click here to invite me to your server!]({invite_url})\n\n"
            "**Permissions requested:**\n"
            "• Kick/Ban Members\n"
            "• Manage Messages/Roles/Channels\n"
            "• View Audit Log\n"
            "• Send Messages & Embeds\n"
            "• Add Reactions\n"
            "• Use External Emojis"
        )

        await ctx.send(embed=embed)

    @commands.command(name='ping')
    async def ping_command(self, ctx):
        """Check bot latency"""
        latency = round(self.bot.latency * 1000, 2)

        embed = create_embed(
            "🏓 Pong!",
            f"Bot latency: **{latency}ms**"
        )

        await ctx.send(embed=embed)

    @commands.command(name='info', aliases=['about'])
    async def info_command(self, ctx):
        """Show bot information"""
        embed = create_embed(
            f"ℹ️ About {self.bot.user.name}",
            "A comprehensive Discord bot with modmail, economy, moderation, and more!"
        )

        embed.add_field(
            name="📊 Statistics",
            value=f"**Servers:** {len(self.bot.guilds)}\n"
                  f"**Users:** {len(self.bot.users)}\n"
                  f"**Commands:** {len(list(self.bot.walk_commands()))}",
            inline=True
        )

        embed.add_field(
            name="🚀 Features",
            value="• ModMail System\n"
                  "• Economy System\n"
                  "• Auto Responses\n"
                  "• Moderation Tools\n"
                  "• Logging System",
            inline=True
        )

        embed.add_field(
            name="🛠️ Technical",
            value=f"**Language:** Python\n"
                  f"**Library:** discord.py\n"
                  f"**Latency:** {round(self.bot.latency * 1000, 2)}ms",
            inline=True
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))