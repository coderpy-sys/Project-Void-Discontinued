import discord
from discord.ext import commands
import aiosqlite

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_table_if_not_exists(self, guild_id):
        async with aiosqlite.connect("db/configs.db") as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS autorole_{guild_id} (role_id INTEGER)"
            )
            await db.commit()

    async def delete_table_if_exists(self, guild_id):
        async with aiosqlite.connect("db/configs.db") as db:
            await db.execute(
                f"DROP TABLE IF EXISTS autorole_{guild_id}"
            )
            await db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with aiosqlite.connect("db/configs.db") as db:
            async with db.execute(
                f"SELECT role_id FROM autorole_{member.guild.id}"
            ) as cursor:
                role_ids = await cursor.fetchall()
                for role_id in role_ids:
                    role = member.guild.get_role(role_id[0])
                    if role:
                        await member.add_roles(role)

    autorole = discord.SlashCommandGroup(name="autorole", description="Autorole commands")

    @autorole.command(name="set", description="Set the autorole for new members")
    @commands.has_permissions(administrator=True)
    async def set_autorole(self, ctx, role: discord.Role):
        await self.create_table_if_not_exists(ctx.guild.id)
        async with aiosqlite.connect("db/configs.db") as db:
            await db.execute(
                f"INSERT INTO autorole_{ctx.guild.id} (role_id) VALUES (?)",
                (role.id,)
            )
            await db.commit()
        embed = discord.Embed(
            title="Autorole Set",
            description=f"Autorole {role.mention} has been set.",
            color=discord.Color.blue(),
        )
        await ctx.respond(embed=embed)

    @autorole.command(name="disable", description="Disable the autorole for new members")
    @commands.has_permissions(administrator=True)
    async def disable_autorole(self, ctx):
        await self.delete_table_if_exists(ctx.guild.id)
        embed = discord.Embed(
            title="Autorole Disabled",
            description=f"Autorole has been disabled for this server.",
            color=discord.Color.blue(),
        )
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(AutoRole(bot))