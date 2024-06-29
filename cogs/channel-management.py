import discord
from discord.ext import commands
from discord import option

class ChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="purge", description="Delete a specified number of messages in the channel.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, message_count: int):
        await ctx.defer()

        if message_count <= 0:
            return await ctx.respond("Please provide a positive number of messages to delete.")

        try:
            deleted = await ctx.channel.purge(limit=message_count + 1)  # Including the command message itself
            embed = discord.Embed(
                title="Purge Successful",
                description=f"Deleted {len(deleted)} messages in {ctx.channel.mention}.",
                color=0x4863A0
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed, delete_after=5)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await ctx.respond(f"Failed to delete messages: {str(e)}")
        except discord.NotFound:
            pass  # Ignore NotFound errors silently

    # sigma moment
    @commands.slash_command(name="lock", description="Lock the channel.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.defer()

        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            embed = discord.Embed(
                title="Channel Locked",
                description=f"{ctx.channel.mention} has been locked.",
                color=0x4863A0
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to lock the channel.")
        except discord.HTTPException as e:
            await ctx.respond(f"Failed to lock the channel: {str(e)}")

    @lock.error
    async def lock_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to lock channels.")

    @commands.slash_command(name="unlock", description="Unlock the channel.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.defer()

        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
            embed = discord.Embed(
                title="Channel Unlocked",
                description=f"{ctx.channel.mention} has been unlocked.",
                color=0x4863A0
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to unlock the channel.")
        except discord.HTTPException as e:
            await ctx.respond(f"Failed to unlock the channel: {str(e)}")

    @unlock.error
    async def unlock_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to unlock channels.")
        

def setup(bot):
    bot.add_cog(ChannelManagement(bot))