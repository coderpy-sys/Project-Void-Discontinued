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
                color=discord.Color.green()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed, delete_after=5)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to delete messages.")
        except discord.HTTPException as e:
            await ctx.respond(f"Failed to delete messages: {str(e)}")
        except discord.NotFound:
            pass  # Ignore NotFound errors silently

def setup(bot):
    bot.add_cog(ChannelManagement(bot))