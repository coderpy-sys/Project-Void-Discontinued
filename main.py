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
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, level INTEGER, coins INTEGER, afk INTEGER, xp INTEGER DEFAULT 0, xp_cooldown INTEGER DEFAULT 0, last_message_time REAL DEFAULT 0)"
        )
        await db.commit()
        await db.execute(
            "CREATE TABLE IF NOT EXISTS afk (guild_id INTEGER, user_id INTEGER, reason TEXT)"
        )
        await db.commit()


def get_xp_for_next_level(level):
    # Simple formula for XP required for next level
    return 1000 * level


# Cooldown period (in seconds)
COOLDOWN_PERIOD = 120


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    async with aiosqlite.connect("./db/database.db") as db:
        async with db.execute(
            "SELECT xp, level, last_message_time FROM users WHERE id = ?",
            (message.author.id,),
        ) as cursor:
            row = await cursor.fetchone()
            current_time = time.time()

            if row:
                xp, level, last_message_time = row
                if last_message_time is None:
                    last_message_time = (
                        0  # Default to 0 if last_message_time is not set
                    )

                if current_time - last_message_time >= COOLDOWN_PERIOD:
                    xp_gain = random.randint(10, 40)
                    xp += xp_gain
                    xp_needed = get_xp_for_next_level(level)
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
                        "UPDATE users SET xp = ?, level = ?, last_message_time = ? WHERE id = ?",
                        (xp, level, current_time, message.author.id),
                    )
            else:
                xp, level = random.randint(10, 40), 1
                await db.execute(
                    "INSERT INTO users (id, xp, level, last_message_time) VALUES (?, ?, ?, ?)",
                    (message.author.id, xp, level, current_time),
                )
            await db.commit()

    # check if afk
    async with aiosqlite.connect("./db/database.db") as db:
        async with db.execute(
            "SELECT reason FROM afk WHERE user_id = ?", (message.author.id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                await db.execute(
                    "DELETE FROM afk WHERE user_id = ?", (message.author.id,)
                )
                await db.commit()
                await message.channel.send(
                    f"{message.author.mention} You are no longer AFK."
                )

    # mention check for afk
    if message.mentions:
        for user in message.mentions:
            async with aiosqlite.connect("./db/database.db") as db:
                async with db.execute(
                    "SELECT reason FROM afk WHERE user_id = ?", (user.id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        await message.channel.send(
                            f"{user.display_name} is AFK: {row[0]}"
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
