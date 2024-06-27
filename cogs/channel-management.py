import discord
from discord.ext import commands
from discord import option
import asyncio

class ChannelManagement(commands.Cog):
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
    
    #lock system
    @commands.slash_command(name="lock", description="Locks a specified channel for an optional duration.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel, duration: int = None):
        await ctx.defer()

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            embed = discord.Embed(
                title="Channel Already Locked",
                description=f"{channel.mention} is already locked.",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            return await ctx.respond(embed=embed)

        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = discord.Embed(
            title="Channel Locked",
            description=f"{channel.mention} has been locked.",
            color=discord.Color.red()
        )
        if duration:
            embed.add_field(name="Duration", value=f"{duration} seconds", inline=False)
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

        if duration:
            await asyncio.sleep(duration)
            overwrite.send_messages = None
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

            embed = discord.Embed(
                title="Channel Unlocked",
                description=f"{channel.mention} has been unlocked.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await channel.send(embed=embed)

    @commands.slash_command(name="unlock", description="Unlocks a specified channel.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel):
        await ctx.defer()

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is not False:
            embed = discord.Embed(
                title="Channel Already Unlocked",
                description=f"{channel.mention} is already unlocked.",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            return await ctx.respond(embed=embed)

        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = discord.Embed(
            title="Channel Unlocked",
            description=f"{channel.mention} has been unlocked.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)
        
    @commands.slash_command(name="purge", description="Purge command")
    @commands.has_permissions(manage_messages=true)
    async def purge(self, ctx, amount: int):
    	await ctx.defer()
		if amount < 1:
			embed = discord.Embed(title="Invalid Amount", description="You must specify a valid amount of messages to purge.", color=discord.Color.red())
		msg = await ctx.respond(embed=embed, delete_after=5)
		
		return
		
		await ctx.channel.purge(limit=amount)
		embed = discord.Embed(title="Purge Complete", description=f"Purged {amount} messages from {ctx.channel.mention}.", color=discord.Color.green())
		embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
		msg = await ctx.respond(embed=embed, delete_after=5)
    

def setup(bot):
    bot.add_cog(ChannelManagement(bot))
