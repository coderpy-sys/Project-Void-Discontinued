import discord
from discord.ext import commands
import aiosqlite

class Exp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_user_table(self, guild_id):
        table_name = f"users_{guild_id}"
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER, guild_id INTEGER, xp INTEGER, level INTEGER, PRIMARY KEY (id, guild_id))"
            )
            await db.commit()

    async def get_user_data(self, guild_id, user_id):
        await self.create_user_table(guild_id)
        table_name = f"users_{guild_id}"
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                f"SELECT xp, level FROM {table_name} WHERE id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    xp, level = row
                else:
                    xp, level = 0, 1
                    await db.execute(
                        f"INSERT INTO {table_name} (id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
                        (user_id, guild_id, xp, level)
                    )
                    await db.commit()
                return xp, level

    async def add_experience(self, guild_id, user_id, xp):
        await self.create_user_table(guild_id)
        table_name = f"users_{guild_id}"
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                f"SELECT xp FROM {table_name} WHERE id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    current_xp = row[0]
                    new_xp = current_xp + xp
                    await db.execute(
                        f"UPDATE {table_name} SET xp = ? WHERE id = ? AND guild_id = ?",
                        (new_xp, user_id, guild_id)
                    )
                else:
                    await db.execute(
                        f"INSERT INTO {table_name} (id, guild_id, xp) VALUES (?, ?, ?)",
                        (user_id, guild_id, xp)
                    )
            await db.commit()

    exp = discord.SlashCommandGroup(name="exp", description="Experience points commands")

    @exp.command(name="add", description="Add experience points to a user")
    @commands.has_permissions(administrator=True)
    async def add_exp(self, ctx, member: discord.Member, amount: int):
        await ctx.defer()
        await self.add_experience(ctx.guild.id, member.id, amount)
        await ctx.respond(f"Added {amount} XP to {member.mention}")

    @exp.command(name="level", description="Get the level of a user")
    async def get_level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        xp, level = await self.get_user_data(ctx.guild.id, member.id)
        await ctx.respond(f"{member.display_name} is level {level} with {xp} XP")

    @exp.command(name="stats", description="Show your stats")
    async def stats(self, ctx):
        xp, level = await self.get_user_data(ctx.guild.id, ctx.author.id)
        
        embed = discord.Embed(title=f"{ctx.author.display_name}'s Stats", color=discord.Color.blue())
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="XP", value=xp, inline=True)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text="Made by Voidsudo")
        
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Exp(bot))
