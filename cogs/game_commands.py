from os import getenv
from discord import app_commands, Interaction, Embed, Color
from discord.ext import commands
from openrouter import OpenRouter

class GameCommands(commands.Cog):
  def __init__(self, bot):
      self.bot = bot

  @app_commands.command(description="test", name="test")
  async def test(self, interaction: Interaction):
    await interaction.response.defer()
    try:
      async with OpenRouter(api_key=getenv("OPENROUTER_API_KEY"), timeout_ms=60000) as client:
        response = await client.chat.send_async(
          model="openai/gpt-4.1",
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
      embed = Embed(
        title="Hello this is a test embedded message",
        description=response.choices[0].message.content,
        color=Color.green()
      )
    except Exception as e:
      print(f"OpenRouter call failed: {e!r}")
      embed = Embed(title="Error", description="The model didn't respond.", color=Color.red())

    await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GameCommands(bot))

