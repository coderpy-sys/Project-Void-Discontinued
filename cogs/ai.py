import discord
from discord.ext import commands
import aiosqlite
from nextchat import NextChat

rsn = NextChat("nextchat_f0l6u16v1zl80lkst3q5lhRq")

class Ai(commands.Cog):
  
  def init(self, bot):
    self.bot = bot
    self.db = aiosqlite.connect("database.db")
    self.cursor = self.db.cursor()
    
  ai = SlashCommandGroup("Ai", "Ai related commands")

  @ai.command(name="setup", description="Set up a ChatBot channel")
  async def setup(self, ctx):
    channel = await ctx.guild.create_text_channel("chatbot")
    async with self.db.execute("INSERT INTO channels (channel_id) VALUES (?)", (channel.id,)) as cursor:
    await self.db.commit()
    await ctx.respond(f"A Channel has been created name <#{channel.id}>")

  @ai.command(name="chat", description="Chat with Chatbot")
  async def chat(self, ctx, message: str):
    reply = await rsn.gemini(message)
    await ctx.respond(reply['message'])

  @commands.cog.listener()
  async def on_message(self, message):
    async with self.db.execute("SELECT channel_id FROM channels") as cursor:
      if message.channel.id in [row[0] for row in await cursor.fetchall()]:
        reply = await rsn.gemini(message.content)
        await message.channel.send(reply['message'])

def setup(bot):
  bot.add_cog(Ai(bot))
