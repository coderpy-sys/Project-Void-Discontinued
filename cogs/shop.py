import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup
import aiosqlite
from datetime import datetime, timedelta
import asyncio

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.update_shop())

    async def create_table_if_not_exists(self, guild_id):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"""CREATE TABLE IF NOT EXISTS shop_{guild_id} (
                    product_name TEXT, 
                    description TEXT, 
                    price INTEGER, 
                    stock INTEGER, 
                    duration INTEGER, 
                    added_at INTEGER
                )"""
            )
            await db.commit()

    async def create_transactions_table_if_not_exists(self, guild_id):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"""CREATE TABLE IF NOT EXISTS transactions_{guild_id} (
                    user_id INTEGER, 
                    product_name TEXT, 
                    price INTEGER, 
                    timestamp INTEGER
                )"""
            )
            await db.commit()

    async def update_shop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild in self.bot.guilds:
                await self.create_table_if_not_exists(guild.id)
                await self.create_transactions_table_if_not_exists(guild.id)
                async with aiosqlite.connect("./db/database.db") as db:
                    now = int(datetime.utcnow().timestamp())
                    async with db.execute(
                        f"SELECT product_name, duration, added_at FROM shop_{guild.id}"
                    ) as cursor:
                        async for row in cursor:
                            product_name, duration, added_at = row
                            remaining_time = max(0, duration - (now - added_at))
                            if remaining_time == 0:
                                await db.execute(f"DELETE FROM shop_{guild.id} WHERE product_name = ?", (product_name,))
                                await db.commit()
            await asyncio.sleep(60)

    servershop = SlashCommandGroup(name="servershop", description="Manage the server shop")

    @servershop.command(name="add", description="Add a product to the shop")
    async def add(self, ctx, product: str, description: str, price: int, stock: int, duration: str = None):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("You need admin permissions to use this command.", ephemeral=True)

        await self.create_table_if_not_exists(ctx.guild.id)

        duration_seconds = 0
        if duration:
            for part in duration.split():
                if part.endswith('d'):
                    duration_seconds += int(part[:-1]) * 86400
                elif part.endswith('h'):
                    duration_seconds += int(part[:-1]) * 3600
                elif part.endswith('m'):
                    duration_seconds += int(part[:-1]) * 60
                elif part.endswith('s'):
                    duration_seconds += int(part[:-1])
        
        added_at = int(datetime.utcnow().timestamp())

        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"INSERT INTO shop_{ctx.guild.id} (product_name, description, price, stock, duration, added_at) VALUES (?, ?, ?, ?, ?, ?)",
                (product, description, price, stock, duration_seconds, added_at)
            )
            await db.commit()

        await ctx.respond(f"Product '{product}' added to the shop.", ephemeral=True)

    @servershop.command(name="remove", description="Remove a product from the shop")
    async def remove(self, ctx, product: str):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("You need admin permissions to use this command.", ephemeral=True)

        await self.create_table_if_not_exists(ctx.guild.id)

        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"DELETE FROM shop_{ctx.guild.id} WHERE product_name = ?",
                (product,)
            )
            await db.commit()

        await ctx.respond(f"Product '{product}' removed from the shop.", ephemeral=True)

    @servershop.command(name="list", description="List all products in the shop")
    async def list(self, ctx):
        await self.create_table_if_not_exists(ctx.guild.id)

        embed = discord.Embed(title="Shop", color=discord.Color.blue())
        now = int(datetime.utcnow().timestamp())
        items_found = False

        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(f"SELECT product_name, description, price, stock, duration, added_at FROM shop_{ctx.guild.id}") as cursor:
                async for row in cursor:
                    items_found = True
                    product_name, description, price, stock, duration, added_at = row
                    remaining_time = max(0, duration - (now - added_at))
                    if remaining_time == 0:
                        await db.execute(f"DELETE FROM shop_{ctx.guild.id} WHERE product_name = ?", (product_name,))
                        await db.commit()
                        continue

                    days, seconds = divmod(remaining_time, 86400)
                    hours, seconds = divmod(seconds, 3600)
                    minutes, seconds = divmod(seconds, 60)
                    duration_str = f"{days}d {hours}h {minutes}m {seconds}s"

                    embed.add_field(
                        name=product_name,
                        value=f"Description: {description}\nPrice: {price} coins\nStock: {stock}\nDuration: {duration_str}",
                        inline=False
                    )

        if not items_found:
            embed.description = "The shop is empty."
        await ctx.respond(embed=embed, ephemeral=True)

    @servershop.command(name="buy", description="Buy a product from the shop")
    async def buy(self, ctx, product: str):
        await self.create_table_if_not_exists(ctx.guild.id)
        await self.create_transactions_table_if_not_exists(ctx.guild.id)

        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                f"SELECT price, stock FROM shop_{ctx.guild.id} WHERE product_name = ?",
                (product,)
            ) as cursor:
                item = await cursor.fetchone()

            if not item:
                return await ctx.respond("This product does not exist.", ephemeral=True)

            price, stock = item

            async with db.execute("SELECT coins FROM users WHERE id = ?", (ctx.author.id,)) as cursor:
                user = await cursor.fetchone()

            if not user or user[0] < price:
                return await ctx.respond("You have insufficient coins to buy this product.", ephemeral=True)

            new_stock = stock - 1
            if new_stock < 0:
                return await ctx.respond("This product is out of stock.", ephemeral=True)

            await db.execute(
                "UPDATE users SET coins = coins - ? WHERE id = ?",
                (price, ctx.author.id)
            )
            await db.execute(
                f"UPDATE shop_{ctx.guild.id} SET stock = ? WHERE product_name = ?",
                (new_stock, product)
            )
            await db.execute(
                f"INSERT INTO transactions_{ctx.guild.id} (user_id, product_name, price, timestamp) VALUES (?, ?, ?, ?)",
                (ctx.author.id, product, price, int(datetime.utcnow().timestamp()))
            )
            await db.commit()

        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                "INSERT INTO inventory (user_id, product_name, guild_id) VALUES (?, ?, ?)",
                (ctx.author.id, product, ctx.guild.id)
            )
            await db.commit()

        await ctx.respond(f"You have bought '{product}' for {price} coins.", ephemeral=True)

    @servershop.command(name="transactions", description="View the transaction history")
    async def transactions(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("You need admin permissions to use this command.", ephemeral=True)

        await self.create_transactions_table_if_not_exists(ctx.guild.id)

        embed = discord.Embed(title="Transaction History", color=discord.Color.blue())
        transactions_found = False

        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                f"SELECT user_id, product_name, price, timestamp FROM transactions_{ctx.guild.id} ORDER BY timestamp DESC LIMIT 10"
            ) as cursor:
                async for row in cursor:
                    transactions_found = True
                    user_id, product_name, price, timestamp = row
                    user = self.bot.get_user(user_id)
                    date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    embed.add_field(
                        name=user.name,
                        value=f"Product: {product_name}\nPrice: {price} coins\nDate: {date}",
                        inline=False
                    )

        if not transactions_found:
            embed.description = "No transactions found."
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Shop(bot))