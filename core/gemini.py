from __future__ import annotations

from collections.abc import Iterator

from google import genai
from google.genai import types

# 利用可能なモデルは Google 側で更新されるため、必要に応じてここを編集する
MODELS = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]
DEFAULT_MODEL = MODELS[0]


def stream_generate(
    prompt: str,
    *,
    system: str,
    api_key: str,
    model: str,
    temperature: float,
) -> Iterator[str]:
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
    )
    for chunk in client.models.generate_content_stream(
        model=model, contents=prompt, config=config
    ):
        if chunk.text:
            yield chunk.text
