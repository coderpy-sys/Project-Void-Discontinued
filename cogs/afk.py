import discord
from discord.ext import commands
import aiosqlite


class afk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    afk = discord.SlashCommandGroup(name="afk", description="Set your AFK status")

    @afk.command(name="set", description="Set your AFK status")
    async def afk_set(self, ctx, *, reason: str):
        async with aiosqlite.connect("./db/database.db") as db:
            # check if user is already afk in guild
            async with db.execute(
                "SELECT reason FROM afk WHERE user_id = ? AND guild_id = ?",
                (ctx.author.id, ctx.guild.id),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return await ctx.respond("You are already AFK in this server.")
            await db.execute(
                "INSERT INTO afk (user_id, guild_id, reason) VALUES (?, ?, ?)",
                (ctx.author.id, ctx.guild.id, reason),
            )
            await db.commit()
            await ctx.respond(f"Set your AFK status to: {reason}")


def setup(bot):
    bot.add_cog(afk(bot))
