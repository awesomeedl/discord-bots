import interactions
import os


# Myself
bot = interactions.Client(token=os.getenv('HELPER_BOT_TOKEN'))

confirm = interactions.Button(
    style=interactions.ButtonStyle.PRIMARY,
    label="Yes",
    custom_id="confirm"
)

deny = interactions.Button(
    style=interactions.ButtonStyle.SECONDARY,
    label="No",
    custom_id="deny"
)


@bot.command(
    name='new_chat',
    description='Start a new chat with ChatGPT',
)
async def new_chat(command_context: interactions.CommandContext) -> None:
    channel = await command_context.get_channel()
    if not channel.name == 'chatgpt':
        await command_context.send(
            "You cannot invoke this command here. Head over to the ChatGPT Channel to use this command!")
        return

    guild = await command_context.get_guild()
    threads = await guild.get_all_active_threads()

    user = command_context.author

    # try to see if there is already an existing thread
    gpt_thread = next((c for c in threads if c.name == f'{user.username} - ChatGPT'), None)

    if gpt_thread: # thread already exists:
        await command_context.send(
            'There is an existing chat with ChatGPT already. Do you want to delete it and start over?',
            components=interactions.spread_to_rows(confirm, deny))
    else:
        gpt_thread = await channel.create_thread(
            f'{user.username} - ChatGPT',
            type=interactions.ChannelType.PRIVATE_THREAD)

        gpt_bot = (await guild.search_members('gpt-bot-dev'))[0]
        await gpt_thread.add_member(user)
        await gpt_thread.add_member(gpt_bot)

        await command_context.send(f'Room created! Enjoy your chat with ChatGPT {gpt_thread.mention}')

bot.start()


