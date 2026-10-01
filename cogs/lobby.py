import random
import secrets

import discord
from discord import app_commands
from discord.ext import commands

from game import Game, games_by_channel
from cogs.relay import MAX_QUESTIONS, VOTE_AT
from utils.channels import create_private_channel


class LobbyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.players: set[int] = set()

    @discord.ui.button(label="Join", style=discord.ButtonStyle.primary)
    async def join(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        user_id = interaction.user.id

        if user_id in self.players:
            await interaction.response.send_message(
                "You already joined!",
                ephemeral=True,
            )
            return

        if len(self.players) >= 2:
            await interaction.response.send_message(
                "The lobby is full!",
                ephemeral=True,
            )
            return

        self.players.add(user_id)

        if len(self.players) == 2:
            button.disabled = True
            content = "Lobby is full! Players joined: 2/2"

            # Random suffix instead of the player's Discord ID, so channel names never identify anyone.
            round_id = secrets.token_hex(3)
            players = list(self.players)
            random.shuffle(players)
            interrogator, witness = players

            print(f"interrogator: {interrogator}, witness: {witness}")

            # Acknowledge the button before the channel API calls.
            await interaction.response.edit_message(content=content, view=self)

            # Track channels we create, so a failure halfway can clean them up.
            created = []
            try:
                interrogator_member = await interaction.guild.fetch_member(interrogator)
                witness_member = await interaction.guild.fetch_member(witness)

                interrogator_channel = await create_private_channel(
                    interaction.guild,
                    interrogator_member,
                    f"round-{round_id}-a",
                )
                created.append(interrogator_channel)

                witness_channel = await create_private_channel(
                    interaction.guild,
                    witness_member,
                    f"round-{round_id}-b",
                )
                created.append(witness_channel)

                game = Game(
                    interrogator=interrogator_member,
                    witness=witness_member,
                    interrogator_channel=interrogator_channel,
                    witness_channel=witness_channel,
                    origin_channel=interaction.channel,
                )
                games_by_channel[interrogator_channel.id] = game
                games_by_channel[witness_channel.id] = game

                await interrogator_channel.send(
                    "You are the interrogator. Ask the witness one question at a time "
                    "by typing it here. After the witness replies you will see two "
                    "answers, A and B: one came from a human, one from an AI. "
                    f"After {VOTE_AT} questions you may vote on which was the AI; "
                    f"after {MAX_QUESTIONS} you must vote."
                )
                await witness_channel.send(
                    "You are the witness. The interrogator's questions will appear "
                    "here. Answer each one in your own words, casually, like yourself. "
                    "An AI is answering the same questions and the interrogator is "
                    "trying to tell you apart, so act natural. You have 90 seconds "
                    "per question or the round is cancelled."
                )
            except Exception as exc:
                # Most likely cause: the bot lacks the Manage Channels permission.
                print(f"Round setup failed: {exc!r}")
                for channel in created:
                    games_by_channel.pop(channel.id, None)
                    try:
                        await channel.delete(reason="Round setup failed")
                    except Exception:
                        pass
                await interaction.channel.send(
                    "Could not set up the round. Check that the bot has the "
                    "Manage Channels permission, then run /play again."
                )
                return
        else:
            content = f"Players joined: {len(self.players)}/2"

            await interaction.response.edit_message(
                content=content,
                view=self,
            )

        await interaction.followup.send(
            "You joined the lobby!",
            ephemeral=True,
        )


class LobbyDemo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="Create a lobby")
    async def lobby(self, interaction: discord.Interaction):
        view = LobbyView()

        await interaction.response.send_message(
            "Players joined: 0/2",
            view=view,
        )


async def setup(bot):
    await bot.add_cog(LobbyDemo(bot))