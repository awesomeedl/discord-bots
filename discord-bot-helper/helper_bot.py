import interactions
from interactions import \
    Button, ButtonStyle, \
    BaseResult, StopCommand, CommandContext, ComponentContext, \
    Channel, ChannelType, \
    Guild, Member
import os

GPT_BOT_NAME = os.getenv('GPT_BOT_NAME')

# Myself
bot = interactions.Client(token=os.getenv('HELPER_BOT_TOKEN'))


confirm = Button(
    style=ButtonStyle.PRIMARY,
    label="Yes",
    custom_id="confirm"
)

deny = Button(
    style=ButtonStyle.SECONDARY,
    label="No",
    custom_id="deny"
)


async def create_gpt_thread(
        guild: Guild,
        member: Member
) -> Channel:
    channels = await guild.get_all_channels()
    gpt_channel = next((c for c in channels if c.name == 'chatgpt'), None)

    if not gpt_channel:
        raise Exception('GPT Channel does not exist!')

    gpt_thread = await gpt_channel.create_thread(
        f'{member.username} - ChatGPT',
        type=ChannelType.PRIVATE_THREAD)

    try:
        gpt_bot = (await guild.search_members(GPT_BOT_NAME))[0]
    except IndexError:
        print(f'GPT Bot not found. \nLooking for: {GPT_BOT_NAME}')

    await gpt_thread.add_member(member)
    await gpt_thread.add_member(gpt_bot)

    return gpt_thread


@bot.component('confirm')
async def reset_chat(component_context: ComponentContext) -> None:
    guild = await component_context.get_guild()
    threads = await guild.get_all_active_threads()
    user = component_context.author

    gpt_thread = next((c for c in threads if c.name == f'{user.username} - ChatGPT'), None)

    if not gpt_thread:
        raise Exception("GPT channel does not exist")

    await gpt_thread.delete()
    gpt_thread = await create_gpt_thread(guild, user)

    await component_context.disable_all_components(content=f"Chat successfully reset {gpt_thread.mention}")



@bot.component('deny')
async def do_nothing(component_context: ComponentContext) -> None:
    await component_context.disable_all_components(content="Ok. If you want to reset the chat, use the command `/chat close`")


@bot.command(name='chat')
async def base_chat(command_context: CommandContext):
    channel = await command_context.get_channel()
    if not channel.name == 'chatgpt':
        await command_context.send(
            "You cannot invoke this command here. Head over to the ChatGPT Channel to use this command!",
            ephemeral=True)
        return StopCommand

    guild = await command_context.get_guild()
    threads = await guild.get_all_active_threads()

    user = command_context.author

    # try to see if there is already an existing thread
    gpt_thread = next((c for c in threads if c.name == f'{user.username} - ChatGPT'), None)

    return {
        'guild': guild,
        'channel': channel,
        'gpt_thread': gpt_thread,
        'user': user
    }


@base_chat.subcommand(
    name='close',
    description='End the current chat with ChatGPT'
)
async def close_chat(command_context: CommandContext, base_res: BaseResult) -> None:
    gpt_thread = base_res.result['gpt_thread']

    if gpt_thread:
        await gpt_thread.delete()
        await command_context.send(
            'Chat successfully deleted',
            ephemeral=True)
    else:
        await command_context.send(
            'I didn\'t find an active chat with ChatGPT',
            ephemeral=True)


@base_chat.subcommand(
    name='new',
    description='Start a new chat with ChatGPT',
)
async def new_chat(command_context: CommandContext, base_res: BaseResult) -> None:
    guild = base_res.result['guild']
    gpt_thread = base_res.result['gpt_thread']
    user = base_res.result['user']

    if gpt_thread:  # thread already exists:
        await command_context.send(
            'There is an existing chat with ChatGPT already. Do you want to delete it and start over?',
            components=interactions.spread_to_rows(confirm, deny),
            ephemeral=True)
    else:
        gpt_thread = await create_gpt_thread(guild, user)

        await command_context.send(
            f'Room created! Enjoy your chat with ChatGPT {gpt_thread.mention}',
            ephemeral=True)

bot.start()
