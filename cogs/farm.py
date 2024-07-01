import discord
from discord.ext import tasks, commands
import aiosqlite
import os
from dotenv import load_dotenv
from colorama import Fore, Style

load_dotenv()
BIO_CHECK = os.getenv("BIO_CHECK")

class Farm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_for_bio.start()

    async def get_user(self, user_id):
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
                user = await cursor.fetchone()
                if user is None:
                    await db.execute(
                        "INSERT INTO users (id, coins, weekly_timestamp, daily_timestamp) VALUES (?, ?, ?, ?)",
                        (user_id, 0, 0, 0),
                    )
                    await db.commit()
                    return {
                        "coins": 0,
                        "weekly_timestamp": 0,
                        "daily_timestamp": 0
                    }
                else:
                    return {
                        "coins": user[1],
                        "weekly_timestamp": user[2],
                        "daily_timestamp": user[3]
                    }

    @tasks.loop(seconds=60)
    async def check_for_bio(self):
        ulen = 0
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.activity:
                    if member.activity.type == discord.ActivityType.custom:
                        if member.activity.name == BIO_CHECK:
                            user = await self.get_user(member.id)
                            async with aiosqlite.connect("./db/database.db") as db:
                                await db.execute(
                                    "UPDATE users SET coins = ? WHERE id = ?",
                                    (user["coins"] + 1, member.id),
                                )
                                await db.commit()
                                ulen += 1
        print(
            f"{Fore.GREEN}INFO: {Style.RESET_ALL}Added 1 coin to {ulen} users{Style.RESET_ALL}"
        )

    @check_for_bio.before_loop
    async def before_check_for_bio(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Farm(bot))