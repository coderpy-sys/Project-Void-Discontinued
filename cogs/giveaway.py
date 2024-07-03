import discord
from discord.ext import commands, tasks
import aiosqlite
import datetime
import random

class GiveawayModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.add_item(discord.ui.InputText(label="Duration (e.g., 1s, 1m, 1h, 1d, 1w)"))
        self.add_item(discord.ui.InputText(label="Prize"))
        self.add_item(discord.ui.InputText(label="Number of Winners"))

    async def callback(self, interaction: discord.Interaction):
        try:
            duration_str = self.children[0].value
            prize = self.children[1].value
            num_winners = int(self.children[2].value)

            duration = self.parse_duration(duration_str)
            if not duration:
                await interaction.response.send_message("Invalid duration format. Please use formats like 1s, 1m, 1h, 1d, 1w.", ephemeral=True)
                return

            end_time = int((datetime.datetime.now() + duration).timestamp())
            embed = discord.Embed(
                title="Giveaway",
                description=f"Prize: **{prize}**\nReact with :tada: to enter!\nEnds: <t:{end_time}:R>\nHosted by: {interaction.user.mention}",
                color=discord.Color.blue()
            )
            message = await interaction.channel.send(embed=embed)
            await message.add_reaction("🎉")

            await self.add_giveaway(interaction.guild_id, interaction.channel_id, message.id, prize, end_time, num_winners, interaction.user.id)
            await interaction.response.send_message("Giveaway started!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid input. Please ensure all fields are filled correctly.", ephemeral=True)

    async def add_giveaway(self, guild_id, channel_id, message_id, prize, end_time, num_winners, host_id):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(f"""
                INSERT INTO giveaways_{guild_id} (channel_id, message_id, prize, end_time, num_winners, host_id, participants)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (channel_id, message_id, prize, end_time, num_winners, host_id, ""))
            await db.commit()

    def parse_duration(self, duration_str):
        unit = duration_str[-1]
        if unit not in "smhdw":
            return None

        try:
            value = int(duration_str[:-1])
        except ValueError:
            return None

        if unit == "s":
            return datetime.timedelta(seconds=value)
        elif unit == "m":
            return datetime.timedelta(minutes=value)
        elif unit == "h":
            return datetime.timedelta(hours=value)
        elif unit == "d":
            return datetime.timedelta(days=value)
        elif unit == "w":
            return datetime.timedelta(weeks=value)

        return None

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()
        self.bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.commit()

    async def ensure_guild_table(self, guild_id):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS giveaways_{guild_id} (
                    channel_id INTEGER,
                    message_id INTEGER,
                    prize TEXT,
                    end_time INTEGER,
                    num_winners INTEGER,
                    host_id INTEGER,
                    participants TEXT
                )
            """)
            await db.commit()

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        async with aiosqlite.connect("./db/database.db") as db:
            now = int(datetime.datetime.now().timestamp())
            for guild in self.bot.guilds:
                await self.ensure_guild_table(guild.id)
                async with db.execute(f"SELECT channel_id, message_id, prize, num_winners, participants FROM giveaways_{guild.id} WHERE end_time <= ?", (now,)) as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        channel_id, message_id, prize, num_winners, participants = row
                        guild = self.bot.get_guild(guild.id)
                        channel = guild.get_channel(channel_id)
                        try:
                            message = await channel.fetch_message(message_id)
                            participants = participants.split(',') if participants else []
                            participants = [p for p in participants if int(p) != self.bot.user.id]
                            if participants:
                                winners = random.sample(participants, min(num_winners, len(participants)))
                                winner_mentions = [guild.get_member(int(winner)).mention for winner in winners]
                                await channel.send(f"Congratulations {', '.join(winner_mentions)}! You won the giveaway for **{prize}**! :tada:")
                            else:
                                await channel.send("No participants for the giveaway. :pensive:")
                            await message.delete()
                        except discord.NotFound:
                            pass
                        await db.execute(f"DELETE FROM giveaways_{guild.id} WHERE message_id = ?", (message_id,))
                await db.commit()

    async def add_participant(self, guild_id, message_id, user_id):
        if user_id == self.bot.user.id:
            return
        async with aiosqlite.connect("./db/database.db") as db:
            await self.ensure_guild_table(guild_id)
            async with db.execute(f"SELECT participants FROM giveaways_{guild_id} WHERE message_id = ?", (message_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    participants = row[0].split(',') if row[0] else []
                    if str(user_id) not in participants:
                        participants.append(str(user_id))
                        await db.execute(f"UPDATE giveaways_{guild_id} SET participants = ? WHERE message_id = ?", (','.join(participants), message_id))
                        await db.commit()

    giveaway = discord.SlashCommandGroup(name="giveaway", description="Giveaway commands")

    @giveaway.command(name="setup", description="Setup a giveaway")
    @commands.has_permissions(administrator=True)
    async def giveaway_setup(self, ctx):
        await self.ensure_guild_table(ctx.guild.id)
        modal = GiveawayModal(self.bot, title="Giveaway Setup")
        await ctx.send_modal(modal)

    @giveaway.command(name="end", description="End a giveaway")
    @commands.has_permissions(administrator=True)
    async def giveaway_end(self, ctx, message_id: str):
        try:
            message_id = int(message_id)
            async with aiosqlite.connect("./db/database.db") as db:
                await self.ensure_guild_table(ctx.guild.id)
                await db.execute(f"UPDATE giveaways_{ctx.guild.id} SET end_time = ? WHERE message_id = ?", (int(datetime.datetime.now().timestamp()), message_id))
                await db.commit()
            await ctx.respond("The giveaway will be ended shortly.", ephemeral=True)
        except ValueError:
            await ctx.respond("Invalid message ID. Please provide a valid integer.", ephemeral=True)

    @giveaway.command(name="list", description="List active giveaways")
    async def giveaway_list(self, ctx):
        async with aiosqlite.connect("./db/database.db") as db:
            await self.ensure_guild_table(ctx.guild.id)
            async with db.execute(f"SELECT channel_id, message_id, prize, end_time FROM giveaways_{ctx.guild.id}") as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    return await ctx.respond("There are no active giveaways.", ephemeral=True)

                embed = discord.Embed(title="Active Giveaways", color=discord.Color.blue())
                for row in rows:
                    channel_id, message_id, prize, end_time = row
                    end_time_str = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
                    embed.add_field(name=f"Giveaway in <#{channel_id}>", value=f"Prize: **{prize}**\nEnds: {end_time_str}\n[Message Link](https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id})", inline=False)
                await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "🎉":
            await self.add_participant(payload.guild_id, payload.message_id, payload.user_id)

def setup(bot):
    bot.add_cog(Giveaway(bot))