"""Data for a running round and its channel lookup."""

import asyncio
from dataclasses import dataclass, field

import discord


@dataclass
class Game:
    interrogator: discord.Member
    witness: discord.Member
    interrogator_channel: discord.TextChannel
    witness_channel: discord.TextChannel
    # Keep system instructions, user questions, and assistant answers here.
    ai_history: list[dict[str, str]] = field(default_factory=list)
    questions_asked: int = 0
    question_in_flight: bool = False
    answer_in_flight: bool = False
    ai_label: str | None = None
    awaiting_vote: bool = False
    ended: bool = False
    witness_timeout_task: asyncio.Task | None = None
    question_delivery: asyncio.Future[bool] | None = None
    # Channel where /play was run; round results are announced here.
    origin_channel: discord.abc.Messageable | None = None



games_by_channel: dict[int, Game] = {}
