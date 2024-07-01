import discord
from discord.ext import commands
import aiosqlite

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.authorized_user_ids = [1218756435664441404, 1129675180344610867, 1116705678745141339]
    
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
            embed = discord.Embed(title="You do not have permission to use this command", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        if ctx.guild is None:
            embed = discord.Embed(title="This command can only be used in a server", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        user_data = await self.get_user(user.id)
        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (amount, user.id),
            )
            await db.commit()
            embed = discord.Embed(
                        title="Developer Commands",
                        description= f"Added {amount} coins to {user.name}",
                        color=discord.Color.green(),
                    )
            return await ctx.respond(embed=embed, delete_after=5)

    @dev.command(name="removecoins", description="Remove coins from a user")
    async def removecoins(self, ctx, user: discord.Member, amount: int):
        if ctx.author.id not in self.authorized_user_ids:
            embed = discord.Embed(title="You do not have permission to use this command", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        if ctx.guild is None:
            embed = discord.Embed(title="This command can only be used in a server", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        user_data = await self.get_user(user.id)
        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute(
                "UPDATE users SET coins = coins - ? WHERE id = ?",
                (amount, user.id),
            )
            await db.commit()
            embed = discord.Embed(
                        title="Developer Commands",
                        description= f"Removed {amount} coins to {user.name}",
                        color=discord.Color.green(),
                    )
            return await ctx.respond(embed=embed, delete_after=5)


    @dev.command(name="addcoupon", description="Add a coupon")
    async def addcoupon(self, ctx, code: str, coins: int, max_uses: int):
        if ctx.author.id not in self.authorized_user_ids:
            embed = discord.Embed(title="You do not have permission to use this command", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        if ctx.guild is None:
            embed = discord.Embed(title="This command can only be used in a server", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        async with aiosqlite.connect("./db/coupons.db") as db:
            await db.execute(
                "INSERT INTO coupons (code, coins, max_uses, usedby) VALUES (?, ?, ?, ?)",
                (code, coins, max_uses, ""),
            )
            await db.commit()
            embed = discord.Embed(
                        title="Developer Commands",
                        description= f"Added coupon {code} with {coins} coins and {max_uses} max uses",
                        color=discord.Color.green(),
                    )
            return await ctx.respond(embed=embed, delete_after=5)
    
    @dev.command(name="removecoupon", description="Remove a coupon")
    async def removecoupon(self, ctx, code: str):
        if ctx.author.id not in self.authorized_user_ids:
            embed = discord.Embed(title="You do not have permission to use this command", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        if ctx.guild is None:
            embed = discord.Embed(title="This command can only be used in a server", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        async with aiosqlite.connect("./db/coupons.db") as db:
            async with db.execute(
                "SELECT * FROM coupons WHERE code = ?", (code,)
            ) as cursor:
                coupon = await cursor.fetchone()
                if coupon is None:
                    embed = discord.Embed(
                        title="Developer Commands",
                        description= f"Coupon doesn't exists.",
                        color=discord.Color.red(),
                    )
                    return await ctx.respond(embed=embed, delete_after=5)
                await db.execute(
                    "DELETE FROM coupons WHERE code = ?",
                    (code,),
                )
                await db.commit()
                await ctx.respond(f"Removed coupon {code}")

    @dev.command(name="listcoupons", description="List all coupons")
    async def listcoupons(self, ctx):
        if ctx.author.id not in self.authorized_user_ids:
            embed = discord.Embed(title="You do not have permission to use this command", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        if ctx.guild is None:
            embed = discord.Embed(title="This command can only be used in a server", color=discord.Color.red())
            return await ctx.respond(embed=embed, delete_after=5)
        async with aiosqlite.connect("./db/coupons.db") as db:
            async with db.execute("SELECT * FROM coupons") as cursor:
                coupons = await cursor.fetchall()
                if len(coupons) == 0:
                    return await ctx.respond("No coupons found")
                response = ""
                for coupon in coupons:
                    response += (
                        f"Code: **{coupon[1]}**, Coins: **{coupon[2]}**, Uses: **{coupon[3]}**\n"
                    )
                embed = discord.Embed(
                    title="Coupons", description=response, color=discord.Color.orange()
                )
                await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Dev(bot))