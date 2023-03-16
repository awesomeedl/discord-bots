import interactions
from interactions import CommandContext
import os
import requests

MANGA_POST_URL = os.getenv('MANGA_POST_URL')

# Myself
bot = interactions.Client(token=os.getenv('HELPER_BOT_TOKEN'))

@bot.command(
    name='subscribe_manga',
    description='Subscribe a manga on Manhuagui',
)
@interactions.option(
    name='manga id',
    type=interactions.OptionType.INTEGER
)
async def subscribe_manga(command_context: CommandContext) -> None:
    await requests.post(url=MANGA_POST_URL, json={})


bot.start()
