import discord
from discord.ext import commands
import aiosqlite

class EconomySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cog.listener()
    async def on_ready(self):
        await self.initialize_db()

    async def initialize_db(self):
        self.db = await aiosqlite.connect("economy.db")
        self.cursor = await self.db.cursor()
        await self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 50
            )
        """)
        await self.db.commit()

    @commands.command(name="balance", aliases=["bal"])
    async def get_balance(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        await self.cursor.execute("SELECT balance FROM users WHERE user_id =?", (user.id,))
        balance = await self.cursor.fetchone()
        if balance is None:
            await self.cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, 0)", (user.id,))
            await self.db.commit()
            balance = 50
        else:
            balance = balance[0]
        embed = discord.Embed(title=f"{user.name}'s Balance", description=f"**{balance}** coins", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="pay", aliases=["transfer", "send"])
    async def pay(self, ctx, user: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("Invalid amount!")
            return
        await self.cursor.execute("SELECT balance FROM users WHERE user_id =?", (ctx.author.id,))
        author_balance = await self.cursor.fetchone()
        if author_balance is None:
            await ctx.send("You don't have an account!")
            return
        author_balance = author_balance[0]
        if author_balance < amount:
            await ctx.send("You don't have enough coins!")
            return
        await self.cursor.execute("UPDATE users SET balance = balance -? WHERE user_id =?", (amount, ctx.author.id))
        await self.cursor.execute("SELECT balance FROM users WHERE user_id =?", (user.id,))
        user_balance = await self.cursor.fetchone()
        if user_balance is None:
            await self.cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, 0)", (user.id,))
            await self.db.commit()
            user_balance = 0
        else:
            user_balance = user_balance[0]
        await self.cursor.execute("UPDATE users SET balance = balance +? WHERE user_id =?", (amount, user.id))
        await self.db.commit()
        await ctx.send(f"Paid **{amount}** coins to {user.mention}!")
        
	@commands.command(name="daily")
	async def daily_reward(self, ctx):
		await self.cursor.execute("SELECT balance FROM users WHERE user_id =?", (ctx.author.id,))
		balance = await self.cursor.fetchone()
		if balance is None:
			await ctx.send("You don't have an account!")
		return
		balance = balance[0]
		reward = 100  # daily reward amount
		await self.cursor.execute("UPDATE users SET balance = balance +? WHERE user_id =?", (reward, ctx.author.id))
		await self.db.commit()
		await ctx.send(f"You received your daily reward of **{reward}** coins!")
		
def setup(bot):
    bot.add_cog(EconomySystem(bot))
