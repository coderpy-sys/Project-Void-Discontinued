import discord
from discord.ext import commands
import aiohttp
import json

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="membercount", description="Displays the member count of the server or a specific role.")
    async def membercount(self, ctx):
        await ctx.defer()  
        members = ctx.guild.member_count
        description = f"This server has {members} members."
        embed = discord.Embed(title="Member Count", description=description, color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)
        
    @commands.slash_command(name="invite", description="Get the bot invite.")
    async def invite(self, ctx):
        await ctx.defer()  
        description = f"Invite the bot from [here](https://bot.projectvoid.tech)"
        embed = discord.Embed(title="Bot Invite", description=description, color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)
    
    @commands.slash_command(name="user_info", description="Fetch a Discord user and display their details.")
    async def user_info(self, ctx, user_id: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://discordlookup.mesalytic.moe/v1/user/{user_id}") as resp:
                if resp.status == 200:
                    user_data = await resp.json()
                else:
                    await ctx.respond("User not found or an error occurred.")
                    return
        
        username = user_data.get("username", "Unknown")
        created_at = user_data.get("created_at", "Unknown")
        avatar_url = user_data.get("avatar", {}).get("link", "")
        banner_url = user_data.get("banner", {}).get("link", "")
        badges = ", ".join(user_data.get("badges", [])) if user_data.get("badges") else "None"
        
        embed = discord.Embed(title=f"User Info: {username}", color=discord.Color.blue())
        embed.add_field(name="Username", value=username, inline=True)
        embed.add_field(name="Created At", value=created_at, inline=True)
        embed.add_field(name="Badges", value=badges, inline=True)
        
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        if banner_url:
            embed.set_image(url=banner_url)
        
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)
        
def setup(bot):
    bot.add_cog(Tools(bot))