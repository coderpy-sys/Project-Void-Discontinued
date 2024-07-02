import discord
from discord.ext import commands
import aiosqlite

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_table_if_not_exists(self):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS inventory (user_id INTEGER, product_name TEXT, owner_id INTEGER)"
            )
            await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_table_if_not_exists()

    inventory = discord.SlashCommandGroup(name="inventory", description="Manage your inventory")

    @inventory.command(name="list", description="List your inventory")
    async def list_inventory(self, ctx):
        await self.create_table_if_not_exists()
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                "SELECT product_name FROM inventory WHERE user_id = ?", (ctx.author.id,)
            ) as cursor:
                items = await cursor.fetchall()
                if not items:
                    return await ctx.respond("Your inventory is empty.", ephemeral=True)
                
                embed = discord.Embed(title="Your Inventory", color=discord.Color.blue())
                for item in items:
                    embed.add_field(name="product_name", value=item[0], inline=False)
                await ctx.respond(embed=embed, ephemeral=True)

    @inventory.command(name="remove", description="Remove an item from your inventory")
    async def remove_inventory(self, ctx, product_name: str):
        await self.create_table_if_not_exists()
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                "SELECT owner_id FROM inventory WHERE user_id = ? AND product_name = ?", (ctx.author.id, product_name)
            ) as cursor:
                item = await cursor.fetchone()
                if not item:
                    return await ctx.respond("You don't own this item.", ephemeral=True)

                class ConfirmRemove(discord.ui.View):
                    def __init__(self, ctx, product_name):
                        super().__init__(timeout=60)
                        self.ctx = ctx
                        self.product_name = product_name

                    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
                    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
                        if interaction.user != self.ctx.author:
                            await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
                            return
                        async with aiosqlite.connect("./db/database.db") as db:
                            await db.execute(
                                "DELETE FROM inventory WHERE user_id = ? AND product_name = ?",
                                (self.ctx.author.id, self.product_name)
                            )
                            await db.commit()
                        await interaction.response.send_message(f"Removed {self.product_name} from your inventory.", ephemeral=True)
                        self.stop()

                    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
                    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
                        if interaction.user != self.ctx.author:
                            await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
                            return
                        await interaction.response.send_message("Cancelled the removal.", ephemeral=True)
                        self.stop()

                view = ConfirmRemove(ctx, product_name)
                await ctx.respond(f"Are you sure you want to remove {product_name} from your inventory?", view=view, ephemeral=True)

    @inventory.command(name="transfer", description="Transfer an item to another user")
    async def transfer_inventory(self, ctx, product_name: str, member: discord.Member):
        await self.create_table_if_not_exists()
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute(
                "SELECT owner_id FROM inventory WHERE user_id = ? AND product_name = ?", (ctx.author.id, product_name)
            ) as cursor:
                item = await cursor.fetchone()
                if not item:
                    return await ctx.respond("You don't own this item.", ephemeral=True)

            await db.execute(
                "UPDATE inventory SET user_id = ? WHERE user_id = ? AND product_name = ?",
                (member.id, ctx.author.id, product_name)
            )
            await db.commit()
        await ctx.respond(f"Transferred {product_name} to {member.display_name}.", ephemeral=True)

def setup(bot):
    bot.add_cog(Inventory(bot))
