import discord
from discord.ext import commands
import aiosqlite
import datetime

class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    coins INTEGER NOT NULL,
                    weekly_timestamp INTEGER NOT NULL,
                    daily_timestamp INTEGER NOT NULL,
                    bank INTEGER NOT NULL
                )
            """)
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect("./db/economy.db") as db:
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
                user = await cursor.fetchone()
                if user is None:
                    await db.execute(
                        "INSERT INTO users (id, coins, weekly_timestamp, daily_timestamp,  bank) VALUES (?, ?, ?, ?, ?)",
                        (user_id, 0, 0, 0, 0),
                    )
                    await db.commit()
                    return {
                        "coins": 0,
                        "weekly_timestamp": 0,
                        "daily_timestamp": 0,
                        "bank": 0
                    }
                else:
                    return {
                        "coins": user[1],
                        "weekly_timestamp": user[2],
                        "daily_timestamp": user[3],
                        "bank": user[4],
                    }

    bank = discord.SlashCommandGroup(name="bank", description="Bank commands")

    @bank.command(name="deposit", description="Deposit coins into your bank")
    async def deposit(self, ctx, amount: int):
        user_data = await self.get_user(ctx.author.id)
        
        if amount <= 0:
            await ctx.respond("The deposit amount must be positive.", ephemeral=True)
            return

        if user_data["coins"] < amount:
            await ctx.respond("You do not have enough coins to deposit.", ephemeral=True)
            return

        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute("UPDATE users SET coins = coins - ?, bank = bank + ? WHERE id = ?", (amount, amount, ctx.author.id))
            await db.commit()

        embed = discord.Embed(
            title="Deposit Successful",
            description=f"You have deposited {amount} coins into your bank.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else "https://i.postimg.cc/fLQ8T6F6/NO-USER.png")
        await ctx.respond(embed=embed)

    @bank.command(name="balance", description="Check your bank balance")
    async def balance(self, ctx, user: discord.Member = None):
        target_user = user if user else ctx.author
        user_data = await self.get_user(target_user.id)
        
        embed = discord.Embed(
            title=f"{target_user.name}'s Bank Balance",
            description=f"Bank: {user_data['bank']} coins\nWallet: {user_data['coins']} coins",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=target_user.avatar.url)
        await ctx.respond(embed=embed)

    @bank.command(name="withdraw", description="Withdraw coins from your bank")
    async def withdraw(self, ctx, amount: int):
        user_data = await self.get_user(ctx.author.id)
        
        if amount <= 0:
            await ctx.respond("The withdraw amount must be positive.", ephemeral=True)
            return

        if user_data["bank"] < amount:
            await ctx.respond("You do not have enough coins in your bank to withdraw.", ephemeral=True)
            return

        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute("UPDATE users SET bank = bank - ?, coins = coins + ? WHERE id = ?", (amount, amount, ctx.author.id))
            await db.commit()

        embed = discord.Embed(
            title="Withdraw Successful",
            description=f"You have withdrawn {amount} coins from your bank.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else "https://i.postimg.cc/fLQ8T6F6/NO-USER.png")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Bank(bot))
