import openai
import os

openai.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL')


async def handle_response(message: str, chat_history: list[dict[str, str]]) -> str:

    completion = await openai.ChatCompletion.acreate(
        model=OPENAI_MODEL,
        messages=chat_history + [{"role": "user", "content": message}]
    )

    return completion.choices[0].message.content




