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

## ticket db
async def create_tickets_db():
    db_path = "./db/tickets.db"
    if not os.path.exists("./db"):
        os.makedirs("./db")
    async with aiosqlite.connect(db_path) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS db_init (init INTEGER)")
        await db.commit()

# ticket interactions
@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        await bot.get_cog("TicketSystem").on_button_click(interaction)

## warn database
async def create_warns_db():
    db_path = "./db/warns.db"
    if not os.path.exists("./db"):
        os.makedirs("./db")
    async with aiosqlite.connect(db_path) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS db_init (init INTEGER)")
        await db.commit()

## exp database
async def create_exp_db():
    db_path = "./db/database.db"
    if not os.path.exists("./db"):
        os.makedirs("./db")
    async with aiosqlite.connect(db_path) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS db_init (init INTEGER)")
        await db.commit()

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

async def create_afk_table(guild_id):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (user_id INTEGER PRIMARY KEY, reason TEXT)"
        )
        await db.commit()

async def remove_afk_status(guild_id, user_id):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        await db.execute(
            f"DELETE FROM {table_name} WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

async def check_afk_status(guild_id, user_id):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        async with db.execute(
            f"SELECT reason FROM {table_name} WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_afk_status(guild_id, user_id, reason):
    table_name = f"afk_{guild_id}"
    async with aiosqlite.connect("./db/database.db") as db:
        await db.execute(
            f"INSERT OR REPLACE INTO {table_name} (user_id, reason) VALUES (?, ?)",
            (user_id, reason)
        )
        await db.commit()

    # Handle AFK system
    await create_afk_table(message.guild.id)

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
    guild_count = len(bot.guilds)  # Number of servers the bot is in
    embed = discord.Embed(title="Bot Status", color=discord.Color.blue())
    embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
    embed.add_field(name="Servers Count", value=guild_count, inline=True)  # Add server count field
    embed.add_field(name="Uptime", value=uptime, inline=False)
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text="Made by Voidsudo")
    await ctx.respond(embed=embed)

bot.run(TOKEN)
