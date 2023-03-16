import openai
import os

openai.api_key = os.getenv('OPENAI_API_KEY')


async def handle_image_response(prompt: str, resolution: str) -> str:

    try:
        image = await openai.Image.acreate(
            prompt=prompt,
            n=1,
            size=resolution
        )
    except Exception:
        raise

    return image.data[0].url




