import discord
from discord.ext import commands
import sqlite3
from rsnchat import RsnChat

rsn = RsnChat("rsnai_1MQfpO7qhSEvxVdb54sQMnnH")
class GPT4(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot
    self.db = sqlite3.connect("database.db")
    self.cursor = self.db.cursor()
    self.chatgpt = ChatGPT()

  ai = SlashCommandGroup("Ai", "Ai related commands")

  @ai.command(name="setup", description="Set up a ChatBot channel")
  async def setup(self, ctx):
    channel = await ctx.guild.create_text_channel("chatbot")
    self.cursor.execute("INSERT INTO channels (channel_id) VALUES (?)", (channel.id,))
    self.db.commit()
    await ctx.respond(f"A Channel has been created name <#{channel_id}>")

  @ai.command(name="chat", description="Chat with Chatbot")
  async def chat(self, ctx, message: str):
    reply = await rsn.gpt(message)
    await ctx.respond(reply['message'])

  @commands.cog.listener()
  async def on_message(self, message):
    if message.channel.id in self.cursor.execute("SELECT channel_id FROM channels").fetchall():
      reply = rsn.gpt(message.content)
      await message.channel.send(response)

def setup(bot):
  bot.add_cog(Ai(bot))
