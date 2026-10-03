import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
  await bot.tree.sync()
  # for development purposes only, to get commadns propogating faster.
  await bot.tree.sync(guild=discord.Object(id=os.getenv("GUILD_ID") or ""))
  print(f"Running, logged in as {bot.user}")

initial_extensions = [
    "cogs.game_commands",
    "cogs.lobby",
    "cogs.relay",
    "cogs.vote",
]

async def main():
    for ext in initial_extensions:
        await bot.load_extension(ext)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

bot.run(os.getenv("DISCORD_TOKEN") or "")
