from os import getenv
from discord import app_commands, Interaction, Embed, Color
from discord.colour import Color 
from discord.ext import commands
from openrouter import OpenRouter

OPENROUTER_API = "https://openrouter.ai/api/v1"

class GameCommands(commands.Cog):
  def __init__(self, bot):
      self.bot = bot

  @app_commands.command(description="test", name="test")
  async def test(self, interaction: Interaction):
    await interaction.response.defer()
    with OpenRouter(api_key=getenv("OPENROUTER_API_KEY")) as client:
      response = client.chat.send(
        model="nvidia/nemotron-3.5-lightning:free",
        messages=[
          {
            "role": "system",
            "content": "You are an undercover mafia underling working for a dangerous man named Don Parmesean. You are playing the part of an underling underling DO NOT BREAK CHARACTER."
          },
          {
            "role": "user",
            "content": "Hello, I am testing your connectivity. How do you copy?"
          }
        ]
      )

      title = "Hello this is a test embedded message"
      description = response.choices[0].message.content

      color = Color.green()
      embed = Embed(
        title=title,
        description=description,
        color=color
      )

      await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GameCommands(bot))

