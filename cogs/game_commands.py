from discord import app_commands, Interaction, Embed, Color
from discord.colour import Color 
from discord.ext import commands

class GameCommands(commands.Cog):
  def __init__(self, bot):
      self.bot = bot

  @app_commands.command(description="test", name="test")
  async def test(self, interaction: Interaction):
    title = "Hello this is a test embedded message"
    description = "A test message."
    color = Color.green()
    embed = Embed(
      title=title,
      description=description,
      color=color
    )

    await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GameCommands(bot))

