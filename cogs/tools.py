import discord
from discord.ext import commands
import time

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="membercount", description="Displays the member count of the server or a specific role.")
    async def membercount(self, ctx, role: discord.Role = None):
        await ctx.defer()  
        if role:
            members = len(role.members)
            description = f"The role {role.name} has {members} members."
        else:
            members = ctx.guild.member_count
            description = f"This server has {members} members."

        embed = discord.Embed(title="Member Count", description=description, color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)
        
def setup(bot):
    bot.add_cog(Tools(bot))