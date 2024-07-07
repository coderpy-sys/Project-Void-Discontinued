import discord
from discord.ext import commands
from discord import SlashCommandGroup

class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    server = SlashCommandGroup("server", "Server related commands")

    @server.command(name="info", description="Get server information")
    async def server_info(self, ctx: discord.ApplicationContext):
        guild = ctx.guild
        owner = guild.owner
        members = guild.member_count
        roles = len(guild.roles)
        category_channels = len(guild.categories)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        threads = len(guild.threads)
        boost_count = guild.premium_subscription_count
        boost_tier = guild.premium_tier
        embed = discord.Embed(title=guild.name, color=discord.Color.blue())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Members", value=members, inline=True)
        embed.add_field(name="Roles", value=roles, inline=True)
        embed.add_field(name="Category Channels", value=category_channels, inline=True)
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Threads", value=threads, inline=True)
        embed.add_field(name="Boost Count", value=f"{boost_count} (Tier {boost_tier})", inline=True)
        embed.set_footer(text=f"ID: {guild.id} | Server Created | {guild.created_at.strftime('%m/%d/%Y %I:%M %p')}")
        await ctx.respond(embed=embed)
    
def setup(bot):
    bot.add_cog(Server(bot))