import discord
from discord.ext import commands

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel = {}

    @commands.slash_command(name="membercount", description="Displays the member count of the server.")
    async def membercount(self, ctx):
        members = ctx.guild.member_count
        embed = discord.Embed(title="Member Count", description=f"This server has {members} members.", color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

    welcome = discord.SlashCommandGroup(name="welcome", description="Welcome commands")

    @welcome.command(name="set", description="Set the welcome channel for the server")
    async def welcome_set(self, ctx, channel: discord.TextChannel):
        self.welcome_channel[ctx.guild.id] = channel.id
        await ctx.respond(f"Welcome channel set to {channel.mention}")

    @welcome.command(name="disable", description="Disable the welcome channel")
    async def welcome_disable(self, ctx):
        if ctx.guild.id in self.welcome_channel:
            del self.welcome_channel[ctx.guild.id]
            await ctx.respond("Welcome channel disabled.")
        else:
            await ctx.respond("No welcome channel set.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id in self.welcome_channel:
            channel_id = self.welcome_channel[member.guild.id]
            channel = member.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title=f"Welcome to {member.guild.name}!",
                    description=f"We are glad to have you, {member.mention}!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.guild.icon.url)
                await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Tools(bot))
