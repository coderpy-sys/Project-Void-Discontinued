import discord
from discord.ext import commands
import time

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel = {}
        self.welcome_messages = {} 

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

    welcome = discord.SlashCommandGroup(name="welcome", description="Welcome commands")

    @welcome.command(name="set", description="Set the welcome channel for the server")
    @commands.has_permissions(administrator=True)
    async def welcome_set(self, ctx, channel: discord.TextChannel):
        self.welcome_channel[ctx.guild.id] = channel.id
        await ctx.respond(f"Welcome channel set to {channel.mention}")

    @welcome.command(name="disable", description="Disable the welcome channel")
    @commands.has_permissions(administrator=True)
    async def welcome_disable(self, ctx):
        if ctx.guild.id in self.welcome_channel:
            del self.welcome_channel[ctx.guild.id]
            await ctx.respond("Welcome channel disabled.")
        else:
            await ctx.respond("No welcome channel set.")

    @welcome.command(name="customize", description="Customize the welcome message")
    @commands.has_permissions(administrator=True)
    async def welcome_customize(self, ctx, *, message: str):
        self.welcome_messages[ctx.guild.id] = message
        await ctx.respond("Welcome message customized.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id in self.welcome_channel:
            channel_id = self.welcome_channel[member.guild.id]
            channel = member.guild.get_channel(channel_id)
            if channel:
                welcome_message = self.welcome_messages.get(member.guild.id, f"We are glad to have you, {member.mention}!")
                embed = discord.Embed(
                    title=f"Welcome to {member.guild.name}!",
                    description=welcome_message,
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.guild.icon.url)
                await channel.send(embed=embed)

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
    bot.add_cog(Tools(bot))
