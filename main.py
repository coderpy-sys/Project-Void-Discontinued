import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import os
from colorama import Fore, Style, Back
import aiosqlite
import time
import random

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)
intents.messages = True
intents.guilds = True


if not os.path.exists("db/"):
    os.makedirs("db/")

start_time = time.time()


def get_uptime():
    current_time = time.time()
    uptime_seconds = current_time - start_time
    minutes, seconds = divmod(int(uptime_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h {minutes}m {seconds}s"

@bot.event
async def on_ready():
    print(f"{Fore.BLUE}INFO:{Style.RESET_ALL} Bot is running!{Style.RESET_ALL} ")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            print(f"{Fore.BLUE}INFO: {Style.RESET_ALL}Loaded cog: {filename}")
    setattr(bot, "db", aiosqlite.connect("./db/database.db"))
    async with bot.db as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS afk (guild_id INTEGER, user_id INTEGER, reason TEXT)"
        )
        await db.commit()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    async with aiosqlite.connect("./db/database.db") as db:
        guild_id = message.guild.id
        table_name = f"users_{guild_id}"
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, guild_id INTEGER, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, last_message_time REAL DEFAULT 0)"
        )
        await db.commit()

        async with db.execute(
            f"SELECT xp, level, last_message_time FROM {table_name} WHERE id = ?",
            (message.author.id,)
        ) as cursor:
            row = await cursor.fetchone()
            current_time = time.time()

            if row:
                xp, level, last_message_time = row
                if last_message_time is None:
                    last_message_time = 0

                COOLDOWN_PERIOD = 120
                if current_time - last_message_time >= COOLDOWN_PERIOD:
                    xp_gain = random.randint(10, 40)
                    xp += xp_gain
                    xp_needed = 500 * level  # Function to calculate XP needed for next level
                    if xp >= xp_needed:
                        level += 1
                        xp -= xp_needed
                        await message.channel.send(
                            embed=discord.Embed(
                                title="Leveled Up!",
                                description=f"Congratulations {message.author.mention}, you leveled up to level {level}!",
                                color=0x4863A0,
                            ).set_footer(text="Made by Voidsudo"),
                            delete_after=5,
                        )
                    await db.execute(
                        f"UPDATE {table_name} SET xp = ?, level = ?, last_message_time = ? WHERE id = ?",
                        (xp, level, current_time, message.author.id)
                    )
            else:
                xp, level = random.randint(10, 40), 1
                await db.execute(
                    f"INSERT INTO {table_name} (id, guild_id, xp, level, last_message_time) VALUES (?, ?, ?, ?, ?)",
                    (message.author.id, guild_id, xp, level, current_time)
                )
            await db.commit()

async def create_afk_table(guild_id):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (user_id INTEGER PRIMARY KEY, reason TEXT)"
        )
        await db.commit()

# Function to remove AFK status for a user in a guild
async def remove_afk_status(guild_id, user_id):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        await db.execute(
            f"DELETE FROM {table_name} WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

# Function to check if user is AFK in a guild
async def check_afk_status(guild_id, user_id):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        async with db.execute(
            f"SELECT reason FROM {table_name} WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

# Function to set AFK status for a user in a guild
async def set_afk_status(guild_id, user_id, reason):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        await db.execute(
            f"INSERT OR REPLACE INTO {table_name} (user_id, reason) VALUES (?, ?)",
            (user_id, reason)
        )
        await db.commit()

# Example of handling AFK checks and mentions in on_message event
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Ensure the afk table for the guild is created if not exists
    await create_afk_table(message.guild.id)

    # Check for AFK status
    async with aiosqlite.connect("./db/database.db") as db:
        table_name = f"afk_{message.guild.id}"
        async with db.execute(
            f"SELECT reason FROM {table_name} WHERE user_id = ?",
            (message.author.id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                await remove_afk_status(message.guild.id, message.author.id)
                await message.channel.send(
                    f"{message.author.mention} You are no longer AFK.",
                    delete_after=5
                )

    # Mention check for AFK users
    if message.mentions:
        for user in message.mentions:
            async with aiosqlite.connect("./db/database.db") as db:
                table_name = f"afk_{message.guild.id}"
                async with db.execute(
                    f"SELECT reason FROM {table_name} WHERE user_id = ?",
                    (user.id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        await message.channel.send(
                            f"{user.display_name} is AFK: {row[0]}",
                            delete_after=5
                        )



for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")


@bot.event
async def on_interaction(interaction):
    if interaction.guild_id is None:
        return await interaction.respond("This command can only be used in a server")
    await bot.process_application_commands(interaction)


@bot.command(name="status", description="Show the bot's status and uptime.")
async def status(ctx):
    uptime = get_uptime()
    embed = discord.Embed(title="Bot Status", color=discord.Color.blue())
    embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
    embed.add_field(name="Uptime", value=uptime, inline=False)
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text="Made by Voidsudo")
    await ctx.respond(embed=embed)


bot.run(TOKEN)
