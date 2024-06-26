import discord
from discord.ext import commands
from discord import option

class SlowMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    slowmode = discord.SlashCommandGroup(name="slowmode", description="Manage slowmode settings for channels")

    @slowmode.command(name="set", description="Set slowmode for a channel")
    @option("channel", description="The channel to set slowmode for", type=discord.TextChannel)
    @option("time", description="The slowmode duration in seconds", type=int)
    @commands.has_permissions(manage_channels=True)
    async def slowmode_set(self, ctx, channel: discord.TextChannel, time: int):
        try:
            await channel.edit(slowmode_delay=time)
            await ctx.respond(f"Set slowmode for {channel.mention} to {time} seconds.")
        except discord.Forbidden:
            await ctx.respond("I don't have permission to manage channels.")
        except discord.HTTPException as e:
            await ctx.respond(f"Failed to set slowmode: {str(e)}")

    @slowmode.command(name="disable", description="Disable slowmode for a channel")
    @option("channel", description="The channel to disable slowmode for", type=discord.TextChannel)
    @commands.has_permissions(manage_channels=True)
    async def slowmode_disable(self, ctx, channel: discord.TextChannel):
        try:
            await channel.edit(slowmode_delay=0)
            await ctx.respond(f"Disabled slowmode for {channel.mention}.")
        except discord.Forbidden:
            await ctx.respond("I don't have permission to manage channels.")
        except discord.HTTPException as e:
            await ctx.respond(f"Failed to disable slowmode: {str(e)}")

def setup(bot):
    bot.add_cog(SlowMode(bot))