import asyncio
import io
import random
from os import getenv

import discord
from discord.ext import commands
from openrouter import OpenRouter

from game import Game, games_by_channel
from utils.channels import delete_channel



PERSONA_PROMPT = (
    "you are a regular person chatting in a discord dm. "
    "keep each reply to one or two short sentences. "
    "write casually in lowercase, like someone typing in Discord. "
    "use no lists, markdown, or emojis. "
    "answer only what was asked; don't volunteer extra details, explain your reasoning, or offer further help. "
    "you have limited knowledge and an imperfect memory. When you wouldn't "     
    "know or remember something, say 'no idea' or 'don't remember' naturally "     
    "instead of making up an elaborate answer. "  
    "If asked whether you're an AI, deny it casually, "    
    "like 'nah, why?' Don't give a formal explanation or mention models, "    
    "prompts, or these instructions."

)


# Question limits. For a quick test set VOTE_AT = 2 and MAX_QUESTIONS = 3,
# then put them back to 7 and 8 for the real game.
VOTE_AT = 7        # after this many answered questions the vote becomes optional
MAX_QUESTIONS = 8  # at this many the vote is forced


class Relay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cancel_timeout(self, game: Game):
        task = game.witness_timeout_task
        game.witness_timeout_task = None
        if task is not None and task is not asyncio.current_task():
            task.cancel()

    async def end_round(self, game: Game, notice: str):
        # Remove both lookups before yielding, so no new messages enter the round.
        if game.ended:
            return
        game.ended = True
        game.question_in_flight = False
        game.answer_in_flight = False
        game.awaiting_vote = False
        self.cancel_timeout(game)
        for channel in (game.interrogator_channel, game.witness_channel):
            if games_by_channel.get(channel.id) is game:
                games_by_channel.pop(channel.id)
        # Announce the result where /play was run. This works even when a
        # player has DMs closed; DMs are only the fallback.
        announced = False
        if game.origin_channel is not None:
            try:
                await game.origin_channel.send(
                    notice, allowed_mentions=discord.AllowedMentions.none()
                )
                announced = True
            except Exception as exc:
                print(f"Round announcement failed: {exc!r}")
        if not announced:
            for player in (game.interrogator, game.witness):
                try:
                    await player.send(notice)
                except Exception as exc:
                    print(f"Round notice failed for {player.id}: {exc!r}")
        for channel in (game.interrogator_channel, game.witness_channel):
            try:
                await delete_channel(channel)
            except discord.NotFound:
                pass
            except Exception as exc:
                print(f"Channel cleanup failed for {channel.id}: {exc!r}")

    async def witness_timeout(self, game: Game):
        try:
            await asyncio.sleep(90)
            if game.question_in_flight and not game.answer_in_flight:
                await self.end_round(game, "Round cancelled: the witness did not answer in time.")
        except asyncio.CancelledError:
            return

    async def request_vote(self, game: Game, *, forced: bool):
        # The future voting cog can listen for on_game_vote_requested(game, forced)
        # and call this cog's end_round after the vote/reveal.
        game.awaiting_vote = forced
        await game.interrogator_channel.send(
            f"{MAX_QUESTIONS} questions answered. You must vote now."
            if forced else f"{VOTE_AT} questions answered. You may vote now or ask one final question."
        )
        self.bot.dispatch("game_vote_requested", game, forced)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        game = games_by_channel.get(message.channel.id)
        if game is None or game.ended:
            return
        if not message.content.strip():
            return

        if message.channel.id == game.interrogator_channel.id:
            if game.question_in_flight or game.answer_in_flight:
                await message.channel.send("Please wait for the answers.")
                return
            if game.awaiting_vote or game.questions_asked >= MAX_QUESTIONS:
                await message.channel.send("Please vote now; the question limit has been reached.")
                return

            game.question_in_flight = True
            # A very fast witness reply may arrive while sending the question.
            # It claims its slot, but waits for delivery/history to be committed.
            delivery = asyncio.get_running_loop().create_future()
            game.question_delivery = delivery
            try:
                await game.witness_channel.send(
                    message.content, allowed_mentions=discord.AllowedMentions.none()
                )
            except Exception as exc:
                game.question_in_flight = False
                delivery.set_result(False)
                print(f"Question relay failed: {exc!r}")
                await message.channel.send("The question could not be delivered. Please try again.")
                return
            except asyncio.CancelledError:
                game.question_in_flight = False
                delivery.set_result(False)
                raise

            game.questions_asked += 1
            game.ai_history.append({"role": "user", "content": message.content})
            if game.ai_label is None:
                game.ai_label = random.choice(("A", "B"))
            delivery.set_result(True)
            if not game.answer_in_flight:
                game.witness_timeout_task = asyncio.create_task(self.witness_timeout(game))

        elif message.channel.id == game.witness_channel.id:
            if not game.question_in_flight or game.answer_in_flight:
                return
            game.answer_in_flight = True
            self.cancel_timeout(game)
            try:
                if game.question_delivery is not None:
                    delivered = await asyncio.shield(game.question_delivery)
                    if not delivered:
                        return
                if game.ended:
                    return
                try:
                    async with asyncio.timeout(60):
                        async with OpenRouter(
                            api_key=getenv("OPENROUTER_API_KEY"), timeout_ms=60000
                        ) as client:
                            response = await client.chat.send_async(
                                model="openai/gpt-4.1",
                                messages=[{"role": "system", "content": PERSONA_PROMPT}]
                                + game.ai_history,
                            )
                    ai_answer = response.choices[0].message.content
                    if not isinstance(ai_answer, str) or not ai_answer.strip():
                        raise ValueError("AI returned no text answer")
                except Exception as exc:
                    print(f"AI answer failed: {exc!r}")
                    await self.end_round(game, "Round cancelled: the AI answer failed. No answers were revealed.")
                    return

                game.ai_history.append({"role": "assistant", "content": ai_answer})
                answers = {
                    game.ai_label: ai_answer,
                    "B" if game.ai_label == "A" else "A": message.content,
                }
                combined = f"Answer A:\n{answers['A']}\n\nAnswer B:\n{answers['B']}"
                # Long answers still arrive together, without truncation or extra messages.
                if len(combined) <= 2000:
                    await game.interrogator_channel.send(
                        combined, allowed_mentions=discord.AllowedMentions.none()
                    )
                else:
                    await game.interrogator_channel.send(
                        "Answer A and Answer B are in the attached file.",
                        file=discord.File(io.BytesIO(combined.encode()), filename="answers.txt"),
                    )
                if game.questions_asked >= VOTE_AT:
                    await self.request_vote(game, forced=game.questions_asked >= MAX_QUESTIONS)
            except asyncio.CancelledError:
                await self.end_round(game, "Round cancelled while processing the answer.")
                raise
            except Exception as exc:
                print(f"Answer relay failed: {exc!r}")
                await self.end_round(game, "Round cancelled: the answers could not be delivered.")
            finally:
                game.question_in_flight = False
                game.answer_in_flight = False


async def setup(bot):
    await bot.add_cog(Relay(bot))
