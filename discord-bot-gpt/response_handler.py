import openai
import os

openai.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL')


async def handle_response(message: str, chat_history: list[dict[str, str]]) -> str:

    try:
        completion = await openai.ChatCompletion.acreate(
            model=OPENAI_MODEL,
            messages=chat_history + [{"role": "user", "content": message}])
    except Exception:
        raise

    return completion.choices[0].message.content


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



