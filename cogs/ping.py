import discord
from discord.ext import commands
import time


class status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    @discord.slash_command(name="ping", description="Get the bot's latency")
    async def ping(self, ctx):
        embed = discord.Embed(
            title="Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms",
            color=0x4863A0,
        )
        embed.set_footer(text=f"Made by Voidsudo")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(status(bot))