import discord
from discord.ext import commands
import aiosqlite

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_settings = {}  # {guild_id: settings}
        self.ticket_role = "ticket-perm"

    @commands.Cog.listener()
    async def on_ready(self):
        await self.initialize_db()
        await self.load_existing_tickets()

    async def initialize_db(self):
        async with aiosqlite.connect("./db/tickets.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    category_id INTEGER,
                    server_icon INTEGER,
                    ticket_limit INTEGER DEFAULT 1,
                    embed_title TEXT DEFAULT 'Ticket System',
                    embed_description TEXT DEFAULT 'Click the button below to create a new ticket.'
                )
            """)
            await db.commit()

    async def load_existing_tickets(self):
        async with aiosqlite.connect("./db/tickets.db") as db:
            async with db.execute("SELECT guild_id, channel_id, category_id, server_icon, ticket_limit, embed_title, embed_description FROM ticket_settings") as cursor:
                async for row in cursor:
                    guild_id, channel_id, category_id, server_icon, ticket_limit, embed_title, embed_description = row
                    self.ticket_settings[guild_id] = {
                        "channel_id": channel_id,
                        "category_id": category_id,
                        "server_icon": server_icon,
                        "ticket_limit": ticket_limit,
                        "embed_title": embed_title,
                        "embed_description": embed_description
                    }
                    await self.create_guild_ticket_table(guild_id)

    async def create_guild_ticket_table(self, guild_id):
        table_name = f"user_tickets_{guild_id}"
        async with aiosqlite.connect("./db/tickets.db") as db:
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    user_id INTEGER,
                    ticket_channel_id INTEGER,
                    PRIMARY KEY (user_id, ticket_channel_id)
                )
            """)
            await db.commit()

    ticket = discord.SlashCommandGroup(name="ticket", description="Ticket system commands")

    def is_ticket_permitted():
        async def predicate(ctx):
            if ctx.author.guild_permissions.administrator:
                return True
            role = discord.utils.get(ctx.guild.roles, name="ticket-perm")
            return role in ctx.author.roles
        return commands.check(predicate)

    @ticket.command(name="setup", description="Set up the ticket system")
    @commands.has_permissions(administrator=True)
    @is_ticket_permitted()
    async def ticket_setup(self, ctx, channel: discord.TextChannel, category: discord.CategoryChannel, server_icon: bool, ticket_limit: int = 1, embed_title: str = "Ticket System", embed_description: str = "Click the button below to create a new ticket."):
        guild_id = ctx.guild.id
        self.ticket_settings[guild_id] = {
            "channel_id": channel.id,
            "category_id": category.id,
            "server_icon": server_icon,
            "ticket_limit": ticket_limit,
            "embed_title": embed_title,
            "embed_description": embed_description
        }
        await self.create_guild_ticket_table(guild_id)

        # Create the ticket-perm role if it doesn't exist
        role = discord.utils.get(ctx.guild.roles, name=self.ticket_role)
        if not role:
            role = await ctx.guild.create_role(name=self.ticket_role)

        async with aiosqlite.connect("./db/tickets.db") as db:
            await db.execute("""
                INSERT OR REPLACE INTO ticket_settings (guild_id, channel_id, category_id, server_icon, ticket_limit, embed_title, embed_description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, channel.id, category.id, int(server_icon), ticket_limit, embed_title, embed_description))
            await db.commit()

        # Create the ticket embed message with a button
        embed = discord.Embed(
            title=embed_title,
            description=embed_description,
            color=discord.Color.blue()
        )
        if server_icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        button = discord.ui.Button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id=f"create_ticket_{guild_id}")

        view = discord.ui.View()
        view.add_item(button)

        await channel.send(embed=embed, view=view)

        # Confirmation embed
        confirm_embed = discord.Embed(
            title="Ticket System Setup",
            description=f"Ticket system set up in {channel.mention} under {category.name}",
            color=discord.Color.green()
        )
        confirm_embed.set_footer(text="Made by Voidsudo")

        await ctx.respond(embed=confirm_embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component and interaction.data['custom_id'].startswith("create_ticket_"):
            await self.create_ticket(interaction)

    async def create_ticket(self, interaction):
        guild_id = interaction.guild.id
        member = interaction.user

        async with aiosqlite.connect("./db/tickets.db") as db:
            async with db.execute("SELECT ticket_limit FROM ticket_settings WHERE guild_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                ticket_limit = row[0] if row else 1

            table_name = f"user_tickets_{guild_id}"
            async with db.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id = ?", (member.id,)) as cursor:
                count_row = await cursor.fetchone()
                ticket_count = count_row[0] if count_row else 0

            if ticket_count >= ticket_limit:
                await interaction.response.send_message(f"You have reached the ticket limit of {ticket_limit}. Please close an existing ticket before creating a new one.", ephemeral=True)
                return

        category_id = self.ticket_settings[guild_id]["category_id"]
        category = interaction.guild.get_channel(category_id)
        if not category:
            await interaction.response.send_message("Category not found!", ephemeral=True)
            return

        # Create ticket channel
        channel_name = f"ticket-{member.name}".replace(" ", "-")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True),
            discord.utils.get(interaction.guild.roles, name=self.ticket_role): discord.PermissionOverwrite(read_messages=True)
        }
        ticket_channel = await interaction.guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title="Ticket Created",
            description=f"Please wait for someone to claim this ticket, {member.mention}.",
            color=discord.Color.blue()
        )
        await ticket_channel.send(embed=embed)

        async with aiosqlite.connect("./db/tickets.db") as db:
            await db.execute(f"INSERT INTO {table_name} (user_id, ticket_channel_id) VALUES (?, ?)", (member.id, ticket_channel.id))
            await db.commit()

        await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)

    @ticket.command(name="close", description="Close a ticket")
    @commands.has_permissions(manage_channels=True)
    @is_ticket_permitted()
    async def close_ticket(self, ctx):
        channel = ctx.channel
        guild_id = ctx.guild.id

        async with aiosqlite.connect("./db/tickets.db") as db:
            async with db.execute("SELECT category_id FROM ticket_settings WHERE guild_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                if not row or channel.category_id != row[0]:
                    await ctx.respond("This is not a ticket channel.", ephemeral=True)
                    return

        await ctx.respond("Are you sure you want to close this ticket? (yes/no)")

        def check(m):
            return m.author == ctx.author and m.content.lower() in ["yes", "no"]

        msg = await self.bot.wait_for("message", check=check)
        if msg.content.lower() == "yes":
            await channel.delete()

            table_name = f"user_tickets_{guild_id}"
            async with aiosqlite.connect("./db/tickets.db") as db:
                await db.execute(f"DELETE FROM {table_name} WHERE ticket_channel_id = ?", (channel.id,))
                await db.commit()
        else:
            await ctx.respond("Ticket closure canceled.")

    @ticket.command(name="closeall", description="Close all open tickets")
    @commands.has_permissions(administrator=True)
    @is_ticket_permitted()
    async def close_all_tickets(self, ctx):
        guild_id = ctx.guild.id
        table_name = f"user_tickets_{guild_id}"

        async with aiosqlite.connect("./db/tickets.db") as db:
            async with db.execute(f"SELECT ticket_channel_id FROM {table_name}") as cursor:
                ticket_channels = await cursor.fetchall()

        for ticket_channel_id in ticket_channels:
            ticket_channel = ctx.guild.get_channel(ticket_channel_id[0])
            if ticket_channel:
                await ticket_channel.delete()

        async with aiosqlite.connect("./db/tickets.db") as db:
            await db.execute(f"DELETE FROM {table_name}")
            await db.commit()

        await ctx.respond("All tickets have been closed.")

def setup(bot):
    bot.add_cog(TicketSystem(bot))