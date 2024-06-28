import discord
from discord.ext import commands
from httpx import AsyncClient
from dotenv import load_dotenv
import os
from colorama import Fore, Style, Back
import aiosqlite
import random
import datetime

load_dotenv("../.env")
PTERO_API_KEY = os.getenv("PTERO_API")
COLOR = os.getenv("COLOR")


class Coupon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        async with aiosqlite.connect("./db/coupons.db") as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS coupons (id INTEGER PRIMARY KEY, code TEXT, coins INTEGER, max_uses INTEGER, usedby TEXT)"
            )
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect("./db/economy.db") as db:
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
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
                        "daily_timestamp": 0,
                    }
                else:
                    return {
                        "coins": user[2],
                        "weekly_timestamp": user[3],
                        "daily_timestamp": user[4],
                    }

    async def update_coins(self, user_id, amount):
        async with aiosqlite.connect("./db/economy.db") as db:
            await db.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (amount, user_id),
            )
            await db.commit()
            return True

    coupon = discord.SlashCommandGroup(name="coupon", description="Coupon commands")

    @coupon.command(name="redeem", description="Redeem a coupon")
    async def redeem(self, ctx, code: str):
        async with aiosqlite.connect("./db/coupons.db") as db:
            async with db.execute(
                "SELECT * FROM coupons WHERE code = ?", (code,)
            ) as cursor:
                coupon = await cursor.fetchone()
                if coupon is None:
                    return await ctx.respond("Invalid coupon code")
                if coupon[3] == 0:
                    return await ctx.respond("This coupon has no uses left")

                # if user has already used coupon
                usedby = coupon[4].split(",")
                if str(ctx.author.id) in usedby:
                    return await ctx.respond("You have already used this coupon")
                user = await self.get_user(ctx.author.id)
                # add user to usedby
                usedby = coupon[4]
                if usedby == "":
                    usedby = str(ctx.author.id)
                else:
                    usedby += f",{ctx.author.id}"
                await db.execute(
                    "UPDATE coupons SET usedby = ? WHERE code = ?",
                    (usedby, code),
                )
                await db.commit()
                await self.update_coins(ctx.author.id, coupon[2])
                # update coupon uses (remove 1)
                await db.execute(
                    "UPDATE coupons SET max_uses = max_uses - 1 WHERE code = ?",
                    (code,),
                )
                await db.commit()
                await ctx.respond(f"Redeemed coupon for {coupon[2]} coins")


def setup(bot):
    bot.add_cog(Coupon(bot))