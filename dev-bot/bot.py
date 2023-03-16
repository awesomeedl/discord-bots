import os
import interactions
from interactions import CommandContext
import response_handler

bot = interactions.Client(token=os.getenv("DEV_BOT_TOKEN"))


@bot.command(description="Generate an image based on the prompt")
@interactions.option("Prompt for the image")
@interactions.option("The resolution of the image",
                     choices=[
                         interactions.Choice(name="High", value="1024x1024"),
                         interactions.Choice(name="Medium", value="512x512"),
                         interactions.Choice(name="Low", value="256x256")
                     ])
async def generate_image(command_context: CommandContext, prompt: str, resolution: str) -> None:
    await command_context.defer(ephemeral=True)
    try:
        img_url = await response_handler.handle_image_response(prompt, resolution)
    except Exception as e:
        await command_context.send(f'Something went wrong, please try again.\n\n>>> {e}', ephemeral=True)

    await command_context.send(
        embeds=interactions.Embed(
            title=prompt,
            image=interactions.EmbedImageStruct(
                url=img_url
            )
        ),
        ephemeral=True
    )


bot.start()
