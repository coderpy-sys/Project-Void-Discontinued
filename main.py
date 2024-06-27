import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import os
from colorama import Fore, Style, Back
import aiosqlite
import time
import random
import logging
import traceback

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)
intents.messages = True
intents.guilds = True


if not os.path.exists("db/"):
    os.makedirs("db/")

start_time = time.time()

async def initialize_database(db_path):
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    async with aiosqlite.connect(db_path) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS db_init (init INTEGER)")
        await db.commit()

async def setup_databases():
    await initialize_database("./db/tickets.db")
    await initialize_database("./db/warns.db")
    await initialize_database("./db/afk.db")

#ticket interactions
@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        await bot.get_cog("TicketSystem").on_button_click(interaction)

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
    await setup_databases()
    print(f"{Fore.BLUE}INFO:{Style.RESET_ALL} All Databases are loaded successfully.{Style.RESET_ALL} ")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            print(f"{Fore.BLUE}INFO: {Style.RESET_ALL}Loaded cog: {filename}")

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

# global error logging
GUILD_ID = 1255769729889603635
CHANNEL_ID = 1255821756778811462

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(traceback.format_exc())
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"```{traceback.format_exc()}```",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

bot.run(TOKEN)
