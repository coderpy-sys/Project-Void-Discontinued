import discord
from discord.ext import commands

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="membercount", description="Displays the member count of the server or a specific role.")
    async def membercount(self, ctx):
        await ctx.defer()
        members = ctx.guild.member_count
        description = f"This server has {members} members."
        embed = discord.Embed(title="Member Count", description=description, color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else "https://i.postimg.cc/fLQ8T6F6/NO-USER.png")
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else "https://i.postimg.cc/fLQ8T6F6/NO-USER.png")
        await ctx.respond(embed=embed)
        
    @commands.slash_command(name="invite", description="Get the bot invite.")
    async def invite(self, ctx):
        await ctx.defer()
        description = f"Invite the bot from [here](https://bot.projectvoid.tech)"
        embed = discord.Embed(title="Bot Invite", description=description, color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else "https://i.postimg.cc/fLQ8T6F6/NO-USER.png")
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else "https://i.postimg.cc/fLQ8T6F6/NO-USER.png")
        await ctx.respond(embed=embed)
        
def setup(bot):
    bot.add_cog(Tools(bot))