import os
import interactions
from interactions import Button, ButtonStyle, \
    BaseResult, StopCommand, CommandContext, ComponentContext, \
    Guild, Member,\
    Channel, ChannelType, Message, MessageType
import response_handler

max_past_conversation = 10

# Myself
bot = interactions.Client(token=os.getenv("GPT_BOT_TOKEN"))


async def get_message_history(channel: Channel) -> list[dict[str, str]]:
    message_history = []

    async for message in channel.history(
            maximum=max_past_conversation,
            check=lambda m: m.type in {MessageType.DEFAULT, MessageType.REPLY}):
        role = "assistant" if message.author == await bot.get_self_user() else "user"
        message_history.append({"role": role, "content": message.content})

    return list(reversed(message_history))






async def send_reply(channel: Channel, message: Message) -> None:
    try:
        async with channel.typing:
            message_history = await get_message_history(channel)

            response = await response_handler.handle_response(message.content, message_history)

            for chunk in response:
                await message.reply(chunk)

    except Exception as e:
        await message.reply(f"Something went wrong, please try again.\n\n>>> {e}")


@bot.event()
async def on_message_create(message: Message):
    channel = await message.get_channel()

    # Don't respond to system messages
    if message.type not in {MessageType.DEFAULT, MessageType.REPLY}:
        return

    # Only respond in private threads
    if channel.type != ChannelType.PRIVATE_THREAD:
        return

    # Don't respond to myself
    if message.author == await bot.get_self_user():
        return

    await send_reply(channel, message)

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

new_chat_btn = Button(
    style=ButtonStyle.SUCCESS,
    label="New Chat",
    custom_id="new_chat_btn"
)

close_chat_btn = Button(
    style=ButtonStyle.DANGER,
    label="Close Chat",
    custom_id="close_chat_btn"
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

    # try:
    #     gpt_bot = (await guild.search_members(GPT_BOT_NAME))[0]
    # except IndexError:
    #     print(f'GPT Bot not found. \nLooking for: {GPT_BOT_NAME}')

    await gpt_thread.add_member(member)
    # await gpt_thread.add_member(gpt_bot)

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

    await component_context.edit(content=f"Chat successfully reset {gpt_thread.mention}", components=[])


@bot.component('deny')
async def do_nothing(component_context: ComponentContext) -> None:
    await component_context.edit(content="Ok. If you want to reset the chat, use the command `/chat close`", components=[])


@bot.component('new_chat_btn')
async def new_chat(component_context: ComponentContext) -> None:
    guild = await component_context.get_guild()
    threads = await guild.get_all_active_threads()
    user = component_context.author

    gpt_thread = next((c for c in threads if c.name == f'{user.username} - ChatGPT'), None)
    if gpt_thread:  # thread already exists:
        await component_context.send(
            f'There is an existing chat already: {gpt_thread.mention}\nDo you want to delete it and start over?',
            components=interactions.spread_to_rows(confirm, deny),
            ephemeral=True)
    else:
        gpt_thread = await create_gpt_thread(guild, user)

        await component_context.send(
            f'Room created! Enjoy your chat with ChatGPT {gpt_thread.mention}',
            ephemeral=True)


@bot.component('close_chat_btn')
async def close_chat(component_context: ComponentContext) -> None:
    guild = await component_context.get_guild()
    threads = await guild.get_all_active_threads()
    user = component_context.author

    gpt_thread = next((c for c in threads if c.name == f'{user.username} - ChatGPT'), None)

    if gpt_thread:
        await gpt_thread.delete()
        await component_context.send(
            'Chat successfully deleted',
            ephemeral=True)
    else:
        await component_context.send(
            'I didn\'t find an active chat with ChatGPT',
            ephemeral=True)


# @bot.command(name='send_welcome')
# async def send_welcome(command_context: CommandContext):
#     channel = await command_context.get_channel()
#
#     await channel.send(
#         embeds=interactions.Embed(
#             color=0xe6b400,
#             title="Welcome to the ChatGPT Channel",
#             description="\n\nUse the buttons below to start a new chat with ChatGPT",
#             thumbnail=interactions.EmbedImageStruct(
#                 url="https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/chatgpt-icon.png"
#             )
#         ),
#         components=interactions.spread_to_rows(new_chat_btn, close_chat_btn)
#     )
#
#     await command_context.send("message sent", ephemeral=True)


@bot.command(name='chat')
async def base_chat(command_context: CommandContext):
    channel = await command_context.get_channel()
    if channel.name != 'chatgpt' and not channel.name.endswith('ChatGPT'):
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
async def chat_close(command_context: CommandContext, base_res: BaseResult) -> None:
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
async def chat_new(command_context: CommandContext, base_res: BaseResult) -> None:
    guild = base_res.result['guild']
    gpt_thread = base_res.result['gpt_thread']
    user = base_res.result['user']

    if gpt_thread:  # thread already exists:
        await command_context.send(
            f'There is an existing chat already: {gpt_thread.mention}\nDo you want to delete it and start over?',
            components=interactions.spread_to_rows(confirm, deny),
            ephemeral=True)
    else:
        gpt_thread = await create_gpt_thread(guild, user)

        await command_context.send(
            f'Room created! Enjoy your chat with ChatGPT {gpt_thread.mention}',
            ephemeral=True)


# @bot.command(description="Generate an image based on the prompt")
# @interactions.option("Prompt for the image")
# @interactions.option("The resolution of the image",
#                      choices=[
#                          interactions.Choice(name="High", value="1024x1024"),
#                          interactions.Choice(name="Medium", value="512x512"),
#                          interactions.Choice(name="Low", value="256x256")
#                      ])
# async def generate_image(command_context: CommandContext, prompt: str, resolution: str) -> None:
#     await command_context.defer(ephemeral=True)
#     try:
#         img_url = await response_handler.handle_image_response(prompt, resolution)
#     except Exception as e:
#         await command_context.send(f'Something went wrong, please try again.\n\n>>> {e}', ephemeral=True)
#
#     await command_context.send(
#         embeds=interactions.Embed(
#             title=prompt,
#             image=interactions.EmbedImageStruct(
#                 url=img_url
#             )
#         ),
#         ephemeral=True
#     )

bot.start()
