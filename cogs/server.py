import discord
from discord.ext import commands
from discord import SlashCommandGroup
import aiohttp
import json
import os

class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.username_cache = {}
        self.username_cache_file = "./temp/username_cache.json"  # Shared cache file
        self.load_username_cache()

    def load_username_cache(self):
        if os.path.exists(self.username_cache_file):
            with open(self.username_cache_file, 'r') as f:
                self.username_cache = json.load(f)
        else:
            self.username_cache = {}

    def save_username_cache(self):
        with open(self.username_cache_file, 'w') as f:
            json.dump(self.username_cache, f)

    async def fetch_username(self, user_id):
        if user_id in self.username_cache:
            return self.username_cache[user_id]

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://discordlookup.mesalytic.moe/v1/user/{user_id}") as resp:
                if resp.status == 200:
                    user_data = await resp.json()
                    username = user_data.get("username", f"User: {user_id}")
                else:
                    username = f"User: {user_id}"

        self.username_cache[user_id] = username
        self.save_username_cache()
        return username

    server = SlashCommandGroup("server", "Server related commands")

    @server.command(name="info", description="Get server information")
    async def server_info(self, ctx: discord.ApplicationContext):
        guild = ctx.guild
        owner = guild.owner
        owner_username = await self.fetch_username(owner.id)
        members = guild.member_count
        roles = len(guild.roles)
        category_channels = len(guild.categories)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        threads = len(guild.threads)
        boost_count = guild.premium_subscription_count
        boost_tier = guild.premium_tier
        embed = discord.Embed(title=guild.name, color=discord.Color.blue())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Owner", value=owner_username, inline=True)
        embed.add_field(name="Members", value=members, inline=True)
        embed.add_field(name="Roles", value=roles, inline=True)
        embed.add_field(name="Category Channels", value=category_channels, inline=True)
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Threads", value=threads, inline=True)
        embed.add_field(name="Boost Count", value=f"{boost_count} (Tier {boost_tier})", inline=True)
        embed.set_footer(text=f"ID: {guild.id} | Server Created | {guild.created_at.strftime('%m/%d/%Y %I:%M %p')}")
        await ctx.respond(embed=embed)
    
def setup(bot):
    bot.add_cog(Server(bot))