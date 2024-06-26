import discord
from discord.ext import commands
import time


class misc(commands.Cog):
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

    @discord.slash_command(name="invite", description="Get the bot's invite")
    async def invite(self, ctx):
        embed = discord.Embed(
            title="Bot Invite",
            description=f"Invite the bot: [here](https://discord.com/oauth2/authorize?client_id=1255047241786200065)",
            color=0x4863A0,
        )
        embed.set_footer(text=f"Made by Voidsudo")
        await ctx.respond(embed=embed)

    @discord.slash_command(name="about", description="See the bot's contributors")
    async def about(self, ctx):
        embed = discord.Embed(
            title="Bot Contributors",
            color=0x4863A0,
        )
        embed.add_field(name="Voidsudo", value="Main Developer", inline=False)
        embed.add_field(name="Vienne", value="Contributor", inline=False)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text="Made by Voidsudo")
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(misc(bot))
