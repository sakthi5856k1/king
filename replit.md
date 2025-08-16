# Discord Moderation Bot

## Overview

This is a comprehensive Discord moderation bot built with Python and discord.py. The bot provides essential server management features including modmail, economy system, auto-responses, moderation tools, and comprehensive logging. It's designed for medium to large Discord servers that need automated moderation assistance and member engagement features.

## User Preferences

Preferred communication style: Simple, everyday language.
Command prefix: "/" (changed from "!" per user request)

## System Architecture

### Core Framework
- **Discord.py Library**: Built using the discord.py library with commands extension for command handling
- **Cog-based Architecture**: Modular design using Discord.py cogs for feature separation and maintainability
- **Event-driven System**: Leverages Discord's event system for real-time message processing and server monitoring

### Data Storage
- **JSON File-based Database**: Simple JSON file storage system for persistence without external database dependencies
- **In-memory Caching**: User data and configurations loaded into memory for fast access
- **Auto-save Mechanism**: Periodic data persistence every 5 minutes to prevent data loss

### Permission System
- **Role-based Access Control**: Custom decorators for staff and moderator permission checking
- **Hierarchy Validation**: Prevents lower-ranked users from moderating higher-ranked members
- **Owner Override**: Special permissions for bot owner

### Modular Components
- **ModMail System**: Private ticket-based communication between users and moderators
- **Economy Module**: Comprehensive economy system with balance tracking, daily rewards, work system, gambling, and full shop functionality
- **Shop System**: Multi-category store with color roles, special roles, temporary perks, and collectible items
- **Inventory System**: User inventory management with item tracking, role assignment, and selling capabilities
- **Perk System**: Temporary boosts including daily boost (50% more daily rewards), work boost (33% more work income), and gamble luck (65% win chance)
- **Auto-response Engine**: Automated message responses with cooldown management
- **Moderation Tools**: Standard moderation commands (kick, ban, mute, warn) with logging
- **Event Logging**: Comprehensive server event tracking and audit trails
- **Help System**: Dynamic help command with categorized information
- **Latest Features Module**: Advanced utilities including polls, reminders, giveaways, and fun commands
- **Welcome System**: Customizable welcome messages, auto role assignment, member management, and GIF image support

### Latest Features Module Details
- **Interactive Polls**: Multi-option polls with reaction voting and real-time results tracking
- **Personal Reminders**: Time-based reminder system with flexible duration parsing (minutes to weeks)
- **Giveaway System**: Automated giveaways with random winner selection and DM notifications
- **Fun Commands**: Coin flip, dice roll, magic 8-ball, choice maker, and inspirational quotes
- **Utility Tools**: Weather integration placeholder and enhanced user engagement features

### Configuration Management
- **Environment Variables**: Bot token and sensitive data through environment variables
- **Centralized Settings**: All configuration options consolidated in settings.py
- **Feature Toggles**: Enable/disable features through configuration flags

### Error Handling and Logging
- **Structured Logging**: File and console logging with different severity levels
- **Graceful Degradation**: Permission-aware error handling for missing bot permissions
- **User Feedback**: Informative embed-based error messages for users

## External Dependencies

### Core Libraries
- **discord.py**: Primary Discord API wrapper for bot functionality
- **asyncio**: Asynchronous programming support for concurrent operations
- **logging**: Built-in Python logging for debugging and monitoring
- **datetime**: Time-based operations for cooldowns and timestamps
- **json**: Data serialization for file-based storage
- **os**: Environment variable access and file system operations
- **random**: Random number generation for games, giveaways, and fun commands

### Discord Platform
- **Discord API**: Real-time message events, user interactions, and server management
- **Discord Permissions**: Role-based permission system integration
- **Discord Embeds**: Rich message formatting for enhanced user experience

### File System
- **Local JSON Storage**: Data persistence through local file system
- **Configuration Files**: Settings and data stored in organized directory structure

### Environment Configuration
- **Environment Variables**: Bot token, owner ID, and other sensitive configuration
- **Configurable Prefixes**: Customizable command prefixes per deployment
- **Feature Flags**: Runtime configuration for enabling/disabling bot features