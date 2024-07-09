import discord
from discord.ext import commands
import aiosqlite

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        async with aiosqlite.connect("db/configs.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS welcome_config (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message TEXT,
                    color TEXT,
                    title TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS welcome_sent (
                    guild_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            await db.commit()

    async def get_welcome_config(self, guild_id):
        async with aiosqlite.connect("db/configs.db") as db:
            async with db.execute("""
                SELECT channel_id, message, color, title FROM welcome_config WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                return await cursor.fetchone()

    async def set_welcome_config(self, guild_id, channel_id=None, message=None, color=None, title=None):
        async with aiosqlite.connect("db/configs.db") as db:
            await db.execute("""
                INSERT OR REPLACE INTO welcome_config (guild_id, channel_id, message, color, title)
                VALUES (
                    ?, 
                    COALESCE(?, (SELECT channel_id FROM welcome_config WHERE guild_id = ?)), 
                    COALESCE(?, (SELECT message FROM welcome_config WHERE guild_id = ?)), 
                    COALESCE(?, (SELECT color FROM welcome_config WHERE guild_id = ?)), 
                    COALESCE(?, (SELECT title FROM welcome_config WHERE guild_id = ?))
                )
            """, (guild_id, channel_id, guild_id, message, guild_id, color, guild_id, title, guild_id))
            await db.commit()

    async def delete_welcome_config(self, guild_id):
        async with aiosqlite.connect("db/configs.db") as db:
            await db.execute("""
                DELETE FROM welcome_config WHERE guild_id = ?
            """, (guild_id,))
            await db.commit()

    async def has_welcome_been_sent(self, guild_id, user_id):
        async with aiosqlite.connect("db/configs.db") as db:
            async with db.execute("""
                SELECT 1 FROM welcome_sent WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                return await cursor.fetchone() is not None

    async def mark_welcome_as_sent(self, guild_id, user_id):
        async with aiosqlite.connect("db/configs.db") as db:
            await db.execute("""
                INSERT INTO welcome_sent (guild_id, user_id)
                VALUES (?, ?)
            """, (guild_id, user_id))
            await db.commit()

    welcome = discord.SlashCommandGroup(name="welcome", description="Welcome commands")

    @welcome.command(name="set", description="Set the welcome channel for the server")
    @commands.has_permissions(administrator=True)
    async def welcome_set(self, ctx, channel: discord.TextChannel):
        await self.set_welcome_config(ctx.guild.id, channel.id)
        embed = discord.Embed(
            title="Welcome Channel Set",
            description=f"Welcome channel set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @welcome.command(name="disable", description="Disable the welcome channel")
    @commands.has_permissions(administrator=True)
    async def welcome_disable(self, ctx):
        await self.delete_welcome_config(ctx.guild.id)
        embed = discord.Embed(
            title="Welcome System",
            description="Welcome channel disabled.",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed)

    @welcome.command(name="customize", description="Customize the welcome message")
    @commands.has_permissions(administrator=True)
    async def welcome_customize(self, ctx, message: str, color: str = "#89CFF0", title: str = None):
        description = (
            "Customize the welcome message. "
            "Use {member.mention} to mention the new member."
        )
        await self.set_welcome_config(ctx.guild.id, message=message, color=color, title=title)
        embed = discord.Embed(
            title="Welcome Message Customized",
            description=f"Welcome message customized.\n\nMessage: {message}\nColor: {color}\nTitle: {title}",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        # Check if welcome has already been sent
        if await self.has_welcome_been_sent(guild_id, user_id):
            return

        # Mark welcome as sent
        await self.mark_welcome_as_sent(guild_id, user_id)

        # Fetch welcome config
        config = await self.get_welcome_config(guild_id)
        if config:
            channel_id, welcome_message, color, title = config
            channel = message.guild.get_channel(channel_id)
            if channel:
                if not welcome_message:
                    welcome_message = "We are glad to have you, {member.mention}!"
                welcome_message = welcome_message.format(member=message.author)
                color = color or "#89CFF0"  # Set default color if color is None
                embed = discord.Embed(
                    title=title or f"Welcome to {message.guild.name}!",
                    description=welcome_message,
                    color=discord.Color(int(color.lstrip("#"), 16))
                )
                embed.set_thumbnail(url=message.author.avatar.url)
                await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))
