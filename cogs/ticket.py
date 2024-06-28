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
        elif interaction.type == discord.InteractionType.component and interaction.data['custom_id'].startswith("close_ticket_"):
            await self.handle_close_ticket(interaction)

    async def create_ticket(self, interaction):
        guild_id = interaction.guild.id
        member = interaction.user

        async with aiosqlite.connect("./db/tickets.db") as db:
            table_name = f"user_tickets_{guild_id}"
            async with db.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id = ?", (member.id,)) as cursor:
                count_row = await cursor.fetchone()
                ticket_count = count_row[0] if count_row else 0

            async with db.execute(f"SELECT ticket_channel_id FROM {table_name} WHERE user_id = ?", (member.id,)) as cursor:
                ticket_rows = await cursor.fetchall()
                existing_ticket_channels = [row[0] for row in ticket_rows]

            for ticket_channel_id in existing_ticket_channels:
                ticket_channel = interaction.guild.get_channel(ticket_channel_id)
                if not ticket_channel:
                    await db.execute(f"DELETE FROM {table_name} WHERE ticket_channel_id = ?", (ticket_channel_id,))
                    await db.commit()
                    ticket_count -= 1

            if ticket_count >= self.ticket_settings[guild_id]["ticket_limit"]:
                await interaction.response.send_message(f"You have reached the ticket limit of {self.ticket_settings[guild_id]['ticket_limit']}. Please close an existing ticket before creating a new one.", ephemeral=True)
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
                    await ctx.respond"This is not a ticket channel.", ephemeral=True)
                    return

        button_yes = discord.ui.Button(label="Yes", style=discord.ButtonStyle.danger, custom_id=f"close_ticket_yes_{guild_id}_{channel.id}")
        button_no = discord.ui.Button(label="No", style=discord.ButtonStyle.success, custom_id=f"close_ticket_no_{guild_id}_{channel.id}")

        view = discord.ui.View()
        view.add_item(button_yes)
        view.add_item(button_no)

        await ctx.respond("Are you sure you want to close this ticket?", view=view)

    async def handle_close_ticket(self, interaction):
        custom_id_parts = interaction.data['custom_id'].split("_")
        if len(custom_id_parts) == 5:
            action, _, guild_id, channel_id = custom_id_parts[0], custom_id_parts[1], custom_id_parts[2], custom_id_parts[3:]
            guild_id = int(guild_id)
            channel_id = int(channel_id[0])
            if action == "close" and custom_id_parts[1] == "ticket" and custom_id_parts[2] == "yes":
                if discord.utils.get(interaction.user.roles, name=self.ticket_role) or interaction.user.guild_permissions.administrator:
                    channel = interaction.guild.get_channel(channel_id)
                    await channel.delete()

                    table_name = f"user_tickets_{guild_id}"
                    async with aiosqlite.connect("./db/tickets.db") as db:
                        await db.execute(f"DELETE FROM {table_name} WHERE ticket_channel_id = ?", (channel_id,))
                        await db.commit()

                    await interaction.response.send_message("Ticket closed.", ephemeral=True)
            elif custom_id_parts[2] == "no":
                await interaction.response.send_message("Ticket closure cancelled.", ephemeral=True)

def setup(bot):
    bot.add_cog(TicketSystem(bot))