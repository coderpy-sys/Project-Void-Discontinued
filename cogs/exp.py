import discord
from discord.ext import commands
import aiosqlite

class Exp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_data(self, user_id):
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                "SELECT xp, level FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    xp, level = row
                else:
                    xp, level = 0, 1
                    await db.execute(
                        "INSERT INTO users (id, xp, level) VALUES (?, ?, ?)",
                        (user_id, xp, level)
                    )
                    await db.commit()
                return xp, level

    async def add_experience(self, user_id, xp):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                "INSERT INTO users (id, xp) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET xp = xp + ?",
                (user_id, xp, xp)
            )
            await db.commit()

    exp = discord.SlashCommandGroup(name="exp", description="Experience points commands")

    @exp.command(name="add", description="Add experience points to a user")
    @commands.has_permissions(administrator=True)
    async def add_exp(self, ctx, member: discord.Member, amount: int):
        await ctx.defer()
        await self.add_experience(member.id, amount)
        await ctx.respond(f"Added {amount} XP to {member.mention}")

    @exp.command(name="level", description="Get the level of a user")
    async def get_level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        xp, level = await self.get_user_data(member.id)
        await ctx.respond(f"{member.display_name} is level {level} with {xp} XP")

    @exp.command(name="stats", description="Show your stats")
    async def stats(self, ctx):
        xp, level = await self.get_user_data(ctx.author.id)
        
        embed = discord.Embed(title=f"{ctx.author.display_name}'s Stats", color=discord.Color.blue())
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="XP", value=xp, inline=True)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text="Made by Voidsudo")
        
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Exp(bot))
