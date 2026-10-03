import discord
from discord.ext import commands

from game import Game


class VoteView(discord.ui.View):
    """Two buttons the interrogator uses to say which answer was the AI."""

    def __init__(self, cog: "Vote", game: Game):
        # timeout=None: the round is ended (and the channel deleted) by
        # end_round, so this view never needs to expire on its own.
        super().__init__(timeout=None)
        self.cog = cog
        self.game = game

    async def cast(self, interaction: discord.Interaction, guess: str):
        game = self.game

        # Only the interrogator may vote, not the witness or anyone else.
        if interaction.user.id != game.interrogator.id:
            await interaction.response.send_message(
                "Only the interrogator can vote.", ephemeral=True
            )
            return

        # If a question is still waiting for answers, voting now would
        # end the round before the interrogator has seen both answers.
        if game.question_in_flight or game.answer_in_flight:
            await interaction.response.send_message(
                "Wait for the answers first.", ephemeral=True
            )
            return

        if game.ended:
            await interaction.response.send_message(
                "This round is already over.", ephemeral=True
            )
            return

        # Respond within Discord's 3 second limit BEFORE the slow work
        # (DMs + channel deletion). Disabling the buttons also stops
        # a double click from voting twice.
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        correct = guess == game.ai_label
        result = (
            f"The interrogator guessed Answer {guess} was the AI. "
            f"The AI was actually Answer {game.ai_label}. "
            + ("The interrogator wins!" if correct else "The AI fooled the interrogator!")
        )

        # end_round (in the Relay cog) removes the game from the lookup,
        # DMs both players, and deletes both private channels.
        relay = self.cog.bot.get_cog("Relay")
        await relay.end_round(game, result)

    @discord.ui.button(label="Answer A is the AI", style=discord.ButtonStyle.primary)
    async def guess_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cast(interaction, "A")

    @discord.ui.button(label="Answer B is the AI", style=discord.ButtonStyle.primary)
    async def guess_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cast(interaction, "B")


class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Relay.request_vote calls bot.dispatch("game_vote_requested", game, forced),
    # which discord.py delivers to a listener named on_game_vote_requested.
    @commands.Cog.listener()
    async def on_game_vote_requested(self, game: Game, forced: bool):
        await game.interrogator_channel.send(
            "Which answer was the AI?", view=VoteView(self, game)
        )


async def setup(bot):
    await bot.add_cog(Vote(bot))
