import discord
from discord.ext import commands
import aiosqlite

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.authorized_user_ids = [1218756435664441404, 1129675180344610867]  # Replace with your actual user IDs
    async def initialize_db(self):
        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    coins INTEGER NOT NULL,
                    weekly_timestamp INTEGER NOT NULL,
                    daily_timestamp INTEGER NOT NULL
                )
            """)
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect("./db/economy.db") as db:
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
                    
                  
    dev = discord.SlashCommandGroup(name="dev", description="Developer commands")

    @dev.command(name="addcoins", description="Add coins to a user")
    async def addcoins(self, ctx, user: discord.Member, amount: int):
        if ctx.author.id not in self.authorized_user_ids:
            return await ctx.respond("You do not have permission to use this command")
        if ctx.guild is None:
            return await ctx.respond("This command can only be used in a server")
        user_data = await self.get_user(user.id)
        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (amount, user.id),
            )
            await db.commit()
            await ctx.respond(f"Added {amount} coins to {user.name}")

def setup(bot):
    bot.add_cog(Dev(bot))