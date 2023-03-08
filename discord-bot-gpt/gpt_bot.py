import os
import interactions
import response_handler

char_limit = 1900

# Myself
bot: interactions.Client = interactions.Client(token=os.getenv("GPT_BOT_TOKEN"))


async def get_message_history(channel: interactions.Channel) -> list[dict[str, str]]:
    message_history = []

    async for message in channel.history(
            maximum=19,
            check=lambda m: m.type in {interactions.MessageType.DEFAULT, interactions.MessageType.REPLY}):
        role = "assistant" if message.author == await bot.get_self_user() else "user"
        message_history.append({"role": role, "content": message.content})

    return list(reversed(message_history))


async def send_reply(message: interactions.Message) -> None:
    channel = await message.get_channel()
    await channel.typing

    message_history = await get_message_history(channel)
    response = await response_handler.handle_response(message.content, message_history)

    # Response is ok, send directly
    if len(response) <= char_limit:
        await message.reply(response)
        return

    # Response is too long
    # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
    if "```" not in response:
        response_chunks = [response[i:i + char_limit] for i in range(0, len(response), char_limit)]

        for chunk in response_chunks:
            await message.reply(chunk)
        return

    # Code block exists
    parts = response.split("```")

    for i in range(0, len(parts)):
        if i % 2 == 0:  # indices that are even are not code blocks

            await message.reply(parts[i])

        # Send the code block in a separate message
        else:  # Odd-numbered parts are code blocks
            code_block = parts[i].split("\n")
            formatted_code_block = ""
            for line in code_block:
                while len(line) > char_limit:
                    # Split the line at the 50th character
                    formatted_code_block += line[:char_limit] + "\n"
                    line = line[char_limit:]
                formatted_code_block += line + "\n"  # Add the line and seperate with new line

            # Send the code block in a separate message
            if len(formatted_code_block) > char_limit + 100:
                code_block_chunks = [formatted_code_block[i:i + char_limit]
                                     for i in range(0, len(formatted_code_block), char_limit)]
                for chunk in code_block_chunks:
                    await message.reply("```" + chunk + "```")
            else:
                await message.reply("```" + formatted_code_block + "```")


@bot.event()
async def on_message_create(message: interactions.api.Message):

    if not (await message.get_channel()).type == interactions.ChannelType.PRIVATE_THREAD:
        return

    if message.author == await bot.get_self_user():
        return

    await send_reply(message)

bot.start()
