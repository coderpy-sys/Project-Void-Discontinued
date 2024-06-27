import discord
from discord.ext import commands
import aiosqlite

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    afk = discord.SlashCommandGroup(name="afk", description="Set your AFK status")

    async def create_afk_table(self, guild_id):
        table_name = f"afk_{guild_id}"
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (user_id INTEGER PRIMARY KEY, reason TEXT)"
            )
            await db.commit()

    @afk.command(name="set", description="Set your AFK status")
    async def afk_set(self, ctx, *, reason: str):
        await self.create_afk_table(ctx.guild.id)
        table_name = f"afk_{ctx.guild.id}"
        async with aiosqlite.connect("./db/database.db") as db:
            # Check if user is already AFK in guild
            async with db.execute(
                f"SELECT reason FROM {table_name} WHERE user_id = ?",
                (ctx.author.id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return await ctx.respond("You are already AFK in this server.")

            # Set user as AFK
            await db.execute(
                f"INSERT INTO {table_name} (user_id, reason) VALUES (?, ?)",
                (ctx.author.id, reason),
            )
            await db.commit()

            # Create an embed response
            embed = discord.Embed(
                title="AFK Status Set",
                description=f"Set your AFK status to: {reason}",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Made by Voidsudo")

            await ctx.respond(embed=embed, delete_after=5)

    @afk.command(name="clearall", description="Clear all AFK statuses (Admin only)")
    @commands.has_permissions(administrator=True)
    async def afk_clearall(self, ctx):
        table_name = f"afk_{ctx.guild.id}"
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(f"DROP TABLE IF EXISTS {table_name}")
            await db.commit()

        await ctx.respond("Cleared all AFK statuses for this server.", delete_after=5)


def setup(bot):
    bot.add_cog(AFK(bot))
