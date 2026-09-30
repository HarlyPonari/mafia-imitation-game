import discord


async def create_private_channel(
    guild: discord.Guild,
    member: discord.Member,
    name: str,
    category: discord.CategoryChannel | None = None,
) -> discord.TextChannel:
    """Create a text channel that only `member` and the bot can see."""
    overwrites = {
        # @everyone: can't even see the channel
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        # the bot itself
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True,
        ),
        # the one player allowed in
        member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        ),
    }
    return await guild.create_text_channel(
        name=name,
        overwrites=overwrites,
        category=category,
        reason="Imitation game round",
    )


async def delete_channel(channel: discord.TextChannel) -> None:
    await channel.delete(reason="Round finished")