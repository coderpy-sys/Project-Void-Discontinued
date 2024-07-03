import discord
from discord.ext import commands
import aiosqlite

class WelcomeModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Customize Welcome")
        self.bot = bot

        self.title_input = discord.ui.InputText(label="Title ([guild_name] for server name)", placeholder="Welcome to [guild_name]!", required=False)
        self.add_item(self.title_input)

        self.message_input = discord.ui.InputText(label="Desc ([member_mention] for mention)", style=discord.InputTextStyle.long, placeholder="We are glad to have you, [member_mention]!", required=False)
        self.add_item(self.message_input)

        self.color_input = discord.ui.InputText(label="Embed Color (e.g., #89CFF0)", placeholder="#89CFF0", required=False)
        self.add_item(self.color_input)

        self.server_pic_input = discord.ui.InputText(label="Use server pic (true/false)", placeholder="true", required=False)
        self.add_item(self.server_pic_input)

        self.user_pic_input = discord.ui.InputText(label="Use user pic (true/false)", placeholder="true", required=False)
        self.add_item(self.user_pic_input)

        self.banner_input = discord.ui.InputText(label="Banner URL (optional)", placeholder="https://example.com/banner.jpg", required=False)
        self.add_item(self.banner_input)

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        title = self.title_input.value or "Welcome to [guild_name]!"
        title = title.replace("[guild_name]", interaction.guild.name)
        message = self.message_input.value or "We are glad to have you, [member_mention]!"
        message = message.replace("[member_mention]", "{member.mention}")
        color = self.color_input.value or "#89CFF0"
        use_server_pic = self.server_pic_input.value.lower() == "true" if self.server_pic_input.value else True
        use_user_pic = self.user_pic_input.value.lower() == "true" if self.user_pic_input.value else True
        banner_url = self.banner_input.value

        await self.bot.get_cog("Welcome").set_welcome_config(
            guild_id, 
            message=message, 
            color=color, 
            title=title,
            use_server_pic=use_server_pic, 
            use_user_pic=use_user_pic,
            banner_url=banner_url
        )

        embed = discord.Embed(
            title="Welcome Message Customized",
            description=f"Welcome message customized.\n\nMessage: {message}\nColor: {color}\nTitle: {title}\nUse Server Picture: {use_server_pic}\nUse User Picture: {use_user_pic}\nBanner URL: {banner_url}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        async with aiosqlite.connect("db/database.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS welcome_config (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message TEXT,
                    color TEXT,
                    title TEXT,
                    use_server_pic BOOLEAN,
                    use_user_pic BOOLEAN,
                    banner_url TEXT
                )
            """)
            await db.commit()

    async def get_welcome_config(self, guild_id):
        async with aiosqlite.connect("db/database.db") as db:
            async with db.execute("""
                SELECT channel_id, message, color, title, use_server_pic, use_user_pic, banner_url FROM welcome_config WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                return await cursor.fetchone()

    async def set_welcome_config(self, guild_id, channel_id=None, message=None, color=None, title=None, use_server_pic=None, use_user_pic=None, banner_url=None):
        async with aiosqlite.connect("db/database.db") as db:
            await db.execute("""
                INSERT OR REPLACE INTO welcome_config (guild_id, channel_id, message, color, title, use_server_pic, use_user_pic, banner_url)
                VALUES (
                    ?, 
                    COALESCE(?, (SELECT channel_id FROM welcome_config WHERE guild_id = ?)), 
                    COALESCE(?, (SELECT message FROM welcome_config WHERE guild_id = ?)), 
                    COALESCE(?, (SELECT color FROM welcome_config WHERE guild_id = ?)), 
                    COALESCE(?, (SELECT title FROM welcome_config WHERE guild_id = ?)), 
                    COALESCE(?, (SELECT use_server_pic FROM welcome_config WHERE guild_id = ?)),
                    COALESCE(?, (SELECT use_user_pic FROM welcome_config WHERE guild_id = ?)),
                    COALESCE(?, (SELECT banner_url FROM welcome_config WHERE guild_id = ?))
                )
            """, (guild_id, channel_id, guild_id, message, guild_id, color, guild_id, title, guild_id, use_server_pic, guild_id, use_user_pic, guild_id, banner_url, guild_id))
            await db.commit()

    async def delete_welcome_config(self, guild_id):
        async with aiosqlite.connect("db/database.db") as db:
            await db.execute("""
                DELETE FROM welcome_config WHERE guild_id = ?
            """, (guild_id,))
            await db.commit()

    welcome = discord.SlashCommandGroup(name="welcome", description="Welcome commands")

    @welcome.command(name="set", description="Set the welcome channel for the server")
    @commands.has_permissions(administrator=True)
    async def welcome_set(self, ctx, channel: discord.TextChannel):
        await self.set_welcome_config(ctx.guild.id, channel.id)
        embed = discord.Embed(
            title="Welcome Channel Set",
            description=f"Welcome channel set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @welcome.command(name="disable", description="Disable the welcome channel")
    @commands.has_permissions(administrator=True)
    async def welcome_disable(self, ctx):
        await self.delete_welcome_config(ctx.guild.id)
        embed = discord.Embed(
            title="Welcome System",
            description="Welcome channel disabled.",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed)

    @welcome.command(name="customize", description="Customize the welcome message")
    @commands.has_permissions(administrator=True)
    async def welcome_customize(self, ctx):
        modal = WelcomeModal(self.bot)
        await ctx.send_modal(modal)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = await self.get_welcome_config(member.guild.id)
        if config:
            channel_id, welcome_message, color, title, use_server_pic, use_user_pic, banner_url = config
            channel = member.guild.get_channel(channel_id)
            if channel:
                if not welcome_message:
                    welcome_message = "We are glad to have you, {member.mention}!"
                welcome_message = welcome_message.format(member=member)
                color = color or "#89CFF0"  # Set default color if color is None
                embed = discord.Embed(
                    title=title or f"Welcome to {member.guild.name}!",
                    description=welcome_message,
                    color=discord.Color(int(color.lstrip("#"), 16))
                )
                if use_server_pic:
                    embed.set_thumbnail(url=member.guild.icon.url)
                if use_user_pic:
                    embed.set_image(url=member.avatar.url)
                if banner_url:
                    embed.set_image(url=banner_url)
                await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))