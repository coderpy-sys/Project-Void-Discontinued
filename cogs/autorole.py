import discord
from discord.ext import commands

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autorole_settings = {}

    autorole = discord.SlashCommandGroup(name="autorole", description="Autorole commands")

    @autorole.command(name="set", description="Set the autorole for the server")
    @commands.has_permissions(administrator=True)
    async def autorole_set(self, ctx, role: discord.Role):
        self.autorole_settings[ctx.guild.id] = role.id
        await ctx.respond(f"Autorole set to {role.mention}")

    @autorole.command(name="disable", description="Disable the autorole")
    @commands.has_permissions(administrator=True)
    async def autorole_disable(self, ctx):
        if ctx.guild.id in self.autorole_settings:
            del self.autorole_settings[ctx.guild.id]
            await ctx.respond("Autorole disabled.")
        else:
            await ctx.respond("No autorole set.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id in self.autorole_settings:
            role_id = self.autorole_settings[member.guild.id]
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)
                await member.send(f"Welcome to {member.guild.name}!")

def setup(bot):
    bot.add_cog(AutoRole(bot))
