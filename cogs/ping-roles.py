import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup
import aiosqlite

class PingRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_table_if_not_exists(self, guild_id):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS ping_roles_{guild_id} (message_id INTEGER, reaction TEXT, role_id INTEGER)"
            )
            await db.commit()

    pingroles = SlashCommandGroup(name="pingroles", description="Manage ping roles")

    @pingroles.command(name="add", description="Add a reaction role")
    async def add(self, ctx, message_id: str, reaction: str, role: discord.Role):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("You need admin permissions to use this command.", ephemeral=True)

        try:
            message_id = int(message_id)
        except ValueError:
            return await ctx.respond("The message ID must be a valid integer.", ephemeral=True)

        await self.create_table_if_not_exists(ctx.guild.id)

        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"INSERT INTO ping_roles_{ctx.guild.id} (message_id, reaction, role_id) VALUES (?, ?, ?)",
                (message_id, reaction, role.id)
            )
            await db.commit()

        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.add_reaction(reaction)
        except discord.NotFound:
            return await ctx.respond("Message not found. Please ensure the message ID is correct.", ephemeral=True)
        except discord.HTTPException as e:
            return await ctx.respond(f"Failed to add reaction: {str(e)}", ephemeral=True)

        await ctx.respond(f"Added reaction role: {reaction} -> {role.name}", ephemeral=True)

    @pingroles.command(name="remove", description="Remove a reaction role")
    async def remove(self, ctx, message_id: str, reaction: str):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.respond("You need admin permissions to use this command.", ephemeral=True)

        try:
            message_id = int(message_id)
        except ValueError:
            return await ctx.respond("The message ID must be a valid integer.", ephemeral=True)

        await self.create_table_if_not_exists(ctx.guild.id)

        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                f"DELETE FROM ping_roles_{ctx.guild.id} WHERE message_id = ? AND reaction = ?",
                (message_id, reaction)
            )
            await db.commit()

        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.clear_reaction(reaction)
        except discord.NotFound:
            return await ctx.respond("Message not found. Please ensure the message ID is correct.", ephemeral=True)
        except discord.HTTPException as e:
            return await ctx.respond(f"Failed to remove reaction: {str(e)}", ephemeral=True)

        await ctx.respond(f"Removed reaction role: {reaction}", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return

        await self.create_table_if_not_exists(payload.guild_id)

        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                f"SELECT role_id FROM ping_roles_{payload.guild_id} WHERE message_id = ? AND reaction = ?",
                (payload.message_id, str(payload.emoji))
            ) as cursor:
                role_data = await cursor.fetchone()
                if role_data:
                    guild = self.bot.get_guild(payload.guild_id)
                    role = guild.get_role(role_data[0])
                    await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if member.bot:
            return

        await self.create_table_if_not_exists(payload.guild_id)

        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                f"SELECT role_id FROM ping_roles_{payload.guild_id} WHERE message_id = ? AND reaction = ?",
                (payload.message_id, str(payload.emoji))
            ) as cursor:
                role_data = await cursor.fetchone()
                if role_data:
                    role = guild.get_role(role_data[0])
                    await member.remove_roles(role)

def setup(bot):
    bot.add_cog(PingRoles(bot))